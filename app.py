from flask import Flask, request, jsonify
from flask_cors import CORS
import urllib.request
import json
import time

app = Flask(__name__)
CORS(app)

PROJECT_ID = "am-smm-panel-1146b"
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
        doc_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{userid}"
        
        # 1. Fetch user document with a strict 5-second timeout so it never hangs
        req = urllib.request.Request(doc_url, method='GET')
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                doc_data = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return jsonify({"error": "User not found in Firestore database"}), 404
            return jsonify({"error": f"Firestore HTTP Error: {e.code}"}), 500
        except Exception as net_err:
            return jsonify({"error": f"Connection Timeout / Network Error: str(net_err)"}), 500

        fields = doc_data.get('fields', {})
        current_balance = float(fields.get('availableBalance', {}).get('doubleValue', fields.get('availableBalance', {}).get('integerValue', 0)))
        current_total = float(fields.get('totalEarnings', {}).get('doubleValue', fields.get('totalEarnings', {}).get('integerValue', 0)))

        new_balance = current_balance + reward_amount
        new_total = current_total + reward_amount
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

        # 2. Update user balance via Firestore REST API
        update_url = f"{doc_url}?updateMask.fieldPaths=availableBalance&updateMask.fieldPaths=totalEarnings&updateMask.fieldPaths=lastUpdated"
        patch_data = {
            "fields": {
                "availableBalance": {"doubleValue": new_balance},
                "totalEarnings": {"doubleValue": new_total},
                "lastUpdated": {"timestampValue": timestamp}
            }
        }

        patch_req = urllib.request.Request(
            update_url, 
            data=json.dumps(patch_data).encode('utf-8'), 
            headers={'Content-Type': 'application/json'}, 
            method='PATCH'
        )
        
        with urllib.request.urlopen(patch_req, timeout=5) as patch_resp:
            pass

        # 3. Add transaction ledger entry
        trans_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/transactions"
        trans_data = {
            "fields": {
                "userId": {"stringValue": userid},
                "type": {"stringValue": "external_postback"},
                "amount": {"doubleValue": reward_amount},
                "description": {"stringValue": "Earned via external postback offer/task"},
                "createdAt": {"timestampValue": timestamp}
            }
        }

        trans_req = urllib.request.Request(
            trans_url, 
            data=json.dumps(trans_data).encode('utf-8'), 
            headers={'Content-Type': 'application/json'}, 
            method='POST'
        )
        
        with urllib.request.urlopen(trans_req, timeout=5) as trans_resp:
            pass

        return "SUCCESS: Balance credited and logged successfully.", 200

    except Exception as err:
        print("Postback Processing Error:", err)
        return jsonify({"error": str(err)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Rewards Hub Lightweight Python Backend is Running Live & Secure!", 200

if __name__ == '__main__':
    app.run(port=3000)
        
