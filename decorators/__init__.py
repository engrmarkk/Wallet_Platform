from func import wraps
from models import Admin
from flask_login import current_user
from flask import redirect, url_for


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Admin.query.filter_by(id=current_user.id).first():
            return redirect(url_for("view.home"))
        return f(*args, **kwargs)

    return decorated_function


def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin = Admin.query.filter_by(id=current_user.id).first()
        if not admin or not admin.is_super_admin:
            return redirect(url_for("view.home"))
        return f(*args, **kwargs)

    return decorated_function


def user_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return redirect(url_for("view.home"))
        return f(*args, **kwargs)

    return decorated_function
