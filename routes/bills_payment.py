from datetime import datetime
from flask_login import current_user, login_required
from flask import (
    redirect,
    url_for,
    flash,
    request,
    render_template,
    Blueprint,
    make_response,
    jsonify,
    session,
)
from form import *
from func import deduct_history, refund, update_transaction, update_status
from services import VtpassService
import datetime
import pytz
from passlib.hash import pbkdf2_sha256 as hasher
from utils import determine_purchase_type, send_notification
import traceback

bills = Blueprint("bills", __name__, template_folder="../templates")

vtpass_service = VtpassService()


@bills.route("/purchase_product", methods=["POST"])
@login_required
def vtpass_payment():
    try:
        tz = pytz.timezone("Africa/Lagos")

        service_id = request.args.get("service_id", "")
        amount = request.form.get("amount")
        phone_number = request.form.get("phone_number")
        billers_code = request.form.get("billers_code")
        type_ = request.form.get("type")
        variation_code = request.form.get("variation_code")
        quantity = request.form.get("quantity")
        pin = request.form.get("transaction_pin")
        customer_name = request.form.get("customer_name")
        request_id = f"{datetime.datetime.now(tz).strftime('%Y%m%d%H%M')}" + str(
            current_user.id
        )
        print("amount: ", amount)
        amount = float(amount)
        verify_number = request.form.get("verify_number", "")

        print(
            "amount: ",
            amount,
            "phone_number: ",
            phone_number,
            "service_id: ",
            service_id,
            "billers_code: ",
            billers_code,
            "type_: ",
            type_,
            "variation_code: ",
            variation_code,
            "quantity: ",
            quantity,
            "request_id: ",
            request_id,
            "customer_name",
            customer_name,
            "verify_number",
            verify_number
        )

        # if not amount or not phone_number or not service_id:
        #     flash("All fields are required", "danger")
        #     return redirect(url_for("view.home"))

        # if not phone_number.isdigit():
        #     flash("Invalid phone number", "danger")
        #     return redirect(url_for("bills.get_variation", service_id=service_id))

        # if not smartcard_number.isdigit():
        #     flash("Invalid smartcard number", "danger")
        #     return redirect(url_for("bills.get_variation", service_id=service_id))

        # if not prepaid_number.isdigit():
        #     flash("Invalid prepaid number", "danger")
        #     return redirect(url_for("bills.get_variation", service_id=service_id))

        if current_user.panic_mode:
            panic = True

            half_of_panic_balance = current_user.panic_balance / 2
            if float(amount) > half_of_panic_balance:
                session["alert"] = "Transaction limit exceeded, please try a lower amount"
                session["bg_color"] = "danger"
                return redirect(url_for("bills.get_variation", service_id=service_id))
            if float(amount) > current_user.account_balance:
                print("INSUFFICIENT FUNDS: PANIC MODE")
                session["alert"] = "Network Error"
                session["bg_color"] = "danger"
                return redirect(url_for("bills.get_variation", service_id=service_id))
            if not hasher.verify(pin, current_user.transaction_pin):
                print("invalid pin")
                session["alert"] = "Invalid transaction pin"
                session["bg_color"] = "danger"
                return redirect(url_for("bills.get_variation", service_id=service_id))
        else:
            panic = False
            if not hasher.verify(pin, current_user.transaction_pin):
                session["alert"] = "Invalid transaction pin"
                session["bg_color"] = "danger"
                return redirect(url_for("bills.get_variation", service_id=service_id))

        purchase_type = determine_purchase_type(service_id)

        transact = deduct_history(
            amount, current_user, request_id, purchase_type, service_id, phone_number,
            customer_name, verify_number, panic
        )

        payload = dict(
            amount=amount,
            phone=phone_number,
            serviceID=service_id,
            request_id=request_id,
            billersCode=billers_code,
            type=type_,
        )

        if purchase_type == "airtime":
            payload["phone"] = "08011111111"
            response, status_code = vtpass_service.purchase_product(payload)
        elif purchase_type == "data":
            payload["phone"] = "08011111111"
            #  Implement error handling to gracefully handle situations where None is returned
            try:
                response, status_code = vtpass_service.purchase_data(payload)
            except Exception as e:
                print(e, "Error occurred")
                session["alert"] = "An error occurred"
                session["bg_color"] = "danger"
                return redirect(url_for("view.home"))
        elif purchase_type == "electricity":
            variation_code = vtpass_service.variation_codes(service_id)["content"]["varations"][0]["variation_code"]
            payload["variation_code"] = variation_code
            if variation_code == "prepaid":
                billers_code = "1111111111111"
            else:
                billers_code = "1010101010101"
            payload = {
                "serviceID": service_id,
                "request_id": request_id,
                "billersCode": billers_code,
                "variation_code": variation_code,
                "amount": amount,
                "phone": phone_number,
                "type": type_,
            }
            response, status_code = vtpass_service.purchase_product(payload)
        elif purchase_type == "cable":
            payload = {
                "serviceID": service_id,
                "request_id": request_id,
                "billersCode": "1212121212",
                "variation_code": variation_code,
                "amount": amount,
                "phone": phone_number,
                "subscription_type": type_,
                "quantity": quantity,
            }
            response, status_code = vtpass_service.purchase_product(payload)
        else:
            session["alert"] = "Invalid service ID"
            session["bg_color"] = "danger"
            return redirect(url_for("view.home"))
        if status_code == 200 and response["code"] == "000":
            # Payment was successful
            # process the wallet history
            if purchase_type == "electricity":
                token = response["token"] if "token" in response else ""
                update_transaction(token, transact)
            update_status(transact, "Success")
            session["alert"] = "Payment successful"
            session["bg_color"] = "success"
            return redirect(url_for("view.home"))
        else:
            update_status(transact, "Failed")
            refund(amount, current_user, request_id, purchase_type, phone_number)
            session["alert"] = "Payment failed"
            session["bg_color"] = "danger"
            # Payment failed
            return redirect(url_for("view.home"))
    except Exception as e:
        print(traceback.format_exc(), "TraceBack")
        print(e, "error@vtpass_payment")
        session["alert"] = "Network Error"
        session["bg_color"] = "danger"
        # Payment failed
        return redirect(url_for("view.home"))


