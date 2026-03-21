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
    '''
    Vérifie si la colonne 'password' existe dans la table 'users' et l'ajoute si elle est absente.

    Comportement :
        - Inspecte les colonnes de la table 'users' via SQLAlchemy
        - Si la colonne 'password' existe déjà, ne fait rien
        - Si la colonne 'password' n'existe pas, exécute un ALTER TABLE pour l'ajouter

    Retourne :
        str : Un message indiquant le résultat de l'opération
            - 'La colonne existe déjà'  → la colonne 'password' était déjà présente
            - 'Colonne ajoutée'         → la colonne 'password' a été créée avec succès
            - 'Problème : <détail>'     → une erreur s'est produite, avec le message d'erreur

    Dépendances :
        - db        : instance SQLAlchemy (flask_sqlalchemy)
        - inspect   : from sqlalchemy import inspect
        - text      : from sqlalchemy import text
    
    Notes : 
        - L'ajout de la colonne 'password' ne peut se faire que par une requête SQL "en dure".
    '''
    try:
        with db.engine.connect() as conn:
            # Vérifier si la colonne existe
            inspector = inspect(db.engine)
            colonnes = [col['name'] for col in inspector.get_columns('users')]
        
            if 'password' in colonnes:
                return 'La colonne existe déjà'
            else:
                conn.execute(text('ALTER TABLE users ADD COLUMN password VARCHAR(255)'))
                conn.commit()
                return 'Colonne ajoutée'
    except Exception as e:
        return f'Problème : {str(e)}'
