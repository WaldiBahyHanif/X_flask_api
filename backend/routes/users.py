from flask import Blueprint, request, jsonify
from db import get_db_connection
import os
from werkzeug.utils import secure_filename

users_bp = Blueprint('users', __name__)

# --- PERBAIKAN LOKASI FOLDER (Sesuai Screenshot) ---
# Mengambil lokasi absolut folder 'backend/static/uploads'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Pastikan folder ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 1. API GET USER PROFILE ---
@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, username, full_name, avatar_url, bio, location, created_at FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({'error': 'User not found'}), 404

    # Hitung Statistik
    cursor.execute("SELECT COUNT(*) as count FROM follows WHERE followed_id = %s", (user_id,))
    followers = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM follows WHERE follower_id = %s", (user_id,))
    following = cursor.fetchone()['count']
    
    conn.close()

    user['stats'] = {
        'followers': followers,
        'following': following
    }
    
    return jsonify(user)

# --- 2. API UPDATE PROFILE ---
@users_bp.route('/update', methods=['POST'])
def update_profile():
    user_id = request.form.get('user_id')
    bio = request.form.get('bio')
    location = request.form.get('location')
    file = request.files.get('avatar')

    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # LOGIKA UPDATE GAMBAR
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            import time
            unique_filename = f"{int(time.time())}_{filename}"
            
            # 1. Simpan file fisik ke backend/static/uploads/
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            # 2. Simpan URL browser ke database (Pakai /static/...)
            db_avatar_url = f"/uploads/{unique_filename}"
            
            sql = "UPDATE users SET bio = %s, location = %s, avatar_url = %s WHERE id = %s"
            cursor.execute(sql, (bio, location, db_avatar_url, user_id))
        
        else:
            # Update teks saja
            sql = "UPDATE users SET bio = %s, location = %s WHERE id = %s"
            cursor.execute(sql, (bio, location, user_id))

        conn.commit()
        
        # Ambil data terbaru untuk respon balik
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, full_name, avatar_url, bio, location FROM users WHERE id = %s", (user_id,))
        updated_user = cursor.fetchone()
        
        conn.close()
        return jsonify({'message': 'Profile updated!', 'user': updated_user})

    except Exception as e:
        conn.rollback()
        conn.close()
        print("Error Update:", e)
        return jsonify({'error': str(e)}), 500