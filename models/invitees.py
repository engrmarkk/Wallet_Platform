from extensions import db
from flask_login import UserMixin


class Invitees(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    invited_by = db.Column(db.Integer, db.ForeignKey("user.id"))
