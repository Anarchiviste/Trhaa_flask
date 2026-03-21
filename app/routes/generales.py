from ..app import app
from flask import render_template
from ..models.models import User, DefTableInstitution, DefAuteur, DefPublication, DefLiaisonSujets, WikidataArchaeologicalSites, WikidataPersons, WikidataPlaces, WikidataConcepts, WikidataOrganizations, WikidataArtMovements, WikidataTimePeriods

@app.route('/')
@app.route('/home')
def home():
    return render_template('pages/base.html')