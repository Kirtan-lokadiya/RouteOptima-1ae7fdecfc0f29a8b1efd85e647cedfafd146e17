import logging
from flask import Flask
from config import Config
from routes import auth_bp, optimization_bp
from flask_mail import Mail
from flask_bcrypt import Bcrypt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ----- Set up Logging -----
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )
    app.logger.info("Application startup")

    # ----- Initialize Extensions -----
    mail = Mail(app)
    bcrypt = Bcrypt(app)

    # ----- Register Blueprints -----
    app.register_blueprint(auth_bp)
    app.register_blueprint(optimization_bp)

    return app

import os

if __name__ == '__main__':
    app = create_app()
    # for https
    # if os.getenv('USE_SSL', 'true').lower() == 'true':
    # for http
    if os.getenv('USE_SSL', 'false').lower() == 'true':
        app.run(host="0.0.0.0", port=5000, ssl_context=('server.cert', 'server.key'))
    else:
        app.run(host="0.0.0.0", port=5000)