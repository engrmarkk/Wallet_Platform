import os
import secrets
from flask import current_app, session, redirect, url_for, flash
from PIL import Image
from functools import wraps
from datetime import datetime, timedelta
from flask_login import logout_user
import pytz


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

