from twilio.rest import Client
from flask import current_app

def send_sms(to_number, message_body):
    client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
    client.messages.create(
        body=message_body,
        from_=current_app.config['TWILIO_PHONE_NUMBER'],
        to=to_number
    )
