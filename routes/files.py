import os

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    flash
)

from flask_login import (
    login_required,
    current_user
)

from werkzeug.utils import secure_filename

from models.user import db
from models.file import File
from models.folder import Folder


files = Blueprint(
    "files",
    __name__
)


UPLOAD_FOLDER = "storage"

# 100 MB storage limit
STORAGE_LIMIT = 100 * 1024 * 1024


# CALCULATE USER STORAGE
def get_user_storage_used(user_id):

    total_size = 0

    user_files = File.query.filter_by(
        user_id=user_id,
        is_deleted=False
    ).all()

    for file in user_files:

        if os.path.exists(file.filepath):

            total_size += os.path.getsize(
                file.filepath
            )

    return total_size


# MY FILES
@files.route("/files")
@login_required
def my_files():

    search = request.args.get(
        "search",
        ""
    )

    query = File.query.filter_by(
        user_id=current_user.id,
        is_deleted=False,
        folder_id=None
    )

    if search:

        query = query.filter(
            File.filename.ilike(
                f"%{search}%"
            )
        )

    user_files = query.all()

    user_folders = Folder.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "files.html",
        files=user_files,
        folders=user_folders,
        search=search
    )


# UPLOAD FILE TO MY FILES
@files.route(
    "/upload",
    methods=["POST"]
)
@login_required
def upload():

    uploaded_file = request.files.get(
        "file"
    )

    if (
        not uploaded_file
        or uploaded_file.filename == ""
    ):

        flash(
            "Please select a file."
        )

        return redirect(
            url_for("files.my_files")
        )

    filename = secure_filename(
        uploaded_file.filename
    )

    # Get file size
    uploaded_file.stream.seek(
        0,
        os.SEEK_END
    )

    file_size = uploaded_file.stream.tell()

    uploaded_file.stream.seek(0)

    # Current storage usage
    current_usage = get_user_storage_used(
        current_user.id
    )

    # Check quota
    if current_usage + file_size > STORAGE_LIMIT:

        flash(
            "Storage limit reached. "
            "Maximum storage is 100 MB."
        )

        return redirect(
            url_for("files.my_files")
        )

    user_folder = os.path.join(
        UPLOAD_FOLDER,
        str(current_user.id)
    )

    os.makedirs(
        user_folder,
        exist_ok=True
    )

    filepath = os.path.join(
        user_folder,
        filename
    )

    uploaded_file.save(
        filepath
    )

    new_file = File(
        filename=filename,
        filepath=filepath,
        user_id=current_user.id,
        folder_id=None,
        is_deleted=False
    )

    db.session.add(new_file)
    db.session.commit()

    flash(
        "File uploaded successfully!"
    )

    return redirect(
        url_for("files.my_files")
    )


# UPLOAD FILE INTO FOLDER
@files.route(
    "/upload-to-folder/<int:folder_id>",
    methods=["POST"]
)
@login_required
def upload_to_folder(folder_id):

    folder = Folder.query.get_or_404(
        folder_id
    )

    if folder.user_id != current_user.id:

        return "Unauthorized", 403

    uploaded_file = request.files.get(
        "file"
    )

    if (
        not uploaded_file
        or uploaded_file.filename == ""
    ):

        flash(
            "Please select a file."
        )

        return redirect(
            url_for(
                "folders.open_folder",
                folder_id=folder.id
            )
        )

    filename = secure_filename(
        uploaded_file.filename
    )

    # Get file size
    uploaded_file.stream.seek(
        0,
        os.SEEK_END
    )

    file_size = uploaded_file.stream.tell()

    uploaded_file.stream.seek(0)

    # Current usage
    current_usage = get_user_storage_used(
        current_user.id
    )

    # Check quota
    if current_usage + file_size > STORAGE_LIMIT:

        flash(
            "Storage limit reached. "
            "Maximum storage is 100 MB."
        )

        return redirect(
            url_for(
                "folders.open_folder",
                folder_id=folder.id
            )
        )

    user_folder = os.path.join(
        UPLOAD_FOLDER,
        str(current_user.id)
    )

    os.makedirs(
        user_folder,
        exist_ok=True
    )

    folder_path = os.path.join(
        user_folder,
        str(folder.id)
    )

    os.makedirs(
        folder_path,
        exist_ok=True
    )

    filepath = os.path.join(
        folder_path,
        filename
    )

    uploaded_file.save(
        filepath
    )

    new_file = File(
        filename=filename,
        filepath=filepath,
        user_id=current_user.id,
        folder_id=folder.id,
        is_deleted=False
    )

    db.session.add(new_file)
    db.session.commit()

    flash(
        "File uploaded to folder successfully!"
    )

    return redirect(
        url_for(
            "folders.open_folder",
            folder_id=folder.id
        )
    )


