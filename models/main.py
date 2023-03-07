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
    savings = db.Column(db.Integer, default=0)
    invite_earn = db.Column(db.Integer, default=0)
    invited_by = db.Column(db.Integer, default=0)
    photo = db.Column(db.Text, nullable=False, default='https://res.cloudinary.com/duwyopabr/image/upload/v1676162283/user_xz7o0f.png')
    transaction_pin = db.Column(db.Integer, nullable=False, default=1)
    secret_question = db.Column(db.Text, nullable=True)
    secret_answer = db.Column(db.String(50), nullable=True)
    pin_set = db.Column(db.Boolean, default=False)
    transacts = db.relationship("Transaction", backref="author", lazy=True)
    beneficiaries = db.relationship("Beneficiary", backref="user_account", lazy=True)
    card = db.relationship("Card", backref="card_owner", cascade="all, delete", lazy=True)
    invitees = db.relationship('Invitees', backref='inviter', cascade="all, delete", lazy=True)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)

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
