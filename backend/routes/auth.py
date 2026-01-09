from flask import Blueprint, request, jsonify
from db import get_db_connection
# Kita pakai Werkzeug (Bawaan Flask) yang lebih simpel
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

# --- 1. REGISTRASI (DAFTAR) ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')

    # Hash Password pakai Werkzeug (Simpel & Aman)
    hashed_pw = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password, full_name) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_pw, full_name)
        )
        conn.commit()
        return jsonify({"status": "Sukses", "pesan": "Registrasi berhasil!"}), 201
    except Exception as e:
        return jsonify({"status": "Gagal", "pesan": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- 2. LOGIN (MASUK) ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            return jsonify({
                "status": "Sukses",
                "message": "Login berhasil",
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "full_name": user['full_name'],
                    "email": user['email']
                }
            }), 200
        else:
            return jsonify({"status": "Gagal", "pesan": "Email atau password salah"}), 401
    finally:
        cursor.close()
        conn.close()