from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

app = Flask(__name__)
CORS(app)

# Safe Initialization for Vercel Serverless
if not firebase_admin._apps:
    try:
        # If serviceAccountKey.json exists, use it safely
        if os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        else:
            # Fallback direct initialization dict
            cred_dict = {
                "type": "service_account",
                "project_id": "am-smm-panel-1146b",
                "private_key_id": "1146b",
                "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDZmBnuU0ckUG+G\nDGTUmeO9eGFCUCGfcObwah2QGevGVzHk74wfDadPH2HQX/QRnTX9ouEz+zX/5tF4\nbaxrET7BIIOhO1ZrNScPKGEqoE9K4JTDvsNtvYEjz6kIw4iyW5BUWw0jgsAqEeNu\nqqBramqqcTCse7ea50vmmoRrnY58oM9fEIKzNdvD9OZB60PHlobBzki4wybecRXb\nkmmzgmZkHRtnv3yOJDiPkGhQYLZHmoVKMz2xdqtodI/t6QPJOJ5iQHJ35rC4c+LDi\nib+g3/cUEWReJtXX1uXoUTeavyh682QntglpQ1s/O0qeBqmCaSr83whE3Zi+IJ5V\nf1xoQSQFAgMBAAECggEAApmFncpS7EUlv/U/8yZPiUD58H/ilvQTXkX2SnV00q7S\nAsk15F0WZaSbV5D96oP1VC1xAVz7/S21zPmKeNEA7e/EgtWhp7A/4jd6SbcWm29p\nd5k83n/IHjRp8Zfcdz0O0WMxGf6C6z3BeN4DAqWH1rd5fGYSAIDI8F1iPaLpQ+Xm\nS+/gSXNcsU85Rxa48oSnQrUMPRiKoFr0xgTXuznMfSAozvv1zfhDaFnWPTexnQAM\n0gvLvF+5/QIudsPzeMEofmy9jd2LV3+AuSPHGCKfpENP/J/rKtUEhEUCvFVMYed+\nXQ7CeFhTxNHcBF/XgMX/ZGvzpyBQAUU/qBxCuCu7gQKBgQD/xa5YPakTlqWhlJlk\6DjIcZZt0wEWl4ID0xzDfck18k3c1cHu0NdEhERrp8XeoepW0q6BcOtYp9wRE69Q\n44EiX6MiIg4oeevh9+/AIFKeFADCdt/c0jWc0wGTKKr9uaIpdvrFIgMhKbS4G+zq\n/lGC2tEKvuXery6fDRkZz7BvZQKBgQDZybcZWd/HoWdFOo+m4sQmfePY44qSw096\nVmYMwXSbqygXNfryC5BVM53iSoBG0mSmsHISbhFzfGsSTj0zVN2idrESXfXnN4j5\n3QhuCfZe7CLcHuOmDw0QbWofl6qn6OsiUOVFOZXZliM7ymbxpUcCj3g5VEhwoalw\Sg+stn8oIQKBgCBJgw2ukvZfEP+Js6dyTSC4fgXVGhERBR+YecwPx+Ogd8XF0hpk\nkJgcnkp8vlSxWdSl+dNrPrpNTlF1i68JWRbOvdgkNmdTpLw8wS4epm9AFSx3NyE4\nA/6NAGjkPFmVImxbkaJq/bwk+KQ5Gjo76mw7VSInIPtwX9FCJQYGGr6lAoGBAMAs\nWzG2eV0pEfwnaXzEGnswmK3YUn2gc/AqbtAQoHmANNcOXcnY5FoaOtXkEX7sxb3E\clPK5gE2pzA284/o8c0a2LKxUHvfKDH6lSasCcbGrRf49b2hCFEXiw4ngYG6aEkW\ngshrwMuHzL1Eo0PVKGyc9mP3+BfSvrWD1IL9YgShAoGBAPWkqO2Scjr0BAgjJUOJ\CHcn+2QyocpsdILSfaaFelTw8fdvSdfXvhBsG9jaLjrbQzuIunbI06NkFMBLRSVt\naRH0Warw4jxc8mxPIXtoChkjUXzmUprvcXy+sL/jf1J5NKkWn08x1tqz4M0a5T68\n9DXFLd57mN/hEhhrrrRnjRdw====\n-----\n",
                "client_email": "firebase-adminsdk-fbsvc@am-smm-panel-1146b.iam.gserviceaccount.com",
                "client_id": "1146b",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40am-smm-panel-1146b.iam.gserviceaccount.com"
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase Init Error: {e}")

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

        user_ref.update({
            'availableBalance': current_balance + reward_amount,
            'totalEarnings': current_total + reward_amount,
            'lastUpdated': firestore.SERVER_TIMESTAMP
        })

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
        
