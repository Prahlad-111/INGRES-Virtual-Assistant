from flask import Flask, render_template
from api.routes import chatbot_api


# --------------------------------------------------
# Create Flask application
# --------------------------------------------------

app = Flask(__name__)


# --------------------------------------------------
# Register chatbot API
# --------------------------------------------------

app.register_blueprint(
    chatbot_api,
    url_prefix="/api"
)


# --------------------------------------------------
# Home page
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.route("/health")
def health():
    return {
        "status": "online",
        "message": "INGRES AI Chatbot is running"
    }


# --------------------------------------------------
# Run application
# --------------------------------------------------

if __name__ == "__main__":

    print("\n======================================")
    print("       INGRES AI CHATBOT SERVER")
    print("======================================")
    print("Server: http://127.0.0.1:5000")
    print("API:    http://127.0.0.1:5000/api/chat")
    print("Health: http://127.0.0.1:5000/health")
    print("======================================\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )