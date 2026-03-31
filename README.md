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

| Variable | Description |
|---|---|
| `DEBUG` | Mode debug Flask (`True` / `False`) |
| `SQLALCHEMY_DATABASE_URI` | Chaîne de connexion PostgreSQL |
| `WTF_CSRF_ENABLE` | Activation de la protection CSRF |
| `SECRET_KEY` | Clé secrète pour le chiffrement des sessions |

L'utilisateur doit ensuite installer le fichier requirement.txt dans un environnement python virtuel

```
python3 -m venv flask
source flask/bin/activate
pip install -r requirement.txt
```

## Initialisation de l'application (app/app)

Au lancement de l'application, l'application execute automatiquement deux fonctions : 

### `password_initialisation()`

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

| Valeur | Signification |
|---|---|
| `'La colonne existe déjà'` | La colonne `password` était déjà présente |
| `'Colonne ajoutée'` | La colonne a été créée avec succès |
| `'Problème : <détail>'` | Une erreur s'est produite |

### `historique_initialisation()`

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

### `signin()`

Nous utilisons un FlaskForm AjoutUtilisateur pour créer un nouveau compte.

**Comportement :**
- Initialise le formulaire `AjoutUtilisateur`
- Valide les données soumises via `validate_on_submit()`
- Vérifie l'intégrité des champs reçus
- En cas de succès → redirige vers `login` avec un message flash
- En cas d'échec → réaffiche `sign-in.html` avec les erreurs

> Les mots de passe sont hachés avant d'être stockés en base. La validation est effectuée côté serveur.

**Dépendances :** Flask, Flask-Login, Flask-WTF, Flask-SQLAlchemy, `User.compte_utilisateur`

### `login()`

 Formulaire `LoginUtilisateur` (FlaskForm) pour authentifier un utilisateur existant.
 
**Comportement :**
- Si l'utilisateur est déjà authentifié → redirige immédiatement vers `home`
- Valide les identifiants (email / mot de passe) via `User.connexion`
- En cas de succès → redirige vers la page demandée initialement (`next`) ou vers `home`
- En cas d'échec → réaffiche `login.html` avec un message d'erreur
 
> `login_view` doit être configuré dans `app.py` via `login.login_view = 'login'` pour que `@login_required` redirige correctement. Le paramètre `next` est géré automatiquement par Flask-Login.
 
**Dépendances :** Flask, Flask-Login (`login_user`, `current_user`), Flask-WTF, Flask-SQLAlchemy, `User.connexion`

--
 
## Recherche documentaire
 
> Module : `app/utils`
 
L'application propose deux modes de recherche : une **recherche simple** plein texte et une **recherche avancée** multi-critères. Les deux fonctions retournent des résultats dans le même format de dictionnaire, ce qui permet d'appliquer un filtrage ultérieur avec `filtrer()`.
 
---
 
### `get_options_filtres()`
 
Retourne toutes les listes nécessaires à l'alimentation du formulaire de recherche avancée.
 
**Retourne :** `dict`
 
| Clé | Type | Source |
|---|---|---|
| `typologies` | `list[str]` | Valeurs codées en dur |
| `langues` | `list[str]` | Valeurs codées en dur |
| `institutions` | `list[str]` | Base de données, ordre alphabétique |
| `sujets_rameau` | `list[str]` | Base de données, ordre alphabétique |
 
---
 
### `recherche_avancee(**kwargs)`
 
Recherche avancée dans la base TRHAA. Tous les paramètres sont optionnels et indépendants ; les filtres actifs se combinent en `AND`.
 
**Paramètres :**
 
| Paramètre | Type | Description |
|---|---|---|
| `auteur` | `str \| None` | Correspondance insensible à la casse sur `DefAuteur.auteur_nom` |
| `institution` | `str \| None` | Valeur exacte issue de `get_options_filtres()` |
| `typologie` | `str \| None` | `'mémoire'`, `'thèse'`, `'ouvrage'` ou `'DPLG'` |
| `langue` | `str \| None` | `'Français'`, `'Anglais'`, `'Allemand'` ou `'Portugais'` |
| `date_min` | `int \| str \| None` | Année entière (ex. `2005`) — la fonction construit `YYYY-01-01` |
| `date_max` | `int \| str \| None` | Année entière (ex. `2015`) |
| `sujet_rameau` | `str \| None` | Valeur exacte issue de `get_options_filtres()` (stockée en minuscules) |
 
**Retourne :** `list[dict]` — chaque dict contient `id`, `titre`, `auteur_nom`, `auteur_prenom`, `institution`, `typologie`, `langue`, `date_publication`.
 
---
 
### `barre_recherche_simple(recherche)`
 
Recherche plein texte dans la base TRHAA, utilisant le **Full Text Search PostgreSQL** avec le dictionnaire `french` (gestion de la morphologie française : accents, pluriels, conjugaisons).
 
