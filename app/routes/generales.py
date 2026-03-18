from ..app import app
from flask import render_template
from ..models.models import User, DefTableInstitution, DefAuteur, DefPublication, DefLiaisonSujets, WikidataArchaeologicalSites, WikidataPersons, WikidataPlaces, WikidataConcepts, WikidataOrganizations, WikidataArtMovements, WikidataTimePeriods

@app.route('/')
def test():
    '''
    Test est une fonction de test de connection entre l'application, l'ORM et la base de donnée postgres.
     Il s'agit d'un simple SELECT * (query.all()) affiché au sein d'un htlm brut.
    '''
    donnees = []
    for institution in DefTableInstitution.query.all():
        donnees.append({
            "id": institution.id,
            "nom": institution.nom
        })
    return f'''
        <html>
            <body>
                <p>{donnees}</p>
            </body>
        </html>
        '''