from ..app import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class AjoutUtilisateur(FlaskForm):
    nom_utilisateur   = StringField("Prénom", validators=[DataRequired()])
    email_utilisateur  = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("S'inscrire")     

class LoginUtilisateur(FlaskForm):
    email_utilisateur = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    submit = SubmitField('Se connecter')