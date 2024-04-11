import os
import secrets
from models import TransactionCategories, Transaction
from flask import current_app, session, redirect, url_for, flash
from PIL import Image
from extensions import db
from functools import wraps
from datetime import datetime, timedelta
from flask_login import logout_user
import pytz
import random
import string


def generate_reference():
    characters = string.digits + string.ascii_uppercase
    return "".join(random.choice(characters) for _ in range(16))


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


trans_cats = ["Transfer", "Airtime", "Electricity", "Tv-Subscription", "Internet-Data", "W2W", "Savings", "Referral"]

# W2W stands for wallet to wallet


def save_transaction_cat():
    if not TransactionCategories.query.first():
        for cat in trans_cats:
            new_cat = TransactionCategories(category=cat)
            db.session.add(new_cat)
            db.session.commit()
        return True
    else:
        return False


def get_all_cats():
    return TransactionCategories.query.order_by(TransactionCategories.category).all()


def get_cat(cat):
    return TransactionCategories.query.filter_by(category=cat).first().id


def return_cat_type(purchase_type):
    if purchase_type == 'airtime':
        return 'Airtime'
    elif purchase_type == 'electricity':
        return 'Electricity'
    elif purchase_type == 'cable':
        return 'Tv-Subscription'
    elif purchase_type == 'data':
        return 'Internet-Data'


def deduct_history(amount, current_user, request_id, purchase_type, service_id, phone="", customer_name=""):
    print(purchase_type, "purchase type")
    print("got here@deduct")
    current_user.account_balance -= amount
    db.session.commit()

    cat = return_cat_type(purchase_type)

    transact = Transaction(
        transaction_type="DBT",
        transaction_amount=amount,
        balance=current_user.account_balance,
        transaction_ref=cat + "-" + request_id,
        phone_number=phone,
        description="Purchase for " + cat + "/" + service_id,
        status="Pending",
        category=get_cat(cat),
        user_id=current_user.id,
        customer_name=customer_name
    )
    db.session.add(transact)
    db.session.commit()
    return transact


def refund(amount, current_user, request_id, purchase_type, service_id, phone=""):
    print("got here@refund")
    current_user.account_balance += amount
    db.session.commit()

    cat = return_cat_type(purchase_type)

    transact = Transaction(
        transaction_type="CRT",
        transaction_amount=amount,
        balance=current_user.account_balance,
        transaction_ref=cat + "-" + request_id,
        category=get_cat(cat),
        phone_number=phone,
        description="Refund for " + cat + "/" + service_id,
        status="Refunded",
        user_id=current_user.id,
    )
    db.session.add(transact)
    db.session.commit()
    return transact


def update_transaction(token, transact):
    print("got here@updateTransaction")
    transact.token = token
    db.session.commit()
    return True


def update_status(transact, status):
    transact.status = status
    db.session.commit()
    return True
