import os
import threading
import subprocess
import uuid

from flask import Flask, request
from slack_sdk import WebClient

# =====================
# App Flask
# =====================
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 3000))

# =====================
# Slack
# =====================
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# =====================
# Background job
# =====================
def processar_links(links, channel_id):
    for url in links:
        filename = f"/tmp/{uuid.uuid4()}.mp4"

        try:
            cookies = os.environ.get("YT_COOKIES")

            cookies_path = "/tmp/cookies.txt"
            with open(cookies_path, "w") as f:
                f.write(cookies)
                
            # Download do vídeo
            subprocess.run(
                [
                    "yt-dlp",
                    "--cookies", cookies_path,
                    "-f", "bv*+ba/best",
                    "-o", filename,
                    url
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            slack_client.chat_postMessage(
                channel=channel_id,
                text=f"✅ Download concluído:\n{url}"
            )

        except subprocess.CalledProcessError as e:
            slack_client.chat_postMessage(
                channel=channel_id,
                text=(
                    f"❌ Erro ao baixar:\n{url}\n"
                    f"```{e.stderr.decode(errors='ignore')}```"
                )
            )

        finally:
            if os.path.exists(filename):
                os.remove(filename)

# =====================
# Slash command
# =====================
@app.route("/slack/baixar", methods=["POST"])
def baixar():
    texto = request.form.get("text", "").strip()
    channel_id = request.form.get("channel_id")

    if not texto:
        return "Envie uma ou mais URLs do YouTube.", 200

    links = texto.split()

    thread = threading.Thread(
        target=processar_links,
        args=(links, channel_id),
        daemon=True
    )
    thread.start()

    return f"⏬ Iniciando download de {len(links)} vídeo(s)...", 200

# =====================
# Start
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

