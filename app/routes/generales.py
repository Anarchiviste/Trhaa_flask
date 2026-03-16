from ..app import app
from flask import render_template
from ..models.models import InstitutionDefinitive

@app.route('/')
def test():
    '''
    Test est une fonction de test de connection entre l'application, l'ORM et la base de donnée postgres.
     Il s'agit d'un simple SELECT * (query.all()) affiché au sein d'un htlm brut.
    '''
    donnees = []
    for institution in InstitutionDefinitive.query.all():
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