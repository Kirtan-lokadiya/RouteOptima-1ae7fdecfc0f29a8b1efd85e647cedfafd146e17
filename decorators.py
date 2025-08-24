# decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash
import jwt
from functools import wraps
from flask import request, jsonify, session, current_app
from pymongo import MongoClient

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only allow access if the user is marked as verified (logged in)
        if not session.get('verified'):
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


SECRET_KEY = "YOUR_SECRET_KEY"

def get_db():
    client = MongoClient(current_app.config["MONGO_URI"])
    return client.get_default_database()

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return redirect(url_for('auth.login'))

        try:
            token = token.split("Bearer ")[1]  # Extract token from "Bearer <token>"
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            session["user_email"] = decoded_token["email"]  # Store in session for convenience
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 403

        return f(*args, **kwargs)
    return decorated_function