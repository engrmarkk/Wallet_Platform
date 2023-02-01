from extensions import db
from flask_login import UserMixin


# creating the User table in the database
class Beneficiary(db.Model, UserMixin):
    __tablename__ = "beneficiary"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    account_number = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # Define a representation with two attribute 'first_name' and 'last_name'
    def __repr__(self):
        return f"Beneficiary('{self.first_name}', '{self.last_name}')"
