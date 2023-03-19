from extensions import db, login_manager, mail, migrate, moment
from flask import redirect, flash, url_for, session, render_template, Flask
from routes import AuthenticationBlueprint, ViewBlueprint
from models import User
from datetime import timedelta
import os
import flask
from flask_login import current_user
from decouple import config

db_name = 'wallet'
# default_uri = "postgres://{}:{}@{}/{}".format('postgres', 'password', 'localhost:5432', db_name)
uri = config('DATABASE_URL')  # or other relevant config var
if uri.startswith('postgres://'):
    uri = uri.replace('postgres://', 'postgresql://', 1)


def create_app():
    base_dir = os.path.dirname(os.path.realpath(__file__))

    # app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    #     base_dir, "wallet.db"
    # )

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "4f557e8e5eb51bfb7c42"
    app.config['DEBUG'] = True
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
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
        return User.query.get(int(id))

    # If the user isn't logged in and tries to access a login required route, this decorator allows the page to
    # redirect page to the login
    @login_manager.unauthorized_handler
    def unauthorized_handler():
        flash("Login to access this page", category="info")
        return redirect(url_for("auth.login"))

    # with app.app_context():
    #     db.create_all()

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=10)
        session.modified = True
        flask.g.user = current_user

    app.register_blueprint(AuthenticationBlueprint)
    app.register_blueprint(ViewBlueprint)

    return app
