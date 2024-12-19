from extensions import db, app
from flask_login import UserMixin
import jwt
from time import time
import uuid
import os
from datetime import datetime


def hexid():
    return uuid.uuid4().hex


# creating the User table in the database
class User(db.Model, UserMixin):
    id = db.Column(db.String(100), default=hexid, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(70), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    panic_password = db.Column(db.Text, nullable=True)
    phone_number = db.Column(db.BigInteger, unique=True, nullable=False)
    account_number = db.Column(db.BigInteger, unique=True, nullable=False)
    account_balance = db.Column(db.Float, default=20000)
    panic_balance = db.Column(db.Float, default=0)
    panic_mode = db.Column(db.Boolean, default=False)
    has_set_panic = db.Column(db.Boolean, default=False)
    savings = db.Column(db.Float, default=0)
    spend_save_amount = db.Column(db.Float, default=0)
    invite_earn = db.Column(db.Integer, nullable=False, default=0)
    invited_by = db.Column(db.BigInteger, nullable=False, default=0)
    photo = db.Column(
        db.Text,
        nullable=False,
        default="https://res.cloudinary.com/duwyopabr/image/upload/v1676162283/user_xz7o0f.png",
    )
    transaction_pin = db.Column(db.Text, nullable=False, default="")
    secret_question = db.Column(db.Text, nullable=True)
    secret_answer = db.Column(db.String(50), nullable=True)
    pin_set = db.Column(db.Boolean, default=False)
    secret_2fa = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    transacts = db.relationship("Transaction", backref="author", lazy=True)
    beneficiaries = db.relationship("Beneficiary", backref="user_account", lazy=True)
    card = db.relationship(
        "Card", backref="card_owner", cascade="all, delete", lazy=True
    )
    invitees = db.relationship(
        "Invitees", backref="inviter", cascade="all, delete", lazy=True
    )
    user_session = db.relationship(
        "UserSession", backref="user", lazy=True, uselist=False
    )
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    enabled_2fa = db.Column(db.Boolean, default=False)
    enabled_spend_save = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime, nullable=True, default=datetime.now)

    # Define a representation with two attribute 'username' and 'email'
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def get_reset_token(self, expires_sec=1800):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_sec},
            key=os.getenv("SECRET_KEY"),
        )

    @staticmethod
    def verify_reset_token(token):
        try:
            id = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])[
                "reset_password"
            ]
        except Exception as e:
            print(e, "error in token verification")
            return None
        return User.query.get(id)


class UserSession(db.Model):
    id = db.Column(db.String(100), default=hexid, primary_key=True)
    user_id = db.Column(db.String(100), db.ForeignKey("user.id"), nullable=False)
    otp = db.Column(db.String(6), nullable=False)


def get_account_number_details(acct_number):
    return User.query.filter_by(account_number=acct_number).first()


def create_user_session(user_id, otp):
    user_session = UserSession.query.filter_by(user_id=user_id).first()
    if user_session:
        user_session.otp = otp
    else:
        user_session = UserSession(user_id=user_id, otp=otp)
        db.session.add(user_session)
    db.session.commit()
    return user_session
