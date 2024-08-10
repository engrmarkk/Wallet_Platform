from flask_mail import Message
from extensions import mail
from flask import render_template, flash
import random


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
