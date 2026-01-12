from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from db import get_db_connection
import os

# Import Blueprints
from routes.auth import auth_bp
from routes.tweets import tweets_bp
from routes.users import users_bp
from routes.comments import comments_bp

app = Flask(__name__, static_folder='../frontend')
app.config['SECRET_KEY'] = 'rahasia-donk' # Dibutuhkan untuk SocketIO
CORS(app)

# --- 1. INISIALISASI SOCKET IO ---
socketio = SocketIO(app, cors_allowed_origins="*")

# Buat folder upload
os.makedirs('static/uploads', exist_ok=True)

# Register API
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(tweets_bp, url_prefix='/api/tweets')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(comments_bp, url_prefix='/api/comments')

# --- 2. LOGIKA CHAT REAL-TIME (SOCKET) ---

@socketio.on('connect')
def handle_connect():
    print('User connected')

# Saat user membuka halaman chat, dia wajib 'Absen' (Join Room) pakai ID-nya sendiri
@socketio.on('join')
def on_join(data):
    user_id = data['user_id']
    room = f"user_{user_id}" # Contoh nama room: "user_1"
    join_room(room)
    print(f"User {user_id} masuk ke room {room}")

# Saat user mengirim pesan
@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    msg_content = data['message']

    # A. Simpan ke Database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (%s, %s, %s)", 
                   (sender_id, receiver_id, msg_content))
    conn.commit()
    cursor.close()
    conn.close()

    # B. Kirim Real-Time ke Penerima (jika dia sedang online)
    receiver_room = f"user_{receiver_id}"
    emit('new_message', {
        'sender_id': sender_id,
        'message': msg_content,
        'is_self': False
    }, room=receiver_room)

    # C. Kirim Real-Time ke Pengirim (biar muncul di layar sendiri)
    emit('new_message', {
        'sender_id': sender_id,
        'message': msg_content,
        'is_self': True
    }, room=f"user_{sender_id}")

# --- 3. API UNTUK MENGAMBIL RIWAYAT CHAT & DAFTAR USER ---

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    user1 = request.args.get('user1') # Kita
    user2 = request.args.get('user2') # Lawan bicara
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ambil pesan bolak-balik antara user1 dan user2
    sql = """
        SELECT * FROM messages 
        WHERE (sender_id = %s AND receiver_id = %s) 
           OR (sender_id = %s AND receiver_id = %s)
        ORDER BY created_at ASC
    """
    cursor.execute(sql, (user1, user2, user2, user1))
    messages = cursor.fetchall()
    conn.close()
    return jsonify(messages)

@app.route('/api/users/all', methods=['GET'])
def get_all_users():
    my_id = request.args.get('my_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Ambil semua user KECUALI diri sendiri
    cursor.execute("SELECT id, username, full_name, avatar_url FROM users WHERE id != %s", (my_id,))
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

# --- ROUTE HALAMAN ---
@app.route('/')
def halaman_utama():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def buka_file(filename):
    return send_from_directory('../frontend', filename)

if __name__ == '__main__':
    # PENTING: Ganti app.run jadi socketio.run !!
    socketio.run(app, debug=True, port=5000)