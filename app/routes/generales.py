from ..app import app
from flask import render_template
from ..models.models import InstitutionDefinitive

@app.route('/')
def home():
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