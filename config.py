class Config:
    SECRET_KEY = 'your-secret-key'
    MONGO_URI = 'mongodb+srv://harsheel:harsheel@auth.kfaj4.mongodb.net/test?retryWrites=true&w=majority&appName=auth'
    
    # Flask-Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'kirtanlokadiya998@gmail.com'
    MAIL_PASSWORD = 'fxxh pqmo upzz osgg'
    
    # Twilio configuration for SMS
    TWILIO_ACCOUNT_SID='AC35338dd798bacdf069a299b4be6f20b4'
    TWILIO_AUTH_TOKEN='8b49c53f1dbc496cb024c45c8ee20394'
    TWILIO_PHONE_NUMBER='+12707139063'
