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
    Interroge Wikidata pour obtenir le label anglais d'un pays à partir d'un label en français. 

    Cette fonction envoie une requête SPARQL à l'API Wikidata pour rechercher un pays dont le label correspond
    au nom fourni en français. Si le pays est trouvé, son label anglais est retourné. Sinon, une alternative
    sans contrainte de langue est tentée via la fonction `sparql_sans_resultat_fr`.

    Paramètres: country_name (str): Le nom d'un pays, typiquement en français, mais peut être dans n'importe quelle langue.

    Retourne: str | None: 
        - Le label en anglais du pays, si trouvé.
        - None si le pays n'est pas trouvé ou en cas d'erreur.

    Exception: Une erreur est imprimée en cas d'échec de la requête SPARQL ou de traitement des résultats.

    Dépendances:
        - `requests`: Utilisé pour envoyer la requête HTTP à l'API SPARQL de Wikidata.
        - `sparql_sans_resultat_fr`: Fonction auxiliaire pour relancer une requête SPARQL sans contrainte de langue.
        - `WIKIDATA_SPARQL_URL`: URL de l'endpoint SPARQL de Wikidata (variable).
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
    Recherche le label anglais d'un pays sans contrainte de langue sur le label d'entrée.

    Cette fonction est utilisée comme solution de repli pour `francais_vers_anglais` lorsque la recherche
    initiale en français ne donne pas de résultat. Elle permet de contourner les cas où le nom du pays
    est déjà en anglais (ex: "France" en français et en anglais), ou lorsqu'il n'existe pas de label
    en français pour ce pays dans Wikidata.
    La requête SPARQL ne filtre pas par langue, ce qui élargit la recherche à toutes les langues.
    Le label anglais est toujours retourné si disponible.

    Paramètres:
        country_name (str): Le nom du pays à rechercher.

    Retourne: str | None:
        - Le label anglais du pays si trouvé.
        - None si le pays n'est pas trouvé ou en cas d'erreur.

    Exception: Une erreur est imprimée en cas d'échec de la requête SPARQL ou de traitement des résultats.

    Dépendances :
        - `requests`: Utilisé pour envoyer la requête HTTP à l'API SPARQL de Wikidata.
        - `WIKIDATA_SPARQL_URL`: URL de l'endpoint SPARQL de Wikidata (variable).

    Notes:
        - Cette fonction peut imprimer des messages de débogage pour indiquer qu'une recherche sans contrainte
          de langue est en cours.
        - Elle est conçue pour être appelée uniquement si la recherche initiale en français échoue.
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
    """
    Construit une carte (dictionnaire) de traduction des noms de pays du français vers l'anglais.
    Cette fonction extrait tous les noms de pays distincts depuis trois tables de la base de données
    (`WikidataPlaces`, `WikidataOrganizations`, `WikidataArchaeologicalSites`), puis utilise l'API
    Wikidata pour traduire chaque nom de pays du français vers l'anglais. Les résultats sont sauvegardés
    dans un fichier JSON pour éviter de refaire la traduction à chaque exécution.

    La fonction utilise `app.app_context()` pour gérer le contexte SQLAlchemy hors application Flask,
    et respecte les limites de l'API Wikidata avec un délai (`time.sleep(0.5)`) entre chaque requête.

    Paramètres:
        app: L'application Flask, pour gérer le contexte SQLAlchemy.
        db: L'objet base de données (SQLAlchemy) pour exécuter les requêtes.

    Retourne: dict: Un dictionnaire où les clés sont les noms de pays en français et les valeurs sont
    les noms de pays en anglais (ou le nom original en français si la traduction échoue).

    Dependencies:
        - `flask.Flask` ou équivalent : Pour gérer le contexte d'application.
        - `sqlalchemy`: Pour exécuter les requêtes SQL sur les tables de la base de données.
        - `json`: Pour sauvegarder les résultats dans un fichier JSON.
        - `os`: Pour construire le chemin du fichier de sortie.
        - `time`: Pour ajouter un délai entre les requêtes à l'API Wikidata.
        - `francais_vers_anglais`: Fonction utilitaire pour traduire les noms de pays.

    Notes:
        - Les tables interrogées sont `WikidataPlaces`, `WikidataOrganizations`, et `WikidataArchaeologicalSites`.
        - Les noms de pays sont dédupliqués avant traitement.
        - Les résultats sont sauvegardés dans `statics/pays_traduits.json` pour être réutilisés.
        - Un délai de 0.5 seconde est ajouté entre chaque requête à Wikidata pour éviter de dépasser les limites.
    """
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