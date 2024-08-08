from flask import (
    request,
    render_template,
    Blueprint,
    jsonify,
)
from extensions import db, mail
from func import get_cat
from flask_mail import Message
from models.main import get_account_number_details
from models.transact import save_transfer_in_transactions
from utils import generate_session_id, generate_transaction_ref

external = Blueprint("external", __name__, template_folder="../templates")


@external.route("/account_lookup", methods=["POST"])
def account_lookup():
    try:
        data = request.get_json()
        account_number = data.get("account_number")
        if not account_number:
            return jsonify({"success": False, "message": "Account number is required", "code": 0})

        details = get_account_number_details(account_number)
        if details:
            return jsonify({"success": True, "message": "Account number found", "code": 1,
                            "account_details": {
                                "account_name": f"{details.last_name} {details.first_name}",
                                "account_number": details.account_number
                            }})
        else:
            return jsonify({"success": False, "message": "Account number not found", "code": 0,
                            "account_details": {}}), 400

    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": "Network Error", "code": 0}), 400


# transfer in
@external.route("/transfer_in", methods=["POST"])
def transfer_in():
    try:
        data = request.get_json()
        account_number = data.get("account_number")
        amount = data.get("transaction_amount")
        sender_account = data.get("sender_account_number")
        sender_name = data.get("sender_name")
        account_name = data.get("account_name")
        description = data.get("narration")
        bank_name = data.get("bank_name")
        if not account_number:
            return jsonify({"success": False, "message": "Account number is required", "code": 0})

        if not amount:
            return jsonify({"success": False, "message": "Amount is required", "code": 0})

        if not sender_account:
            return jsonify({"success": False, "message": "Sender account number is required", "code": 0})

        if not sender_name:
            return jsonify({"success": False, "message": "Sender name is required", "code": 0})

        if not account_name:
            return jsonify({"success": False, "message": "Account name is required", "code": 0})

        if not bank_name:
            return jsonify({"success": False, "message": "Bank name is required", "code": 0})

        details = get_account_number_details(account_number)
        trans_ref = generate_transaction_ref()
        sess_id = generate_session_id()
        if details:
            balance_before_topup = details.account_balance
            balance = balance_before_topup + amount
            trans = save_transfer_in_transactions(transaction_type="CRT", transaction_amount=amount,
                                                  user_id=details.id, balance=balance,
                                                  description=description or "TopUp",
                                                  category=get_cat("Wallet-Topup"),
                                                  transaction_ref=trans_ref, session_id=sess_id,
                                                  sender_account=str(sender_account),
                                                  receiver_account=str(account_number), sender=sender_name,
                                                  receiver=f"{details.last_name} {details.first_name}",
                                                  status="Success", bank_name=bank_name)
            details.account_balance = balance
            db.session.commit()

            try:
                msg = Message(
                    subject="CREDIT ALERT",
                    sender="EasyTransact <easytransact.send@gmail.com>",
                    recipients=[details.email],
                )
                msg.html = render_template(
                    "topup.html",
                    user=details,
                    amount=f"{amount:,.2f}",
                    balance=f"{details.account_balance:,.2f}",
                    date=trans.date_posted,
                    acct=str(details.account_number),
                    sender=sender_name,
                    sender_acct=sender_account,
                    bank_name=bank_name,
                )
                mail.send(msg)
            except Exception as e:
                print(e, "ERROR")

            return jsonify({"success": True, "message": "Transfer in successful", "code": 1,
                            "transaction": {
                                "receiver_account_name": f"{details.last_name} {details.first_name}",
                                "receiver_account_number": details.account_number,
                                "sender_account_name": sender_name,
                                "sender_account_number": sender_account,
                                "session_id": sess_id,
                                "amount": amount,
                                "date": trans.date_posted.strftime("%d-%m-%Y %H:%M:%S"),
                            }}), 200
        else:
            return jsonify({"success": False, "message": "Transfer in failed", "code": 0,
                            "transaction": {}}), 400

    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": "Network Error", "code": 0}), 400
