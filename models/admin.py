from extensions import db, app
from flask_login import UserMixin
import uuid
from datetime import datetime


def hexid():
    return uuid.uuid4().hex


# creating the User table in the database
class Admin(db.Model, UserMixin):
    id = db.Column(db.String(100), default=hexid, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(70), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True)
    phone_number = db.Column(db.String(30), unique=True, nullable=True)
    is_super_admin = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        db.session.commit()
