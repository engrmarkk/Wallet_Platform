from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    IntegerField,
    BooleanField,
    TelField,
    TextAreaField,
    # ValidationError
)
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask import flash
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, ValidationError


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
    secret_answer = StringField("Enter a secret answer (This answer cannot be changed)", validators=[DataRequired(), Length(min=2, max=50)])
    submit = SubmitField("Create")


class ChangeTransferPin(FlaskForm):
    new_pin = IntegerField("Enter new 4 digits transfer pin", validators=[DataRequired(), NumberRange(min=1000, max=9999)])
    secret_answer = StringField("Enter your secret answer", validators=[DataRequired(), Length(min=2, max=50)])
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
    invited_by = TelField("Invited by (optional)", validators=[Length(max=10)])
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

    def validate_image(self, field):
        if field.data:
            if len(field.data.read()) > 1 * 1024 * 1024:
                flash("File size should be less than 1 MB.", category="danger")
                raise ValidationError("File size should be less than 1 MB.")


class ConfirmAccount(FlaskForm):
    account_number = TelField("Wallet Account Number", validators=[DataRequired(), Length(max=10)])


class CardForm(FlaskForm):
    card_number = TelField("Card Number", validators=[DataRequired(), Length(max=16)])
    card_name = StringField("Card Name", validators=[DataRequired(), Length(min=2, max=30)])
    card_expiry = StringField("Card Expiry", validators=[DataRequired(), Length(max=5)])
    card_cvv = TelField("Card CVV", validators=[DataRequired(), Length(max=3)])
    card_pin = TelField("Card PIN", validators=[DataRequired(), Length(max=4)])
    submit = SubmitField("Add Card")


class SaveMoneyForm(FlaskForm):
    amount = IntegerField("Amount", validators=[DataRequired(), NumberRange(min=100)])
    submit = SubmitField("Save")