La recherche porte simultanément sur `DefPublication.titre`, `DefAuteur.auteur_nom` et `DefAuteur.auteur_prenom`. Les résultats sont triés par score de pertinence décroissant (`ts_rank`).
 
**Paramètre :**
 
| Paramètre | Type | Exemples |
|---|---|---|
| `recherche` | `str` | `"peinture flamande"`, `"Prunet"`, `"archéologie romaine Gaule"` |
 
**Retourne :** `list[dict]` dans le même format que `recherche_avancee()`. Retourne une liste vide si la recherche est vide ou ne produit aucun résultat.
 
**Historique :** après sérialisation des résultats, la fonction enregistre automatiquement jusqu'à 50 entrées dans la table `Historique` pour l'utilisateur connecté :
 
```python
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
```
 
> Le champ `result_sujet_rameau` est laissé vide car il n'existe pas dans les résultats de la recherche simple. Le `commit` est effectué une seule fois après la boucle.
 
---

## Historique de recherche
 
> Module : `app/generales`
 
### Enregistrement automatique
 
Toutes les fonctions de recherche (`recherche_avancee`, `barre_recherche_simple`) enregistrent leurs résultats dans la table `Historique` après chaque appel réussi, à condition que l'utilisateur soit authentifié. L'entrée contient l'identifiant et le nom de l'utilisateur ainsi qu'un horodatage.
 
### Route `historique` — Consulter son historique
 
Affiche l'historique des recherches de l'utilisateur connecté.
 
**Comportement :**
- Interroge la table `Historique` filtrée sur `current_user.id`
- Trie les entrées par `id` décroissant (résultats les plus récents en premier)
- Sérialise les entrées en liste de dicts via `to_dict()`
- Passe les données au template sous deux formes : objets ORM et JSON
 
**Variables de template :**
 
| Variable | Type | Usage |
|---|---|---|
| `historique` | `list[Historique]` | Accès aux attributs ORM dans Jinja2 |
| `historique_json` | `list[dict]` | Consommation JavaScript / export JSON |
 
**Dépendances :** `flask_login` (`login_required`, `current_user`), modèle `Historique`
 
---
 
## Export de l'historique
 
> Partiel : `partials/part_ui.html`
 
La classe `Historique` expose une méthode `to_dict()` utilisée par la route `historique` pour produire `historique_json`. Un script JavaScript intégré au template permet de télécharger l'historique complet au format JSON.
 
```html
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
    const a   = document.createElement('a');
    a.href     = url;
    a.download = 'historique_recherches.json';
    a.click();
    URL.revokeObjectURL(url);
  }
</script>
```
 
Le fichier téléchargé est nommé `historique_recherches.json` et contient l'ensemble des entrées de l'historique de l'utilisateur.

## Consultation des notices 

Il est possible de consulter les notices, grâce aux injections jinja et la route `/notice/<pub_id>` d'afficher la page html `p_notice` contenant toutes informations concernant la publications souhaitée.
La fonction `e_notice()` affiche la notice détaillée d'une publication identifiée par son ID. Elle interroge la base de données pour récupérer les informations détaillées d'une publication (titre, date, langue, typologie, liens, auteur, institution) via une requête SQL avec des jointures sur les tables `def_auteur` et `def_table_institution`. Si la publication n'est pas trouvée, une réponse 404 est retournée. Sinon, la notice est affichée via un template HTML dédié.

    Paramètres:
        pub_id (str): L'identifiant unique de la publication à afficher.

    Retourne:
        Response (flask.Response):
            - Si la publication est trouvée : rendu du template `p_notice.html` avec les données de la publication.
            - Si la publication est introuvable : une réponse HTTP 404 avec le message "Notice introuvable".
 
## Page de cartographie 

La page "cartographie" figure une carte leaflet. Lors du survol de la souris une infobulle s'affiche. Elle indique si le pays est représenté dans la base de données et si oui, dans combien de publications. Cliquer sur un pays mène à la page recherche_avancée et affiche les publications concernées. 

### Etape préalable à la création de la page

Afin de délimiter la frontière des pays de notre carte, nous utilisons un fichier GeoJson hébergé sur Github contenant les données géographiques des frontières. Or, le nom des pays de ce fichier sont en anglais mais les pays de notre base de données sont en français. Nous devons donc traduire le nom de ces pays en premier. C'est l'objectif du script trad_pays.py, composé de 3 fonctions. 

**francais_vers_anglais() :** Elle fait appelle à l'API Wikidata pour trouver la traduction en anglais des noms de pays en français.
    Cette fonction envoie une requête SPARQL à l'API Wikidata pour rechercher un pays dont le label correspond au nom fourni en français. Si le pays est trouvé, son label anglais est retourné. Sinon, une alternative sans contrainte de langue est tentée via la fonction `sparql_sans_resultat_fr`.

    Paramètres: country_name (str): Le nom d'un pays, typiquement en français, mais peut être dans n'importe quelle langue.

    Retourne: str | None: 
        - Le label en anglais du pays, si trouvé.
        - None si le pays n'est pas trouvé ou en cas d'erreur.

