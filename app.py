from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin SDK safely
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
SECRET_KEY = "arbab_rewards_secure_key_99"

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
        return jsonify({"error": "Invalid parameters: 'userid' and numeric 'reward' are required"}), 400

    if not userid:
        return jsonify({"error": "Invalid parameters: 'userid' and numeric 'reward' are required"}), 400

    try:
        user_ref = db.collection('users').document(userid)
        user_snapshot = user_ref.get()

        if not user_snapshot.exists:
            return jsonify({"error": "User not found in Firestore database"}), 404

        user_data = user_snapshot.to_dict()
        current_balance = user_data.get('availableBalance', 0)
        current_total = user_data.get('totalEarnings', 0)

        # Update user balance securely via Firebase Admin SDK
        user_ref.update({
            'availableBalance': current_balance + reward_amount,
            'totalEarnings': current_total + reward_amount,
            'lastUpdated': firestore.SERVER_TIMESTAMP
        })

        # Add transaction ledger entry
        db.collection('transactions').add({
            'userId': userid,
            'type': 'external_postback',
            'amount': reward_amount,
            'description': 'Earned via external postback offer/task',
            'createdAt': firestore.SERVER_TIMESTAMP
        })

        return "SUCCESS: Balance credited and logged successfully.", 200

    except Exception as err:
        print("Postback Processing Error:", err)
        return jsonify({"error": str(err)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Rewards Hub Python Backend Server is Running Live & Secure!", 200

if __name__ == '__main__':
    app.run(port=3000)
        
