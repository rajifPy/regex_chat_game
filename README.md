# Regex Chat Game (Levels & Lives)

Perubahan utama:
- Menambahkan 3 level.
- Pemain memiliki total 3 nyawa (lives) untuk seluruh permainan.
- Setiap jawaban salah mengurangi 1 nyawa. Nyawa habis -> game over.
- Menyelesaikan level akan lanjut ke level berikutnya sampai level 3, kemudian menang.

## Cara menjalankan (sama seperti README sebelumnya)
1. Buat virtualenv
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Jalankan
   ```
   python app.py
   ```
3. Buka http://127.0.0.1:5000
