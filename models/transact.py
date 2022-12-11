from extensions import db
from flask_login import UserMixin
from datetime import datetime


# creating the Transaction table in the database
class Transaction(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    transaction_amount = db.Column(db.Integer, nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
