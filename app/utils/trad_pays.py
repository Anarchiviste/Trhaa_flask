# build_country_map.py
import json
import time
import requests
from ..app import app, db
from ..models.models import WikidataPlaces, WikidataArchaeologicalSites, WikidataOrganizations
import os


WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

def francais_vers_anglais(country_name: str) -> str | None:
    """
    Interroge Wikidata pour trouver le label anglais d'un pays
    à partir d'un label dans n'importe quelle langue.
    """
    # Requête SPARQL : cherche une entité de type "pays" (Q6256) dont un label (toutes langues) correspond au nom fourni
    sparql_query = f"""
    SELECT ?country ?countryLabel WHERE {{
      ?country wdt:P31/wdt:P279* wd:Q6256 .
      ?country rdfs:label "{country_name}"@fr .   # essai en français d'abord
      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en" .
      }}
    }}
    LIMIT 1
    """

    # headers correspond aux métadonnées de l'envoie à l'API de Wikidata. C'est obligatoire
    headers = {"Accept": "application/json", # On précise que l'on veut notre réponse en Json
               "User-Agent": "Flask_traduction_français_anglais/1.0" # User-Agent nous identifie. Obligatoire aussi, fait partie de la politique de Wikidata de s'identifier.
               }

    try: # Traitement de la réponse
        # Envoie une requête Get à l'API SPARQL de Wikidata
        response = requests.get(WIKIDATA_SPARQL_URL, params={"query": sparql_query, "format": "json"}, headers=headers,timeout=10)
        data = response.json() # La réponse est en Json
        results = data["results"]["bindings"] # Extrait les résultats de la clé

        if results:
            return results[0]["countryLabel"]["value"] # Si il y a un résultat, retourner le premier

        # Si pas trouvé en @fr, on retente sans contrainte de langue
        return sparql_sans_resultat_fr(country_name)

    except Exception as e:
        print(f"Erreur Wikidata pour '{country_name}': {e}")
        return None

def sparql_sans_resultat_fr(country_name: str) -> str | None:
    """
    Recherche sans contrainte de langue — utile si le nom est déjà en anglais ou dans une autre langue.
    Cela parait contre-intuitif puisque nous savons que notre BDD est entièrement en français. Mais c'est surtout pour contrer des erreurs. 
    Par exemple, comme France, se dit aussi "France" en anglais, il ne trouvera pas de noms en français et s'arrêtera là.
    """
    print("Recherche d'un nom dans une autre langue que le français")
    sparql_query = f"""
    SELECT ?country ?countryLabel WHERE {{
      ?country wdt:P31/wdt:P279* wd:Q6256 .
      ?country rdfs:label "{country_name}" .
      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en" .
      }}
    }}
    LIMIT 1
    """
    headers = {"Accept": "application/json",
               "User-Agent": "Flask_traduction_français_anglais/1.0"}
    try:
        response = requests.get(
            WIKIDATA_SPARQL_URL,
            params={"query": sparql_query, "format": "json"},
            headers=headers,
            timeout=10
        )
        data = response.json()
        results = data["results"]["bindings"]
        return results[0]["countryLabel"]["value"] if results else None
    except Exception as e:
        print(f"Erreur Wikidata pour '{country_name}': {e}")
        return None

def build_country_map(app, db):
    with app.app_context(): # Nous devons utiliser "app_context" parce que nous utilisons SqlAlchemy dans ce script hors application. Ce n'est pas fait pour et il a besoin d'un contexte. C'est ce que fait app_context
        # Récupère tous les noms de pays. 
        rows_places = db.session.query(WikidataPlaces.country)\
                                .distinct()\
                                .filter(WikidataPlaces.country.isnot(None))\
                                .all()

        # Requête sur WikidataOrganizations
        rows_orgs = db.session.query(WikidataOrganizations.country)\
                              .distinct()\
                              .filter(WikidataOrganizations.country.isnot(None))\
                              .all()
        
        rows_archeological = db.session.query(WikidataArchaeologicalSites.country)\
                              .distinct()\
                              .filter(WikidataArchaeologicalSites.country.isnot(None))\
                              .all()

        # Prend le résultat des requêtes ci-dessus, les fusionne, supprime les doublons et les met dans une liste.
        country_names = list({r.country for r in rows_places} | {r.country for r in rows_orgs} | {r.country for r in rows_archeological})

        print(f"→ {len(country_names)} pays distincts trouvés en base\n")

        #Liste destinée à stocker les résultats de la traduction. 
        pays_traduits = {}

        # Appelle la fonction "francais_vers_anglais" pour chaque pays.
        for nom in country_names:
            print(f"  Recherche : '{nom}'")
            pays_anglais = francais_vers_anglais(nom)

            if pays_anglais: #Si le nom est trouvé.
                pays_traduits[nom] = pays_anglais #Il est ajouté au dictionnaire "pays_traduits"
                print({pays_anglais}) # Et imprimé
            else: # Si on ne trouve pas nom
                pays_traduits[nom] = nom # On garde le nom intacte.
                print("Nom non trouvé, conservé tel quel")

            time.sleep(0.5)  # Pour éviter de casser l'API. Obligatoire pour utiliser l'API de Wikidata. 

        # Sauvegarde dans un fichier JSON. Ainsi il le résultat est en cache et ça évite de recharger ce résultat à chaque fois (et croyez moi ça prend du temps.)
        output_path=os.path.join(os.path.dirname(__file__), "..", "statics", "pays_traduits.json") # Le fichier est sauvegardé dans le même dossier que le script. 
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(pays_traduits, f, ensure_ascii=False, indent=2) # On écrit le dictionnaire "fichiers_traduits" dans le fichier json. 

        print(f"\n✅ pays_traduits.json généré, contient ({len(pays_traduits)} entrées)")
        return pays_traduits

if __name__ == "__main__":
    build_country_map()