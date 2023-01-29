from extensions import db, app
from flask_login import UserMixin
import jwt
from time import time


# creating the User table in the database
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(70), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    phone_number = db.Column(db.Integer, unique=True, nullable=False)
    account_number = db.Column(db.Integer, unique=True, nullable=False)
    account_balance = db.Column(db.Integer, default=20000)
    transacts = db.relationship("Transaction", backref="author", lazy=True)

    # Define a representation with two attribute 'username' and 'email'
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def get_reset_token(self, expires_sec=1800):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_sec}, key=app.config['SECRET_KEY'])

    @staticmethod
    def verify_reset_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(id)