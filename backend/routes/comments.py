from flask import Blueprint, jsonify, request
from db import get_db_connection

comments_bp = Blueprint('comments', __name__)

# --- 1. AMBIL KOMENTAR (DENGAN TOTAL LIKE & MENTION) ---
@comments_bp.route('/<int:tweet_id>', methods=['GET'])
def get_comments(tweet_id):
    # Kita butuh ID user yang login untuk cek apakah dia like komen ini
    my_id = request.args.get('my_id') 

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Query lebih canggih: Ambil komentar + Hitung Like + Cek Like Kita
        sql = """
            SELECT 
                comments.*, 
                users.username, users.full_name, users.avatar_url,
                (SELECT COUNT(*) FROM comment_likes WHERE comment_likes.comment_id = comments.id) as total_likes
            FROM comments
            JOIN users ON comments.user_id = users.id
            WHERE comments.tweet_id = %s
            ORDER BY comments.created_at ASC
        """
        cursor.execute(sql, (tweet_id,))
        comments = cursor.fetchall()
        
        # Cek manual status 'is_liked'
        for c in comments:
            c['is_liked'] = False
            if my_id:
                cursor.execute("SELECT * FROM comment_likes WHERE user_id = %s AND comment_id = %s", (my_id, c['id']))
                if cursor.fetchone():
                    c['is_liked'] = True

        return jsonify({"status": "Sukses", "data": comments}), 200
    finally:
        cursor.close()
        conn.close()

# --- 2. KIRIM KOMENTAR ---
@comments_bp.route('/', methods=['POST'])
def post_comment():
    data = request.json
    user_id = data.get('user_id')
    tweet_id = data.get('tweet_id')
    content = data.get('content')
    parent_id = data.get('parent_id')

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

# --- 3. LIKE KOMENTAR (FITUR BARU) ---
@comments_bp.route('/like', methods=['POST'])
def toggle_comment_like():
    data = request.json
    user_id = data.get('user_id')
    comment_id = data.get('comment_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Cek sudah like belum?
        cursor.execute("SELECT * FROM comment_likes WHERE user_id = %s AND comment_id = %s", (user_id, comment_id))
        if cursor.fetchone():
            cursor.execute("DELETE FROM comment_likes WHERE user_id = %s AND comment_id = %s", (user_id, comment_id))
            action = "unliked"
        else:
            cursor.execute("INSERT INTO comment_likes (user_id, comment_id) VALUES (%s, %s)", (user_id, comment_id))
            action = "liked"
        conn.commit()
        return jsonify({"status": "Sukses", "action": action}), 200
    finally:
        cursor.close()
        conn.close()

# --- 4. HAPUS KOMENTAR ---
@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM comments WHERE id = %s", (comment_id,))
        conn.commit()
        return jsonify({"status": "Sukses", "pesan": "Komentar dihapus"}), 200
    except Exception as e:
        return jsonify({"status": "Gagal", "pesan": str(e)}), 500
    finally:
        cursor.close()
        conn.close()