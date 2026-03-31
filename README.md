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
