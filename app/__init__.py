import logging
import os

from flask import Flask, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access BroLift.'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                static_folder=os.path.join(root, 'static'),
                template_folder=os.path.join(root, 'app', 'templates'))
    app.config.from_object(config_class)
    # Render terminates TLS at its proxy; trust X-Forwarded-* so url_for builds https URLs
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    if not app.debug:
        logging.basicConfig(level=logging.INFO)
    if not (os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY')):
        app.logger.warning('SECRET_KEY is not set; using a random key. Sessions will not survive restarts.')
    if not app.config['GOOGLE_MAPS_API_KEY']:
        app.logger.warning('GOOGLE_MAPS_API_KEY is not set; maps and place search will not work.')

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.rides import rides_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(rides_bp)
    app.register_blueprint(dashboard_bp)

    from app.utils.time import now_local
    app.jinja_env.globals['now_local'] = now_local

    with app.app_context():
        from app.utils.migrations import migrate_database
        db.create_all()
        migrate_database()

    @app.route('/healthz')
    def healthz():
        return {'status': 'ok'}

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template('400.html', reason='Your session expired. Please go back, refresh and try again.'), 400

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.exception('Server error')
        return render_template('500.html'), 500

    return app
