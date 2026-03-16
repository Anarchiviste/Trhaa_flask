from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy

app = Flask(
    __name__,
    template_folder='app/templates',
    static_folder='app/statics')

app.config.from_object(Config)

db = SQLAlchemy(app)

from .routes import generales