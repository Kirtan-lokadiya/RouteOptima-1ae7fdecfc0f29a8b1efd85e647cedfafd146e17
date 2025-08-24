# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from pymongo import MongoClient
import random, string, bcrypt

from services.email_service import send_email_otp
from services.sms_service import send_sms
from services.hashing import hash_password

auth_bp = Blueprint('auth', __name__)

def get_db():
    client = MongoClient(current_app.config["MONGO_URI"])
    db = client.get_default_database()
    return db

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        current_app.logger.info("Signup form submitted")
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Basic validation
        if not all([email, password, confirm_password]):
            flash("All fields are required", "danger")
            return redirect(url_for('auth.signup'))
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('auth.signup'))
        if len(password) < 8:
            flash("Password must be at least 8 characters", "danger")
            return redirect(url_for('auth.signup'))

        db = get_db()
        if db.users.find_one({"email": email}):
            flash("Email already registered", "danger")
            return redirect(url_for('auth.signup'))

        # Hash password
        hashed_password = hash_password(password)

        # Create user record
        user_data = {
            "email": email,
            "password": hashed_password,
            "email_verified": False,
            "mobile_verified": False
        }
        db.users.insert_one(user_data)
        current_app.logger.info("User inserted into database: %s", email)

        # Generate and send OTP for email verification
        email_otp = ''.join(random.choices(string.digits, k=6))
        session['email_otp'] = email_otp
        session['user_email'] = email
        try:
            send_email_otp(email, "User", email_otp)
            current_app.logger.info("Email OTP sent to: %s", email)
        except Exception as e:
            current_app.logger.error("Failed to send email OTP: %s", e)
            flash("Failed to send email OTP. Please check your email configuration.", "warning")

        # Generate and send OTP for mobile verification
        mobile_otp = ''.join(random.choices(string.digits, k=6))
        session['mobile_otp'] = mobile_otp
        session['mobile'] = request.form.get('mobile')
        try:
            send_sms(session['mobile'], f"Your RouteOptima OTP is {mobile_otp}")
            current_app.logger.info("OTP sent to mobile: %s", session['mobile'])
        except Exception as e:
            current_app.logger.error("Failed to send mobile OTP: %s", e)
            flash("Failed to send mobile OTP. Please check your mobile configuration.", "warning")

        flash("Signup successful! Please verify your email and mobile.", "success")
        return redirect(url_for('auth.verify_email_otp'))
    return render_template('signup.html')

@auth_bp.route('/verify_email_otp', methods=['GET', 'POST'])
def verify_email_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        if entered_otp == session.get('email_otp'):
            db = get_db()
            result = db.users.update_one({"email": session.get('user_email')}, {"$set": {"email_verified": True}})
            if result.modified_count:
                flash("Email verified successfully!", "success")
                current_app.logger.info("Email verified for: %s", session.get('user_email'))
            else:
                flash("Email already verified or user not found.", "info")

            # Check if both email and mobile are verified
            user = db.users.find_one({"email": session.get('user_email')})
            if user and user.get("email_verified") and user.get("mobile_verified"):
                session['verified'] = True
                return redirect(url_for('optimization.home'))  # Redirect to the home page
            else:
                flash("Please complete mobile verification as well.", "danger")
                return redirect(url_for('auth.verify_mobile'))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for('auth.verify_email_otp'))
    return render_template('verify_email_otp.html')

@auth_bp.route('/verify_mobile', methods=['GET', 'POST'])
def verify_mobile():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        if entered_otp == session.get('mobile_otp'):
            mobile = session.get('mobile')
            db = get_db()
            result = db.users.update_one({"email": session.get('user_email')}, {"$set": {"mobile_verified": True}})
            if result.modified_count:
                flash("Mobile number verified successfully!", "success")
                current_app.logger.info("Mobile verified for: %s", mobile)
            else:
                flash("Mobile already verified or user not found.", "info")

            # Check if both email and mobile are verified
            user = db.users.find_one({"email": session.get('user_email')})
            if user and user.get("email_verified") and user.get("mobile_verified"):
                session['verified'] = True
                return redirect(url_for('optimization.home'))  # Redirect to the home page
            else:
                flash("Please complete email verification as well.", "danger")
                return redirect(url_for('auth.verify_email_otp'))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for('auth.verify_mobile'))
    return render_template('verify_mobile.html')
    
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        db = get_db()
        user = db.users.find_one({"email": email})
        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
                session['verified'] = True
                session['user_email'] = email
                flash("Logged in successfully!", "success")
                current_app.logger.info("User logged in: %s", email)
                return redirect(url_for('optimization.home'))
            else:
                flash("Invalid password.", "danger")
        else:
            flash("User not found.", "danger")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('auth.login'))