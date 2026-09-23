import re
from functools import wraps

from flask import flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import create_user, user_by_email

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MIN_PASSWORD_LENGTH = 8


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            if request.path.startswith("/api/"):
                return jsonify({"error": {"code": "AUTHENTICATION_REQUIRED", "message": "Please sign in to continue."}}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def register_auth_routes(app):
    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if session.get("user_id") is not None:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            errors = []
            if not name:
                errors.append("Full name is required.")
            if not EMAIL_PATTERN.match(email):
                errors.append("Enter a valid email address.")
            if not password:
                errors.append("Password is required.")
            elif len(password) < MIN_PASSWORD_LENGTH:
                errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
            if password != confirm_password:
                errors.append("Passwords do not match.")
            if not errors and user_by_email(email):
                errors.append("An account with this email already exists.")
            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("signup.html", name=name, email=email), 400
            create_user(name, email, generate_password_hash(password))
            flash("Your account was created. Sign in to continue.", "success")
            return redirect(url_for("login"))
        return render_template("signup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user_id") is not None:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = user_by_email(email)
            if not user or not check_password_hash(user["password_hash"], password):
                flash("Invalid email or password.", "error")
                return render_template("login.html", email=email), 401
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.get("/logout")
    def logout():
        session.clear()
        flash("You have been logged out successfully.", "success")
        return redirect(url_for("login"))