@bills.route("/purchase_data", methods=["POST"])
@login_required
def purchase_data():
    try:
        tz = pytz.timezone("Africa/Lagos")
        service_id = request.args.get("service_id", "")
        amount = request.form.get("amount")
        phone_number = request.form.get("phone_number")
        billers_code = "08011111111"
        # get the variation code via backend from the api response using the service_id
        variation_code = vtpass_service.variation_codes(service_id)["content"]["varations"][0]["variation_code"]
        pin = request.form.get("transaction_pin")

        # print(amount, "AMOUNTT")
        request_id = f"{datetime.datetime.now(tz).strftime('%Y%m%d%H%M')}" + str(
            current_user.id
        )
        amount = float(amount)

        if not phone_number.isdigit():
            session["alert"] = "Invalid phone number"
            session["bg_color"] = "danger"
            return redirect(url_for("bills.get_variation", service_id=service_id))

        if current_user.panic_mode:
            panic = True

            half_of_panic_balance = current_user.panic_balance / 2
            if float(amount) > half_of_panic_balance:
                session["alert"] = "Transaction limit exceeded, please try a lower amount"
                session["bg_color"] = "danger"
                return redirect(url_for("bills.get_variation", service_id=service_id))
            if float(amount) > current_user.account_balance:
                print("INSUFFICIENT FUNDS: PANIC MODE")
                session["alert"] = "Network Error"
                session["bg_color"] = "danger"
                return redirect(url_for("bills.get_variation", service_id=service_id))
            if not hasher.verify(pin, current_user.transaction_pin):
                print("invalid pin")
                session["alert"] = "Invalid transaction pin"
                session["bg_color"] = "danger"
                return redirect(url_for("bills.get_variation", service_id=service_id))
        else:
            panic = False
            if not hasher.verify(pin, current_user.transaction_pin):
                session["alert"] = "Invalid transaction pin"
                session["bg_color"] = "danger"
                return redirect(url_for("bills.get_variation", service_id=service_id))

        purchase_type = "data"

        transact = deduct_history(
            amount, current_user, request_id, purchase_type, service_id=service_id, phone=phone_number, panic=panic
        )

        payload = dict(
            amount=amount,
            phone="08011111111",
            serviceID=service_id,
            request_id=request_id,
            billersCode=billers_code,
            variation_code=variation_code
        )

        print(payload, "payload")

        try:
            response, status_code = vtpass_service.purchase_data(payload)
        except Exception as e:
            print(e, "Error occurred")
            session["alert"] = "An error occurred"
            session["bg_color"] = "danger"
            return redirect(url_for("view.home"))

        if status_code == 200 and response["code"] == "000":
            token = response["token"] if "token" in response else ""
            update_transaction(token, transact)
            update_status(transact, "Success")
            session["alert"] = "Payment successful"
            session["bg_color"] = "success"
            return redirect(url_for("view.home"))
        else:
            update_status(transact, "Failed")
            refund(amount, current_user, request_id, purchase_type, phone_number)
            session["alert"] = "Payment failed"
            session["bg_color"] = "danger"
            return redirect(url_for("view.home"))
    except Exception as e:
        print(traceback.format_exc(), "TraceBack")
        print(e, "error@vtpass_payment")
        session["alert"] = "Network Error"
        session["bg_color"] = "danger"
        # Payment failed
        return redirect(url_for("view.home"))


