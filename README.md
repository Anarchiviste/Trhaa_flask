# Travaux de recherche en histoire de l'art et archéologie

## Installer l'application

Pour lancer l'application, il faut d'abord créer et compléter le .env.

```
cp .env.example .env
```
L'utilisateur doit compléter le lien de connexion à postgres et la clef secrète qui sert à chiffrer les mots de passe des utilisateurs.

```
# Format : postgresql://UTILISATEUR:MOT_DE_PASSE@HOTE:PORT/NOM_BASE

DEBUG=True
SQLALCHEMY_DATABASE_URI=postgresql://UTILISATEUR:MOT_DE_PASSE@HOTE:PORT/NOM_BASE
WTF_CSRF_ENABLE=True
SECRET_KEY=your_secret_key
```

## Initialisation de l'application (app/app)

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

## Créer un utilisateur (app/generales)

Plusieurs fonctionnalités de notre application demande la création d'un compte utilisateur. La création du compte passe par la route signin, et la connexion par la route login

_signin_

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

_login_

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

## Faire une recherche (app/utils)

Dans notre application nous avons deux types de recherches, la recherche simple et la recherche avancée. 

La route de recherche avancée utilise deux fonctions : 

_get_options_filtres_

    Retourne un dictionnaire contenant toutes les listes nécessaires au formulaire.

    dict avec les clés :
        typologies    : list[str] valeurs hardcodées
        langues       : list[str] valeurs hardcodées
        institutions  : list[str] triées alphabétiquement depuis la base
        sujets_rameau : list[str] triés alphabétiquement depuis la base

_recherche_avancee_

    Recherche avancée dans la base TRHAA.

    Tous les paramètres sont optionnels et indépendants. Les filtres actifs se combinent en AND.

    auteur : str | None
    Correspondance stricte insensible à la casse sur DefAuteur.auteur_nom. Exemple : 'dupont' matche 'Dupont'.

    institution : str | None
    Valeur exacte issue de la liste retournée par get_options_filtres(). Comparaison stricte insensible à la casse.

    typologie : str | None
    Une des quatre valeurs : 'mémoire', 'thèse', 'ouvrage', 'DPLG'. Comparaison exacte (les valeurs en base sont déjà propres).

    langue : str | None
    Une des quatre valeurs : 'Français', 'Anglais', 'Allemand', 'Portugais'. Comparaison exacte.

    date_min : int | str | None
    Année entière ex. 2005. La fonction construit 'YYYY-01-01'.

    date_max : int | str | None
    Année entière ex. 2015.

    sujet_rameau : str | None
    Valeur exacte issue de la liste retournée par get_options_filtres().Les valeurs en base sont toutes en minuscules.

    Retourne
    list[dict]
    Chaque dictionnaire contient :
    id, titre, auteur_nom, auteur_prenom,
    institution, typologie, langue, date_publication

_barre_recherche_simple_

    Recherche plein texte dans la base TRHAA.

    Utilise le Full Text Search PostgreSQL avec le dictionnaire 'french' qui gère la morphologie française (accents, pluriels, conjugaisons).

    La recherche porte simultanément sur :
        - DefPublication.titre
        - DefAuteur.auteur_nom
        - DefAuteur.auteur_prenom

    Les résultats sont triés par pertinence décroissante — les publications dont le texte correspond le mieux à la recherche apparaissent en premier.

    Paramètres
    recherche : str
    Texte libre saisi par l'utilisateur. Exemples :
        "peinture flamande"
        "Prunet"
        "archéologie romaine Gaule"

    Retourne
    list[dict]
    Chaque dict contient :
        id, titre, auteur_nom, auteur_prenom,
        institution, typologie, langue, date_publication
    Liste vide si la recherche est vide ou ne donne aucun résultat.

## Utiliser l'historique de recherche (app/generales)

Toutes les fonctions de recherche rendent une variable résultats suivit d'un commit permettant d'ajouter à la table de résultat nos recherches pour l'historique. L'historique enregistre l'utilisateur chercheur et une date.

    if resultats and current_user.is_authenticated:
        for res in resultats[:50]:
            db.session.add(Historique(
                id_user             = str(current_user.id),
                nom_user            = current_user.name,
                result_author       = f"{res.get('auteur_nom', '')} {res.get('auteur_prenom', '')}".strip()[:100] or '',
                result_title        = (res.get('titre') or '')[:200],
                result_institution  = (res.get('institution') or '')[:100],
                result_date_min     = res.get('date_publication') or '',
                result_typologie    = (res.get('typologie') or '')[:100],
                result_langue       = (res.get('langue') or '')[:100],
                result_sujet_rameau = '',
                timestamp           = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            ))
        db.session.commit()   

Pour accéder à l'historique, il suffit d'utiliser la route _historique_. La route historique ne rend que les informations liés à l'utilisateur connecté. 

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

## Télécharger ses résultats depuis son historique 

La classe Historique intègre une fonction _to_dict_ qui est donné à la route historique pour créer un paramètre historique_json qui est ensuite traité par un scripte javascript dans partials/part_ui.html et qui permet de générer et de télécharger un fichier json de l'historique de l'utililisateur.

```
<script id="historique-data" type="application/json">
  {{ historique_json | tojson }}
</script>

<script>
  const donneesHistorique = JSON.parse(
    document.getElementById('historique-data').textContent
  );

  function telechargerJSON() {
    const blob = new Blob([JSON.stringify(donneesHistorique, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'historique_recherches.json';
    a.click();
    URL.revokeObjectURL(url);
  }
</script>
```
