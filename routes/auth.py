from datetime import datetime
from extensions import db, mail
from flask_login import current_user, login_user, logout_user, login_required
from flask import redirect, url_for, flash, request, render_template, Blueprint, session
from models import User, Invitees
from form import *
from flask_mail import Message
from utils import authenticate_auth_code
from random import randint
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import OperationalError

auth = Blueprint("auth", __name__, template_folder="../templates")

otp = randint(100000, 999999)


@auth.route("/validate/<email>", methods=["GET", "POST"])
def validate(email):
    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    if request.method == "POST":
        user_otp = request.form["otp"]
        if not user_otp:
            session["alert"] = "Please enter the OTP"
            session["bg_color"] = "danger"
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
            session["alert"] = "Email verification successful"
            session["bg_color"] = "success"
            return redirect(url_for("auth.login"))
        else:
            alert = "Try again, invalid code"
            bg_color = "danger"

    return render_template("confirmation.html", email=email, date=datetime.utcnow(),
                           alert=alert, bg_color=bg_color)


@auth.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    try:
        # If the logged-in user is trying to access the login url, redirects the user to the homepage
        if current_user.is_authenticated:
            return redirect(url_for("view.home"))

        alert = session.pop("alert", None)
        bg_color = session.pop("bg_color", None)
        # Assign the LoginForm created in the form.py file to a variable 'form'
        form = LoginForm()
        if request.method == "POST":
            # If the form gets validated on submit
            if form.validate_on_submit():
                # Query the User model and assign the queried data to the variable 'user'
                user = User.query.filter_by(email=form.email.data.lower()).first()
                email = form.email.data.lower()
                if user and not user.confirmed:
                    try:
                        session["alert"] = "First validate your email"
                        session["bg_color"] = "danger"

                        msg = Message(
                            subject="Email Verification",
                            sender="Easytransact <easytransact.send@gmail.com>",
                            recipients=[email],
                        )
                        msg.html = render_template("email_verification.html", otp=str(otp))
                        mail.send(msg)
                    except Exception as e:
                        print(e, "ERROR")
                        alert = "Failed to validate"
                        bg_color = "danger"
                        return render_template(
                            "login.html", date=datetime.utcnow(), form=form, alert=alert, bg_color=bg_color
                        )

                    return redirect(url_for("auth.validate", email=email))
                # Check if the user exist in the database and if the inputted password is same with the one attached to
                # the user on the database
                if user:
                    # ************* THIS IS FOR PANIC LOGIN ***************
                    if user.has_set_panic:
                        if check_password_hash(user.panic_password, form.password.data):
                            if user.enabled_2fa:
                                return render_template("login.html", date=datetime.utcnow(),
                                                       form=form, alert=alert, bg_color=bg_color,
                                                       email=email, open_modal=True)
                            # If the check passed, login the user and flash a message to the user when redirected to the
                            # homepage
                            session["alert"] = "Login Successful"
                            session["bg_color"] = "success"
                            user.panic_mode = True
                            login_user(user, remember=False)
                            return redirect(url_for("view.home"))
                    # ************* END OF PANIC LOGIN ***************

                    if check_password_hash(user.password, form.password.data):
                        if user.enabled_2fa:
                            return render_template("login.html", date=datetime.utcnow(),
                                                   form=form, alert=alert, bg_color=bg_color,
                                                   email=email, open_modal=True)
                        # If the check passed, login the user and flash a message to the user when redirected to the
                        # homepage
                        session["alert"] = "Login Successful"
                        session["bg_color"] = "success"
                        user.panic_mode = False
                        login_user(user, remember=False)
                        return redirect(url_for("view.home"))
                    else:
                        # If the check failed, flash a message to the user while still on the same page
                        session["alert"] = "Check your password"
                        session["bg_color"] = "danger"
                        return redirect(url_for("auth.login"))
                else:
                    # If the user doesn't exist, flash a message to the user while still on the same page
                    session["alert"] = "User doesn't exist"
                    session["bg_color"] = "danger"
                    return redirect(url_for("auth.login"))

                    """not using this"""
                    # return redirect(url_for("auth.login"))
                    """end of block"""

        # This for a get request, if u click on the link that leads to the login page, this return statement get
        # called upon
        return render_template("login.html", date=datetime.utcnow(),
                               form=form, alert=alert, bg_color=bg_color, open_modal=False)

    except OperationalError as e:
        print(e, "ERROR")
        alert = "Please check your internet connection"
        bg_color = "danger"
        return render_template("login.html", date=datetime.utcnow(), form=form,
                               alert=alert, bg_color=bg_color)

    except Exception as e:
        print(e, "ERROR")
        alert = "Something went wrong"
        bg_color = "danger"
        return render_template("login.html", date=datetime.utcnow(), form=form,
                               alert=alert, bg_color=bg_color)