@bills.route("/display_service/<string:service>")
@login_required
def display_service(service):
    try:
        response = vtpass_service.service_identifier(service)
        # print(response, "response")
        return render_template(
            "display_serv.html",
            services=response["content"],
            date=datetime.datetime.utcnow(),
            service=service,
        )
    except Exception as e:
        print(traceback.format_exc(), "TraceBack")
        print(e, "error@vtpass_payment")
        session["alert"] = "Network Error"
        session["bg_color"] = "danger"
        return redirect(url_for("view.display_service"))


@bills.route("/display_variation/<string:service_id>", methods=["GET"])
@login_required
def get_variation(service_id):
    try:
        alert = session.pop("alert", None)
        bg_color = session.pop("bg_color", None)
        img = session.get("img", "")
        if not img:
            session["alert"] = "Session timed out"
            session["bg_color"] = "info"
            return redirect(url_for("view.home"))
        response = (
            vtpass_service.variation_codes(service_id)
            if service_id.lower() not in ["mtn", "glo", "etisalat", "airtel"]
            else True
        )
        # print(response, "response")
        return render_template(
            "display_serv.html",
            variations=response["content"]["varations"]
            if isinstance(response, dict)
            else [],
            date=datetime.datetime.utcnow(),
            service_id=service_id,
            variations_code=1,
            img=img,
            alert=alert,
            bg_color=bg_color,
        )
    except Exception as e:
        print(traceback.format_exc(), "TraceBack")
        print(e, "error@vtpass_payment")
        session["alert"] = "Network Error"
        session["bg_color"] = "danger"
        return redirect(url_for("view.get_variation"))


@bills.route("/set_img_and_redirect/<string:service_id>", methods=["GET"])
def set_img_and_redirect(service_id):
    img = request.args.get("img")
    session["img"] = img
    return redirect(url_for("bills.get_variation", service_id=service_id))


@bills.route("/verify_number", methods=["POST"])
def verify_number():
    try:
        data = request.json
        billers_code = data.get("billers_code", "")
        service_id = data.get("service_id", "")
        type_ = data.get("type", "")

        print(billers_code, service_id, type_)

        if not billers_code:
            return jsonify({"status": "failed", "msg": "please provide the number you want to verify"}), 400

        if not service_id:
            return jsonify({"status": "failed", "msg": "service id is required"}), 400

        if not type_:
            return jsonify({"status": "failed", "msg": "type is required"}), 400

        purchase_type = determine_purchase_type(service_id)

        print(purchase_type, "purchase type")

        if purchase_type == "electricity":
            billersCode = "1111111111111" if type_.lower() == "prepaid" else "1010101010101"
        else:
            billersCode = "1212121212"

        payload = dict(
            billersCode=billersCode,
            serviceID=service_id,
        )

        if type_:
            payload["type"] = type_
        response = vtpass_service.verify_meter_and_smartcard_number(payload)
        if not response:
            return jsonify({"status": "failed", "msg": "Network Error", "customer_name": current_user.last_name.title() + " " + current_user.first_name.title()}), 502
        print(response, "response")
        return jsonify({"customer_name": response["content"]["Customer_Name"]}), 200
    except Exception as e:
        print(traceback.format_exc(), "TraceBack")
        print(e, "error@vtpass_payment")
        session["alert"] = "Network Error"
        session["bg_color"] = "danger"
        return redirect(url_for("view.verify_number"))
