from datetime import datetime
from extensions import db, mail
from flask_login import current_user, login_user, logout_user, login_required
from flask import redirect, url_for, flash, request, render_template, Blueprint
from models import User, Invitees
from form import *
from flask_mail import Message
from random import randint
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint("auth", __name__, template_folder="../templates")

otp = randint(100000, 999999)


@auth.route("/validate/<email>", methods=["GET", "POST"])
def validate(email):
    if request.method == "POST":
        user_otp = request.form["otp"]
        if not user_otp:
            flash("Please enter the OTP", category="danger")
            return redirect(url_for("auth.validate", email=email))
        user = User.query.filter_by(email=email).first_or_404()
        in_num = int(user.invited_by)
        if int(user_otp) == otp:
            user.confirmed = True
            if user.invited_by:
                user1 = User.query.filter_by(account_number=in_num).first()
                user1.invite_earn += 100
                invitee = Invitees(
                    first_name=user.first_name,
                    last_name=user.last_name,
                    invited_by=user1.id,
                )
                db.session.add(invitee)
            db.session.commit()
            flash("Email verification successful", category="success")
            return redirect(url_for("auth.login"))
        else:
            flash("try again, invalid code", category="danger")

    return render_template("confirmation.html", email=email, date=datetime.utcnow())


@auth.route("/login/", methods=["GET", "POST"])
def login():
    # If the logged-in user is trying to access the login url, redirects the user to the homepage
    if current_user.is_authenticated:
        return redirect(url_for("view.home"))
    # Assign the LoginForm created in the form.py file to a variable 'form'
    form = LoginForm()
    if request.method == "POST":
        # If the form gets validated on submit
        if form.validate_on_submit():
            # Query the User model and assign the queried data to the variable 'user'
            user = User.query.filter_by(email=form.email.data.lower()).first()
            email = form.email.data
            if user and not user.confirmed:
                try:
                    flash("First validate your email", category="danger")

                    msg = Message(
                        subject="Email Verification",
                        sender="Easytransact <easytransact.send@gmail.com>",
                        recipients=[email],
                    )
                    msg.html = render_template("email_verification.html", otp=str(otp))
                    mail.send(msg)
                except Exception as e:
                    print(e, "ERROR")
                    flash("failed to validate", "danger")
                    return render_template(
                        "login.html", date=datetime.utcnow(), form=form
                    )

                return redirect(url_for("auth.validate", email=email))
            # Check if the user exist in the database and if the inputted password is same with the one attached to
            # the user on the database
            if user:
                if check_password_hash(user.password, form.password.data):
                    # If the check passed, login the user and flash a message to the user when redirected to the
                    # homepage
                    flash("Login Successful", "success")
                    login_user(user, remember=False)
                    return redirect(url_for("view.home"))
                else:
                    # If the check failed, flash a message to the user while still on the same page
                    flash("Check your Password", "danger")
            else:
                # If the user doesn't exist, flash a message to the user while still on the same page
                flash("User doesn't exist", "danger")

                """not using this"""
                # return redirect(url_for("auth.login"))
                """end of block"""

    # This for a get request, if u click on the link that leads to the login page, this return statement get called upon
    return render_template("login.html", date=datetime.utcnow(), form=form)


@auth.route("/register/", methods=["GET", "POST"])
def register():
    # If the logged-in user is trying to access the login url, redirects the user to the homepage
    if current_user.is_authenticated:
        return redirect(url_for("view.home"))
    # Assign the RegistrationForm created in the form.py file to a variable 'form'
    form = RegistrationForm()
    # If the request is a post request and the form doesn't get validated, redirect the user to that same page
    if request.method == "POST":
        """not using this line anymore"""
        # if not form.validate_on_submit():
        #     flash("All fields are required", category="danger")
        #     # return redirect(url_for("auth.register"))
        """end of block"""

        # If the form gets validated on submit
        if form.validate_on_submit():
            # Check if the username already exist
            user = User.query.filter_by(username=form.username.data.lower()).first()
            # if the username exist
            if user:
                # Flash this message to the user and redirect the user to that same page
                flash("User with this username already exist", category="danger")
                return redirect(url_for("auth.register"))

            # Check if email exist
            existing_email = User.query.filter_by(email=form.email.data.lower()).first()
            # if the email exist
            if existing_email:
                # Flash this message to the user and redirect the user to that same page
                flash("User with this email already exist", category="danger")
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form
                )

            # Check if phone number exist
            existing_phone = User.query.filter_by(
                account_number=form.phone_number.data[1:]
            ).first()
            # if the phone number exist
            if existing_phone:
                # Flash this message to the user and redirect the user to that same page
                flash("User with this phone number already exist", category="danger")
                return redirect(url_for("auth.register"))
            if not form.phone_number.data.isnumeric():
                flash("This is not a valid number", category="danger")
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form
                )

            first_name = form.first_name.data.lower()
            last_name = form.last_name.data.lower()
            username = form.username.data.lower()
            email = form.email.data.lower()
            # phone_number = str(form.phone_number.data)
            phone_number = form.phone_number.data
            # account_number = int(str(phone_number)[1:])
            account_number = form.phone_number.data
            password_hash = generate_password_hash(form.password.data)

            # to check if the password is the mixture of uppercase, lowercase and a number at least
            letters = set(form.password.data)
            mixed = (
                any(letter.islower() for letter in letters)
                and any(letter.isupper() for letter in letters)
                and any(letter.isdigit() for letter in letters)
            )
            if not mixed:
                flash(
                    "Password should contain at least an uppercase, lowercase and a number",
                    "danger",
                )
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form
                )

            if len(phone_number) != 11:
                flash("Phone number must be 11 digits", "danger")
                return redirect(url_for("auth.register"))

            if (
                form.invited_by.data
                and not User.query.filter_by(
                    account_number=form.invited_by.data
                ).first()
            ):
                flash("Invalid referral code", "danger")
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form
                )

            if not form.invited_by.data:
                invited_by = 0
            else:
                invited_by = int(form.invited_by.data)

            # variable 'new_user'
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                username=username,
                phone_number=form.phone_number.data,
                email=email,
                account_number=form.phone_number.data,
                invited_by=invited_by,
                password=password_hash,
                confirmed=False,
            )
            try:
                msg = Message(
                    subject="Email Verification",
                    sender="EasyTransact <easytransact.send@gmail.com>",
                    recipients=[email],
                )
                msg.html = render_template("email_verification.html", otp=str(otp))
                mail.send(msg)
            except Exception as e:
                print(e)
                flash("failed to verify email", "danger")
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form
                )

            # Add the 'new_user'
            db.session.add(new_user)
            db.session.commit()

            flash(
                "A confirmation email has been sent to you via email",
                category="success",
            )
            return redirect(url_for("auth.validate", email=email))

    return render_template("register.html", date=datetime.utcnow(), form=form)


@auth.route("/logout/")
@login_required
def logout():
    logout_user()
    flash("You've been logged out successfully", "success")
    return redirect(url_for("view.front_page"))
