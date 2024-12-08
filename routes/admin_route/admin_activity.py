from flask import Blueprint, render_template, request, url_for, session, redirect
from flask_login import login_required, current_user
from func import get_all_admins, create_admin, create_super_admin, get_all_users, get_one_user, get_one_admin,\
    get_user_transactions
import traceback
from extensions import db
from decorators import super_admin_required, admin_required


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
            phone = request.args.get("phone")
            admins = get_all_admins(page, per_page, email, is_super_admin, fullname, phone)
            return render_template("admin_temp/all_admins.html",
                                   admins=admins, alert=alert, bg_color=bg_color, all_admins=True)

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


# update admin
@admin_blp.route("/admin/<admin_id>", methods=["GET"])
@login_required
@super_admin_required
def one_admin(admin_id):
    try:
        admin = get_one_admin(admin_id)
        deactivate = request.args.get("deactivate", None)
        if not admin:
            session["alert"] = "Admin not found"
            session["bg_color"] = "danger"
            return redirect(url_for("admin_blp.get_admins"))
        if deactivate:
            admin.active = not admin.active
            db.session.commit()
            session["alert"] = "Admin updated successfully"
            session["bg_color"] = "success"
            return redirect(url_for("admin_blp.get_admins"))
        return render_template("admin_temp/one_admin.html", admin=admin, all_admins=True)
    except Exception as e:
        print(e, "error in one admin")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("view.home"))


# get users
@admin_blp.route("/users", methods=["GET"])
@login_required
def get_users():
    try:
        alert = session.pop("alert", None)
        bg_color = session.pop("bg_color", None)
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        email = request.args.get("email")
        fullname = request.args.get("fullname")
        phone_number = request.args.get("phone_number")
        user_name = request.args.get("user_name")
        account_number = request.args.get("account_number")
        has_set_panic = request.args.get("has_set_panic")
        users, user_count, completed_user, active_users = get_all_users(page, per_page, email, fullname, phone_number, user_name, account_number, has_set_panic)
        return render_template("admin_temp/all_users.html", users=users, alert=alert, bg_color=bg_color,
                               user_count=user_count, all_users=True, completed_user=completed_user,
                               uncompleted_user=user_count - completed_user, active_users=active_users,
                               inactive_users=user_count - active_users)
    except Exception as e:
        print(e, "error in get users")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("admin_blp.get_users"))


# update user
@admin_blp.route("/user/<user_id>", methods=["GET"])
@login_required
# @super_admin_required
def one_user(user_id):
    try:
        alert = session.pop("alert", None)
        bg_color = session.pop("bg_color", None)
        user = get_one_user(user_id)
        deactivate = request.args.get("deactivate", None)
        if not user:
            session["alert"] = "User not found"
            session["bg_color"] = "danger"
            return redirect(url_for("admin_blp.get_users"))
        if deactivate:
            user.active = not user.active
            db.session.commit()
            session["alert"] = "User deactivated successfully" if not user.active else "User activated successfully"
            session["bg_color"] = "success"
            return redirect(url_for("admin_blp.one_user", user_id=user.id))
        return render_template("admin_temp/one_user.html", user=user, all_users=True,
                               alert=alert, bg_color=bg_color)
    except Exception as e:
        print(e, "error in one user")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("admin_blp.one_user", user_id=user_id))


# user transaction
@admin_blp.route("/user/<user_id>/transactions", methods=["GET"])
@login_required
def user_transactions(user_id):
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        transaction_type = request.args.get("transaction_type")
        status = request.args.get("status")
        category = request.args.get("category")
        user = get_one_user(user_id)
        if not user:
            session["alert"] = "User not found"
            session["bg_color"] = "danger"
            return redirect(url_for("admin_blp.one_user", user_id=user_id))
        paginated_transactions, all_transactions, successful_transactions, pending_transactions, failed_transactions, inflow_transactions, outflow_transactions = get_user_transactions(page, per_page, transaction_type, status, category, user)
        return render_template("admin_temp/user_transactions.html", user=user, all_users=True,
                               paginated_transactions=paginated_transactions, all_transactions_count=all_transactions,
                               successful_transactions=successful_transactions, pending_transactions=pending_transactions,
                               failed_transactions=failed_transactions, inflow_transactions=inflow_transactions,
                               outflow_transactions=outflow_transactions)
    except Exception as e:
        print(e, "error in user transactions")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("admin_blp.one_user", user_id=user_id))


# admin dashboard
@admin_blp.route(f"/dashboard", methods=["GET"])
@login_required
def admin_dashboard():
    try:
        if not current_user.is_admin:
            return redirect(url_for("view.home"))
        return render_template("admin_temp/admin_dashboard.html", admin_dashboard=True)
    except Exception as e:
        print(e, "error in admin dashboard")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("view.home"))
