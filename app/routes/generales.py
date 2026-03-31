from ..app import app, db
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from ..models.models import User, DefTableInstitution, DefAuteur, DefPublication, DefLiaisonSujets, WikidataArchaeologicalSites, WikidataPersons, WikidataPlaces, WikidataConcepts, WikidataOrganizations, WikidataArtMovements, WikidataTimePeriods, Historique
from sqlalchemy import text, inspect
from ..models.formulaires import AjoutUtilisateur, LoginUtilisateur
from ..utils.recherche_avancee import recherche_avancee, get_options_filtres
from flask_login import current_user, login_required, logout_user, login_user
from datetime import datetime
from ..utils.recherche_simple import barre_recherche_simple
from ..utils.chronologie import get_donnees_chronologie
import json
import os


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

        # Mémorisation des paramètres de recherche pour la chronologie
        session['recherche_params'] = {
            'q':           q,
            'auteur':      request.form.get('auteur', ''),
            'institution': request.form.get('institution', ''),
            'typologie':   request.form.get('typologie', ''),
            'langue':      request.form.get('langue', ''),
            'date_min':    request.form.get('date_min', ''),
            'date_max':    request.form.get('date_max', ''),
            'sujet_rameau':request.form.get('sujet_rameau', ''),
        }

    return render_template('pages/home.html', resultats=resultats, q=q)

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
    pays = request.args.get('pays', '')

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
    elif pays:
        # Arrivée depuis la carte : lancer la recherche directement
        resultats = recherche_avancee(pays=pays)

    return render_template(
        'pages/recherche_avancee.html',
        options=options,
        resultats=resultats,
        pays_selectionne=pays, 
    )
    
@app.context_processor
def inject_recherche():
    ROUTES_AVEC_OPTIONS = ('home')
    if request.endpoint in ROUTES_AVEC_OPTIONS:
        try:
            return dict(options=get_options_filtres(), resultats=None)
        except Exception:
            return dict(options={}, resultats=None)
    return {}

@app.route('/chronologie')
def chronologie():
    """
    Affiche la frise chronologique des sujets Rameau.

    Comportement :
        - Si une recherche a été effectuée sur /home, ses paramètres sont stockés
          en session (recherche_params). La route les rejoue pour obtenir les IDs
          filtrés, puis appelle get_donnees_chronologie() avec ces IDs.
        - Sans recherche préalable, affiche le corpus complet (ids=None).

    Retourne :
        render_template('pages/p_chronologie.html') avec les variables :
            donnees          dict  données brutes pour Chart.js (| tojson en template)
            est_filtre       bool  True si les données proviennent d'une recherche
            nb_resultats     int   publications uniques dans la plage 1990-2024
            nb_sujets_total  int   nombre de sujets distincts avant plafonnement
            top_n_applique   bool  True si limité au Top 10
            aucun_resultat   bool  True si aucune donnée disponible
    """
    params     = session.get('recherche_params')
    est_filtre = params is not None

    if params:
        ids_a_inclure = None
        if params.get('q'):
            resultats_simple = barre_recherche_simple(params['q'])
            ids_a_inclure    = [r['id'] for r in resultats_simple]

        resultats = recherche_avancee(
            auteur        = params.get('auteur')       or None,
            institution   = params.get('institution')  or None,
            typologie     = params.get('typologie')    or None,
            langue        = params.get('langue')       or None,
            date_min      = params.get('date_min')     or None,
            date_max      = params.get('date_max')     or None,
            sujet_rameau  = params.get('sujet_rameau') or None,
            ids_a_inclure = ids_a_inclure,
        )
        ids = [r['id'] for r in resultats] if resultats else []
    else:
        ids = None

    donnees = get_donnees_chronologie(ids)

    return render_template(
        'pages/p_chronologie.html',
        donnees         = donnees,
        est_filtre      = est_filtre,
        nb_resultats    = donnees['nb_resultats'],
        nb_sujets_total = donnees['nb_sujets_total'],
        top_n_applique  = donnees['top_n_applique'],
        aucun_resultat  = donnees['aucun_resultat'],
    )


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

@app.route('/p_tableau_resultats')
def p_tableau_resultats():
    resultats = db.session.query(
        DefAuteur.auteur_nom,
        DefAuteur.auteur_prenom,
        DefPublication.titre,
        DefPublication.date_publication
    ).join(DefPublication, DefAuteur.id == DefPublication.id_auteur).all()

    return render_template("pages/tableau_resultats.html", resultats=resultats)

