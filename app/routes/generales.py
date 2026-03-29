from ..app import app, db
from flask import render_template, redirect, url_for, flash, request
from ..models.models import User, DefTableInstitution, DefAuteur, DefPublication, DefLiaisonSujets, WikidataArchaeologicalSites, WikidataPersons, WikidataPlaces, WikidataConcepts, WikidataOrganizations, WikidataArtMovements, WikidataTimePeriods
from sqlalchemy import text, inspect
from ..models.formulaires import AjoutUtilisateur, LoginUtilisateur
from ..utils.recherche_avancee import recherche_avancee, get_options_filtres
from ..utils.recherche_simple import barre_recherche_simple


@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    q = (request.form.get('q') or request.args.get('q', '')).strip()
    resultats = None

    if request.method == 'POST' or q:
        ids_a_inclure = None
        if q:
            resultats_simple = barre_recherche_simple(q)
            ids_a_inclure = [r['id'] for r in resultats_simple]

        resultats = recherche_avancee(
            auteur        = request.form.get('auteur'),
            institution   = request.form.get('institution'),
            typologie     = request.form.get('typologie'),
            langue        = request.form.get('langue'),
            date_min      = request.form.get('date_min'),
            date_max      = request.form.get('date_max'),
            sujet_rameau  = request.form.get('sujet_rameau'),
            ids_a_inclure = ids_a_inclure,
        )

    return render_template('pages/home.html', resultats=resultats, q=q)

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    FlaskForm LoginUtilisateur pour authentifier un utilisateur existant.

    Comportement :
        - Initialise le formulaire avec la classe LoginUtilisateur
        - Récupère les données avec validate_on_submit()
        - Vérifie l'authenticité des identifiants (email/mot de passe)
        - Si la connexion est réussie, redirige vers la page d'accueil
        - Sinon, réaffiche la page de login avec un message d'erreur

    Retourne :
        Connexion réussie
            - Redirige vers la route home avec un message flash de succès.
        Connexion échouée
            - Réaffiche la page login.html avec le message d'erreur et le formulaire.
        Formulaire non soumis/valide
            - Affiche la page login.html avec le formulaire.
        
    Dépendances :
        - Flask
        - Flask-Login
        - Flask-WTF
        - Flask-SQLAlchemy
        - User.connexion : Méthode statique pour vérifier les identifiants utilisateur
        - Flaskform LoginUtilisateur
    '''
    form = LoginUtilisateur()
    if form.validate_on_submit():
        statut, donnees = User.connexion(
            email=form.email_utilisateur.data,
            password=form.password.data
        )
        if statut is True:
            flash("Connexion réussie", "success")
            app.logger.info('login success')
            return redirect(url_for('home'))
        else:
            flash(donnees, "error")
            app.logger.info('login no success')
    return render_template('pages/login.html', form=form)

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    '''
    FlaskForm AjoutUtilisateur pour créer un nouveau compte.

    Comportement :
        - Initialise le formulaire avec la bonne classe
        - Récupère les données avec validate_on_submit()
        - Vérifie l'intégrité des champs reçus
        - Si l'ajout est réussi, renvoit vers le login, 
        sinon renvoit de nouveau vers le signin

    Retourne : 
        Création réussie
            - Redirige vers la route login avec un message flash de succès.
        Création échouée
            - Réaffiche la page sign-in.html avec les erreurs et le formulaire.
        Formulaire non soumis/valide
            - Affiche la page sign-in.html avec le formulaire.
        
    Dépendances : 
        - Flask
        - Flask-Login
        - Flask-WTF
        - Flask-SQLAlchemy
        - User.compte_utilisateur : Méthode statique pour créer un compte utilisateur.
        - Flaskform AjoutUtilistateur

    Notes : 
        Validation des données : Le formulaire est validé côté serveur pour éviter les soumissions malveillantes.
        Hachage des mots de passe : Les mots de passe sont hachés avant d'être stockés en base de données.

    '''
    form = AjoutUtilisateur()

    if form.validate_on_submit():
        statut, donnees = User.compte_utilisateur(    
            nom=form.nom_utilisateur.data,            
            email=form.email_utilisateur.data,        
            password=form.password.data               
            )

        if statut is True:
            flash("Ajout effectué", "success")
            app.logger.info('signin success')

            return redirect(url_for('login'))

        else:
            flash(",".join(donnees), "error")
            app.logger.info('signin no success')
            return render_template('/pages/sign-in.html', form=form)
    
    else:
        app.logger.info('lancement de la page de sign-in')
        return render_template('pages/sign-in.html', form=form)

login.login_view = 'connexion'


@app.context_processor
def inject_recherche():
    return dict(
        options=get_options_filtres(),
        resultats=None
    )