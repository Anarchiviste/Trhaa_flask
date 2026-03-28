from flask import Flask, jsonify
from .config import Config
from flask_sqlalchemy import SQLAlchemy

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='statics')

app.config.from_object(Config)

db = SQLAlchemy(app)

from .routes import generales

from .utils.trad_pays import build_country_map

@app.route('/trad')
def trad():
    country_map=build_country_map(app,db)
    return jsonify(country_map)
