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
from services import VtpassService
import random
import datetime
import cloudinary
import os
import requests
import cloudinary.uploader
import cloudinary_config
from routes.auth import login
from utils import determine_purchase_type

bills = Blueprint("bills", __name__, template_folder='../templates')

vtpass_service = VtpassService()


@bills.route("/purchase_product", methods=["POST"])
@login_required
def vtpass_payment():
    amount = request.form.get("amount")
    phone_number = request.form.get("phone_number")
    service_id = request.form.get("service_id")
    request_id = str(datetime.datetime.now().timestamp()) + str(current_user.id),

    if not amount or not phone_number or not service_id:
        flash("All fields are required", "danger")
        return redirect(url_for("view.home"))

    purchase_type = determine_purchase_type(service_id)

    payload = dict(
        amount=amount,
        phone_number=phone_number,
        service_id=service_id,
        request_id=request_id
    )

    if purchase_type == "airtime":
        response, status_code = vtpass_service.purchase_airtime(
            payload
        )
    elif purchase_type == "data":
        response, status_code = vtpass_service.purchase_data(
            payload
        )
    elif purchase_type == "electricity":
        response, status_code = vtpass_service.purchase_electricity(
            payload
        )
    elif purchase_type == "cable":
        response, status_code = vtpass_service.purchase_cable(
            payload
        )
    else:
        flash("Invalid service ID", "danger")
        return redirect(url_for("view.home"))
    if status_code == 200:
        # Payment was successful
        # process the wallet history
        flash("Payment successful", "success")
        return redirect(url_for("view.home"))
    else:
        # Payment failed
        flash("Payment failed", "danger")
        return redirect(url_for("view.home"))
