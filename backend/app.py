from flask import Flask, send_from_directory
from flask_cors import CORS
import os

# Import Blueprints (Fitur-fitur yang sudah kita buat)
from routes.auth import auth_bp
from routes.tweets import tweets_bp
from routes.users import users_bp
from routes.comments import comments_bp

# --- KONFIGURASI PENTING ---
# Kita beri tahu Flask kalau folder HTML ada di '../frontend' (mundur satu langkah, lalu masuk frontend)
app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Buat folder upload jika belum ada
os.makedirs('static/uploads', exist_ok=True)

# Register API (Otak Backend)
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(tweets_bp, url_prefix='/api/tweets')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(comments_bp, url_prefix='/api/comments')

# --- ROUTE UNTUK MEMBUKA WEBSITE ---

# 1. Saat link http://127.0.0.1:5000 dibuka -> Muncul index.html (Login)
@app.route('/')
def halaman_utama():
    return send_from_directory('../frontend', 'index.html')

# 2. Untuk membuka file lain (register.html, feed.html, style.css, gambar, dll)
@app.route('/<path:filename>')
def buka_file(filename):
    return send_from_directory('../frontend', filename)

if __name__ == '__main__':
    print("✅ Server Berjalan! Klik link ini: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)