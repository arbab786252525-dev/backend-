from flask import Flask, request, jsonify
from flask_cors import CORS
import urllib.request
import json
import hashlib

app = Flask(__name__)
CORS(app)

# Supabase Configuration (Integrated)
SUPABASE_URL = "https://xhzicbwqkzqstuzukizs.supabase.co"
SUPABASE_KEY = "Sb_publishable_50-wiYfCl-IXmUQoNTajUg_6ckJvjr1"
SECRET_KEY = "arbab_rewards_secure_key_99"

@app.route('/', methods=['GET'])
def home():
    return "Rewards Hub Custom Backend with Supabase is Running Live!", 200

# 1. سائن اپ روٹ
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json or {}
    userid = data.get('userid')
    email = data.get('email')
    password = data.get('password')

    if not userid or not email or not password:
        return jsonify({"error": "All fields (userid, email, password) are required"}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    payload = json.dumps({
        "id": userid,
        "email": email,
        "password": hashed_password,
        "balance": 0.0,
        "totalEarnings": 0.0
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/users",
        data=payload,
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as response:
            return jsonify({"status": "SUCCESS", "message": f"User {userid} registered successfully!"}), 200
    except urllib.error.HTTPError as e:
        error_message = e.read().decode('utf-8')
        return jsonify({"error": "User already exists or database error", "details": error_message}), 400

# 2. لاگ ان روٹ
@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    userid = data.get('userid')
    password = data.get('password')

    if not userid or not password:
        return jsonify({"error": "Userid and password are required"}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/users?id=eq.{userid}&select=id,password,balance",
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
    )

    try:
        with urllib.request.urlopen(req) as response:
            users = json.loads(response.read().decode('utf-8'))
            if not users:
                return jsonify({"error": "User not found!"}), 404
            
            user = users[0]
            if user.get('password') == hashed_password:
                return jsonify({"status": "SUCCESS", "message": "Login successful!", "balance": user.get('balance', 0)}), 200
            else:
                return jsonify({"error": "Invalid password!"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. پوسٹ بیک روٹ (بیلنس ایڈ کرنے کے لیے)
@app.route('/postback', methods=['GET'])
def postback():
    userid = request.args.get('userid')
    reward_str = request.args.get('reward')
    key = request.args.get('key')

    if key != SECRET_KEY:
        return jsonify({"error": "Unauthorized: Invalid secret postback key"}), 403

    try:
        reward_amount = float(reward_str)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid parameters: numeric 'reward' is required"}), 400

    if not userid:
        return jsonify({"error": "Invalid parameters: 'userid' is required"}), 400

    fetch_req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/users?id=eq.{userid}&select=balance,totalEarnings",
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
    )

    try:
        with urllib.request.urlopen(fetch_req) as resp:
            users = json.loads(resp.read().decode('utf-8'))
            
            if users:
                current_balance = float(users[0].get('balance', 0.0))
                current_total = float(users[0].get('totalEarnings', 0.0))
                new_balance = current_balance + reward_amount
                new_total = current_total + reward_amount

                update_payload = json.dumps({
                    "balance": new_balance,
                    "totalEarnings": new_total
                }).encode('utf-8')

                update_req = urllib.request.Request(
                    f"{SUPABASE_URL}/rest/v1/users?id=eq.{userid}",
                    data=update_payload,
                    headers={
                        'apikey': SUPABASE_KEY,
                        'Authorization': f'Bearer {SUPABASE_KEY}',
                        'Content-Type': 'application/json',
                        'Prefer': 'return=minimal'
                    },
                    method='PATCH'
                )
                with urllib.request.urlopen(update_req):
                    pass
            else:
                insert_payload = json.dumps({
                    "id": userid,
                    "balance": reward_amount,
                    "totalEarnings": reward_amount
                }).encode('utf-8')

                insert_req = urllib.request.Request(
                    f"{SUPABASE_URL}/rest/v1/users",
                    data=insert_payload,
                    headers={
                        'apikey': SUPABASE_KEY,
                        'Authorization': f'Bearer {SUPABASE_KEY}',
                        'Content-Type': 'application/json',
                        'Prefer': 'return=minimal'
                    },
                    method='POST'
                )
                with urllib.request.urlopen(insert_req):
                    pass

        return f"SUCCESS: Balance {reward_amount} credited for user {userid}.", 200

    except Exception as err:
        print("Postback Error:", err)
        return jsonify({"error": str(err)}), 500

if __name__ == '__main__':
    app.run(port=3000)
    
