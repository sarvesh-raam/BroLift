from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access BroLift.'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                static_folder=os.path.join(root, 'static'),
                template_folder=os.path.join(root, 'app', 'templates'))
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.rides import rides_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(rides_bp)
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        db.create_all()

    return app
