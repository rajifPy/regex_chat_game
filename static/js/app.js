const chatEl = document.getElementById('chat');
const btnNew = document.getElementById('btnNew');
const sendBtn = document.getElementById('send');
const answerInput = document.getElementById('answer');
const levelEl = document.getElementById('level');
const livesEl = document.getElementById('lives');
const totalEl = document.getElementById('total');

function appendBubble(who, text) {
  const div = document.createElement('div');
  div.className = 'row';
  const bubble = document.createElement('div');
  bubble.className = 'bubble ' + (who === 'girl' ? 'girl' : 'boy');
  bubble.innerText = text;
  div.appendChild(bubble);
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

async function newPuzzle() {
  const res = await fetch('/api/new', { method: 'POST' });
  const data = await res.json();
  if (!data.ok) { alert('Error: ' + (data.error || '')); return; }
  // set meta
  levelEl.innerText = data.level;
  livesEl.innerText = data.lives;
  totalEl.innerText = data.total_levels;
  // show conversation: girl sends message (pattern combined with text)
  appendBubble('girl', `Cewek: "${data.text}"\n(regex: ${data.pattern})`);
  appendBubble('girl', `Cewek: Tebak apa yang dicari regex tersebut. Jawab dengan daftar hasil, pisahkan koma jika banyak.`);
}

async function sendAnswer() {
  const answer = answerInput.value.trim();
  if (!answer) return;
  appendBubble('boy', `Cowok: ${answer}`);
  answerInput.value = '';
  const res = await fetch('/api/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answer })
  });
  const data = await res.json();
  if (!data.ok) { appendBubble('girl', 'Server error: ' + (data.error || '')); return; }

  if (data.result === 'won_game') {
    appendBubble('girl', data.message);
    levelEl.innerText = data.level || totalEl.innerText;
    livesEl.innerText = data.lives || 0;
    appendBubble('girl', 'Selamat! Kamu menang. 🎉');
  } else if (data.result === 'level_up') {
    appendBubble('girl', data.message);
    levelEl.innerText = data.level;
    livesEl.innerText = data.lives;
    appendBubble('girl', `Level ${data.level}: "${data.text}"\n(regex: ${data.pattern})`);
    appendBubble('girl', 'Tebak lagi ya!');
  } else if (data.result === 'wrong') {
    appendBubble('girl', data.message);
    livesEl.innerText = data.lives;
  } else if (data.result === 'gameover') {
    appendBubble('girl', data.message);
    livesEl.innerText = 0;
    appendBubble('girl', `Jawaban yang benar untuk level ini adalah: ${data.expected ? data.expected.join(', ') : '-'}`);
  } else if (data.result === 'correct') {
    // backward compat, though server no longer sends 'correct'
    appendBubble('girl', data.message);
  } else {
    // generic message
    appendBubble('girl', data.message || JSON.stringify(data));
  }
}

function showWinAnimation() {
  const container = document.getElementById("hearts-container");
  container.style.display = "block";
  container.innerHTML = "";

  // munculkan banyak heart jatuh
  for (let i = 0; i < 15; i++) {
    const heart = document.createElement("div");
    heart.innerHTML = "❤️";
    heart.classList.add("falling-heart");
    heart.style.left = Math.random() * 100 + "vw";
    heart.style.animationDelay = Math.random() * 2 + "s";
    container.appendChild(heart);
  }

  setTimeout(() => container.style.display = "none", 4000);
}

function showLoseAnimation() {
  const broken = document.getElementById("broken-heart");
  broken.style.display = "block";

  setTimeout(() => broken.style.display = "none", 2000);
}


btnNew.addEventListener('click', newPuzzle);
sendBtn.addEventListener('click', sendAnswer);
answerInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendAnswer(); });
