from extensions import db
from flask_login import UserMixin
from datetime import datetime
import random
import uuid


def hexid():
    return uuid.uuid4().hex


class TransactionCategories(db.Model):
    __tablename__ = "transaction_categories"
    id = db.Column(db.String(100), default=hexid, primary_key=True)
    category = db.Column(db.String(100), nullable=False)

    # relationship to transaction table
    transaction = db.relationship("Transaction", backref="trans_category", lazy=True)


# creating the Transaction table in the database
class Transaction(db.Model, UserMixin):
    __tablename__ = "transaction"
    id = db.Column(db.String(100), default=hexid, primary_key=True)
    transaction_type = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    transaction_amount = db.Column(db.Float, nullable=False)
    balance = db.Column(db.Float, nullable=False)
    transaction_ref = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), db.ForeignKey("transaction_categories.id"))
    token = db.Column(db.String(200))
    description = db.Column(db.String(200))
    status = db.Column(db.String(100))
    phone_number = db.Column(db.String(100))
    sender = db.Column(db.String(100))
    user_id = db.Column(db.String(100), db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"Transaction('{self.transaction_type}', '{self.date_posted}')"


class Card(db.Model):
    __tablename__ = "card"
    id = db.Column(db.String(100), default=hexid, primary_key=True)
    card_number = db.Column(db.String(16), unique=True, nullable=False)
    cvv = db.Column(db.String(3), nullable=False)
    expiry_date = db.Column(db.String(5), nullable=False)
    user_id = db.Column(db.String(100), db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
