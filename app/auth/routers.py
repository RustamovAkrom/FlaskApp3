from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import LoginForm, RegistrationForm
from app.models import User
from app import db, login_manager


auth = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return render_template("main.index")
    
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username = username).first()

        if user and user.check_password(password) :

            login_user(user, remember=True)
            next_page = request.args.get("next")

            return redirect(next_page) if next_page else redirect(url_for("main.index"))
        
        flash("You have successfully Sign in.", "danger")
        return redirect(url_for("main.index"))
    
    flash("Error in loggin !")
    return render_template("auth/login.html", form=form)


@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return render_template("main.index")
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            first_name = form.first_name.data,
            last_name = form.last_name.data,
            username = form.username.data,
            email = form.email.data,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("you successfully registered", "success")
        return redirect(url_for("main.index"))
    
    flash("You already exists!", "danger")
    return render_template("auth/register.html", form = form)


@auth.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth.route("/account")
@login_required
def account():
    return render_template("auth/account.html")

