from datetime import datetime
from extensions import mail, db
from flask_mail import Message
from flask_login import current_user, login_required
from flask import redirect, url_for, flash, request, render_template, Blueprint
from models import User, Transaction
from form import *

view = Blueprint("view", __name__)


@view.route("/")
def front_page():
    if current_user.is_authenticated:
        return redirect(url_for("view.home"))
    return render_template("front.html", date=datetime.utcnow())


@view.route("/account/")
def account():
    return render_template("account.html", date=datetime.utcnow())


@view.route("/home/")
@login_required
def home():
    balance = f"{current_user.account_balance:,}"
    return render_template(
        "home.html", date=datetime.utcnow(), user=current_user, balance=balance
    )


@view.route("/pay/", methods=["GET", "POST"])
@login_required
def pay():
    form = SendMoneyForm()
    if request.method == "POST":
        if form.validate_on_submit():
            account_number = form.account_number.data
            amount = form.amount.data
            user1 = User.query.filter_by(account_number=account_number).first()
            if not user1:
                flash("Invalid account number", "danger")
                return redirect(url_for("view.pay"))
            if current_user.account_balance < amount:
                flash("Insufficient Funds", "danger")
                return redirect(url_for("view.pay"))
            user1.account_balance += amount
            db.session.commit()
            transact1 = Transaction(
                transaction_type="CRT",
                transaction_amount=amount,
                sender=current_user.username,
                user_id=user1.id,
            )
            db.session.add(transact1)
            db.session.commit()

            current_user.account_balance -= amount
            db.session.commit()
            transact2 = Transaction(
                transaction_type="DBT",
                transaction_amount=amount,
                sender=user1.username,
                user_id=current_user.id,
            )
            db.session.add(transact2)
            db.session.commit()
            flash(f"{amount} Naira has been sent to {user1.username}", "success")
            return redirect(url_for("view.pay"))
    return render_template("pay.html", date=datetime.utcnow(), form=form)


@view.route("/reset-password/", methods=["GET", "POST"])
def reset_password():
    form = ResetForm()
    if request.method == "POST":
        if form.validate_on_submit():
            email = form.email.data
            if not email:
                flash("Provide your email please", "danger")
                return redirect(url_for("view.reset_password"))
    return render_template("reset.html", date=datetime.utcnow(), form=form)


@view.route("/send/")
@login_required
def display_profile():
    return render_template("display-profile.html", date=datetime.utcnow())


@view.route("/contact/", methods=["GET", "POST"])
@login_required
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

    return render_template("contact.html", form=form, date=datetime.utcnow())
