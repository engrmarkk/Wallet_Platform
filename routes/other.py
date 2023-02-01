from datetime import datetime
from extensions import mail, db
from flask_mail import Message
from flask_login import current_user, login_required
from flask import redirect, url_for, flash, request, render_template, Blueprint
from models import User, Transaction, Beneficiary
from form import *
from func import save_image
from werkzeug.security import generate_password_hash

view = Blueprint("view", __name__)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender="engrnark.send@gmail.com", recipients=[user.email])
    msg.html = render_template('reset_email.html', user=user, token=token)

    mail.send(msg)


@view.route("/")
def front_page():
    if current_user.is_authenticated:
        return redirect(url_for("view.home"))
    return render_template("front.html", date=datetime.utcnow())


@view.route("/account/")
def account():
    return render_template("account.html", date=datetime.utcnow())


@view.route("/home/", methods=["GET", "POST"])
@login_required
def home():
    form = ConfirmAccount()
    beneficials = Beneficiary.query.filter_by(user_id=current_user.id).all()
    balance = f"{current_user.account_balance:,}"
    if request.method == "POST":
        if form.validate_on_submit():
            account_num = int(form.account_number.data)
            user1 = User.query.filter_by(account_number=account_num).first()
            if not user1:
                flash("Invalid account number", "danger")
                return redirect(url_for("view.home"))
            if account_num == current_user.account_number:
                flash("You can't send money to yourself", "info")
                return redirect(url_for("view.home"))

            return redirect(url_for("view.pay", acct=account_num))

    return render_template("home.html", date=datetime.utcnow(), beneficials=beneficials, user=current_user, balance=balance, form=form)


@view.route("/pay/<acct>/", methods=["GET", "POST"])
@login_required
def pay(acct):
    form = SendMoneyForm()
    beneficial = []
    user = User.query.filter_by(account_number=acct).first()
    beneficials = Beneficiary.query.filter_by(user_id=current_user.id).all()
    for each in beneficials:
        beneficial.append(each.account_number)
    if request.method == "POST":
        if form.validate_on_submit():
            amount = form.amount.data
            user1 = User.query.filter_by(account_number=acct).first()
            if current_user.account_balance < amount:
                flash("Insufficient Funds", "danger")
                return redirect(url_for("view.pay"))
            if form.add_beneficiary.data:
                ben = Beneficiary(first_name=user1.first_name.lower(), last_name=user1.last_name.lower(),
                                  account_number=acct, user_id=current_user.id
                                  )
                db.session.add(ben)
                db.session.commit()
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
            return redirect(url_for("view.pay", acct=acct))
    return render_template("pay.html", date=datetime.utcnow(), form=form, user1=user, beneficial=beneficial)


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
            
    return render_template("reset.html", date=datetime.utcnow(), form=form)


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
    return render_template("reset_verified.html", date=datetime.utcnow(), form=form)


@view.route("/send/", methods=["GET", "POST"])
@login_required
def display_profile():
    form = PhotoForm()
    if request.method == "POST":
        try:
            f = form.image.data
            if not f:
                flash('nothing to upload', 'danger')
                return redirect(url_for('view.display_profile'))
            image_file = save_image(f)
            current_user.photo = image_file
            db.session.commit()
            flash('Profile photo uploaded successfully', 'success')
            return redirect(url_for('view.display_profile'))
        except Exception as e:
            flash(e, 'danger')
    return render_template("display-profile.html", date=datetime.utcnow(), form=form)


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