# ---
# Page Cartographie 
# ---

# Lancer le script de traduction
from ..utils.trad_pays import build_country_map
@app.route('/trad')
def trad():
    """
    Retourne une carte des pays traduits via une requête HTTP GET.

    Cette fonction lance le script trad_pays.py et stocke le résultat
     de la fonction build_country_map dans country_map sous forme de réponse JSON.

    Returns: flask.Response:Une réponse JSON contenant la traduction des pays du 
    français à l'anglais.
        Format attendu : `{"pays": "traduction", ...}`.
    """
    country_map=build_country_map(app,db)
    return jsonify(country_map)

# Chargement du dictionnaire de traduction des pays au démarrage de l'application. Afin de pouvoir envoyer les demandes à l'API GeoJson
liste_pays_traduits = os.path.join(os.path.dirname(__file__), '..', 'statics', 'pays_traduits.json')

with open(liste_pays_traduits, encoding="utf-8") as f:
    # Lit et parse le contenu JSON du fichier
    COUNTRY_MAP = json.load(f)

# Dictionnaire inversé : {"Germany": ["Allemagne"], "Italy": ["Italie"], ...}
COUNTRY_MAP_INVERSE = {}
for db_name, en_name in COUNTRY_MAP.items():
    COUNTRY_MAP_INVERSE.setdefault(en_name, []).append(db_name)

# Affiche la page avec la carte. 
@app.route('/p_carto')
def p_carto():
    """
    Retourne une page HTML de cartographie des pays ayant au moins une publication.

    Cette fonction collecte les noms français des pays enregistrés dans les tables
    `WikidataPlaces`, `WikidataOrganizations` et `WikidataArchaeologicalSites` via des requêtes SQL,
    puis filtre et traduit ces noms en anglais pour identifier les pays éligibles.
    Enfin, elle rend un template Flask avec les données nécessaires à la visualisation cartographique.

    Processus :
    1. Interroge la base de données pour récupérer les pays distincts (avec `country` non null).
    2. Fusionne les résultats en un ensemble (`set`) pour éviter les doublons.
    3. Traduit les noms français en noms anglais via `COUNTRY_MAP`.
    NB : COUNTRY_MAP contient le json pays_traduits.json
    4. Charge le fichier JSON de traduction (`pays_traduits.json`) pour le rendre accessible dans le
    fichier HTML. 
    5. Rend le template `pages/p_carto.html` avec :
       - `COUNTRY_MAP` : Carte complète des traductions pays.
       - `PAYS_AVEC_PUBLICATIONS` : Liste des pays éligibles (en anglais).

    Returns: flask.Response: Page HTML rendue (`render_template`) avec les variables nécessaires à la cartographie.

    Dépendances :
        - Flask (app, render_template)
        - SQLAlchemy (db.session, query, join, filter, distinct)
        - Modules Python : os, json
        - Classes : WikidataPlaces, WikidataOrganizations, WikidataArchaeologicalSites, DefLiaisonSujets
        - Fichier statique : `statics/pays_traduits.json`

    Notes:
        - `COUNTRY_MAP` est un dictionnaire global de correspondance (ex: {"France": "France", ...}).
        - Le fichier `pays_traduits.json` est attendu dans le dossier `statics` du projet.
        - La liste `pays_en_avec_publications` est filtrée pour exclure les valeurs `None`.
    """
    # Collecte les noms français distincts des pays ayant ≥ 1 publication
    pays_places = db.session.query(WikidataPlaces.country).join(
        DefLiaisonSujets, DefLiaisonSujets.qid_places == WikidataPlaces.qid
    ).filter(WikidataPlaces.country.isnot(None)).distinct()

    pays_orgs = db.session.query(WikidataOrganizations.country).join(
        DefLiaisonSujets, DefLiaisonSujets.qid_organizations == WikidataOrganizations.qid
    ).filter(WikidataOrganizations.country.isnot(None)).distinct()

    pays_archeo = db.session.query(WikidataArchaeologicalSites.country).join(
        DefLiaisonSujets, DefLiaisonSujets.qid_archaeological_sites == WikidataArchaeologicalSites.qid
    ).filter(WikidataArchaeologicalSites.country.isnot(None)).distinct()

    # Union des trois sets
    pays_fr = set(
        [r[0] for r in pays_places] +
        [r[0] for r in pays_orgs] +
        [r[0] for r in pays_archeo]
    )
    # Traduit en noms anglais (clés du GeoJSON) via COUNTRY_MAP
    pays_en_avec_publications = list(filter(None, [
        COUNTRY_MAP.get(nom_fr) for nom_fr in pays_fr
    ]))
    with open(os.path.join(os.path.dirname(__file__), '..', 'statics', 'pays_traduits.json'),
              encoding='utf-8') as f:
        country_map = json.load(f)

    return render_template(
        "pages/p_carto.html", COUNTRY_MAP=country_map, PAYS_AVEC_PUBLICATIONS=pays_en_avec_publications
    )

