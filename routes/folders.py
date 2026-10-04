from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from models.user import db
from models.folder import Folder
from models.file import File


folders = Blueprint(
    "folders",
    __name__
)


# ALL FOLDERS
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


# CREATE FOLDER
@folders.route(
    "/create-folder",
    methods=["POST"]
)
@login_required
def create_folder():

    folder_name = request.form.get(
        "folder_name"
    )

    if not folder_name:

        flash(
            "Folder name cannot be empty."
        )

        return redirect(
            url_for("folders.my_folders")
        )

    existing_folder = Folder.query.filter_by(
        user_id=current_user.id,
        name=folder_name
    ).first()

    if existing_folder:

        flash(
            "A folder with this name already exists."
        )

        return redirect(
            url_for("folders.my_folders")
        )

    new_folder = Folder(
        name=folder_name,
        user_id=current_user.id
    )

    db.session.add(new_folder)
    db.session.commit()

    flash(
        "Folder created successfully!"
    )

    return redirect(
        url_for("folders.my_folders")
    )


# OPEN FOLDER
@folders.route(
    "/folder/<int:folder_id>"
)
@login_required
def open_folder(folder_id):

    folder = Folder.query.get_or_404(
        folder_id
    )

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


# DELETE FOLDER
@folders.route(
    "/delete-folder/<int:folder_id>"
)
@login_required
def delete_folder(folder_id):

    folder = Folder.query.get_or_404(
        folder_id
    )

    if folder.user_id != current_user.id:

        return "Unauthorized", 403

    # Remove folder reference from files
    folder_files = File.query.filter_by(
        folder_id=folder.id
    ).all()

    for file in folder_files:

        file.folder_id = None

    db.session.delete(folder)

    db.session.commit()

    flash(
        "Folder deleted successfully."
    )

    return redirect(
        url_for("folders.my_folders")
    )