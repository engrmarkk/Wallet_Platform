import os
import secrets
from models import TransactionCategories, Transaction, Admin, User
from flask import current_app, session, redirect, url_for, flash
from PIL import Image
from extensions import db
from functools import wraps
from datetime import datetime, timedelta, date
from flask_login import logout_user
import pytz
import random
import string
from utils import send_notification, send_credit_notification
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func


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
        print("creating admin with is super admin", is_super_admin)
        admin = Admin(first_name=first_name, last_name=last_name, email=email,
                      password=password, is_super_admin=is_super_admin)
        db.session.add(admin)
        db.session.commit()
        return admin
    except IntegrityError:
        db.session.rollback()
        return "Email already exists"
    except Exception as e:
        print(e)
        db.session.rollback()
        return None


# create super admin
def create_super_admin(first_name, last_name, email, password):
    print("I am creating super admin")
    return create_admin(first_name, last_name, email, password, is_super_admin=True)


# get all admins
def get_all_admins(page, per_page, email, is_super_admin, fullname, phone):
    try:
        admins = Admin.query
        if email:
            admins = admins.filter(Admin.email.ilike(f"%{email}%"))
        if is_super_admin:
            admins = admins.filter(Admin.is_super_admin == True)
        if phone:
            admins = admins.filter(Admin.phone_number.ilike(f"%{phone}%"))
        if fullname:
            admins = admins.filter(Admin.first_name.ilike(f"%{fullname}%") | Admin.last_name.ilike(f"%{fullname}%"))
        paginated_admins = admins.order_by(Admin.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return paginated_admins
    except Exception as e:
        print(e, "error in get_all_admins")
        db.session.rollback()
        return None


def get_all_users(page, per_page, email, fullname, phone_number, user_name, account_number, has_set_panic):
    try:
        users = User.query
        user_count = users.count()
        completed_user = users.filter(User.confirmed == True).count()
        active_users = users.filter(User.active == True).count()
        if email:
            users = users.filter(User.email.ilike(f"%{email}%"))
        if fullname:
            users = users.filter(User.first_name.ilike(f"%{fullname}%")) | users.filter(
                User.last_name.ilike(f"%{fullname}%"))
        if phone_number:
            users = users.filter(User.phone_number.ilike(f"%{phone_number}%"))
        if user_name:
            users = users.filter(User.username.ilike(f"%{user_name}%"))
        if account_number:
            users = users.filter(User.account_number.ilike(f"%{account_number}%"))
        if has_set_panic:
            users = users.filter(User.has_set_panic == True)
        paginated_users = users.order_by(User.date_joined.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return paginated_users, user_count, completed_user, active_users
    except Exception as e:
        print(e, "error in get_all_users")
        db.session.rollback()
        return None, None, None, None


# get one user
def get_one_user(user_id):
    try:
        user = User.query.get(user_id)
        return user
    except Exception as e:
        print(e, "error in get_one_user")
        db.session.rollback()
        return None


def get_one_admin(admin_id):
    try:
        admin = Admin.query.get(admin_id)
        return admin
    except Exception as e:
        print(e, "error in get_one_admin")
        db.session.rollback()
        return None


def get_user_transactions(page, per_page, transaction_type, status, category, user):
    try:
        transactions = Transaction.query.filter(Transaction.user_id == user.id)
        all_transactions = transactions.count()
        successful_transactions = transactions.filter(Transaction.status == "Success").count()
        pending_transactions = transactions.filter(Transaction.status == "Pending").count()
        failed_transactions = transactions.filter(Transaction.status == "Failed").count()
        inflow_transactions = transactions.filter(Transaction.transaction_type == "CRT").count()
        outflow_transactions = transactions.filter(Transaction.transaction_type == "DBT").count()
        if transaction_type:
            transactions = transactions.filter(Transaction.transaction_type == transaction_type)
        if status:
            transactions = transactions.filter(Transaction.status == status)
        if category:
            transactions = transactions.filter(Transaction.category == category)
        paginated_transactions = transactions.order_by(Transaction.date_posted.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return paginated_transactions, all_transactions, successful_transactions, pending_transactions, failed_transactions, inflow_transactions, outflow_transactions
    except Exception as e:
        print(e, "error in get_user_transactions")
        db.session.rollback()
        return None, None, None, None, None, None, None


def get_all_transactions(page, per_page, status, transaction_type, category, bank_name, receiver):
    try:
        transactions = Transaction.query
        all_trans_count = transactions.count()
        success_counts = transactions.filter(Transaction.status == "Success").count()
        pending_counts = transactions.filter(Transaction.status == "Pending").count()
        failed_counts = transactions.filter(Transaction.status == "Failed").count()
        inflow = transactions.filter(Transaction.transaction_type == "CRT").count()
        outflow = transactions.filter(Transaction.transaction_type == "DBT").count()
        if status:
            transactions = transactions.filter(Transaction.status.ilike(status))
        if transaction_type:
            transactions = transactions.filter(Transaction.transaction_type.ilike(transaction_type))
        if category:
            transactions = transactions.filter(Transaction.category == category)
        if bank_name:
            transactions = transactions.filter(Transaction.bank_name.ilike(f"%{bank_name}%"))
        if receiver:
            transactions = transactions.filter(Transaction.receiver.ilike(f"%{receiver}%"))
        paginated_transactions = transactions.order_by(Transaction.date_posted.desc()).paginate(page=page,
                                                                                                per_page=per_page, error_out=False)
        return paginated_transactions, all_trans_count, success_counts, pending_counts, failed_counts, inflow, outflow
    except Exception as e:
        print(e, "error in get_all_transactions")
        db.session.rollback()
        return None, None, None, None, None, None


def statistics():
    """
    Collect various statistics regarding users and transactions.
    """
    try:
        all_users = User.query.count()

        # Helper function to handle None values
        def safe_first(query_result):
            return query_result if query_result is not None else (0, 0)

        # Aggregate transactions
        transaction_stats = {
            "all": safe_first(Transaction.query.with_entities(
                func.count(), func.sum(Transaction.transaction_amount)
            ).first()),
            "success": safe_first(Transaction.query.filter(Transaction.status == "Success").with_entities(
                func.count(), func.sum(Transaction.transaction_amount)
            ).first()),
            "pending": safe_first(Transaction.query.filter(Transaction.status == "Pending").with_entities(
                func.count(), func.sum(Transaction.transaction_amount)
            ).first()),
            "failed": safe_first(Transaction.query.filter(Transaction.status == "Failed").with_entities(
                func.count(), func.sum(Transaction.transaction_amount)
            ).first()),
            "inflow": safe_first(Transaction.query.filter(Transaction.transaction_type == "CRT").with_entities(
                func.count(), func.sum(Transaction.transaction_amount)
            ).first()),
            "outflow": safe_first(Transaction.query.filter(Transaction.transaction_type == "DBT").with_entities(
                func.count(), func.sum(Transaction.transaction_amount)
            ).first()),
        }

        # Transaction counts and amounts by category
        categories = [
            "Electricity", "Airtime", "Internet-Data",
            "TV Subscription", "W2W", "Transfer", "Wallet-Topup"
        ]

        category_stats = {}
        for category in categories:
            count, amount = (
                db.session.query(
                    func.count(),
                    func.sum(Transaction.transaction_amount)
                )
                .join(TransactionCategories, Transaction.category == TransactionCategories.id)
                .filter(TransactionCategories.category == category)
                .first() or (0, 0)
            )
            category_stats[category] = {
                "count": count,
                "amount": amount or 0
            }

        # Transactions per day
        current_date = date.today()
        transactions_today = safe_first(
            Transaction.query.filter(func.date(Transaction.date_posted) == current_date)
            .with_entities(func.count(), func.sum(Transaction.transaction_amount))
            .first()
        )

        # Prepare results
        results = {
            "all_users": all_users,
            "all_transactions_count": transaction_stats["all"][0],
            "all_transactions_amount": transaction_stats["all"][1] or 0,
            "success_count": transaction_stats["success"][0],
            "success_amount": transaction_stats["success"][1] or 0,
            "pending_count": transaction_stats["pending"][0],
            "pending_amount": transaction_stats["pending"][1] or 0,
            "failed_count": transaction_stats["failed"][0],
            "failed_amount": transaction_stats["failed"][1] or 0,
            "inflow_count": transaction_stats["inflow"][0],
            "inflow_amount": transaction_stats["inflow"][1] or 0,
            "outflow_count": transaction_stats["outflow"][0],
            "outflow_amount": transaction_stats["outflow"][1] or 0,
            **category_stats,
            "transactions_today_count": transactions_today[0],
            "transactions_today_amount": transactions_today[1] or 0
        }

        return results
    except Exception as e:
        print(e, "error in statistics")
        db.session.rollback()
        return {}
