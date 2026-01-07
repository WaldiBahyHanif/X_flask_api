from flask import Blueprint, jsonify, request
from db import get_db_connection

comments_bp = Blueprint('comments', __name__)

# --- 1. AMBIL KOMENTAR UNTUK TWEET TERTENTU ---
@comments_bp.route('/<int:tweet_id>', methods=['GET'])
def get_comments(tweet_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Ambil komentar beserta nama user yang komen
        sql = """
            SELECT comments.*, users.username, users.full_name, users.avatar_url
            FROM comments
            JOIN users ON comments.user_id = users.id
            WHERE comments.tweet_id = %s
            ORDER BY comments.created_at ASC
        """
        cursor.execute(sql, (tweet_id,))
        comments = cursor.fetchall()
        return jsonify({"status": "Sukses", "data": comments}), 200
    finally:
        cursor.close()
        conn.close()

# --- 2. KIRIM KOMENTAR / BALASAN ---
@comments_bp.route('/', methods=['POST'])
def post_comment():
    data = request.json
    user_id = data.get('user_id')
    tweet_id = data.get('tweet_id')
    content = data.get('content')
    parent_id = data.get('parent_id') # Kalau null berarti komen biasa, kalau ada angka berarti reply

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO comments (user_id, tweet_id, content, parent_id) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (user_id, tweet_id, content, parent_id))
        conn.commit()
        return jsonify({"status": "Sukses", "pesan": "Komentar terkirim!"}), 201
    finally:
        cursor.close()
        conn.close()