# Compte le nombre de publication associées à un pays
@app.route('/c_publication_count')
def get_publications_count():
    """
    Retourne le nombre de publications associées à un pays donné, via une requête HTTP GET.

    Cette fonction prend en paramètre un nom de pays en anglais (format GeoJSON) et retourne
    le nombre total de publications liées à ce pays dans la base de données. Elle utilise des
    jointures externes (`isouter=True`) pour inclure les publications liées aux lieux, organisations
    ou sites archéologiques, même en l'absence de correspondance directe.

    Args:
        request.args.get('country', str):
            Nom du pays en anglais (ex: "France", "Germany"). Si non fourni, retourne le compte total.

    Processus :
    1. Convertit le nom anglais en noms français via `COUNTRY_MAP_INVERSE`.
    2. Exécute une requête SQL pour compter les publications associées aux pays correspondants.
    3. Utilise des jointures externes pour inclure toutes les tables liées (`WikidataPlaces`, etc.).
    4. Filtre les résultats pour ne garder que les publications liées aux pays ciblés.
    5. Retourne le compte sous forme de JSON.

    Returns:
        flask.Response:
            Réponse JSON contenant le nombre de publications :
            `{"count": <int>}`.

    Dépendances :
        - Flask (app, request)
        - SQLAlchemy (db.session, query, join, filter, count, isouter)
        - Modules Python : json
        - Classes : DefPublication, DefLiaisonSujets, WikidataPlaces, WikidataOrganizations, WikidataArchaeologicalSites
        - Constantes : COUNTRY_MAP_INVERSE

    Notes:
        - La conversion `COUNTRY_MAP_INVERSE` est utilisée pour retrouver les noms français en base.
        - Les jointures externes (`isouter=True`) garantissent que toutes les publications sont comptées,
          même sans correspondance directe dans les tables de lieux/organisations/sites.
        - La requête filtre les résultats avec un `OR` logique sur les trois tables.
    """
    country_en = request.args.get('country', '')

    # Convertit le nom anglais (GeoJSON) → noms français stockés en base
    db_names = COUNTRY_MAP_INVERSE.get(country_en, [country_en])

    count = db.session.query(DefPublication).join(
        DefLiaisonSujets, DefPublication.id == DefLiaisonSujets.id_publication
    ).join(
        WikidataPlaces,
        DefLiaisonSujets.qid_places == WikidataPlaces.qid,
        isouter=True
    ).join(
        WikidataOrganizations,
        DefLiaisonSujets.qid_organizations == WikidataOrganizations.qid,
        isouter=True
    ).join(
        WikidataArchaeologicalSites,
        DefLiaisonSujets.qid_archaeological_sites == WikidataArchaeologicalSites.qid,
        isouter=True
    ).filter(
        (WikidataPlaces.country.in_(db_names)) |
        (WikidataOrganizations.country.in_(db_names)) |
        (WikidataArchaeologicalSites.country.in_(db_names))
    ).count()

    return jsonify({'count': count})

# Page de notices 
@app.route('/notice/<pub_id>')
def e_notice(pub_id):
    """
    Affiche la notice détaillée d'une publication.
    Récupère les infos depuis def_publication, def_auteur et def_table_institution.
    """
    resultat = db.session.query(
        DefPublication.titre,
        DefPublication.date_publication,
        DefPublication.langue,
        DefPublication.typologie,
        DefPublication.linkagorha,
        DefPublication.linkpublication,
        DefAuteur.auteur_nom,
        DefAuteur.auteur_prenom,
        DefTableInstitution.nom.label('institution')
    ).outerjoin(DefAuteur, DefPublication.id_auteur == DefAuteur.id
    ).outerjoin(DefTableInstitution, DefPublication.id_institution == DefTableInstitution.id
    ).filter(DefPublication.id == pub_id
    ).first()

    if not resultat:
        return "Notice introuvable", 404

    return render_template('pages/p_notice.html', pub=resultat)