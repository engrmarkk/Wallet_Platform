from datetime import datetime
from extensions import db, mail
from flask_login import current_user, login_user, logout_user, login_required
from flask import redirect, url_for, flash, request, render_template, Blueprint
from models import User
from form import *
from flask_mail import Message
from random import randint
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint("auth", __name__)

otp = randint(100000, 999999)


@auth.route('/validate', methods=['GET', 'POST'])
def validate():
    if request.method == "POST":
        user_otp = request.form['otp']
        if otp == int(user_otp):
            User.confirmed = True
            flash("Email verification successful", category="success")
            return redirect(url_for("auth.login"))
        else:
            flash("try again", category="danger")

    return render_template('confirmation.html', date=datetime.utcnow())


@auth.route("/login/", methods=["GET", "POST"])
def login():
    # If the logged-in user is trying to access the login url, redirects the user to the homepage
    if current_user.is_authenticated:
        return redirect(url_for("view.home"))
    # Assign the LoginForm created in the form.py file to a variable 'form'
    form = LoginForm()
    # If the form gets validated on submit
    if form.validate_on_submit():
        # Query the User model and assign the queried data to the variable 'user'
        user = User.query.filter_by(email=form.email.data.lower()).first()
        # Check if the user exist in the database and if the inputted password is same with the one attached to the user on the database
        if user:
            if check_password_hash(user.password, form.password.data):
                # If the check passed, login the user and flash a message to the user when redirected to the homepage
                flash("Login Successful", "success")
                login_user(user, remember=True)
                return redirect(url_for("view.home", id=user.id, user=current_user))
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
                return redirect(url_for("auth.register"))

            # Check if phone number exist
            existing_phone = User.query.filter_by(email=form.phone_number.data).first()
            # if the phone number exist
            if existing_phone:
                # Flash this message to the user and redirect the user to that same page
                flash("User with this phone number already exist", category="danger")
                return redirect(url_for("auth.register"))

            first_name = form.first_name.data.lower()
            last_name = form.last_name.data.lower()
            username = form.username.data.lower()
            email = form.email.data.lower()
            phone_number = str(form.phone_number.data)
            account_number = int(str(phone_number)[1:])
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
                return redirect(url_for("auth.register"))

            if len(phone_number) is not 11:
                flash("Phone number must be 11 digits", "danger")
                return redirect(url_for('auth.register'))

            # variable 'new_user'
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                username=username,
                phone_number=phone_number,
                email=email,
                account_number=account_number,
                password=password_hash,
                confirmed=False
            )            

            msg = Message(subject='Email Verification', sender='noah13victor@gmail.com', recipients=[email])
            msg.html = render_template("email_verification.html", first_name=first_name, otp=str(otp))
            mail.send(msg)

            # Add the 'new_user'
            db.session.add(new_user)
            db.session.commit()

            flash("A confirmation email has been sent to you via email", category="success")
            return redirect(url_for("auth.validate"))

    return render_template("register.html", date=datetime.utcnow(), form=form)


@auth.route("/logout/")
@login_required
def logout():
    logout_user()
    flash("You've been logged out successfully", "success")
    return redirect(url_for("view.front_page"))
