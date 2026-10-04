import os

from flask import Flask, render_template
from flask_mail import Mail
from dotenv import load_dotenv

from models.user import db, User
from models.file import File
from models.folder import Folder

from routes.auth import auth
from routes.files import files
from routes.folders import folders

from flask_login import LoginManager, login_required, current_user


load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "cloudvault-secret-key"
)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///cloudvault.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Email configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)
db.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(files)
app.register_blueprint(folders)


@app.route("/")
def home():
    return render_template("index.html")


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

    total_size = 0

    for file in user_files:
        if os.path.exists(file.filepath):
            total_size += os.path.getsize(file.filepath)

    storage_limit_bytes = 100 * 1024 * 1024

    storage_percentage = min(
        (total_size / storage_limit_bytes) * 100,
        100
    )

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


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )
