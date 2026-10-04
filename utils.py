from flask import current_app
from flask_mail import Message


def send_email(recipient, subject, body):
    message = Message(
        subject=subject,
        sender=current_app.config["MAIL_USERNAME"],
        recipients=[recipient]
    )

    message.body = body

    current_app.extensions["mail"].send(message)