from ..app import db
from ..models.models import DefPublication, DefLiaisonSujets

# Constantes
TOP_N    = 10
ANNEE_MIN = 1990
ANNEE_MAX = 2024


def get_donnees_chronologie(ids_publications=None):
    """
    Construit les données pour le graphique chronologique des sujets Rameau.

    Paramètres :
    ids_publications : list | None
        - None  → corpus complet (aucune recherche effectuée)
        - list  → liste d'IDs issus de la recherche (peut être vide)

    Retourne:
    dict JSON-sérialisable :
        annees           list[int]         [1990, …, 2024]
        sujets           dict[str, list]   {sujet: [count_1990, …, count_2024]}
        nb_sujets_total  int               nombre de sujets distincts avant plafonnement
        top_n_applique   bool              True si limité à TOP_N
        nb_resultats     int               publications uniques dans la plage 1990-2024
        aucun_resultat   bool              True si 0 résultat ou liste vide
    """
    annees    = list(range(ANNEE_MIN, ANNEE_MAX + 1))
    nb_annees = len(annees)

    # Cas de liste vide
    if ids_publications is not None and len(ids_publications) == 0:
        return _vide(annees)

    # Requête principale
    query = (
        db.session.query(
            DefPublication.id,
            DefPublication.date_publication,
            DefLiaisonSujets.rameau,
        )
        .join(DefLiaisonSujets, DefPublication.id == DefLiaisonSujets.id_publication)
        .filter(
            DefLiaisonSujets.rameau.isnot(None),
            DefLiaisonSujets.rameau != '',
        )
    )

    if ids_publications is not None:
        query = query.filter(DefPublication.id.in_(ids_publications))

    rows = query.all()

    # Comptage en Python
    comptages      = {}   # {(annee, sujet): count}
    ids_dans_plage = set()

    for id_pub, date_pub, rameau in rows:
        if not date_pub:
            continue
        try:
            annee = int(str(date_pub).strip()[:4])
        except (ValueError, TypeError):
            continue
        if not (ANNEE_MIN <= annee <= ANNEE_MAX):
            continue
        ids_dans_plage.add(id_pub)
        key = (annee, rameau)
        comptages[key] = comptages.get(key, 0) + 1

    if not comptages:
        return _vide(annees)

    # Totaux par sujet 
    totaux = {}
    for (_, sujet), count in comptages.items():
        totaux[sujet] = totaux.get(sujet, 0) + count

    nb_sujets_total = len(totaux)
    top_n_applique  = nb_sujets_total > TOP_N

    # Top n sujets afin d'avoir une visualisation
    sujets_tries  = sorted(totaux.items(), key=lambda x: x[1], reverse=True)
    top_sujets    = {s for s, _ in sujets_tries[:TOP_N]}

    # Initialisation des séries
    sujets_data = {s: [0] * nb_annees for s in top_sujets}
    if top_n_applique:
        sujets_data['Autres'] = [0] * nb_annees

    # Remplissage
    for (annee, sujet), count in comptages.items():
        idx = annee - ANNEE_MIN
        if sujet in top_sujets:
            sujets_data[sujet][idx] += count
        elif top_n_applique:
            sujets_data['Autres'][idx] += count

    # Tri final
    sujets_ordonnes = sorted(
        [(s, sujets_data[s]) for s in top_sujets],
        key=lambda x: totaux.get(x[0], 0),
        reverse=True,
    )
    if top_n_applique:
        sujets_ordonnes.append(('Autres', sujets_data['Autres']))

    return {
        "annees":          annees,
        "sujets":          {s: counts for s, counts in sujets_ordonnes},
        "nb_sujets_total": nb_sujets_total,
        "top_n_applique":  top_n_applique,
        "nb_resultats":    len(ids_dans_plage),
        "aucun_resultat":  False,
    }


# Helpers privés pour les données vides

def _vide(annees):
    return {
        "annees":          annees,
        "sujets":          {},
        "nb_sujets_total": 0,
        "top_n_applique":  False,
        "nb_resultats":    0,
        "aucun_resultat":  True,
    }
