
import os

from flask import Flask, render_template
from flask_mail import Mail
from dotenv import load_dotenv

from api.routes import chatbot_api
from api.auth import auth_bp

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Gmail SMTP configuration
app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "true").lower()
    in ("true", "1", "yes"),
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER"),
)

# Initialize Flask-Mail
mail = Mail(app)

# Register existing API blueprints
app.register_blueprint(chatbot_api, url_prefix="/api")
app.register_blueprint(auth_bp)


# ==============================
# PAGE ROUTES
# ==============================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")


# ==============================
# HEALTH CHECK
# ==============================

@app.route("/health")
def health():
    return {
        "status": "online",
        "message": "INGRES AI Chatbot is running"
    }


# ==============================
# RUN SERVER
# ==============================

if __name__ == "__main__":
    print("\n======================================")
    print("       INGRES AI CHATBOT SERVER")
    print("======================================")
    print("Server:   http://127.0.0.1:5000")
    print("Home:     http://127.0.0.1:5000/")
    print("Login:    http://127.0.0.1:5000/login")
    print("Register: http://127.0.0.1:5000/register")
    print("Forgot:   http://127.0.0.1:5000/forgot-password")
    print("API:      http://127.0.0.1:5000/api/chat")
    print("Auth:     http://127.0.0.1:5000/api/auth")
    print("Health:   http://127.0.0.1:5000/health")
    print("======================================\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
