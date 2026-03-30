"""
Expose une fonction publique :

    barre_recherche_simple(recherche)
        Recherche plein texte sur les titres et les auteurs. Retourne une liste de dicts triée par pertinence, dans le même format que recherche_avancee() pour permettre un filtrage ultérieur avec filtrer().
"""

from sqlalchemy import func
from ..models.models import (
    DefPublication,
    DefAuteur,
    DefTableInstitution,
    Historique, 
)
from datetime import datetime
from flask_login import current_user
from ..app import db                            # ← ajout

def barre_recherche_simple(recherche):
    """
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
    """

    if not recherche or not recherche.strip():
        return []

    # Vecteur de recherche : concatène les différents champs sur lesquels on doit agir
    # coalesce remplace les None par '' pour éviter que la concaténation retourne None si l'un des champs est absent
    vecteur = func.to_tsvector(
        'french',
        func.coalesce(DefPublication.titre, '') + ' ' +
        func.coalesce(DefAuteur.auteur_nom, '') + ' ' +
        func.coalesce(DefAuteur.auteur_prenom, '')
    )

    # Requête de recherche
    # plainto_tsquery accepte du langage naturel sans syntaxe spéciale
    requete = func.plainto_tsquery('french', recherche.strip())

    # Score de pertinence ts_rank selon la fréquence et la position des termes
    score = func.ts_rank(vecteur, requete)

    query = (
        DefPublication.query
        .outerjoin(DefAuteur, DefPublication.id_auteur == DefAuteur.id)
        .outerjoin(DefTableInstitution, DefPublication.id_institution == DefTableInstitution.id)
        .filter(vecteur.op('@@')(requete))
        .order_by(score.desc())
    )

    publications = query.all()
    
    resultats    = [_serialise(pub) for pub in publications]
    
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

    return [_serialise(pub) for pub in publications]


# Sérialisation : rend un dictionnaire python qui peut être pris dans la recherche avancée

def _serialise(pub):
    """Convertit un objet DefPublication en dict plat."""
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