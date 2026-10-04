from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_login import (
    login_user,
    logout_user,
    login_required
)

from datetime import datetime, timedelta

import secrets

from models.user import (
    db,
    User,
    PasswordResetOTP
)

from utils import send_email


auth = Blueprint(
    "auth",
    __name__
)


# REGISTER
@auth.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:

            flash("Please fill in all fields.")

            return redirect(
                url_for("auth.register")
            )

        email = email.strip().lower()

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash("Email already registered.")

            return redirect(
                url_for("auth.register")
            )

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        try:

            send_email(
                email,
                "CloudVault Registration Successful",
                f"""Hello {name},

Your CloudVault account has been registered successfully.

You can now log in and start using CloudVault.

Regards,
CloudVault Team
"""
            )

            print(
                "REGISTRATION EMAIL SENT TO:",
                email
            )

        except Exception as e:

            print(
                "Registration email error:",
                repr(e)
            )

        flash(
            "Registration successful! Please login."
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/register.html"
    )


# LOGIN
@auth.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        email = email.strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            print("LOGIN SUCCESSFUL")

            print(
                "SENDING LOGIN EMAIL TO:",
                user.email
            )

            try:

                send_email(
                    user.email,
                    "CloudVault Login Successful",
                    f"""Hello {user.name},

You have successfully logged in to your CloudVault account.

If this was not you, please secure your account immediately.

Regards,
CloudVault Team
"""
                )

                print(
                    "LOGIN EMAIL SENT SUCCESSFULLY"
                )

            except Exception as e:

                print(
                    "Login email error:",
                    repr(e)
                )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password."
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/login.html"
    )


# LOGOUT
@auth.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("auth.login")
    )


# PROFILE
@auth.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html"
    )


# FORGOT PASSWORD
@auth.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")

        if not email:

            flash(
                "Please enter your email address."
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        email = email.strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()

        if user:

            PasswordResetOTP.query.filter_by(
                user_id=user.id,
                used=False
            ).delete()

            otp = f"{secrets.randbelow(1000000):06d}"

            otp_hash = generate_password_hash(
                otp
            )

            expires_at = (
                datetime.utcnow()
                + timedelta(minutes=5)
            )

            reset_otp = PasswordResetOTP(
                user_id=user.id,
                otp_hash=otp_hash,
                expires_at=expires_at
            )

            db.session.add(reset_otp)
            db.session.commit()

            session["password_reset_id"] = (
                reset_otp.id
            )

            try:

                send_email(
                    user.email,
                    "CloudVault Password Reset OTP",
                    f"""Hello {user.name},

Your CloudVault password reset OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request a password reset, please ignore this email.

Regards,
CloudVault Team
"""
                )

                print(
                    "PASSWORD RESET OTP SENT TO:",
                    user.email
                )

            except Exception as e:

                print(
                    "Password reset email error:",
                    repr(e)
                )

        flash(
            "If an account exists with this email, "
            "a password reset OTP has been sent."
        )

        return redirect(
            url_for("auth.verify_otp")
        )

    return render_template(
        "auth/forgot_password.html"
    )


# VERIFY OTP
@auth.route(
    "/verify-otp",
    methods=["GET", "POST"]
)
def verify_otp():

    reset_id = session.get(
        "password_reset_id"
    )

    if not reset_id:

        flash(
            "Please request a password reset first."
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    reset_otp = PasswordResetOTP.query.get(
        reset_id
    )

    if not reset_otp:

        flash(
            "Invalid password reset request."
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if reset_otp.used:

        flash(
            "This OTP has already been used."
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if datetime.utcnow() > reset_otp.expires_at:

        flash(
            "OTP has expired. Please request a new one."
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if reset_otp.attempts >= 5:

        flash(
            "Too many incorrect attempts. Please request a new OTP."
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "POST":

        otp = request.form.get("otp")

        if not otp:

            flash("Please enter the OTP.")

            return redirect(
                url_for("auth.verify_otp")
            )

        reset_otp.attempts += 1

        if check_password_hash(
            reset_otp.otp_hash,
            otp
        ):

            db.session.commit()

            session["otp_verified"] = True

            return redirect(
                url_for("auth.reset_password")
            )

        db.session.commit()

        flash(
            "Invalid OTP. Please try again."
        )

        return redirect(
            url_for("auth.verify_otp")
        )

    return render_template(
        "auth/verify_otp.html"
    )


# RESET PASSWORD
@auth.route(
    "/reset-password",
    methods=["GET", "POST"]
)
def reset_password():

    if not session.get("otp_verified"):

        flash(
            "Please verify your OTP first."
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    reset_id = session.get(
        "password_reset_id"
    )

    reset_otp = PasswordResetOTP.query.get(
        reset_id
    )

    if not reset_otp or reset_otp.used:

        flash(
            "Invalid password reset request."
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    user = db.session.get(
        User,
        reset_otp.user_id
    )

    if not user:

        flash("User not found.")

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "POST":

        new_password = request.form.get(
            "password"
        )

        confirm_password = request.form.get(
            "confirm_password"
        )

        if not new_password or not confirm_password:

            flash(
                "Please fill in all fields."
            )

            return redirect(
                url_for("auth.reset_password")
            )

        if new_password != confirm_password:

            flash(
                "Passwords do not match."
            )

            return redirect(
                url_for("auth.reset_password")
            )

        if len(new_password) < 8:

            flash(
                "Password must be at least 8 characters."
            )

            return redirect(
                url_for("auth.reset_password")
            )

        user.password = generate_password_hash(
            new_password
        )

        reset_otp.used = True

        db.session.commit()

        session.pop(
            "password_reset_id",
            None
        )

        session.pop(
            "otp_verified",
            None
        )

        flash(
            "Password reset successful! Please login."
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html"
    )