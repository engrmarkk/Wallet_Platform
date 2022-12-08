from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
# from flask_login import login_user, current_user, logout_user, login_required, UserMixin, LoginManager
from flask_login import LoginManager


db = SQLAlchemy()
app = Flask(__name__)
mail = Mail()
login_manager = LoginManager()
