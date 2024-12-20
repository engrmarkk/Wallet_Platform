from datetime import datetime

from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.security import check_password_hash
from extensions import mail, db
from flask_mail import Message
from flask_login import current_user, login_required
from flask import (
    redirect,
    url_for,
    request,
    session,
    render_template,
    Blueprint,
    make_response,
    jsonify,
)
from models import User, Transaction, Beneficiary, Card, Invitees
from models.transact import save_transfer_in_transactions, save_spend_and_save_transaction
from form import *
from func import save_transaction_cat, get_cat, get_all_cats
from werkzeug.security import generate_password_hash
from sqlalchemy import func
import random
import datetime
import cloudinary
import os
import requests
import cloudinary.uploader
import cloudinary_config
from routes.auth import login
from passlib.hash import pbkdf2_sha256 as hasher
import random
import string
from utils import (
    generate_session_id,
    generate_transaction_ref,
    get_uri,
    authenticate_auth_code,
)
from paystack.paystack_endpoint import PaystackEndpoints

view = Blueprint("view", __name__, template_folder="../templates")

pay_stack = PaystackEndpoints()


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message(
        "Password Reset Request",
        sender="EasyTransact <easytransact.send@gmail.com>",
        recipients=[user.email],
    )
    msg.html = render_template("reset_email.html", user=user, token=token)

    mail.send(msg)


def generate_reference():
    characters = string.digits + string.ascii_uppercase
    return "".join(random.choice(characters) for _ in range(16))


def generate_card_number():
    card_number = "".join([str(random.randint(0, 9)) for i in range(16)])
    if Card.query.filter_by(card_number=card_number).first() is None:
        return card_number
    else:
        return generate_card_number()


x = datetime.datetime.now()
z = x.strftime("%m" + "/" + "%y")


def create_expiry_date(days_to_expire):
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=days_to_expire)
    return expiry_date.strftime("%m" + "/" + "%y")


expiration = create_expiry_date(912)


@view.route("/")
def front_page():
    try:
        # save_transaction_cat()
        alert = session.pop("alert", None)
        bg_color = session.pop("bg_color", None)
        if current_user.is_authenticated:
            return redirect(url_for("view.home"))
        return render_template("front.html", date=x, alert=alert, bg_color=bg_color)
    except Exception as e:
        print(e, "error in front page")


@view.route("/account/", methods=["GET", "POST"])
@login_required
def account():
    form = PhotoForm()
    pinset = current_user.pin_set

    if not current_user.enabled_2fa:
        qr_data = get_uri(current_user)
        uri = qr_data["uri"]
    else:
        uri = ""

    print(uri, "URI")

    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if request.method == "POST":
        try:
            f = form.image.data
            if not f:
                session["alert"] = "Nothing to upload"
                session["bg_color"] = "danger"
                return redirect(url_for("view.display_profile"))
            if f.content_length > request.max_content_length:  # check file size
                session["alert"] = "File is too large. Maximum file size is 1MB."
                session["bg_color"] = "danger"
                return redirect(url_for("view.account"))
            result = cloudinary.uploader.upload(
                f, transformation=[{"width": 176, "height": 176, "crop": "fill"}]
            )
            image_url = result["secure_url"]
            current_user.photo = image_url
            db.session.commit()
            session["alert"] = "Profile photo uploaded successfully"
            session["bg_color"] = "success"
            return redirect(url_for("view.account"))
        except ValidationError as e:
            session["alert"] = str(e)
            session["bg_color"] = "danger"
            return redirect(url_for("view.account"))
        except RequestEntityTooLarge:
            session["alert"] = "File is too large. Maximum file size is 1MB."
            session["bg_color"] = "danger"
            return redirect(url_for("view.account"))
    return render_template(
        "account.html",
        pinset=pinset,
        date=x,
        form=form,
        alert=alert,
        bg_color=bg_color,
        uri=uri,
    )


