from flask_mail import Message
from flask import current_app
from flask_mail import Message
from flask import current_app
from flask_mail import Message
from flask import current_app

def send_email_otp(recipient, first_name, otp):
    msg = Message("Email Verification OTP - RouteOptima",
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[recipient])
    msg.body = (f"Hi {first_name},\n\n"
                f"Your OTP for email verification is: {otp}\n\n"
                "Please enter this OTP in the application to verify your email.\n"
                "If you did not sign up, please ignore this message.")
    from flask_mail import Mail
    mail = Mail(current_app)
    mail.send(msg)
