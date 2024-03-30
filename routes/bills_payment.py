from datetime import datetime
from flask_login import current_user, login_required
from flask import redirect, url_for, flash, request, \
    render_template, Blueprint, make_response, jsonify, session
from form import *
from func import deduct_history, refund, update_transaction, update_status
from services import VtpassService
import datetime
import pytz
from utils import determine_purchase_type

bills = Blueprint("bills", __name__, template_folder='../templates')

vtpass_service = VtpassService()


@bills.route("/purchase_product", methods=["POST"])
@login_required
def vtpass_payment():
    tz = pytz.timezone("Africa/Lagos")

    service_id = request.args.get("service_id", "")
    amount = request.form.get("amount")
    phone_number = request.form.get("phone_number")
    billers_code = request.form.get("billers_code")
    type_ = request.form.get("type")
    variation_code = request.form.get("variation_code")
    quantity = request.form.get("quantity")
    request_id = f"{datetime.datetime.now(tz).strftime('%Y%m%d%H%M')}" + str(current_user.id)
    transaction_pin = request.form.get("transaction_pin")
    amount = float(amount)

    print("amount: ", amount, "phone_number: ", phone_number, "service_id: ", service_id,
          "billers_code: ", billers_code, "type_: ", type_, "variation_code: ", variation_code, "quantity: ", quantity,
          "request_id: ", request_id)

    if not amount or not phone_number or not service_id:
        flash("All fields are required", "danger")
        return redirect(url_for("view.home"))

    if not phone_number.isdigit():
        flash("Invalid phone number", "danger")
        return redirect(url_for("bills.get_variation", service_id=service_id))

    purchase_type = determine_purchase_type(service_id)

    transact = deduct_history(amount, current_user, request_id, purchase_type, service_id, phone_number)

    payload = dict(
        amount=amount,
        phone=phone_number,
        serviceID=service_id,
        request_id=request_id,
        billersCode=billers_code,
        type=type_
    )

    if purchase_type == "airtime":
        payload["phone"] = "08011111111"
        response, status_code = vtpass_service.purchase_airtime(
            payload
        )
    elif purchase_type == "data":
        payload["phone"] = "08011111111"
        response, status_code = vtpass_service.purchase_data(
            payload
        )
    elif purchase_type == "electricity":
        payload["billers_code"] = "1111111111111" if type_.lower() == "prepaid" else "1010101010101"
        response, status_code = vtpass_service.purchase_electricity(
            payload
        )
    elif purchase_type == "cable":
        payload = {
            "serviceID": service_id,
            "request_id": request_id,
            "billersCode": "1212121212",
            "variation_code": variation_code,
            "amount": amount,
            "phone": phone_number,
            "subscription_type": type_,
            "quantity": quantity
        }
        response, status_code = vtpass_service.purchase_cable(
            payload
        )
    else:
        flash("Invalid service ID", "danger")
        return redirect(url_for("view.home"))
    if status_code == 200 and response['code'] == "000":
        # Payment was successful
        # process the wallet history
        if purchase_type == "electricity":
            token = response["token"] if "token" in response else ""
            update_transaction(token, transact)
        update_status(transact, "Success")
        flash("Payment successful", "success")
        return redirect(url_for("view.home"))
    else:
        update_status(transact, "Failed")
        refund(amount, current_user, request_id, purchase_type, phone_number)
        # Payment failed
        flash("Payment failed", "danger")
        return redirect(url_for("view.home"))


@bills.route("/display_service/<string:service>")
@login_required
def display_service(service):
    response = vtpass_service.service_identifier(service)
    print(response, "response")
    return render_template("display_serv.html", services=response['content'], date=datetime.datetime.utcnow(),
                           service=service)


@bills.route("/display_variation/<string:service_id>", methods=["GET"])
def get_variation(service_id):
    img = session.get('img')
    response = vtpass_service.variation_codes(service_id) if service_id.lower() not in ["mtn", "glo", "etisalat",
                                                                                        "airtel"] else True
    print(response, "response")
    return render_template("display_serv.html",
                           variations=response['content']['varations'] if isinstance(response, dict) else [],
                           date=datetime.datetime.utcnow(),
                           service_id=service_id, variations_code=1, img=img)


@bills.route("/set_img_and_redirect/<string:service_id>", methods=["GET"])
def set_img_and_redirect(service_id):
    img = request.args.get('img')
    session['img'] = img
    return redirect(url_for('bills.get_variation', service_id=service_id))


@bills.route("/verify_number", methods=["GET"])
def verify_number():
    data = request.json()
    billers_code = data.get('billers_code', "")
    service_id = data.get('service_id', "")
    type_ = data.get('type', "")

    payload = dict(
        billersCode=billers_code,
        serviceID=service_id,
    )

    if type_:
        payload['type'] = type_
    response = vtpass_service.verify_meter_and_smartcard_number(payload)
    print(response, "response")
    return jsonify({"customer_name": response['content']['Customer_Name']}), 200
