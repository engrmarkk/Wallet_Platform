from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    IntegerField,
    BooleanField,
    TelField,
    TextAreaField,
)
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SendMoneyForm(FlaskForm):
    amount = IntegerField("Amount", validators=[DataRequired(), NumberRange(min=100)])
    add_beneficiary = BooleanField("Add as beneficiary")
    transfer_pin = IntegerField("Enter 4 digits transfer pin", validators=[DataRequired()])
    submit = SubmitField("Send")

class CreateTransferPin(FlaskForm):
    transfer_pin = IntegerField("Create 4 digits transfer pin", validators=[DataRequired(), NumberRange(min=1000, max=9999)])
    confirm_transfer_pin = IntegerField("Confirm 4 digits transfer pin", validators=[DataRequired(), EqualTo("transfer_pin")])
    submit = SubmitField("Create")

class ChangeTransferPin(FlaskForm):
    new_pin = IntegerField("Enter new 4 digits transfer pin", validators=[DataRequired(), NumberRange(min=1000, max=9999)])
    confirm_new_pin = IntegerField("Confirm 4 digits transfer pin", validators=[DataRequired(), EqualTo("new_pin")])
    email = StringField("Enter your email address", validators=[DataRequired(), Email()])
    submit = SubmitField("Change")


class RegistrationForm(FlaskForm):
    first_name = StringField(
        "First Name", validators=[DataRequired(), Length(min=2, max=30)]
    )
    last_name = StringField(
        "Last Name", validators=[DataRequired(), Length(min=2, max=30)]
    )
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=25)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone_number = TelField("Phone Number", validators=[DataRequired(), Length(max=11)])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign Up")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=5)])
    submit = SubmitField()


class ResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")


class PhotoForm(FlaskForm):
    image = FileField(validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])


class ConfirmAccount(FlaskForm):
    account_number = TelField("Wallet Account Number", validators=[DataRequired(), Length(max=10)])
