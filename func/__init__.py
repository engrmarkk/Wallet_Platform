import os
import secrets
from flask import current_app, session, redirect, url_for, flash
from PIL import Image
from functools import wraps
from datetime import datetime, timedelta
from flask_login import logout_user


def save_image(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static\\images\\profile', picture_fn)

    output_size = (1200, 1200)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def check_user_activity(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        last_activity = session.get('last_activity')
        if last_activity is not None and datetime.now() - last_activity > timedelta(minutes=5):
            logout_user()  # or you could call your custom logout function here
            flash("Session expired", "danger")
            return redirect(url_for('auth.login'))
        session['last_activity'] = datetime.now()
        return f(*args, **kwargs)
    return decorated_function
