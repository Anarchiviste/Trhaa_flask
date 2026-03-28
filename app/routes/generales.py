from ..app import app, db
from flask import render_template, jsonify, request
from ..models.models import User, DefTableInstitution, DefAuteur, DefPublication, DefLiaisonSujets, WikidataArchaeologicalSites, WikidataPersons, WikidataPlaces, WikidataConcepts, WikidataOrganizations, WikidataArtMovements, WikidataTimePeriods
import json
import os

@app.route('/')
def test():
    '''
    Test est une fonction de test de connection entre l'application, l'ORM et la base de donnée postgres.
     Il s'agit d'un simple SELECT * (query.all()) affiché au sein d'un htlm brut.
    '''
    donnees = []
    for institution in DefTableInstitution.query.all():
        donnees.append({
            "id": institution.id,
            "nom": institution.nom
        })
    return f'''
        <html>
            <body>
                <p>{donnees}</p>
            </body>
        </html>
        '''

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

# Chargement du dictionnaire de traduction des pays au démarrage de l'application. Afin de pouvoir envoyer les demandes à l'API GeoJson
liste_pays_traduits = os.path.join(os.path.dirname(__file__), '..', 'utils', 'pays_traduits.json')

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
    with open(os.path.join(os.path.dirname(__file__), '..', 'static', 'pays_traduits.json'),
              encoding='utf-8') as f:
        country_map = json.load(f)

    return render_template(
        "pages/carto.html", COUNTRY_MAP=country_map, PAYS_AVEC_PUBLICATIONS=pays_en_avec_publications
    )

# Compte le nombre de publication associées à un pays
@app.route('/c_publication_count')
def get_publications_count():
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

# Affiche la page de résultat avec les publications. 
@app.route('/resultat_pays/<country_name>')
def afficherpublications(country_name):
    # country_name est le nom anglais (GeoJSON) → convertir en noms français
    db_names = COUNTRY_MAP_INVERSE.get(COUNTRY_MAP.get(country_name, country_name), [country_name])

    publications = db.session.query(
        DefAuteur.auteur_nom,
        DefAuteur.auteur_prenom,
        DefPublication.titre,
        DefPublication.date_publication
    ).join(
        DefPublication, DefAuteur.id == DefPublication.id_auteur
    ).join(
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
    ).all()

    # Rend un template HTML avec les publications
    return render_template('pages/tableau_resultats.html', publications=publications, country=country_name)