import os
from flask import Flask, request, jsonify

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 3000))

@app.route("/slack/baixar", methods=["POST"])
def baixar():
    texto = request.form.get("text")

    if not texto:
        return jsonify({
            "response_type": "ephemeral",
            "text": "❌ Você precisa enviar um link.\nExemplo: /baixar https://..."
        })

    # por enquanto só retorna o link
    return jsonify({
        "response_type": "ephemeral",
        "text": f"📥 Link recebido:\n{texto}"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
