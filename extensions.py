from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_migrate import Migrate


db = SQLAlchemy()
app = Flask(__name__)
mail = Mail()
login_manager = LoginManager()
migrate = Migrate()
