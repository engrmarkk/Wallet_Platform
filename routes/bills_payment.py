from datetime import datetime

from werkzeug.exceptions import RequestEntityTooLarge

from extensions import mail, db
from flask_mail import Message
from flask_login import current_user, login_required
from flask import redirect, url_for, flash, request, \
    render_template, Blueprint, make_response, jsonify
from models import User, Transaction, Beneficiary, Card, Invitees
from form import *
# from func import check_user_activity
from werkzeug.security import generate_password_hash
import random
import datetime
import cloudinary
import os
import requests
import cloudinary.uploader
import cloudinary_config
from routes.auth import login

bills = Blueprint("bills", __name__, template_folder='../templates')


@bills.route("/purchase_product", methods=["POST"])
@login_required
def vtpass_payment():
    amount = request.form.get("amount")
    phone_number = request.form.get("phone_number")
    service_id = request.form.get("service_id")

    if not amount or not phone_number or not service_id:
        flash("All fields are required", "danger")
        return redirect(url_for("view.home"))

    # Make a request to the VTPass API to initiate the payment
    response = requests.post(
        "https://vtpass.com/api/pay",
        headers={"Content-Type": "application/json"},
        json={
            "request_id": str(datetime.datetime.now().timestamp()) + str(current_user.id),
            "amount": amount,
            "phone_number": phone_number,
            "serviceID": glo,
            "phone": current_user.phone_number,
        }
    )

    if response.status_code == 200:
        # Payment was successful
        flash("Payment successful", "success")
        return redirect(url_for("view.home"))
    else:
        # Payment failed
        flash("Payment failed", "danger")
        return redirect(url_for("view.home"))