@view.route("/transaction-history")
@login_required
def showtransaction():
    cats = get_all_cats()
    category = None
    types = None
    status = None
    show = False
    category_ = request.args.get("category")
    status_ = request.args.get("status")
    transaction_type = request.args.get("types")
    ref = request.args.get("ref")

    # remove the spaces that might come with the ref
    ref = ref.strip() if ref else ref
    page = request.args.get("page", 1, type=int)
    per_page = 10  # You can adjust the number of items per page as needed
    # print(category, status)
    # print(ref, "reference")
    category = category_ if category_ else category
    status = status_ if status_ else status
    types = transaction_type if transaction_type else types
    if category_ or status_ or transaction_type or ref:
        show = True
    transactions = (
        Transaction.query.filter(
            Transaction.user_id == current_user.id,
            func.lower(Transaction.category) == category_.lower() if category else True,
            func.lower(Transaction.status) == status_.lower() if status else True,
            (
                func.lower(Transaction.transaction_type) == transaction_type.lower()
                if transaction_type
                else True
            ),
            func.lower(Transaction.transaction_ref) == ref.lower() if ref else True,
        )
        .order_by(Transaction.date_posted.desc())
        .paginate(page=page, per_page=per_page)
    )
    # print(transactions.items, "transactions")
    return render_template(
        "show-histories.html",
        date=x,
        transactions=transactions,
        cats=cats,
        types=types,
        status=status,
        category=category,
        ref=ref,
        show=show,
    )


@view.route("/home/", methods=["GET", "POST"])
@login_required
def home():
    form = ConfirmAccount()
    banks = pay_stack.list_banks()
    beneficials = Beneficiary.query.filter_by(user_id=current_user.id).all()
    balance = (
        f"{current_user.panic_balance:,.2f}"
        if current_user.panic_mode and current_user.has_set_panic
        else f"{current_user.account_balance:,.2f}"
    )
    pinset = current_user.pin_set

    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if request.method == "POST":
        try:
            if form.validate_on_submit():
                account_num = int(form.account_number.data)
                user1 = User.query.filter_by(account_number=account_num).first()
                if not user1:
                    session["alert"] = "Invalid account number"
                    session["bg_color"] = "danger"
                    return redirect(url_for("view.home"))
                if account_num == current_user.account_number:
                    session["alert"] = "You can't send money to yourself"
                    session["bg_color"] = "info"
                    return redirect(url_for("view.home"))
                return redirect(url_for("view.pay", acct=account_num))
        except ValueError:
            session["alert"] = "Invalid account number"
            session["bg_color"] = "danger"
            return redirect(url_for("view.home"))

    return render_template(
        "home.html",
        date=x,
        beneficials=beneficials,
        user=current_user,
        balance=balance,
        form=form,
        pinset=pinset,
        banks=banks["data"],
        alert=alert,
        bg_color=bg_color,
    )


@view.route("/create-transfer-pin/", methods=["GET", "POST"])
@login_required
def create_transfer_pin():
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if current_user.pin_set:
        session["alert"] = "Transfer pin already set"
        session["bg_color"] = "info"
        return redirect(url_for("view.home"))
    form = CreateTransferPin()
    if request.method == "POST":
        if form.validate_on_submit():
            pin = int(form.transfer_pin.data)
            secret_question = request.form.get("secret_question")
            secret_answer = form.secret_answer.data.lower()
            user = current_user
            user.secret_question = secret_question
            user.secret_answer = secret_answer
            user.transaction_pin = hasher.hash(str(pin))
            user.pin_set = True
            db.session.commit()
            session["alert"] = "Transfer pin created successfully"
            session["bg_color"] = "success"
            return redirect(url_for("view.home"))
    return render_template(
        "create_transfer_pin.html", date=x, form=form, alert=alert, bg_color=bg_color
    )


# create panic password
@view.route("/create-panic-password/", methods=["GET", "POST"])
@login_required
def create_panic_password():
    try:
        alert = session.pop("alert", None)
        bg_color = session.pop("bg_color", None)
        if current_user.has_set_panic:
            session["alert"] = "Panic password already set"
            session["bg_color"] = "info"
            return redirect(url_for("view.account"))
        if request.method == "POST":
            panic_password = request.form.get("panic_password")
            panic_password2 = request.form.get("panic_password2")
            panic_amount = request.form.get("panic_amount")
            if not panic_password:
                session["alert"] = "Please enter panic password"
                session["bg_color"] = "danger"
                return redirect(url_for("view.create_panic_password"))
            if not panic_password2:
                session["alert"] = "Please confirm panic password"
                session["bg_color"] = "danger"
                return redirect(url_for("view.create_panic_password"))
            if not panic_amount:
                session["alert"] = "Please enter panic amount"
                session["bg_color"] = "danger"
                return redirect(url_for("view.create_panic_password"))
            if panic_password != panic_password2:
                session["alert"] = "Panic passwords do not match"
                session["bg_color"] = "danger"
                return redirect(url_for("view.create_panic_password"))
            if check_password_hash(current_user.password, panic_password):
                session["alert"] = (
                    "Panic password cannot be the same as your login password"
                )
                session["bg_color"] = "danger"
                return redirect(url_for("view.create_panic_password"))
            current_user.panic_password = generate_password_hash(panic_password)
            current_user.panic_balance = float(panic_amount)
            current_user.has_set_panic = True
            db.session.commit()
            session["alert"] = "Panic password created successfully"
            session["bg_color"] = "success"
            return redirect(url_for("view.home"))
        return render_template(
            "create_panic_password.html", date=x, alert=alert, bg_color=bg_color
        )
    except Exception as e:
        print(e, "error in create panic password")


# delete panic password
@view.route("/delete-panic-password/")
@login_required
def delete_panic_password():
    try:
        current_user.panic_password = ""
        current_user.panic_balance = 0
        current_user.has_set_panic = False
        db.session.commit()
        session["alert"] = "Panic password deactivated successfully"
        session["bg_color"] = "success"
        return redirect(url_for("view.account"))
    except Exception as e:
        print(e, "error in delete panic password")
        session["alert"] = "Network Error"
        session["bg_color"] = "danger"
        return redirect(url_for("view.account"))


@view.route("/change-transfer-pin/", methods=["GET", "POST"])
@login_required
def change_transfer_pin():
    form = ChangeTransferPin()
    if request.method == "POST":
        if form.validate_on_submit():
            pin = int(form.new_pin.data)
            user = User.query.filter_by(id=current_user.id).first()
            secret_answer = form.secret_answer.data.lower()
            if secret_answer != current_user.secret_answer:
                session["alert"] = "Invalid answer"
                session["bg_color"] = "danger"
                return redirect(url_for("view.change_transfer_pin"))
            user.transaction_pin = hasher.hash(str(pin))
            db.session.commit()
            session["alert"] = "Transfer pin changed successfully"
            session["bg_color"] = "success"
            return redirect(url_for("view.home"))

    return render_template(
        "change_transfer_pin.html",
        date=x,
        form=form,
        secret_question=current_user.secret_question,
    )


# transfer to bank
@view.route("/transfer-to-bank", methods=["GET", "POST"])
@login_required
def transfer_to_bank():
    bank_code = request.args.get("bank_code")
    account_number = request.args.get("account_number")
    bank_name = request.args.get("bank_name")

    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)

    res, status_code = pay_stack.resolve_account(account_number, bank_code)
    if status_code != 200:
        session["alert"] = "Invalid account number"
        session["bg_color"] = "danger"
        return redirect(url_for("view.home"))
    account_name = res["data"]["account_name"]

    if request.method == "POST":
        transaction_pin = request.form.get("pin")
        narration = request.form.get("narration")
        amount = request.form.get("amount")

        if not amount:
            alert = "Please enter amount"
            bg_color = "danger"
            return redirect(
                url_for(
                    "view.transfer_to_bank",
                    bank_code=bank_code,
                    account_number=account_number,
                    bank_name=bank_name,
                    alert=alert,
                    bg_color=bg_color,
                )
            )
        if not transaction_pin:
            alert = "Please enter your transaction pin"
            bg_color = "danger"
            return redirect(
                url_for(
                    "view.transfer_to_bank",
                    bank_code=bank_code,
                    account_number=account_number,
                    bank_name=bank_name,
                    alert=alert,
                    bg_color=bg_color,
                )
            )

        if not hasher.verify(transaction_pin, current_user.transaction_pin):
            alert = "Invalid transaction pin"
            bg_color = "danger"
            return redirect(
                url_for(
                    "view.transfer_to_bank",
                    bank_code=bank_code,
                    account_number=account_number,
                    bank_name=bank_name,
                    alert=alert,
                    bg_color=bg_color,
                )
            )

        if current_user.panic_mode:
            print("PANIC MODE")
            half_of_panic_balance = current_user.panic_balance / 2
            if float(amount) > half_of_panic_balance:
                session["alert"] = (
                    "Transaction limit exceeded, please try a lower amount"
                )
                session["bg_color"] = "danger"
                return redirect(
                    url_for(
                        "view.transfer_to_bank",
                        bank_code=bank_code,
                        account_number=account_number,
                        bank_name=bank_name,
                        alert=alert,
                        bg_color=bg_color,
                    )
                )
            if float(amount) > current_user.account_balance:
                print("INSUFFICIENT FUNDS: PANIC MODE")
                session["alert"] = "Network Error"
                session["bg_color"] = "danger"
                return redirect(
                    url_for(
                        "view.transfer_to_bank",
                        bank_code=bank_code,
                        account_number=account_number,
                        bank_name=bank_name,
                        alert=alert,
                        bg_color=bg_color,
                    )
                )

            trans_ref = generate_transaction_ref("Transfer")
            sess_id = generate_session_id()

            # remove from user balance
            balance = current_user.account_balance
            balance -= float(amount)
            current_user.panic_balance -= float(amount)
        else:
            print("NORMAL MODE")
            if float(amount) > current_user.account_balance:
                alert = "Insufficient funds"
                bg_color = "danger"
                return redirect(
                    url_for(
                        "view.transfer_to_bank",
                        bank_code=bank_code,
                        account_number=account_number,
                        bank_name=bank_name,
                        alert=alert,
                        bg_color=bg_color,
                    )
                )

            trans_ref = generate_transaction_ref("Transfer")
            sess_id = generate_session_id()

            # remove from user balance
            balance = current_user.account_balance
            balance -= float(amount)

        trans = save_transfer_in_transactions(
            transaction_type="DBT",
            transaction_amount=amount,
            user_id=current_user.id,
            balance=balance,
            description=narration or "Transfer",
            category=get_cat("Transfer"),
            transaction_ref=trans_ref,
            session_id=sess_id,
            sender_account=str(current_user.account_number),
            receiver_account=str(account_number),
            sender=f"{current_user.last_name} {current_user.first_name}".title(),
            receiver=account_name.title(),
            status="Success",
            bank_name=bank_name.title(),
        )
        current_user.account_balance = balance
        db.session.commit()

        try:
            msg = Message(
                subject="DEBIT ALERT",
                sender="EasyTransact <easytransact.send@gmail.com>",
                recipients=[current_user.email],
            )
            msg.html = render_template(
                "transfer.html",
                user=current_user,
                amount=f"{float(amount):,.2f}",
                balance=f"{current_user.account_balance:,.2f}",
                date=trans.date_posted,
                acct=str(current_user.account_number),
                receiver=account_name,
                receiver_acct=str(account_number),
                bank_name=bank_name,
            )
            mail.send(msg)
        except Exception as e:
            print(e, "ERROR")

        save_spend_and_save_transaction(current_user, float(amount), generate_reference(), get_cat("Spend&Save"))

        return redirect(
            url_for(
                "view.transaction_successful",
                amount=f"{float(amount):,.2f}",
                sender=f"{current_user.last_name} {current_user.first_name}".title(),
                receiver=account_name.title(),
                sender_acct=str(current_user.account_number),
                bank_name=bank_name.title(),
                receiver_acct=str(account_number),
                date=trans.date_posted.strftime("%d %b, %Y %H:%M:%S"),
            )
        )
    return render_template(
        "transfer_to_bank.html",
        date=x,
        account_name=account_name,
        bank_name=bank_name,
        account_number=account_number,
        alert=alert,
        bg_color=bg_color,
    )


@view.route("/pay/<acct>/", methods=["GET", "POST"])
@login_required
def pay(acct):
    form = SendMoneyForm()
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    beneficial = []
    user = User.query.filter_by(account_number=acct).first()
    beneficials = Beneficiary.query.filter_by(user_id=current_user.id).all()
    transfer_pin = current_user.transaction_pin
    for each in beneficials:
        beneficial.append(each.account_number)
    if request.method == "POST":
        if form.validate_on_submit():
            amount = form.amount.data
            pin = int(form.transfer_pin.data)
            user1 = User.query.filter_by(account_number=acct).first()
            if current_user.panic_mode:
                print("PANIC MODE")
                panic = True
                half_of_panic_balance = current_user.panic_balance / 2
                if float(amount) > half_of_panic_balance:
                    session["alert"] = (
                        "Transaction limit exceeded, please try a lower amount"
                    )
                    session["bg_color"] = "danger"
                    return redirect(url_for("view.pay", acct=acct))
                if float(amount) > current_user.account_balance:
                    print("INSUFFICIENT FUNDS: PANIC MODE")
                    session["alert"] = "Network Error"
                    session["bg_color"] = "danger"
                    return redirect(url_for("view.pay", acct=acct))

                if not hasher.verify(str(pin), current_user.transaction_pin):
                    session["alert"] = "Invalid transaction pin"
                    session["bg_color"] = "danger"
                    return redirect(url_for("view.pay", acct=acct))

                # remove from user balance
                current_user.account_balance -= amount
                current_user.panic_balance -= amount
                user1.account_balance += amount
            else:
                panic = False
                print("NORMAL MODE")
                if current_user.account_balance < amount:
                    session["alert"] = "Insufficient Funds"
                    session["bg_color"] = "danger"
                    return redirect(url_for("view.pay", acct=acct))
                if not hasher.verify(str(pin), current_user.transaction_pin):
                    session["alert"] = "Invalid transaction pin"
                    session["bg_color"] = "danger"
                    return redirect(url_for("view.pay", acct=acct))

                current_user.account_balance -= amount
                user1.account_balance += amount
            if form.add_beneficiary.data:
                ben = Beneficiary(
                    first_name=user1.first_name.lower(),
                    last_name=user1.last_name.lower(),
                    account_number=acct,
                    user_id=current_user.id,
                )
                db.session.add(ben)
                db.session.commit()

            db.session.commit()
            transact1 = Transaction(
                transaction_type="CRT",
                transaction_amount=amount,
                balance=user1.account_balance,
                transaction_ref="W2W-" + generate_reference(),
                category=get_cat("W2W"),
                description="W2W Transfer from " + current_user.username,
                status="Success",
                sender=f"{current_user.last_name} {current_user.first_name}".title(),
                receiver=f"{user1.last_name} {user1.first_name}".title(),
                sender_account=str(current_user.account_number),
                receiver_account=str(acct),
                user_id=user1.id,
                panic_mode=panic,
            )

            transact2 = Transaction(
                transaction_type="DBT",
                transaction_amount=amount,
                balance=current_user.account_balance,
                transaction_ref="W2W-" + generate_reference(),
                category=get_cat("W2W"),
                description="W2W Transfer to " + user1.username,
                status="Success",
                receiver=f"{user1.last_name} {user1.first_name}".title(),
                sender=f"{current_user.last_name} {current_user.first_name}".title(),
                sender_account=str(current_user.account_number),
                receiver_account=str(acct),
                user_id=current_user.id,
                panic_mode=panic,
            )
            db.session.add_all([transact1, transact2])
            db.session.commit()
            session["alert"] = (
                f"{amount} Naira has been sent to {user1.last_name.title()} {user1.first_name.title()}"
            )
            session["bg_color"] = "success"

            # ALERTS WHEN FUNDS HAS BEEN SENT
            # alert for debit transaction
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
                    balance=f"{current_user.account_balance:,.2f}",
                    date=x,
                    acct=str(current_user.account_number),
                )
                mail.send(msg)
            except Exception as e:
                print(e, "ERROR")
                session["alert"] = "Network Error"
                session["bg_color"] = "danger"

            # alert for credit transaction
            try:
                msg = Message(
                    subject="CREDIT ALERT",
                    sender="EasyTransact <easytransact.send@gmail.com>",
                    recipients=[user1.email],
                )
                msg.html = render_template(
                    "credit.html",
                    user=user1,
                    amount=f"{amount:,.2f}",
                    balance=f"{user1.account_balance:,.2f}",
                    date=x,
                    acct=str(user1.account_number),
                )
                mail.send(msg)
            except Exception as e:
                print(e, "ERROR")
                session["alert"] = "Network Error"
                session["bg_color"] = "danger"

            save_spend_and_save_transaction(current_user, amount, generate_reference(), get_cat("Spend&Save"))
            return redirect(
                url_for(
                    "view.transaction_successful",
                    amount=f"{amount:,.2f}",
                    sender=f"{current_user.last_name} {current_user.first_name}".title(),
                    receiver=f"{user1.last_name} {user1.first_name}".title(),
                    sender_acct=str(current_user.account_number),
                    bank_name="EasyTransact",
                    receiver_acct=str(acct),
                    date=transact1.date_posted.strftime("%d %b, %Y %H:%M:%S"),
                )
            )
    return render_template(
        "pay.html",
        date=x,
        form=form,
        user1=user,
        beneficial=beneficial,
        alert=alert,
        bg_color=bg_color,
    )


