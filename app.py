import os
from flask import Flask, request, jsonify

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 3000))

@app.route("/slack/baixar", methods=["POST"])
def baixar():
    texto = request.form.get("text", "").strip()

    if not texto:
        return "Envie uma ou mais URLs do YouTube.", 200

    links = texto.split()

    resposta = "Recebi os links:\n"
    resposta += "\n".join(f"- {l}" for l in links)

    return resposta, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

