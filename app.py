from flask import Flask, render_template, request, jsonify, session
import random, re
from puzzles import PUZZLES
from flask_session import Session

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'change_this_to_a_secure_random_value'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

MAX_PATTERN_LEN = 120
MAX_MATCHES = 200
TOTAL_LEVELS = 3
STARTING_LIVES = 3

def compute_expected(pattern, text):
    try:
        if len(pattern) > MAX_PATTERN_LEN:
            return {'error': 'Pattern terlalu panjang.'}
        prog = re.compile(pattern)
        raw = prog.findall(text)
        matches = []
        for r in raw:
            if isinstance(r, tuple):
                matches.append(''.join(r).strip())
            else:
                matches.append(str(r).strip())
        matches = [m for m in matches if m != '']
        matches = list(dict.fromkeys(matches))
        if len(matches) > MAX_MATCHES:
            return {'error': 'Hasil matches terlalu banyak.'}
        return {'matches': matches}
    except re.error as e:
        return {'error': f'Regex error: {e}'}

def choose_puzzle_for_level(level):
    # collect indices for puzzles matching the requested level
    indices = [i for i, p in enumerate(PUZZLES) if p.get('level', 1) == level]
    if not indices:
        return None, None  # no puzzle for this level
    used_by_level = session.get('used_indices', {})
    used = used_by_level.get(str(level), [])
    remaining = [i for i in indices if i not in used]
    if not remaining:
        # reset used for this level
        used = []
        remaining = indices.copy()
    idx = random.choice(remaining)
    # mark used
    used.append(idx)
    used_by_level[str(level)] = used
    session['used_indices'] = used_by_level
    return idx, PUZZLES[idx]

@app.before_request
def ensure_user():
    import uuid
    if 'uid' not in session:
        session['uid'] = str(uuid.uuid4())
    if 'used_indices' not in session:
        session['used_indices'] = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new', methods=['POST'])
def new_game():
    # start a new game: reset level and lives, pick level 1 puzzle
    session['level'] = 1
    session['lives'] = STARTING_LIVES
    session['status'] = 'playing'
    session['used_indices'] = session.get('used_indices', {})  # keep previous but per-level prevents repeats
    idx, p = choose_puzzle_for_level(session['level'])
    if p is None:
        return jsonify({'ok': False, 'error': 'Tidak ada puzzle untuk level ini.'}), 500
    comp = compute_expected(p['pattern'], p['text'])
    if 'error' in comp:
        return jsonify({'ok': False, 'error': comp['error']}), 400
    session['pattern'] = p['pattern']
    session['text'] = p['text']
    session['expected'] = comp['matches']
    return jsonify({
        'ok': True,
        'pattern': p['pattern'],
        'text': p['text'],
        'level': session['level'],
        'lives': session['lives'],
        'total_levels': TOTAL_LEVELS
    })

@app.route('/api/answer', methods=['POST'])
def answer():
    if 'status' not in session or session.get('status') != 'playing':
        return jsonify({'ok': False, 'error': 'Tidak ada permainan aktif. Tekan Mulai Puzzle Baru.'}), 400

    data = request.get_json() or {}
    player_text = data.get('answer', '')
    cand = [x.strip() for x in re.split(r'[,\n]+', player_text) if x.strip()!='']
    cand_norm = [x.lower() for x in cand]

    expected = session.get('expected', [])
    expected_norm = [x.lower() for x in expected]

    # check correctness: exact set match
    if set(cand_norm) == set(expected_norm):
        # correct for this level
        current_level = session.get('level', 1)
        if current_level >= TOTAL_LEVELS:
            session['status'] = 'won'
            return jsonify({
                'ok': True,
                'result': 'won_game',
                'message': 'Yeay! Kamu lulus semua level, cowok paham regexnya. Hubungan aman 😉',
                'level': current_level,
                'lives': session.get('lives', 0)
            })
        else:
            # advance to next level and auto-send next puzzle
            session['level'] = current_level + 1
            idx, p = choose_puzzle_for_level(session['level'])
            if p is None:
                session['status'] = 'won'
                return jsonify({'ok': True, 'result': 'won_game', 'message': 'Semua level selesai (tidak ada puzzle berikutnya).'})
            comp = compute_expected(p['pattern'], p['text'])
            if 'error' in comp:
                return jsonify({'ok': False, 'error': comp['error']}), 400
            session['pattern'] = p['pattern']
            session['text'] = p['text']
            session['expected'] = comp['matches']
            return jsonify({
                'ok': True,
                'result': 'level_up',
                'message': f'Benar! Lanjut ke level {session["level"]}.',
                'level': session['level'],
                'lives': session.get('lives', 0),
                'pattern': p['pattern'],
                'text': p['text'],
                'total_levels': TOTAL_LEVELS
            })
    else:
        # wrong answer: lose one life
        session['lives'] = session.get('lives', 0) - 1
        lives_left = session['lives']
        if lives_left <= 0:
            session['status'] = 'gameover'
            return jsonify({
                'ok': True,
                'result': 'gameover',
                'message': 'Salah dan nyawa habis. Game over — putus.',
                'lives': 0,
                'expected': session.get('expected', [])
            })
        else:
            return jsonify({
                'ok': True,
                'result': 'wrong',
                'message': f'Salah. Kamu kehilangan 1 nyawa. Sisa nyawa: {lives_left}',
                'lives': lives_left,
                'level': session.get('level', 1)
            })

@app.route('/api/state', methods=['GET'])
def state():
    return jsonify({
        'pattern': session.get('pattern'),
        'text': session.get('text'),
        'level': session.get('level'),
        'lives': session.get('lives'),
        'status': session.get('status'),
        'total_levels': TOTAL_LEVELS
    })

if __name__ == '__main__':
    app.run(debug=True)
