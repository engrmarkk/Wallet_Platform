from flask_mail import Message
from extensions import mail
from flask import render_template, flash

def determine_purchase_type(service_id):
    if service_id.lower() in ["mtn", "glo", "etisalat", "airtel"]:
        return "airtime"
    elif service_id.lower() in ["mtn-data", "glo-data", "etisalat-data", "airtel-data", "smiles", "spectranet"]:
        return "data"
    elif service_id.lower() in ["ikeja-electric", "eko-electric", "abuja-electric", "kano-electric", "portharcourt-electric",
                                "jos-electric", "kaduna-electric", "enugu-electric", "ibadan-electric", "benin-electric",
                                "aba-electric", "yola-electric"]:
        return "electricity"
    elif service_id.lower() in ["dstv", "gotv", "startimes", "showmax"]:
        return "cable"
    else:
        return None


def send_notification(current_user, amount, user1, x):
    try:
        msg = Message(
            subject="DEBIT ALERT",
            sender="EasyTransact <easytransact.send@gmail.com>",
            recipients=[current_user.email],
        )
        msg.html = render_template(
            "debit.html",
            amount=f"{amount:,.2f}",
            user=user1,
            balance=f"{current_user.account_balance:,}",
            date=x,
            acct=str(current_user.account_number),
        )
        mail.send(msg)
    except Exception as e:
        print(e, "ERROR")
        flash("Network Error", "danger")
