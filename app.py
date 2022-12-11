from extensions import app, db, login_manager, mail
from flask import redirect, flash, url_for
from routes import AuthenticationBlueprint, ViewBlueprint
from models import User
import os


def create_app():
    base_dir = os.path.dirname(os.path.realpath(__file__))

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        base_dir, "wallet.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "4f557e8e5eb51bfb7c42"
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 465
    app.config["MAIL_USERNAME"] = "atmme1992@gmail.com"
    app.config["MAIL_PASSWORD"] = "dvogogdoinarpugn"
    app.config["MAIL_USE_TLS"] = False
    app.config["MAIL_USE_SSL"] = True

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

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

    app.register_blueprint(AuthenticationBlueprint)
    app.register_blueprint(ViewBlueprint)

    return app
