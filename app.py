import os
import requests
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# =====================
# App Flask
# =====================
app = Flask(__name__)

PORT = int(os.environ.get("PORT", 3000))

# =====================
# Slack
# =====================
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

slack_client = WebClient(token=SLACK_BOT_TOKEN)
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

# =====================
# Google Drive
# =====================
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

credentials = Credentials.from_service_account_info(
    eval(GOOGLE_CREDENTIALS_JSON),
    scopes=["https://www.googleapis.com/auth/drive"]
)

drive_service = build("drive", "v3", credentials=credentials)

# =====================
# Rotas
# =====================
@app.route("/slack/events", methods=["POST"])
def slack_events():
    if not signature_verifier.is_valid_request(
        request.get_data(), request.headers
    ):
        return jsonify({"error": "invalid request"}), 403

    payload = request.json

    # Verificação inicial do Slack
    if payload.get("type") == "url_verification":
        return jsonify({"challenge": payload.get("challenge")})

    event = payload.get("event", {})

    # Quando um arquivo é enviado no Slack
    if event.get("type") == "file_shared":
        file_id = event.get("file_id")

        file_info = slack_client.files_info(file=file_id)["file"]
        download_url = file_info["url_private_download"]
        filename = file_info["name"]

        headers = {
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
        }

        response = requests.get(download_url, headers=headers)

        local_path = f"/tmp/{filename}"
        with open(local_path, "wb") as f:
            f.write(response.content)

        media = MediaFileUpload(local_path, resumable=True)
        drive_service.files().create(
            media_body=media,
            body={
                "name": filename,
                "parents": [GOOGLE_DRIVE_FOLDER_ID]
            }
        ).execute()

    return jsonify({"ok": True})

# =====================
# Start
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
