from ..app import app, db
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

@app.route('/p_tableau_resultats')
def p_tableau_resultats():
    resultats = db.session.query(
        DefAuteur.auteur_nom,
        DefAuteur.auteur_prenom,
        DefPublication.titre,
        DefPublication.date_publication
    ).join(DefPublication, DefAuteur.id == DefPublication.id_auteur).all()

    return render_template("pages/tableau_resultats.html", resultats=resultats)
