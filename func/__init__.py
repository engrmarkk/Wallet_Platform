import os
import secrets
from models import TransactionCategories, Transaction, Admin
from flask import current_app, session, redirect, url_for, flash
from PIL import Image
from extensions import db
from functools import wraps
from datetime import datetime, timedelta
from flask_login import logout_user
import pytz
import random
import string
from utils import send_notification, send_credit_notification


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


trans_cats = ["Transfer", "Airtime", "Electricity", "Tv-Subscription",
              "Internet-Data", "W2W", "Savings", "Referral", "Wallet-Topup", "Transfer"]

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


def deduct_history(amount, current_user, request_id, purchase_type, service_id, phone="", customer_name="", verify_number="", panic=False):
    print(purchase_type, "purchase type")
    print("got here@deduct")

    if panic:
        current_user.panic_balance -= amount
    current_user.account_balance -= amount
    db.session.commit()

    cat = return_cat_type(purchase_type)

    description = "Purchase for " + cat + "/" + service_id
    if verify_number:
        description = description + "/" + verify_number

    transact = Transaction(
        transaction_type="DBT",
        transaction_amount=amount,
        balance=current_user.account_balance,
        transaction_ref=cat + "-" + request_id,
        phone_number=phone,
        description=description,
        status="Pending",
        category=get_cat(cat),
        user_id=current_user.id,
        customer_name=customer_name,
        panic_mode=panic
    )
    db.session.add(transact)
    db.session.commit()
    send_notification(current_user, amount, description, transact.date_posted, phone)
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
        panic_mode=True if current_user.panic_mode else False
    )
    db.session.add(transact)
    db.session.commit()
    send_credit_notification("REFUND", current_user, amount, transact.description, transact.date_posted, phone)
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


#  create admin
def create_admin(first_name, last_name, email, password, is_super_admin=False):
    try:
        admin = Admin(first_name=first_name, last_name=last_name, email=email,
                      password=password, is_super_admin=is_super_admin)
        db.session.add(admin)
        db.session.commit()
        return admin
    except Exception as e:
        print(e)
        db.session.rollback()
        return None


# create super admin
def create_super_admin(first_name, last_name, email, password):
    return create_admin(first_name, last_name, email, password, is_super_admin=True)


# get all admins
def get_all_admins(page, per_page, email, is_super_admin, fullname):
    try:
        admins = Admin.query
        if email:
            admins = admins.filter(Admin.email.ilike(f"%{email}%"))
        if is_super_admin:
            admins = admins.filter(Admin.is_super_admin == True)
        if fullname:
            admins = admins.filter(Admin.first_name.ilike(f"%{fullname}%") | Admin.last_name.ilike(f"%{fullname}%"))
        paginated_admins = admins.order_by(Admin.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return paginated_admins
    except Exception as e:
        print(e, "error in get_all_admins")
        db.session.rollback()
        return None
