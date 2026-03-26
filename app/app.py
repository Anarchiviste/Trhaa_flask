from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from flask_login import LoginManager

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='statics')

app.config.from_object(Config)

db = SQLAlchemy(app)

login = LoginManager(app)

from .routes import generales

def password_initialisation():
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


def historique_initialisation():
    '''
    Vérifie si la table 'historique' existe dans la base de données et la crée si elle est absente.

    Comportement :
        - Récupère la liste des tables existantes via SQLAlchemy
        - Si la table 'historique' existe déjà, ne fait rien
        - Si la table 'historique' est absente, exécute un CREATE TABLE pour la créer
          avec les colonnes : id (clé primaire), nom_user (VARCHAR 100), requete (VARCHAR 255)

    Retourne :
        None : la fonction ne retourne rien, elle agit uniquement par effets de bord
            - Log INFO  → la table existait déjà ou a été créée avec succès
            - Log ERROR → une exception s'est produite, avec le message d'erreur

    Dépendances :
        - app       : instance Flask
        - db        : instance SQLAlchemy (flask_sqlalchemy)
        - inspect   : from sqlalchemy import inspect
        - text      : from sqlalchemy import text
    '''
    try:
        with app.app_context():
            with db.engine.connect() as init:
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()        
                if 'historique' in tables:                  
                    app.logger.info('La table existe déjà')
                else:
                    try:
                        init.execute(text('''
                            CREATE TABLE historique (
                                id      SERIAL PRIMARY KEY,
                                nom_user    VARCHAR(100),   
                                requete VARCHAR(255)        
                            )
                        '''))                               
                        init.commit()
                        app.logger.info('La table a été créée')
                    except Exception as e:
                        app.logger.error(f'Problème création : {str(e)}')
    except Exception as e:
        app.logger.error(f'Problème : {str(e)}')

historique_initialisation()