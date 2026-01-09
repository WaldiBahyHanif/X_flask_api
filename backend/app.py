from flask import Flask, send_from_directory
from flask_cors import CORS
import os

# Import Blueprints
from routes.auth import auth_bp
from routes.tweets import tweets_bp
from routes.users import users_bp
from routes.comments import comments_bp

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# --- BAGIAN JWT DIHAPUS ---
# Tidak ada lagi jwt manager atau secret key

# Buat folder upload jika belum ada
os.makedirs('static/uploads', exist_ok=True)

# Register API
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(tweets_bp, url_prefix='/api/tweets')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(comments_bp, url_prefix='/api/comments')

# Route Halaman Web
@app.route('/')
def halaman_utama():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def buka_file(filename):
    return send_from_directory('../frontend', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)