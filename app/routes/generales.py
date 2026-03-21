from ..app import app, db
from flask import render_template
from ..models.models import User, DefTableInstitution, DefAuteur, DefPublication, DefLiaisonSujets, WikidataArchaeologicalSites, WikidataPersons, WikidataPlaces, WikidataConcepts, WikidataOrganizations, WikidataArtMovements, WikidataTimePeriods
from sqlalchemy import text, inspect

@app.route('/')
@app.route('/home')
def home():
    return render_template('pages/base.html')

@app.route('/login')
def login():
    return redirect('/')
