from ..app import app, db
from flask import render_template, redirect, url_for, flash, request
from ..models.models import User, DefTableInstitution, DefAuteur, DefPublication, DefLiaisonSujets, WikidataArchaeologicalSites, WikidataPersons, WikidataPlaces, WikidataConcepts, WikidataOrganizations, WikidataArtMovements, WikidataTimePeriods, Historique
from sqlalchemy import text, inspect
from ..models.formulaires import AjoutUtilisateur, LoginUtilisateur
from ..utils.recherche_avancee import recherche_avancee, get_options_filtres
from flask_login import current_user, login_required, logout_user, login_user
from datetime import datetime


@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('pages/home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    FlaskForm LoginUtilisateur pour authentifier un utilisateur existant.
    Comportement :
        - Redirige vers home si l'utilisateur est déjà authentifié
        - Initialise le formulaire avec la classe LoginUtilisateur
        - Récupère les données avec validate_on_submit()
        - Vérifie l'authenticité des identifiants (email/mot de passe)
        - Si la connexion est réussie, redirige vers la page demandée initialement
          ou vers home si aucune page n'était demandée
        - Sinon, réaffiche la page de login avec un message d'erreur
    Retourne :
        Utilisateur déjà connecté
            - Redirige immédiatement vers la route home.
        Connexion réussie
            - Redirige vers la route 'next' (page demandée initialement) ou home,
              avec un message flash de succès.
        Connexion échouée
            - Réaffiche la page login.html avec le message d'erreur et le formulaire.
        Formulaire non soumis/valide
            - Affiche la page login.html avec le formulaire.
    Dépendances :
        - Flask
        - Flask-Login : login_user, current_user
        - Flask-WTF
        - Flask-SQLAlchemy
        - User.connexion : Méthode statique pour vérifier les identifiants utilisateur
        - LoginUtilisateur : FlaskForm de connexion
    Notes :
        - login_view doit être configuré dans app.py via login.login_view = 'login'
          pour que @login_required redirige correctement vers cette route
        - Le paramètre 'next' est géré automatiquement par Flask-Login lors d'une
          tentative d'accès à une route protégée par @login_required
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
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
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


@app.route('/e_recherche_avancee', methods=['GET', 'POST'])
@login_required
def e_recherche_avancee():
    """
    Route Flask gérant la recherche avancée de ressources documentaires et la
    persistance de ses résultats en historique utilisateur.
    Comportements :
        - Charge les options de filtres disponibles à chaque appel (GET et POST)
        - En GET  : affiche le formulaire de recherche vide
        - En POST : récupère les 7 filtres soumis (auteur, institution, typologie,
                    langue, date_min, date_max, sujet_rameau) et exécute la recherche
        - Itère sur chaque résultat retourné et crée une entrée Historique en base
        - Compose le nom complet de l'auteur depuis auteur_nom + auteur_prenom
        - Effectue un commit unique après la boucle
        - Logue le premier résultat brut via app.logger.info pour le débogage
    Retourne :
        - render_template('pages/recherche_avancee.html') avec :
            - options  : dict des filtres disponibles pour alimenter le formulaire
            - resultats: liste de dicts des documents trouvés (None si GET ou aucun résultat)
    Dépendances :
        - Flask        : request, render_template, current_app (app.logger)
        - flask_login  : login_required, current_user
        - helpers      : get_options_filtres(), recherche_avancee()
        - models       : Historique (SQLAlchemy ORM), db.session
        - stdlib       : datetime
    """
    options = get_options_filtres()
    resultats = None

    if request.method == 'POST':
        resultats = recherche_avancee(
            auteur       = request.form.get('auteur'),
            institution  = request.form.get('institution'),
            typologie    = request.form.get('typologie'),
            langue       = request.form.get('langue'),
            date_min     = request.form.get('date_min'),
            date_max     = request.form.get('date_max'),
            sujet_rameau = request.form.get('sujet_rameau'),
        )

        if resultats:
            app.logger.info(f'{resultats[0]}')
            for res in resultats[:50]:  # ← limite à 50 entrées max en historique
                historique_entry = Historique(
                id_user             = str(current_user.id),
                nom_user            = current_user.name,
                result_author       = f"{res.get('auteur_nom', '')} {res.get('auteur_prenom', '')}".strip()[:100] or '',
                result_title        = (res.get('titre') or '')[:200],        # ← tronqué à 200
                result_institution  = (res.get('institution') or '')[:100],  # ← tronqué à 100
                result_date_min     = res.get('date_publication') or '',
                result_typologie    = (res.get('typologie') or '')[:100],
                result_langue       = (res.get('langue') or '')[:100],
                result_sujet_rameau = (res.get('sujet_rameau') or '')[:100],
                timestamp           = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                )
                db.session.add(historique_entry)
                db.session.commit()

    return render_template(
        'pages/recherche_avancee.html',
        options=options,
        resultats=resultats
    )
    
@app.context_processor
def inject_recherche():
    ROUTES_AVEC_OPTIONS = ('home', 'e_recherche_avancee')
    if request.endpoint in ROUTES_AVEC_OPTIONS:
        try:
            return dict(options=get_options_filtres(), resultats=None)
        except Exception:
            return dict(options={}, resultats=None)
    return {}

@app.route('/historique', methods=['GET'])
@login_required
def historique():
    """
    Route Flask affichant l'historique des recherches de l'utilisateur connecté.

    Comportements :
        - Interroge la table Historique en filtrant sur l'id de l'utilisateur courant
        - Trie les entrées par id décroissant (résultats les plus récents en premier)
        - Sérialise l'ensemble des entrées en liste de dicts via to_dict()
        - Passe les données sous deux formes au template : objets ORM et JSON

        - render_template('pages/historique.html') avec :
            - historique      : liste d'objets Historique (accès aux attributs ORM dans le template)
            - historique_json : liste de dicts sérialisés (prête pour un usage JS/JSON dans le template)

    Dépendances :
        - flask_login : login_required, current_user
        - models      : Historique (SQLAlchemy ORM)
    """    
    historique = Historique.query.filter_by(
        id_user=str(current_user.id)
    ).order_by(Historique.id.desc()).all() 
        
    historique_json = [entree.to_dict() for entree in historique]

    return render_template(
        'pages/historique.html',
        historique=historique,
        historique_json=historique_json
    )

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Route Flask gérant la déconnexion de l'utilisateur courant.

    Comportements :
        - Vérifie que l'utilisateur est bien authentifié avant d'agir
        - Appelle logout_user() pour invalider la session Flask-Login
        - Envoie un message flash de confirmation à l'utilisateur
        - Redirige vers la page d'accueil après déconnexion

    Retourne :
        - redirect(url_for("home")) : redirection vers la route 'home'

    Dépendances :
        - Flask       : redirect, url_for, flash
        - flask_login : current_user, logout_user
    """    
    if current_user.is_authenticated is True:
        logout_user()
    flash('Vous êtes déconnecté', 'info')
    return redirect(url_for("home"))    