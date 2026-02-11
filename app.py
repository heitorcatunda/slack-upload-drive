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
        cookies_path = "/tmp/cookies.txt"

        # Log inicial
        slack_client.chat_postMessage(
            channel=channel_id,
            text=f"🚀 Iniciando download:\n{url}"
        )

        try:
            # =====================
            # Cookies
            # =====================
            import base64

            cookies_b64 = os.environ.get("YT_COOKIES_B64")
            
            if not cookies_b64:
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text="❌ Variável YT_COOKIES_B64 não definida."
                )
                continue
            
            cookies = base64.b64decode(cookies_b64).decode("utf-8")
            
            with open(cookies_path, "w") as f:
                f.write(cookies)

            # =====================
            # Download
            # =====================
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--cookies", cookies_path,
                    "-f", "bv*+ba/best",
                    "-o", filename,
                    url
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,  # ⏱ evita travar pra sempre
                text=True
            )

            if result.returncode != 0:
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=(
                        f"❌ Erro no yt-dlp:\n{url}\n"
                        f"```{result.stderr}```"
                    )
                )
                continue

            # =====================
            # Sucesso
            # =====================
            slack_client.chat_postMessage(
                channel=channel_id,
                text=(
                    f"✅ Download concluído:\n{url}\n"
                    f"```{result.stdout}```"
                )
            )

        except subprocess.TimeoutExpired:
            slack_client.chat_postMessage(
                channel=channel_id,
                text=f"⏱ Timeout ao baixar:\n{url}"
            )

        except Exception as e:
            slack_client.chat_postMessage(
                channel=channel_id,
                text=f"🔥 Erro inesperado:\n{str(e)}"
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

