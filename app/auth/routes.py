from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from app.forms import LoginForm
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login=form.login.data).first()
        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash("Невозможно аутентифицироваться с указанными логином и паролем", "danger")
            return render_template("login.html", form=form)

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("main.index")
        return redirect(next_page)

    return render_template("login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    next_page = request.referrer or url_for("main.index")
    return redirect(next_page)
