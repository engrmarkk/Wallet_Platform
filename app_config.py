from extensions import db, login_manager, mail, migrate, moment
from flask import redirect, url_for, session, render_template, Flask, sessions
from routes import AuthenticationBlueprint, ViewBlueprint, BillsBlueprint, ExternalBlueprint
from models import User, Transaction, Beneficiary, Card, Invitees, TransactionCategories
from datetime import timedelta
import os
import flask
from flask_login import current_user
from decouple import config
from sqlalchemy.exc import OperationalError

db_name = 'wallet'
default_uri = "postgres://{}:{}@{}/{}".format('postgres', 'password', 'localhost:5432', db_name)
uri = config('DATABASE_URL')  # or other relevant config var
if uri.startswith('postgres://'):
    uri = uri.replace('postgres://', 'postgresql://', 1)


def create_app():
    base_dir = os.path.dirname(os.path.realpath(__file__))

    app = Flask(__name__)

    # app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    #     base_dir, "easytransact.db"
    # )

    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "4f557e8e5eb51bfb7c42"
    app.config['DEBUG'] = False
    app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 465
    app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
    app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASS")
    app.config["MAIL_USE_TLS"] = False
    app.config["MAIL_USE_SSL"] = True

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)

    # The decorator that loads the user using the user's id
    @login_manager.user_loader
    def user_loader(id):
        try:
            return User.query.get(id)
        except Exception as e:
            print(e, "error in user loader")
            db.session.rollback()
            return None

    # If the user isn't logged in and tries to access a login required route, this decorator allows the page to
    # redirect page to the login
    @login_manager.unauthorized_handler
    def unauthorized_handler():
        session["alert"] = "Login to access this page"
        session["bg_color"] = "info"
        return redirect(url_for("auth.login"))

    with app.app_context():
        db.create_all()

    @app.errorhandler(413)
    def too_large(e):
        session["alert"] = "File too large, max size is 1MB"
        session["bg_color"] = "danger"
        return redirect(url_for("view.account"))

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # 500
    @app.errorhandler(500)
    def internal_server_error(e):
        print(e, "error in 500")
        return render_template('500.html'), 500

    # operational error
    @app.errorhandler(OperationalError)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # teardown request
    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()
        if exception and db.session.is_active:
            db.session.rollback()

    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=20)
        session.modified = True
        flask.g.user = current_user

    app.register_blueprint(AuthenticationBlueprint)
    app.register_blueprint(ViewBlueprint)
    app.register_blueprint(BillsBlueprint)
    app.register_blueprint(ExternalBlueprint, url_prefix="/api/v1")

    return app
