from flask import Blueprint, jsonify, request
from db import get_db_connection

users_bp = Blueprint('users', __name__)

# --- 1. CARI USER (SEARCH) ---
@users_bp.route('/search', methods=['GET'])
def search_users():
    keyword = request.args.get('q', '')
    my_id = request.args.get('my_id') # ID kita, biar gak munculin diri sendiri
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Cari user yang namanya mirip keyword, TAPI bukan diri sendiri
        query = "SELECT id, username, full_name FROM users WHERE (username LIKE %s OR full_name LIKE %s) AND id != %s"
        search_term = f"%{keyword}%"
        cursor.execute(query, (search_term, search_term, my_id))
        results = cursor.fetchall()
        
        # Cek status follow untuk setiap hasil pencarian
        for user in results:
            cursor.execute("SELECT * FROM follows WHERE follower_id = %s AND followed_id = %s", (my_id, user['id']))
            is_following = cursor.fetchone()
            user['is_followed'] = True if is_following else False

        return jsonify({"status": "Sukses", "data": results}), 200
    finally:
        cursor.close()
        conn.close()

# --- 2. FOLLOW / UNFOLLOW ---
@users_bp.route('/follow', methods=['POST'])
def toggle_follow():
    data = request.json
    follower_id = data.get('follower_id') # Kita
    followed_id = data.get('followed_id') # Orang yang mau difollow

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Cek apakah sudah follow?
        cursor.execute("SELECT * FROM follows WHERE follower_id = %s AND followed_id = %s", (follower_id, followed_id))
        existing = cursor.fetchone()

        if existing:
            cursor.execute("DELETE FROM follows WHERE follower_id = %s AND followed_id = %s", (follower_id, followed_id))
            action = "unfollowed"
        else:
            cursor.execute("INSERT INTO follows (follower_id, followed_id) VALUES (%s, %s)", (follower_id, followed_id))
            action = "followed"
        
        conn.commit()
        return jsonify({"status": "Sukses", "action": action}), 200
    finally:
        cursor.close()
        conn.close()

# --- 3. STATISTIK PROFIL (Follower & Following) ---
@users_bp.route('/stats/<int:user_id>', methods=['GET'])
def get_stats(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Hitung Followers (Orang yang follow kita)
        cursor.execute("SELECT COUNT(*) FROM follows WHERE followed_id = %s", (user_id,))
        followers_count = cursor.fetchone()[0]

        # Hitung Following (Orang yang kita follow)
        cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = %s", (user_id,))
        following_count = cursor.fetchone()[0]

        return jsonify({
            "status": "Sukses", 
            "followers": followers_count, 
            "following": following_count
        }), 200
    finally:
        cursor.close()
        conn.close()