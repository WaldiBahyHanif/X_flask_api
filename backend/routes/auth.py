from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token 
from db import get_db_connection

# Membuat Blueprint (Kelompok Rute)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        if cursor.fetchone():
            return jsonify({"status": "Gagal", "pesan": "Username/Email sudah terdaftar!"}), 400

        hashed_pw = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, email, password, full_name) VALUES (%s, %s, %s, %s)", 
                       (username, email, hashed_pw, full_name))
        conn.commit()
        return jsonify({"status": "Sukses", "pesan": "Akun berhasil dibuat!"}), 201
    finally:
        cursor.close()
        conn.close()

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

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # --- INI BAGIAN BARUNYA ---
            # Kita buat token. Di dalam token kita selipkan ID user (identity)
            access_token = create_access_token(identity=user['id'])
            
            return jsonify({
                "status": "Sukses",
                "message": "Login berhasil",
                "token": access_token,  # <--- Kirim Token
                "user": {               # Data user tetap dikirim buat tampilan profil
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