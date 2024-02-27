from extensions import db
from flask_login import UserMixin
import uuid


def hexid():
    return uuid.uuid4().hex


class Invitees(db.Model, UserMixin):
    id = db.Column(db.String(100), default=hexid, primary_key=True)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    invited_by = db.Column(db.String(100), db.ForeignKey("user.id"))
