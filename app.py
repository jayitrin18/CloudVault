from flask import Flask, render_template
from flask_mail import Mail
from dotenv import load_dotenv
import os

from models.user import db, User, PasswordResetOTP
from models.file import File
from models.folder import Folder

from routes.auth import auth
from routes.files import files
from routes.folders import folders

from flask_login import (
    LoginManager,
    login_required,
    current_user
)


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# CREATE FLASK APP
# =========================================================

app = Flask(__name__)


# =========================================================
# APP CONFIGURATION
# =========================================================

app.config["SECRET_KEY"] = "cloudvault-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cloudvault.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# =========================================================
# EMAIL CONFIGURATION
# =========================================================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True

app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")


mail = Mail(app)


# =========================================================
# DATABASE
# =========================================================

db.init_app(app)


# =========================================================
# LOGIN SYSTEM
# =========================================================

login_manager = LoginManager()

login_manager.login_view = "auth.login"

login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


# =========================================================
# ROUTES
# =========================================================

app.register_blueprint(auth)

app.register_blueprint(files)

app.register_blueprint(folders)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    user_files = File.query.filter_by(
        user_id=current_user.id,
        is_deleted=False
    ).all()

    user_folders = Folder.query.filter_by(
        user_id=current_user.id
    ).all()

    trash_files = File.query.filter_by(
        user_id=current_user.id,
        is_deleted=True
    ).all()

    # Calculate storage used
    total_size = 0

    for file in user_files:

        if os.path.exists(file.filepath):

            total_size += os.path.getsize(file.filepath)

    # Storage limit = 100 MB
    storage_limit = 100 * 1024 * 1024

    storage_percentage = min(
        (total_size / storage_limit) * 100,
        100
    )

    # Convert storage size to readable format
    if total_size < 1024:

        storage_used = f"{total_size} B"

    elif total_size < 1024 * 1024:

        storage_used = f"{total_size / 1024:.2f} KB"

    elif total_size < 1024 * 1024 * 1024:

        storage_used = f"{total_size / (1024 * 1024):.2f} MB"

    else:

        storage_used = f"{total_size / (1024 * 1024 * 1024):.2f} GB"

    return render_template(
        "dashboard.html",
        file_count=len(user_files),
        folder_count=len(user_folders),
        trash_count=len(trash_files),
        storage_used=storage_used,
        storage_limit="100 MB",
        storage_percentage=storage_percentage
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return {"status": "healthy"}, 200


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

with app.app_context():

    db.create_all()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )