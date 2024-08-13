from datetime import datetime

from werkzeug.exceptions import RequestEntityTooLarge

from extensions import mail, db
from flask_mail import Message
from flask_login import current_user, login_required
from flask import (
    redirect,
    url_for,
    flash,
    request,
session,
    render_template,
    Blueprint,
    make_response,
    jsonify,
)
from models import User, Transaction, Beneficiary, Card, Invitees
from models.transact import save_transfer_in_transactions
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
from utils import generate_session_id, generate_transaction_ref
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
    save_transaction_cat()
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if current_user.is_authenticated:
        return redirect(url_for("view.home"))
    return render_template("front.html", date=x, alert=alert, bg_color=bg_color)


@view.route("/account/", methods=["GET", "POST"])
@login_required
def account():
    form = PhotoForm()
    pinset = current_user.pin_set

    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if request.method == "POST":
        try:
            f = form.image.data
            if not f:
                # flash("Nothing to upload", "danger")
                session["alert"] = "Nothing to upload"
                session["bg_color"] = "danger"
                return redirect(url_for("view.display_profile"))
            if f.content_length > request.max_content_length:  # check file size
                # flash("File is too large. Maximum file size is 1MB.", "danger")
                session["alert"] = "File is too large. Maximum file size is 1MB."
                session["bg_color"] = "danger"
                return redirect(url_for("view.account"))
            result = cloudinary.uploader.upload(
                f, transformation=[{"width": 176, "height": 176, "crop": "fill"}]
            )
            image_url = result["secure_url"]
            current_user.photo = image_url
            db.session.commit()
            # flash("Profile photo uploaded successfully", "success")
            session["alert"] = "Profile photo uploaded successfully"
            session["bg_color"] = "success"
            return redirect(url_for("view.account"))
        except ValidationError as e:
            # flash(str(e), "danger")
            session["alert"] = str(e)
            session["bg_color"] = "danger"
            return redirect(url_for("view.account"))
        except RequestEntityTooLarge:
            # flash("File is too large. Maximum file size is 1MB.", "danger")
            session["alert"] = "File is too large. Maximum file size is 1MB."
            session["bg_color"] = "danger"
            return redirect(url_for("view.account"))
    return render_template("account.html", pinset=pinset, date=x, form=form,
                           alert=alert, bg_color=bg_color)


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
            func.lower(Transaction.transaction_type) == transaction_type.lower()
            if transaction_type
            else True,
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
    balance = f"{current_user.account_balance:,.2f}"
    pinset = current_user.pin_set

    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if request.method == "POST":
        try:
            if form.validate_on_submit():
                account_num = int(form.account_number.data)
                user1 = User.query.filter_by(account_number=account_num).first()
                if not user1:
                    # flash("Invalid account number", "danger")
                    session["alert"] = "Invalid account number"
                    session["bg_color"] = "danger"
                    return redirect(url_for("view.home"))
                if account_num == current_user.account_number:
                    # flash("You can't send money to yourself", "info")
                    session["alert"] = "You can't send money to yourself"
                    session["bg_color"] = "info"
                    return redirect(url_for("view.home"))
                return redirect(url_for("view.pay", acct=account_num))
        except ValueError:
            # flash("Invalid account number", "danger")
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
        bg_color=bg_color
    )


@view.route("/create-transfer-pin/", methods=["GET", "POST"])
@login_required
def create_transfer_pin():
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if current_user.pin_set:
        # flash("Transfer pin already set", "info")
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
            # flash("Transfer pin created successfully", "success")
            session["alert"] = "Transfer pin created successfully"
            session["bg_color"] = "success"
            return redirect(url_for("view.home"))
    return render_template("create_transfer_pin.html", date=x, form=form,
                           alert=alert, bg_color=bg_color)


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
                flash("Invalid answer", "danger")
                return redirect(url_for("view.change_transfer_pin"))
            user.transaction_pin = hasher.hash(str(pin))
            db.session.commit()
            flash("Transfer pin changed successfully", "success")
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

    res, status_code = pay_stack.resolve_account(account_number, bank_code)
    if status_code != 200:
        flash("Invalid account number", "danger")
        return redirect(url_for("view.home"))
    account_name = res["data"]["account_name"]

    if request.method == "POST":
        transaction_pin = request.form.get("pin")
        narration = request.form.get("narration")
        amount = request.form.get("amount")

        if not amount:
            flash("Please enter amount", "danger")
            return redirect(url_for("view.transfer_to_bank", bank_code=bank_code,
                                    account_number=account_number, bank_name=bank_name))
        if not transaction_pin:
            flash("Please enter your transaction pin", "danger")
            return redirect(url_for("view.transfer_to_bank", bank_code=bank_code,
                                    account_number=account_number, bank_name=bank_name))

        if not hasher.verify(transaction_pin, current_user.transaction_pin):
            flash("Invalid transaction pin", "danger")
            return redirect(url_for("view.transfer_to_bank", bank_code=bank_code,
                                    account_number=account_number, bank_name=bank_name))

        if float(amount) > current_user.account_balance:
            flash("Insufficient funds", "danger")
            return redirect(url_for("view.transfer_to_bank", bank_code=bank_code,
                                    account_number=account_number, bank_name=bank_name))

        trans_ref = generate_transaction_ref("Transfer")
        sess_id = generate_session_id()

        # remove from user balance
        balance = current_user.account_balance
        balance -= float(amount)

        trans = save_transfer_in_transactions(transaction_type="DBT", transaction_amount=amount,
                                              user_id=current_user.id, balance=balance,
                                              description=narration or "Transfer",
                                              category=get_cat("Transfer"),
                                              transaction_ref=trans_ref, session_id=sess_id,
                                              sender_account=str(current_user.account_number),
                                              receiver_account=str(account_number),
                                              sender=f"{current_user.last_name} {current_user.first_name}".title(),
                                              receiver=account_name.title(),
                                              status="Success", bank_name=bank_name.title())
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
    return render_template("transfer_to_bank.html", date=x, account_name=account_name,
                           bank_name=bank_name, account_number=account_number)


@view.route("/pay/<acct>/", methods=["GET", "POST"])
@login_required
def pay(acct):
    form = SendMoneyForm()
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
            if current_user.account_balance < amount:
                flash("Insufficient Funds", "danger")
                return redirect(url_for("view.pay", acct=acct))
            if not hasher.verify(str(pin), current_user.transaction_pin):
                flash("Invalid transaction pin", "danger")
                return redirect(url_for("view.pay", acct=acct))
            if form.add_beneficiary.data:
                ben = Beneficiary(
                    first_name=user1.first_name.lower(),
                    last_name=user1.last_name.lower(),
                    account_number=acct,
                    user_id=current_user.id,
                )
                db.session.add(ben)
                db.session.commit()
            user1.account_balance += amount
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
            )
            db.session.add(transact1)
            db.session.commit()

            current_user.account_balance -= amount
            db.session.commit()
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
            )
            db.session.add(transact2)
            db.session.commit()
            flash(f"{amount} Naira has been sent to {user1.last_name.title()} {user1.first_name.title()}", "success")

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
                flash("Network Error", "danger")

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
                flash("Network error", "danger")
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
        "pay.html", date=x, form=form, user1=user, beneficial=beneficial
    )


@view.route("/reset-password/", methods=["GET", "POST"])
def reset_password():
    form = ResetForm()
    if request.method == "POST":
        if form.validate_on_submit():
            email = form.email.data
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("Provide valid email please", "danger")
                return redirect(url_for("view.reset_password"))
            else:
                send_reset_email(user)
                flash("An email has been sent to you", "success")
                return redirect(url_for("view.reset_password"))

    return render_template("reset.html", date=x, form=form)


@view.route("/reset-password-verified/<token>", methods=["GET", "POST"])
def reset_password_verified(token):
    form = ResetPasswordForm()
    if request.method == "POST":
        if form.validate_on_submit():
            password = generate_password_hash(form.password.data)
            user = User.verify_reset_token(token)
            if not user:
                flash("Invalid token", "danger")
                return redirect(url_for("view.reset_password"))
            else:
                user.password = password
                db.session.commit()
                flash("Password changed successfully", "success")
                return redirect(url_for("auth.login"))
    return render_template("reset_verified.html", date=x, form=form)


@view.route("/create-card/", methods=["GET", "POST"])
@login_required
def create_card():
    if current_user.card:
        flash("You already have a card", "success")
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
        flash("Card created successfully", "success")
        return redirect(url_for("view.card"))
    return render_template("create_card.html", date=x)


@view.route("/card/", methods=["GET", "POST"])
@login_required
def card():
    card = Card.query.filter_by(user_id=current_user.id).first()
    return render_template("card.html", date=x, card=card)


@view.route("/contact/", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if request.method == "POST":
        """not using this block again"""
        # if not form.validate_on_submit():
        #     flash("All fields are required", "danger")
        #     return redirect(url_for("view.contact"))
        """end of block"""

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
                flash("Message Sent", "success")
                return redirect(url_for("view.contact"))
            except:
                flash("Your data connection is off", category="danger")

    return render_template("contact.html", form=form, date=x)


@view.route("/team")
def team():
    return render_template("team.html", date=x)


@view.route("/download_pdf", methods=["GET"])
def download_pdf():
    if not current_user.transacts:
        flash("You have no transaction history", "danger")
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
        flash("Cannot generate your account's statement", "danger")
        return redirect(url_for("view.account"))


@view.route("/faq")
def faq():
    return render_template("faq.html", date=x)


@view.route("/completed/<amount>/<receiver>/<sender>/<sender_acct>/<bank_name>/<receiver_acct>/<date>")
def transaction_successful(amount, receiver,
                           sender, sender_acct, bank_name, receiver_acct, date):
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
    form = SaveMoneyForm()
    n = 0
    if request.method == "POST":
        amount = form.amount.data
        n += 1
        if form.validate_on_submit():
            if current_user.account_balance < amount:
                flash("Insufficient Amount", "danger")
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
                flash("Saved successfully", "success")
                savings_interest()
            return render_template("savings.html", date=x, form=form, n=n)
    return render_template("savings.html", date=x, form=form, n=n)


@view.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    form = SaveMoneyForm()
    amount = current_user.savings
    if not current_user.savings:
        flash("No savings to withdraw", "danger")
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
    flash("Withdraw successful", "success")
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
        flash(f"Withdrawal of N{amount} successful", "success")
    else:
        flash("No earnings to withdraw", "danger")
    return redirect(url_for("view.home"))


# view one transaction
@view.route("/transaction/<string:trans_id>")
@login_required
def view_transaction(trans_id):
    trans = Transaction.query.filter_by(id=trans_id).first()
    return render_template("view_transaction.html", date=x, trans=trans)