@view.route("/reset-password/", methods=["GET", "POST"])
def reset_password():
    form = ResetForm()
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if request.method == "POST":
        if form.validate_on_submit():
            email = form.email.data
            user = User.query.filter_by(email=email).first()
            if not user:
                session["alert"] = "Provide valid email please"
                session["bg_color"] = "danger"
                return redirect(url_for("view.reset_password"))
            else:
                if not user.active:
                    session["alert"] = "Account is inactive"
                    session["bg_color"] = "danger"
                    return redirect(url_for("view.home"))
                send_reset_email(user)
                session["alert"] = "An email has been sent to you"
                session["bg_color"] = "success"
                return redirect(url_for("view.reset_password"))

    return render_template(
        "reset.html", date=x, form=form, alert=alert, bg_color=bg_color
    )


@view.route("/reset-password-verified/<token>", methods=["GET", "POST"])
def reset_password_verified(token):
    form = ResetPasswordForm()
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if request.method == "POST":
        if form.validate_on_submit():
            password = generate_password_hash(form.password.data)
            user = User.verify_reset_token(token)
            if not user:
                session["alert"] = "Invalid token"
                session["bg_color"] = "danger"
                return redirect(url_for("view.reset_password"))
            else:
                user.password = password
                db.session.commit()
                session["alert"] = "Password changed successfully"
                session["bg_color"] = "success"
                return redirect(url_for("auth.login"))
    return render_template(
        "reset_verified.html", date=x, form=form, alert=alert, bg_color=bg_color
    )


@view.route("/create-card/", methods=["GET", "POST"])
@login_required
def create_card():
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if current_user.card:
        return redirect(url_for("view.card"))
    if request.method == "POST":
        card_number = "".join([str(random.randint(0, 9)) for i in range(16)])
        expiry_date = expiration
        cvv = "".join(str(random.randint(0, 9)) for _ in range(3))
        card = Card(
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
            user_id=current_user.id,
        )

        db.session.add(card)
        db.session.commit()
        session["alert"] = "Card created successfully"
        session["bg_color"] = "success"
        return redirect(url_for("view.card"))
    return render_template("create_card.html", date=x, alert=alert, bg_color=bg_color)


@view.route("/card/", methods=["GET", "POST"])
@login_required
def card():
    card = Card.query.filter_by(user_id=current_user.id).first()
    return render_template("card.html", date=x, card=card)


