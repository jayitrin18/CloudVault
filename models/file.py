from models.user import db


class File(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    filepath = db.Column(
        db.String(500),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    folder_id = db.Column(
        db.Integer,
        db.ForeignKey("folder.id"),
        nullable=True
    )

    is_deleted = db.Column(
        db.Boolean,
        default=False
    )