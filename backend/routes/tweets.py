import os
import uuid
from flask import Blueprint, jsonify, request, send_from_directory
from db import get_db_connection
from werkzeug.utils import secure_filename

# Hapus import jwt_required dll

tweets_bp = Blueprint('tweets', __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@tweets_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@tweets_bp.route('/', methods=['GET'])
def get_tweets():
    my_id = request.args.get('my_id') 
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        sql = """
            SELECT 
                tweets.id, tweets.content, tweets.image_url, tweets.created_at,
                users.username, users.full_name, users.avatar_url,
                (SELECT COUNT(*) FROM likes WHERE likes.tweet_id = tweets.id) as total_likes,
                (SELECT COUNT(*) FROM comments WHERE comments.tweet_id = tweets.id) as total_comments
            FROM tweets
            JOIN users ON tweets.user_id = users.id
            ORDER BY tweets.created_at DESC
        """
        cursor.execute(sql)
        tweets = cursor.fetchall()
        
        base_url = request.host_url + 'api/tweets/uploads/'
        for tweet in tweets:
            if tweet['image_url']:
                tweet['image_url'] = base_url + tweet['image_url']
            tweet['is_liked'] = False
            if my_id:
                cursor.execute("SELECT * FROM likes WHERE user_id = %s AND tweet_id = %s", (my_id, tweet['id']))
                if cursor.fetchone():
                    tweet['is_liked'] = True
        return jsonify({"status": "Sukses", "data": tweets}), 200
    finally:
        cursor.close()
        conn.close()

# --- POST TWEET (TANPA JWT) ---
@tweets_bp.route('/', methods=['POST'])
# @jwt_required() <-- GEMBOK DIHAPUS
def create_tweet():
    # Ambil user_id dari kiriman Frontend
    user_id = request.form.get('user_id') 
    content = request.form.get('content')
    file = request.files.get('file')

    filename_to_save = None
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = str(uuid.uuid4()) + "." + ext
        file.save(os.path.join(UPLOAD_FOLDER, unique_filename))
        filename_to_save = unique_filename

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tweets (user_id, content, image_url) VALUES (%s, %s, %s)", 
                       (user_id, content, filename_to_save))
        conn.commit()
        return jsonify({"status": "Sukses", "pesan": "Tweet terkirim!"}), 201
    finally:
        cursor.close()
        conn.close()

# (Route like dan delete di bawah biarkan saja, sudah aman)
@tweets_bp.route('/like', methods=['POST'])
def toggle_like():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    # ... (kode like tetap sama) ...
    # Biar tidak kepanjangan, bagian like/delete tidak saya ubah karena tidak pakai JWT
    try:
        cursor.execute("SELECT * FROM likes WHERE user_id = %s AND tweet_id = %s", (data['user_id'], data['tweet_id']))
        if cursor.fetchone():
            cursor.execute("DELETE FROM likes WHERE user_id = %s AND tweet_id = %s", (data['user_id'], data['tweet_id']))
            action = "unliked"
        else:
            cursor.execute("INSERT INTO likes (user_id, tweet_id) VALUES (%s, %s)", (data['user_id'], data['tweet_id']))
            action = "liked"
        conn.commit()
        return jsonify({"status": "Sukses", "action": action}), 200
    finally:
        cursor.close()
        conn.close()