**sparql_sans_resultat_fr() :** Se met en marche si aucun nom n'a été trouvé en français. Fait la même chose que précédemment mais en cherchant le nom du pays dans toutes les langues. 
    Recherche le label anglais d'un pays sans contrainte de langue sur le label d'entrée.

    Cette fonction est utilisée comme solution de repli pour `francais_vers_anglais` lorsque la recherche initiale en français ne donne pas de résultat. Elle permet de contourner les cas où le nom du pays est déjà en anglais (ex: "France" en français et en anglais), ou lorsqu'il n'existe pas de label en français pour ce pays dans Wikidata. La requête SPARQL ne filtre pas par langue, ce qui élargit la recherche à toutes les langues. Le label anglais est toujours retourné si disponible.

    Paramètres:
        country_name (str): Le nom du pays à rechercher.

    Retourne: str | None:
        - Le label anglais du pays si trouvé.
        - None si le pays n'est pas trouvé ou en cas d'erreur.

**build_country_map() :** 
- Select distinct tous les noms de pays
- Les place dans une liste. 
- Crée un dictionnaire avec la traduction en anglais de ces pays
- Stocke le résultat dans un fichier Json **pays_traduits.json**, stockés dans les *statics*. 

    Paramètres:
        app: L'application Flask, pour gérer le contexte SQLAlchemy.
        db: L'objet base de données (SQLAlchemy) pour exécuter les requêtes.

    Retourne: dict: Un dictionnaire où les clés sont les noms de pays en français et les valeurs sont les noms de pays en anglais (ou le nom original en français si la traduction échoue).

### Fonctionnalités de la page

Le fichier Json issu de ce script est stocké dans les `statics` et appelé dans la route `p_carto` qui le transmet au fichier html `p_carto.html` afin qu'il soit utilisé dans le script javascript. Cette même route lance la page HTML. 
    
**p_carto :** Retourne une page HTML de cartographie des pays ayant au moins une publication.
- Cette fonction interroge la base de données pour récupérer tous les noms de pays distincts (en français) qui sont associés à au moins une publication via les tables `WikidataPlaces`, `WikidataOrganizations`, ou `WikidataArchaeologicalSites`. 
- Les noms sont traduits en anglais via un dictionnaire de traduction (`COUNTRY_MAP`)
- Le résultat est passé à un template HTML pour affichage cartographique. 
La fonction utilise des jointures avec la table `DefLiaisonSujets` pour filtrer les pays qui ont des publications associées. Le dictionnaire de traduction est chargé depuis un fichier JSON pour éviter de refaire les traductions à chaque appel.

    Retourne:
        render_template: Affiche la page `p_carto.html` avec les données nécessaires :
            - `COUNTRY_MAP` : Dictionnaire de traduction français → anglais. Fichier pays_traduits.json
            - `PAYS_AVEC_PUBLICATIONS` : Liste des noms de pays en anglais ayant au moins une publication.

Une fois arrivé sur la page, le survol de la souris affiche si le pays sélectionné apparait dans la base de données, et si oui, combien de fois. Cette action mobilise plusieurs fonctions javascript et deux routes : 
- **styleDefault()** affiche les couleurs de bases des pays en fonction de leur présence dans la base de données
- **styleHover()** fait changer la couleur des pays survolés. 
- **tooltip** créer l'infobulle et **buildTooltipHTML()** la remplie en fonction des informations de la base de données.
- **fetchPubCount()** récuppère le nombre de publications grâce à la route **c_publication_count()** : 
    - Cette fonction interroge la base de données pour compter le nombre de publications liées à un pays, en utilisant son nom en anglais. 
    - Le nom anglais est converti en noms français (stockés en base) via `COUNTRY_MAP_INVERSE`. 
    La requête SQL utilise des jointures avec les tables `WikidataPlaces`, `WikidataOrganizations`, et `WikidataArchaeologicalSites` pour couvrir tous les types d'entités géographiques associées aux publications.

    Paramètres:
        country (str, optionnel): Le nom du pays en anglais (ex: "France"). Si non fourni, retourne le compte total.

    Retourne:
        Response (flask.Response): Une réponse JSON contenant le nombre de publications associées : `{ "count": <int> }`.
- Tout cela est concrétisé par la fonction jv **onEachFeature()** qui prend en compte toutes les actions réalisables par pays. Elle détermine si il se passe quelque chose quand la souris arrive sur un pays et qu'elle en sort, soit l'affichage et la disparition de l'infobulle. Et enfin elle déterminer ce qu'il se passe quand on clique sur un pays. Cette action mobilise la route **e_recherche_avancee()**.

## Consultations de notice


