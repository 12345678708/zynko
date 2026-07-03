from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .forms import LoginForm, RegisterForm
from ..extensions import db
from ..models import User
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy.exc import OperationalError

auth_bp = Blueprint("auth", __name__, url_prefix="")


def ensure_tables_exist():
    try:
        inspector = sqlalchemy_inspect(db.engine)
        tables = inspector.get_table_names()
        if 'user' not in tables:
            current_app.logger.info('User table missing; creating tables via db.create_all()')
            db.create_all()
            current_app.logger.info('db.create_all() completed from ensure_tables_exist')
    except Exception as e:
        # Log but do not raise to avoid crashing the request
        current_app.logger.warning('ensure_tables_exist failed: %s', e)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        # Ensure DB tables exist before querying
        ensure_tables_exist()
        try:
            if User.query.filter_by(username=form.username.data).first():
                flash("Nom d'utilisateur déjà pris.", "danger")
                return render_template("register.html", form=form), 400
            user = User(username=form.username.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Compte créé et connecté.", "success")
            return redirect(url_for("main.dashboard"))
        except OperationalError as oe:
            current_app.logger.warning('DB operational error during register: %s', oe)
            flash('Le service de base de données n\'est pas disponible pour le moment. Réessayez plus tard.', 'danger')
            return render_template('register.html', form=form), 503
        except Exception as e:
            current_app.logger.exception('Unexpected error during register: %s', e)
            flash('Erreur interne lors de la création du compte.', 'danger')
            return render_template('register.html', form=form), 500
    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        # Ensure DB tables exist before querying
        ensure_tables_exist()
        try:
            user = User.query.filter_by(username=form.username.data).first()
        except OperationalError as oe:
            current_app.logger.warning('DB operational error during login: %s', oe)
            flash('Le service de base de données n\'est pas disponible pour le moment. Réessayez plus tard.', 'danger')
            return render_template('login.html', form=form), 503
        try:
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for("main.dashboard"))
            flash("Identifiants invalides", "danger")
        except Exception as e:
            current_app.logger.exception('Unexpected error during login: %s', e)
            flash('Erreur interne lors de la connexion.', 'danger')
            return render_template('login.html', form=form), 500
    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Déconnecté.", "info")
    return redirect(url_for("main.index"))
