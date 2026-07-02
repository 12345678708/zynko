from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

class RegisterForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired(), Length(3, 80)])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(6, 128)])
    confirm = PasswordField("Confirmer", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("S'inscrire")

class LoginForm(FlaskForm):
    username = StringField("Nom d'utilisateur", validators=[DataRequired()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    remember = BooleanField("Se souvenir")
    submit = SubmitField("Se connecter")
