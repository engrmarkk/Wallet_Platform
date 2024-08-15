from flask_mail import Message
from extensions import mail
from flask import render_template, flash
import random
import pyotp
from extensions import db


def determine_purchase_type(service_id):
    if service_id.lower() in ["mtn", "glo", "etisalat", "airtel"]:
        return "airtime"
    elif service_id.lower() in ["mtn-data", "glo-data", "etisalat-data", "airtel-data", "smiles", "spectranet"]:
        return "data"
    elif service_id.lower() in ["ikeja-electric", "eko-electric", "abuja-electric", "kano-electric",
                                "portharcourt-electric",
                                "jos-electric", "kaduna-electric", "enugu-electric", "ibadan-electric",
                                "benin-electric",
                                "aba-electric", "yola-electric"]:
        return "electricity"
    elif service_id.lower() in ["dstv", "gotv", "startimes", "showmax"]:
        return "cable"
    else:
        return None


def send_notification(current_user, amount, description, x, phone):
    try:
        msg = Message(
            subject="DEBIT ALERT",
            sender="EasyTransact <easytransact.send@gmail.com>",
            recipients=[current_user.email],
        )
        msg.html = render_template(
            "debit_bills.html",
            amount=f"{amount:,.2f}",
            description=description,
            phone=phone,
            balance=f"{current_user.account_balance:,.2f}",
            date=x,
            acct=str(current_user.account_number),
        )
        mail.send(msg)
    except Exception as e:
        print(e, "ERROR")
        flash("Network Error", "danger")


def send_credit_notification(subject, current_user, amount, description, x, phone):
    try:
        msg = Message(
            subject=subject,
            sender="EasyTransact <easytransact.send@gmail.com>",
            recipients=[current_user.email],
        )
        msg.html = render_template(
            "credit_bills.html",
            amount=f"{amount:,.2f}",
            balance=f"{current_user.account_balance:,}",
            description=description,
            phone=phone,
            user=current_user,
            date=x,
            acct=str(current_user.account_number),
        )
        mail.send(msg)
    except Exception as e:
        print(e, "ERROR")
        flash("Network error", "danger")


def generate_session_id():
    return f"000011{str(random.randint(1000000000, 9999999999))}"


def generate_transaction_ref(tr_type):
    return f"{tr_type}-{str(random.randint(1000000000, 9999999999))}"


def generate_secret_key():
    return pyotp.random_base32()


def generate_uri(secret_key, user, issuer_name="EasyTransact"):
    return pyotp.totp.TOTP(secret_key).provisioning_uri(name=user.email, issuer_name=issuer_name)


def get_uri(user):
    secret_for_user = generate_secret_key() if not user.secret_2fa else user.secret_2fa
    uri = generate_uri(secret_for_user, user)

    print(user.secret_2fa, "before")
    user.secret_2fa = secret_for_user
    db.session.commit()

    print(user.secret_2fa, "after")

    res = {
        'uri': uri,
        'secret': user.secret_2fa,
        'issuer_name': 'EasyTransact',
        'account_name': user.email
    }

    print(res, "res")

    return res


def verify_totp_factor(user, auth_code):
    return pyotp.TOTP(user.secret_2fa).verify(auth_code)


def authenticate_auth_code(user, auth_code):
    is_approved = verify_totp_factor(user, auth_code)
    return is_approved