@view.route("/contact/", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if request.method == "POST":
        if form.validate_on_submit():
            try:
                name = form.name.data.title()
                email = form.email.data.lower()
                message = form.message.data.title()
                msg = Message(
                    "EasyTransact: from " + name,
                    sender=email,
                    recipients=[
                        "atmme1992@gmail.com",
                        "greatsoma2019@gmail.com",
                        "vnoah410@gmail.com",
                    ],
                )
                msg.body = f"{message}\nMy email address is: {email}"
                mail.send(msg)
                session["alert"] = "Message Sent"
                session["bg_color"] = "success"
                return redirect(url_for("view.contact"))
            except Exception as e:
                print(e)
                session["alert"] = "Your data connection is off"
                session["bg_color"] = "danger"
                return redirect(url_for("view.contact"))

    return render_template(
        "contact.html", form=form, date=x, alert=alert, bg_color=bg_color
    )


@view.route("/team")
def team():
    return render_template("team.html", date=x)


@view.route("/download_pdf", methods=["GET"])
def download_pdf():
    if not current_user.transacts:
        session["alert"] = "You have no transaction history"
        session["bg_color"] = "danger"
        return redirect(url_for("view.account"))
    try:
        # render the Jinja2 template with the desired context
        html = render_template("statement.html")

        # convert the HTML to PDF using pdfshift.io
        response = requests.post(
            "https://api.pdfshift.io/v3/convert/pdf",
            auth=(
                "api",
                f'{os.environ.get(random.choice(["PDF_KEY", "PDF_KEY2", "PDF_KEY3", "PDF_KEY4"]))}',
            ),
            json={"source": html, "landscape": False, "use_print": False},
        )

        response.raise_for_status()

        # return the PDF as a Flask response
        return (
            response.content,
            200,
            {
                "Content-Type": "application/pdf",
                "Content-Disposition": f'attachment; filename={current_user.last_name.title() + " " + current_user.first_name.title()}.pdf',
            },
        )
    except Exception as e:
        print(e, "error from pdfshift.io")
        session["alert"] = "Cannot generate your account's statement"
        session["bg_color"] = "danger"
        return redirect(url_for("view.account"))


@view.route("/faq")
def faq():
    return render_template("faq.html", date=x)


@view.route(
    "/completed/<amount>/<receiver>/<sender>/<sender_acct>/<bank_name>/<receiver_acct>/<date>"
)
def transaction_successful(
    amount, receiver, sender, sender_acct, bank_name, receiver_acct, date
):
    return render_template(
        "trans_success.html",
        date=date,
        amount=amount,
        receiver=receiver,
        sender=sender,
        sender_acct=sender_acct,
        bank_name=bank_name,
        receiver_acct=receiver_acct,
    )


@view.route("/coming-soon")
def coming_soon():
    return render_template("coming-soon.html")


@view.route("/profile")
@login_required
def user_profile():
    return render_template("profile.html", date=x)


def savings_interest():
    payday = datetime.datetime.now().day
    paytime = datetime.datetime.now().hour
    if payday == 1 and paytime == 0:
        users = User.query.all()
        for user in users:
            if user.savings > 0:
                user.savings += user.savings * 0.05
                db.session.commit()
    else:
        pass


@view.route("/savings", methods=["GET", "POST"])
@login_required
def savings():
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    form = SaveMoneyForm()
    n = 0
    if request.method == "POST":
        amount = form.amount.data
        n += 1
        if form.validate_on_submit():
            if current_user.account_balance < amount:
                session["alert"] = "Insufficient Amount"
                session["bg_color"] = "danger"
                return redirect(url_for("view.savings"))
            else:
                current_user.account_balance -= amount
                current_user.savings += amount
                db.session.commit()

                transact2 = Transaction(
                    transaction_type="DBT",
                    transaction_amount=amount,
                    balance=current_user.account_balance,
                    transaction_ref="Savings-" + generate_reference(),
                    category=get_cat("Savings"),
                    description="Savings",
                    status="Success",
                    sender=current_user.username + " " + "savings",
                    user_id=current_user.id,
                )
                db.session.add(transact2)
                db.session.commit()
                alert = "Saved successfully"
                bg_color = "success"
                savings_interest()
            return render_template(
                "savings.html", date=x, form=form, n=n, alert=alert, bg_color=bg_color
            )
    return render_template(
        "savings.html", date=x, form=form, n=n, alert=alert, bg_color=bg_color
    )


# spend and save
@view.route("/spend", methods=["GET", "POST"])
@login_required
def spend_and_save():
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    form = SaveMoneyForm()
    n = 0
    if request.method == "POST":
        amount = form.amount.data
        n += 1
        if form.validate_on_submit():
            if not current_user.spend_save_amount:
                session["alert"] = "You have nothing to withdraw"
                session["bg_color"] = "info"
                return redirect(url_for("view.spend_and_save"))

            if current_user.spend_save_amount < amount:
                current_user.account_balance += amount
                current_user.spend_save_amount -= amount
                db.session.commit()

                transact2 = Transaction(
                    transaction_type="CRT",
                    transaction_amount=amount,
                    balance=current_user.account_balance,
                    transaction_ref="Spend&Save-" + generate_reference(),
                    category=get_cat("Spend&Save"),
                    description="Spend Save Withdrawal",
                    status="Success",
                    sender=current_user.username + " " + "spend and save",
                    user_id=current_user.id,
                )
                db.session.add(transact2)
                db.session.commit()
                session['alert'] = "Withdrawal successful"
                session['bg_color'] = "success"
                return redirect(url_for("view.home"))
            else:
                session["alert"] = "Insufficient Amount"
                session["bg_color"] = "danger"
                return redirect(url_for("view.spend_and_save"))
    return render_template("spend_and_save.html",
                           date=x, form=form,
                           alert=alert, bg_color=bg_color)


# enable or disable spend and save
@view.route("/enable_spend_and_save", methods=["GET", "POST"])
@login_required
def enable_spend_and_save():
    # If the user has enabled spend and save wants to disable, send his money into his account
    if current_user.enabled_spend_save and current_user.spend_save_amount:
        amount = current_user.spend_save_amount
        current_user.account_balance += amount
        current_user.spend_save_amount -= amount
        db.session.commit()

        transact2 = Transaction(
            transaction_type="CRT",
            transaction_amount=amount,
            balance=current_user.account_balance,
            transaction_ref="Spend&Save-" + generate_reference(),
            category=get_cat("Spend&Save"),
            description="Spend Save Disabled Withdrawal",
            status="Success",
            sender=current_user.username + " " + "spend and save",
            user_id=current_user.id,
        )
        db.session.add(transact2)
        db.session.commit()
    current_user.enabled_spend_save = not current_user.enabled_spend_save
    db.session.commit()
    session["alert"] = "Spend and save " + ("enabled" if current_user.enabled_spend_save else "disabled")
    session["bg_color"] = "success"
    return redirect(url_for("view.spend_and_save"))


@view.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    form = SaveMoneyForm()
    amount = current_user.savings
    if not current_user.savings:
        session["alert"] = "No savings to withdraw"
        session["bg_color"] = "danger"
        return redirect(url_for("view.home"))
    current_user.account_balance += current_user.savings
    current_user.savings -= current_user.savings
    db.session.commit()

    transact1 = Transaction(
        transaction_type="CRT",
        transaction_amount=amount,
        balance=current_user.account_balance,
        transaction_ref="Savings-" + generate_reference(),
        category=get_cat("Savings"),
        description="Savings withdrawal",
        status="Success",
        sender=current_user.username + " " + "savings",
        user_id=current_user.id,
    )
    db.session.add(transact1)
    db.session.commit()
    session["alert"] = "Withdraw successful"
    session["bg_color"] = "success"
    return redirect(url_for("view.home"))


@view.route("/invite_and_earn", methods=["GET", "POST"])
def invite_and_earn():
    invitees = Invitees.query.filter_by(invited_by=current_user.id).all()
    all_invitees = len(invitees)
    return render_template("invite_and_earn.html", date=x, len=all_invitees)


@view.route("/withdraw-earnings")
def withdraw_earnings():
    if current_user.invite_earn:
        amount = current_user.invite_earn
        current_user.account_balance += amount
        current_user.invite_earn -= amount

        transact1 = Transaction(
            transaction_type="CRT",
            transaction_amount=amount,
            balance=current_user.account_balance,
            transaction_ref="Referral-" + generate_reference(),
            description="Referral earnings",
            status="Success",
            category=get_cat("Referral"),
            sender=current_user.username + " " + "invite earning",
            user_id=current_user.id,
        )
        db.session.add(transact1)
        db.session.commit()
        session["alert"] = f"Withdrawal of N{amount} successful"
        session["bg_color"] = "success"
    else:
        session["alert"] = "No earnings to withdraw"
        session["bg_color"] = "danger"
    return redirect(url_for("view.home"))


# view one transaction
@view.route("/transaction/<string:trans_id>")
@login_required
def view_transaction(trans_id):
    trans = Transaction.query.filter_by(id=trans_id).first()
    return render_template("view_transaction.html", date=x, trans=trans)


# toggle enabled_2fa
@view.route("/toggle_2fa", methods=["POST"])
@login_required
def toggle_2fa():
    auth_code = request.form["auth_code"]

    if not auth_code:
        session["alert"] = "Please enter the authentication code"
        session["bg_color"] = "danger"
        return redirect(url_for("view.account"))

    if not authenticate_auth_code(current_user, auth_code):
        session["alert"] = "Invalid authentication code"
        session["bg_color"] = "danger"
        return redirect(url_for("view.account"))

    current_user.enabled_2fa = not current_user.enabled_2fa
    db.session.commit()
    if current_user.enabled_2fa:
        session["alert"] = "2FA enabled"
        session["bg_color"] = "success"
    else:
        session["alert"] = "2FA disabled"
        session["bg_color"] = "success"

    return redirect(url_for("view.account"))
