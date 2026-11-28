from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

SECRET_KEY = "arbab_rewards_secure_key_99"

# ہوم روٹ یہ چیک کرنے کے लिए کہ سرور زندہ ہے یا نہیں
@app.route('/', methods=['GET'])
def home():
    return "Rewards Hub Custom Backend is Running Live & Secure!", 200

# سائن اپ روٹ (نیا اکاؤنٹ بنانے کے لیے)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json or {}
    userid = data.get('userid')
    email = data.get('email')
    password = data.get('password')

    if not userid or not email or not password:
        return jsonify({"error": "All fields (userid, email, password) are required"}), 400

    # یہاں ہم آگے JSONBin یا ڈیٹا بیس کا لاجک فٹ کریں گے
    return jsonify({
        "status": "SUCCESS",
        "message": f"User {userid} registered successfully!",
        "userid": userid
    }), 200

# لاگ ان روٹ
@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # یہاں لاگ ان وریفیکیشن آئے گی
    return jsonify({
        "status": "SUCCESS",
        "message": "Login successful!"
    }), 200

# پوسٹ بیک روٹ (بیلنس ایڈ کرنے کے لیے)
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

    # یہاں پوسٹ بیک کا بیلنس اپڈیٹ کا لاجک آئے گا
    return f"SUCCESS: Balance {reward_amount} credited for user {userid}.", 200

if __name__ == '__main__':
    app.run(port=3000)
        
