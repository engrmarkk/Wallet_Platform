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
    customer_name = db.Column(db.String(200))
    bank_name = db.Column(db.String(200))
    session_id = db.Column(db.String(100))
    status = db.Column(db.String(100))
    phone_number = db.Column(db.String(100))
    sender = db.Column(db.String(100))
    sender_account = db.Column(db.String(100))
    receiver_account = db.Column(db.String(100))
    receiver = db.Column(db.String(100))
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


def save_transfer_in_transactions(transaction_type, transaction_amount, user_id, balance, description, category,
                                  transaction_ref, session_id, sender_account, receiver_account, sender, receiver,
                                  status, bank_name):
    trans = Transaction(
        transaction_type=transaction_type,
        transaction_amount=transaction_amount,
        user_id=user_id,
        balance=balance,
        description=description,
        category=category,
        transaction_ref=transaction_ref,
        session_id=session_id,
        sender_account=sender_account,
        receiver_account=receiver_account,
        sender=sender,
        receiver=receiver,
        status=status,
        bank_name=bank_name
    )
    db.session.add(trans)
    db.session.commit()
    return trans
