from flask import Blueprint, render_template, request, url_for, session, redirect
from flask_login import login_required
from func import get_all_admins, create_admin, create_super_admin
import traceback


admin_blp = Blueprint("admin_blp", __name__, template_folder="../templates")

# get admins
@admin_blp.route("/admins", methods=["GET", "POST"])
@login_required
def get_admins():
    try:
        alert = session.pop("alert", None)
        bg_color = session.pop("bg_color", None)
        if request.method == "GET":
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 10))
            email = request.args.get("email")
            is_super_admin = request.args.get("is_super_admin")
            fullname = request.args.get("fullname")
            admins = get_all_admins(page, per_page, email, is_super_admin, fullname)
            return render_template("admin_temp/all_admins.html", admins=admins, alert=alert, bg_color=bg_color)

        # This is for post request
        email = request.form.get("email")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        is_super_admin = request.form.get("is_super_admin")
        password = request.form.get("password")
        if not first_name or not last_name or not email or not password:
            session["alert"] = "Please fill all the fields"
            session["bg_color"] = "danger"
            return redirect(url_for("admin_blp.get_admins"))
        resp = create_admin(first_name, last_name, email, password) if not is_super_admin \
            else create_super_admin(first_name, last_name, email, password)
        if not resp:
            session["alert"] = "Admin creation failed"
            session["bg_color"] = "danger"
            return redirect(url_for("admin_blp.get_admins"))
        session["alert"] = "Admin created successfully"
        session["bg_color"] = "success"
        return redirect(url_for("admin_blp.get_admins"))
    except Exception as e:
        print(e, "error in get admins")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("view.home"))


