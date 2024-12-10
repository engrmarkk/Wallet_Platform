from flask import Blueprint, render_template, request, url_for, session, redirect
from flask_login import login_required, current_user
from func import get_all_admins, create_admin, create_super_admin, get_all_users, get_one_user, get_one_admin,\
    get_user_transactions, get_all_transactions, statistics
import traceback
from extensions import db
from decorators import super_admin_required, admin_required, user_admin_required
from passlib.hash import pbkdf2_sha256 as hasher
from sqlalchemy.exc import IntegrityError


admin_blp = Blueprint("admin_blp", __name__, template_folder="../templates")


# get admins
@admin_blp.route("/admins", methods=["GET", "POST"])
@login_required
@admin_required
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
        print("is super admin", is_super_admin)
        resp = create_admin(first_name, last_name, email, password) if not is_super_admin \
            else create_super_admin(first_name, last_name, email, password)
        if not resp or isinstance(resp, str):
            session["alert"] = "Admin creation failed" if not isinstance(resp, str) else resp
            session["bg_color"] = "danger"
            return redirect(url_for("admin_blp.get_admins"))
        session["alert"] = "Admin created successfully"
        session["bg_color"] = "success"
        return redirect(url_for("admin_blp.get_admins"))
    except IntegrityError as e:
        print(e, "error in get admins")
        print(traceback.format_exc(), "TraceBack")
        session["alert"] = "Email already exists"
        session["bg_color"] = "danger"
        return redirect(url_for("admin_blp.get_admins"))
    except Exception as e:
        print(e, "error in get admins")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("admin_blp.get_admins"))


# update admin
@admin_blp.route("/admin/<admin_id>", methods=["GET", "POST"])
@login_required
@admin_required
def one_admin(admin_id):
    try:
        admin = get_one_admin(admin_id)
        delete = request.args.get("delete", None)
        update = request.args.get("update", None)
        active_status = request.form.get("is_active", None)
        is_super_admin_status = request.form.get("is_super_admin", None)
        print(request.form)
        if not admin:
            session["alert"] = "Admin not found"
            session["bg_color"] = "danger"
            return redirect(url_for("admin_blp.get_admins"))
        if delete:
            print("deleting admin")
            if admin.id == current_user.id:
                session["alert"] = "You cannot delete yourself"
                session["bg_color"] = "danger"
                return redirect(url_for("admin_blp.get_admins"))
            admin.delete()
            session["alert"] = "Admin deleted successfully"
            session["bg_color"] = "success"
            return redirect(url_for("admin_blp.get_admins"))
        if update:
            admin.first_name = request.form.get("first_name", admin.first_name)
            admin.last_name = request.form.get("last_name", admin.last_name)
            admin.email = request.form.get("email", admin.email)
            if request.form.get("password"):
                admin.password = hasher.hash(request.form.get("password"))
            admin.is_super_admin = True if is_super_admin_status else False
            admin.active = True if active_status else False
            db.session.commit()
            session["alert"] = "Admin updated successfully"
            session["bg_color"] = "success"
            return redirect(url_for("admin_blp.get_admins"))
        return render_template("admin_temp/one_admin.html", admin=admin, all_admins=True)
    # except integrityerror:
    except IntegrityError as e:
        print(e, "error in one admin")
        print(traceback.format_exc(), "TraceBack")
        session["alert"] = "Email already exists"
        session["bg_color"] = "danger"
        return redirect(url_for("admin_blp.get_admins"))
    except Exception as e:
        print(e, "error in one admin")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("admin_blp.get_admins"))


# get users
@admin_blp.route("/users", methods=["GET"])
@login_required
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
def admin_dashboard():
    try:
        alert = session.pop("alert", None)
        bg_color = session.pop("bg_color", None)
        # get from sesssion
        # if "stats" in session:
        #     stats = session["stats"]
        #     return render_template("admin_temp/admin_dashboard.html", admin_dashboard=True,
        #                            stats=stats, alert=alert, bg_color=bg_color)
        stats = statistics()
        # store in session
        session["stats"] = stats
        return render_template("admin_temp/admin_dashboard.html", admin_dashboard=True,
                               stats=stats, alert=alert, bg_color=bg_color)
    except Exception as e:
        print(e, "error in admin dashboard")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("admin_blp.admin_dashboard"))


# get all user transaction
@admin_blp.route("/transactions", methods=["GET"])
@login_required
@admin_required
def get_all_user_transactions():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 15))
        status = request.args.get("status")
        transaction_type = request.args.get("transaction_type")
        category = request.args.get("category")
        bank_name = request.args.get("bank_name")
        receiver = request.args.get("receiver")

        transactions, all_trans_count, success_counts, pending_counts, failed_counts, inflow, outflow = get_all_transactions(page, per_page, status, transaction_type, category, bank_name, receiver)
        return render_template("admin_temp/all_transactions.html",
                               all_transactions=True, paginated_transactions=transactions,
                               all_transactions_count=all_trans_count,
                               successful_transactions=success_counts,
                               pending_transactions=pending_counts,
                               failed_transactions=failed_counts,
                               inflow_transactions=inflow,
                               outflow_transactions=outflow)
    except Exception as e:
        print(e, "error in get all user transactions")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("admin_blp.admin_dashboard"))


# message user
@admin_blp.route("/message-user", methods=["GET", "POST"])
@login_required
@admin_required
def message_user():
    try:
        return render_template("admin_temp/message_user.html", admin_dashboard=True)
    except Exception as e:
        print(e, "error in message user")
        print(traceback.format_exc(), "TraceBack")
        return redirect(url_for("admin_blp.admin_dashboard"))