# verify_2fa
@auth.route("/verify_2fa", methods=["POST"])
def verify_2fa():
    form = LoginForm()
    auth_code = request.form.get("auth_code")
    email = request.form.get("email")
    if not auth_code:
        alert = "Please enter the authentication code"
        bg_color = "danger"
        return render_template("login.html", date=datetime.utcnow(),
                               form=form, alert=alert, bg_color=bg_color,
                               email=email, open_modal=True)
    user = User.query.filter_by(email=email).first()
    if not authenticate_auth_code(user, auth_code):
        alert = "Invalid authentication code"
        bg_color = "danger"
        return render_template("login.html", date=datetime.utcnow(),
                               form=form, alert=alert, bg_color=bg_color,
                               email=email, open_modal=True)
    session["alert"] = "Login Successful"
    session["bg_color"] = "success"
    login_user(user, remember=False)
    return redirect(url_for("view.home"))


@auth.route("/register/", methods=["GET", "POST"])
def register():
    # If the logged-in user is trying to access the login url, redirects the user to the homepage
    if current_user.is_authenticated:
        return redirect(url_for("view.home"))

    alert = session.pop("alert", None)
    bg_color = session.pop("bg_color", None)
    # Assign the RegistrationForm created in the form.py file to a variable 'form'
    form = RegistrationForm()
    # If the request is a post request and the form doesn't get validated, redirect the user to that same page
    if request.method == "POST":
        # If the form gets validated on submit
        if form.validate_on_submit():
            # Check if the username already exist
            user = User.query.filter_by(username=form.username.data.lower()).first()
            # if the username exist
            if user:
                session["alert"] = "User with this username already exist"
                session["bg_color"] = "danger"
                return redirect(url_for("auth.register"))

            # Check if email exist
            existing_email = User.query.filter_by(email=form.email.data.lower()).first()
            # if the email exist
            if existing_email:
                alert = "User with this email already exist"
                bg_color = "danger"
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form,
                    alert=alert, bg_color=bg_color
                )

            # Check if phone number exist
            existing_phone = User.query.filter_by(
                account_number=form.phone_number.data[1:]
            ).first()
            # if the phone number exist
            if existing_phone:
                session["alert"] = "User with this phone number already exist"
                session["bg_color"] = "danger"
                return redirect(url_for("auth.register"))
            if not form.phone_number.data.isnumeric():
                alert = "This is not a valid number"
                bg_color = "danger"
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form,
                    alert=alert, bg_color=bg_color
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
                alert = "Password should contain at least an uppercase, lowercase and a number"
                bg_color = "danger"
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form,
                    alert=alert, bg_color=bg_color
                )

            if len(phone_number) != 11:
                session["alert"] = "Phone number must be 11 digits"
                session["bg_color"] = "danger"
                return redirect(url_for("auth.register"))

            if (
                form.invited_by.data
                and not User.query.filter_by(
                    account_number=form.invited_by.data
                ).first()
            ):
                alert = "Invalid referral code"
                bg_color = "danger"
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form,
                    alert=alert, bg_color=bg_color
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
                alert = "Failed to verify email"
                bg_color = "danger"
                return render_template(
                    "register.html", date=datetime.utcnow(), form=form,
                    alert=alert, bg_color=bg_color
                )

            # Add the 'new_user'
            db.session.add(new_user)
            db.session.commit()

            session["alert"] = "A confirmation email has been sent to you via email"
            session["bg_color"] = "success"
            return redirect(url_for("auth.validate", email=email))

    return render_template("register.html", date=datetime.utcnow(), form=form,
                           alert=alert, bg_color=bg_color)


@auth.route("/logout/")
@login_required
def logout():
    logout_user()
    session["alert"] = "You've been logged out successfully"
    session["bg_color"] = "success"
    return redirect(url_for("view.front_page"))
