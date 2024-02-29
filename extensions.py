from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_moment import Moment


db = SQLAlchemy()
app = Flask(__name__)
mail = Mail()
login_manager = LoginManager()
migrate = Migrate()
sess = Session()
moment = Moment()