# MOVE FILE INTO FOLDER
@files.route(
    "/move/<int:file_id>",
    methods=["POST"]
)
@login_required
def move_file(file_id):

    file = File.query.get_or_404(
        file_id
    )

    if file.user_id != current_user.id:

        return "Unauthorized", 403

    folder_id = request.form.get(
        "folder_id"
    )

    if not folder_id:

        flash(
            "Please select a folder."
        )

        return redirect(
            url_for("files.my_files")
        )

    folder = Folder.query.get_or_404(
        int(folder_id)
    )

    if folder.user_id != current_user.id:

        return "Unauthorized", 403

    folder_path = os.path.join(
        UPLOAD_FOLDER,
        str(current_user.id),
        str(folder.id)
    )

    os.makedirs(
        folder_path,
        exist_ok=True
    )

    new_path = os.path.join(
        folder_path,
        file.filename
    )

    if os.path.exists(
        file.filepath
    ):

        os.rename(
            file.filepath,
            new_path
        )

    file.filepath = new_path
    file.folder_id = folder.id

    db.session.commit()

    flash(
        "File moved to folder successfully."
    )

    return redirect(
        url_for("files.my_files")
    )


# DOWNLOAD
@files.route(
    "/download/<int:file_id>"
)
@login_required
def download(file_id):

    file = File.query.get_or_404(
        file_id
    )

    if file.user_id != current_user.id:

        return "Unauthorized", 403

    if file.is_deleted:

        return "File is in trash.", 404

    if not os.path.exists(
        file.filepath
    ):

        return "File not found.", 404

    return send_file(
        file.filepath,
        as_attachment=True,
        download_name=file.filename
    )


# RENAME
@files.route(
    "/rename/<int:file_id>",
    methods=["POST"]
)
@login_required
def rename(file_id):

    file = File.query.get_or_404(
        file_id
    )

    if file.user_id != current_user.id:

        return "Unauthorized", 403

    new_name = request.form.get(
        "filename"
    )

    if not new_name:

        flash(
            "Filename cannot be empty."
        )

        return redirect(
            url_for("files.my_files")
        )

    new_name = secure_filename(
        new_name
    )

    folder = os.path.dirname(
        file.filepath
    )

    new_path = os.path.join(
        folder,
        new_name
    )

    if os.path.exists(
        file.filepath
    ):

        os.rename(
            file.filepath,
            new_path
        )

    file.filename = new_name
    file.filepath = new_path

    db.session.commit()

    flash(
        "File renamed successfully."
    )

    return redirect(
        url_for("files.my_files")
    )


# DELETE / MOVE TO TRASH
@files.route(
    "/delete/<int:file_id>"
)
@login_required
def delete(file_id):

    file = File.query.get_or_404(
        file_id
    )

    if file.user_id != current_user.id:

        return "Unauthorized", 403

    original_folder_id = file.folder_id

    file.is_deleted = True

    db.session.commit()

    flash(
        "File moved to Trash."
    )

    if original_folder_id:

        return redirect(
            url_for(
                "folders.open_folder",
                folder_id=original_folder_id
            )
        )

    return redirect(
        url_for("files.my_files")
    )


# TRASH
@files.route("/trash")
@login_required
def trash():

    deleted_files = File.query.filter_by(
        user_id=current_user.id,
        is_deleted=True
    ).all()

    return render_template(
        "trash.html",
        files=deleted_files
    )


# RESTORE
@files.route(
    "/restore/<int:file_id>"
)
@login_required
def restore(file_id):

    file = File.query.get_or_404(
        file_id
    )

    if file.user_id != current_user.id:

        return "Unauthorized", 403

    # Check quota before restoring
    if os.path.exists(file.filepath):

        file_size = os.path.getsize(
            file.filepath
        )

        current_usage = get_user_storage_used(
            current_user.id
        )

        if current_usage + file_size > STORAGE_LIMIT:

            flash(
                "Cannot restore file. "
                "Your 100 MB storage limit would be exceeded."
            )

            return redirect(
                url_for("files.trash")
            )

    file.is_deleted = False

    db.session.commit()

    flash(
        "File restored successfully."
    )

    return redirect(
        url_for("files.trash")
    )