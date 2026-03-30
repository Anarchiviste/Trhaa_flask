# Travaux de recherche en histoire de l'art et archéologie

## Initialisation de l'application

Au lancement de l'application, l'application execute automatiquement deux fonctions : 

_password_initialisation()_

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

_historique_initialisation()_

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
