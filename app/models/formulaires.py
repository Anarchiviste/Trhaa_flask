from ..app import db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length

class Ajout_utilisateur(FlaskForm):
    prenom   = StringField("Prénom", validators=[DataRequired()])
    email    = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mot de passe", validators=[DataRequired(), Length(min=6)])