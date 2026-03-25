"""
Deux fonctions :

    get_options_filtres()
        Retourne les listes nécessaires pour peupler les recherches "contraintes". À appeler depuis la route qui sert la page.

    recherche_avancee(...)
        Exécute la requête filtrée après avoir cliqué sur un bouton "rechercher" et retourne une liste de publications. Tous les paramètres sont optionnels.
"""

from sqlalchemy import func, or_
from ..models.models import (
    DefPublication,
    DefAuteur,
    DefTableInstitution,
    DefLiaisonSujets,
)

"""
OPTIONS FILTRES
L'idée là c'est de requêter l'entiereté d'une colonne d'une table pour faire une liste de choix contraints
"""

# Pour plus de dynamisme on ne souhaiterait pas de valeurs codées en dur mais dans ce cas il y a très peu d'options
# Les typologies sont une liste finie mais les langues pourraient évoluer en remplissant à nouveau la base, on pourrait éventuellement les remettre dans une fonction mais à voir avec vous

TYPOLOGIES = ['mémoire', 'thèse', 'ouvrage', 'DPLG']
LANGUES    = ['Français', 'Anglais', 'Allemand', 'Portugais']


# Dynamiques

def get_options_filtres():
    """
    Retourne un dictionnaire contenant toutes les listes nécessaires au formulaire.

    dict avec les clés :
        typologies    : list[str] valeurs hardcodées
        langues       : list[str] valeurs hardcodées
        institutions  : list[str] triées alphabétiquement depuis la base
        sujets_rameau : list[str] triés alphabétiquement depuis la base
    """
    institutions = [
        row.nom
        for row in DefTableInstitution.query.order_by(DefTableInstitution.nom).all()
    ]

    sujets_rameau = [
        row.rameau
        for row in (
            DefLiaisonSujets.query
            .with_entities(DefLiaisonSujets.rameau)
            .filter(DefLiaisonSujets.rameau.isnot(None))
            .distinct()
            .order_by(DefLiaisonSujets.rameau)
            .all()
        )
    ]

    return {
        "typologies":    TYPOLOGIES,
        "langues":       LANGUES,
        "institutions":  institutions,
        "sujets_rameau": sujets_rameau,
    }


"""
FONTION DE LA RECHERCHE AVANCEE
Véritable recherche dans la base depuis l'appli
"""

def recherche_avancee(
    auteur=None,
    institution=None,
    typologie=None,
    langue=None,
    date_min=None,
    date_max=None,
    sujet_rameau=None,
):
    """
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
    """

    query = (
        DefPublication.query
        .outerjoin(DefAuteur, DefPublication.id_auteur == DefAuteur.id)
        .outerjoin(DefTableInstitution, DefPublication.id_institution == DefTableInstitution.id)
    )

    # Filtre auteur : correspondance stricte insensible à la casse
    
    if auteur and auteur.strip():
        termes = auteur.strip().split()
        conditions = [
            or_(
                DefAuteur.auteur_nom.ilike(f"%{terme}%"),
                DefAuteur.auteur_prenom.ilike(f"%{terme}%")
            )
            for terme in termes
        ]
        for condition in conditions:
            query = query.filter(condition)

    # Filtre institution : correspondance stricte insensible à la casse
    if institution and institution.strip():
        query = query.filter(
            DefTableInstitution.nom.ilike(institution.strip())
        )

    # Filtre typologie : comparaison exacte
    if typologie:
        query = query.filter(DefPublication.typologie == typologie)

    # Filtre langue : comparaison exacte
    if langue:
        query = query.filter(DefPublication.langue == langue)

    # Filtres dates : conversion année entière format base 'YYYY-01-01'
    if date_min:
        query = query.filter(
            DefPublication.date_publication >= f"{date_min}-01-01"
        )
    if date_max:
        query = query.filter(
            DefPublication.date_publication <= f"{date_max}-01-01"
        )

    # Filtre sujet rameau : sous-requête sur def_liaison_sujets. On passe par une sous-requête plutôt qu'une jointure directe pour éviter de multiplier les lignes quand une publication a plusieurs sujets associés.
    if sujet_rameau and sujet_rameau.strip():
        sous_requete = (
            DefLiaisonSujets.query
            .filter(DefLiaisonSujets.rameau == sujet_rameau.lower())
            .with_entities(DefLiaisonSujets.id_publication)
            .subquery()
        )
        query = query.filter(DefPublication.id.in_(sous_requete))

    publications = query.distinct().all()

    return [_serialise(pub) for pub in publications]


# Sérialisation

def _serialise(pub):
    # Convertit un objet DefPublication en dictionnaire.
    return {
        "id":               pub.id,
        "titre":            pub.titre,
        "auteur_nom":       pub.auteur.auteur_nom    if pub.auteur      else None,
        "auteur_prenom":    pub.auteur.auteur_prenom if pub.auteur      else None,
        "institution":      pub.institution.nom      if pub.institution else None,
        "typologie":        pub.typologie,
        "langue":           pub.langue,
        "date_publication": pub.date_publication,
    }