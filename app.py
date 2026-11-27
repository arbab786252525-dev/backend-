from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app)

# Initialize Firebase Admin using serviceAccountKey.json
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
SECRET_KEY = "arbab_rewards_secure_key_99"

# 1. Postback Endpoint
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

        # Firestore Transaction to update balance and log transaction safely
        @firestore.transactional
        def update_in_transaction(transaction, user_ref, reward_amount, userid):
            user_snapshot = user_ref.get(transaction=transaction)
            if not user_snapshot.exists:
                raise Exception("User not found in Firestore database")
            
            user_data = user_snapshot.to_dict()
            current_balance = user_data.get('availableBalance', 0)
            current_total = user_data.get('totalEarnings', 0)

            # Update balances
            transaction.update(user_ref, {
                'availableBalance': current_balance + reward_amount,
                'totalEarnings': current_total + reward_amount,
                'lastUpdated': firestore.SERVER_TIMESTAMP
            })

            # Add ledger entry
            tx_ref = db.collection('transactions').document()
            transaction.set(tx_ref, {
                'userId': userid,
                'type': 'external_postback',
                'amount': reward_amount,
                'description': 'Earned via external postback offer/task',
                'createdAt': firestore.SERVER_TIMESTAMP
            })

        transaction = db.transaction()
        update_in_transaction(transaction, user_ref, reward_amount, userid)

        return "SUCCESS: Balance credited and logged successfully.", 200

    except Exception as err:
        print("Postback Processing Error:", err)
        return jsonify({"error": str(err)}), 500

# 2. Health Check Route
@app.route('/', methods=['GET'])
def home():
    return "Rewards Hub Python Backend Server is Running Live & Secure!", 200

if __name__ == '__main__':
    app.run(port=3000)
