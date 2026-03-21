from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='statics')

app.config.from_object(Config)

db = SQLAlchemy(app)

from .routes import generales

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
        with app.app_context():
            with db.engine.connect() as conn:
                # Vérifier si la colonne existe
                inspector = inspect(db.engine)
                colonnes = [col['name'] for col in inspector.get_columns('users')]
        
                if 'password' in colonnes:
                    app.logger.info('La colonne existe déjà')
                else:
                    conn.execute(text('ALTER TABLE users ADD COLUMN password VARCHAR(255)'))
                    conn.commit()
                    app.logger.info('La colonne a été ajoutée')

    except Exception as e:
        app.logger.error(f'Problème : {str(e)}')

login()