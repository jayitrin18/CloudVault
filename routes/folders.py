from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user

from models.user import db
from models.folder import Folder
from models.file import File


folders = Blueprint("folders", __name__)


# =========================================================
# MY FOLDERS
# =========================================================

@folders.route("/folders")
@login_required
def my_folders():

    user_folders = Folder.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "folders.html",
        folders=user_folders
    )


# =========================================================
# CREATE FOLDER
# =========================================================

@folders.route("/folders/create", methods=["POST"])
@login_required
def create_folder():

    name = request.form.get("name")

    if not name:
        flash("Folder name cannot be empty.")
        return redirect(
            url_for("folders.my_folders")
        )

    new_folder = Folder(
        name=name,
        user_id=current_user.id
    )

    db.session.add(new_folder)
    db.session.commit()

    flash("Folder created successfully.")

    return redirect(
        url_for("folders.my_folders")
    )


# =========================================================
# OPEN FOLDER
# =========================================================

@folders.route("/folders/open/<int:folder_id>")
@login_required
def open_folder(folder_id):

    folder = Folder.query.get_or_404(folder_id)

    if folder.user_id != current_user.id:
        return "Unauthorized", 403

    folder_files = File.query.filter_by(
        user_id=current_user.id,
        folder_id=folder.id,
        is_deleted=False
    ).all()

    return render_template(
        "folder_view.html",
        folder=folder,
        files=folder_files
    )


# =========================================================
# DELETE FOLDER
# =========================================================

@folders.route("/folders/delete/<int:folder_id>")
@login_required
def delete_folder(folder_id):

    folder = Folder.query.get_or_404(folder_id)

    if folder.user_id != current_user.id:
        return "Unauthorized", 403

    # Check if folder contains active files
    files_in_folder = File.query.filter_by(
        folder_id=folder.id,
        user_id=current_user.id,
        is_deleted=False
    ).count()

    if files_in_folder > 0:

        flash(
            "This folder contains files. "
            "Move or delete the files before deleting the folder."
        )

        return redirect(
            url_for("folders.my_folders")
        )

    db.session.delete(folder)
    db.session.commit()

    flash("Folder deleted successfully.")

    return redirect(
        url_for("folders.my_folders")
    )