from ..app import app, db
from flask import render_template, redirect, url_for
from ..models.models import User, DefTableInstitution, DefAuteur, DefPublication, DefLiaisonSujets, WikidataArchaeologicalSites, WikidataPersons, WikidataPlaces, WikidataConcepts, WikidataOrganizations, WikidataArtMovements, WikidataTimePeriods
from sqlalchemy import text, inspect
from ..models.formulaires import Ajout_utilisateur

@app.route('/')
@app.route('/home')
def home():
    return render_template('pages/base.html')

@app.route('/login')
def login():
    return redirect(url_for('home'))

@app.route('/signin' )
def signin():
    return redirect(url_for('home'))
