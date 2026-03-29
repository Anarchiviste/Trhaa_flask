from ..app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user


# ----------------------------------------------------------------
# MODÈLE USER
# ----------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return f'<User {self.name}>'
    
    @staticmethod
    def compte_utilisateur(nom, email, password):
        """
        Valide et crée un nouveau compte utilisateur en base de données.

        Comportements :
        - Valide la présence et la longueur minimale (6 car.) des trois champs
        - Vérifie l'unicité du nom et de l'email dans la table User (OR logique)
        - Hache le mot de passe avant persistance via generate_password_hash
        - Retourne les erreurs accumulées sans interrompre à la première rencontrée
        - Encapsule le commit dans un try/except pour capturer les erreurs base

        Retourne :
        - (False, list[str]) : en cas d'erreur de validation ou d'exception base
        - (True,  User)      : en cas de création réussie, avec l'objet User créé

        Dépendances :
        - models          : User, db.session, db.or_
        - werkzeug.security : generate_password_hash
        """        
        erreurs=[]
        if not nom:
            erreurs.append('Un pseudonyme est nécessaire')
        if not email:
            erreurs.append('Un mail est nécessaire')
        if not password or len(password) < 6:
            erreurs.append('Le mot de passe est trop court')

        unique = User.query.filter(
            db.or_(User.name == nom, User.email == email)
        ).count()

        if unique > 0:
            erreurs.append('Le nom existe déjà')

        if len(erreurs) > 0:
            return False, erreurs

        utilisateur = User(
            name=nom,      
            email=email,
            password=generate_password_hash(password)
            )

        try:
            db.session.add(utilisateur)
            db.session.commit()
            return True, utilisateur

        except Exception as erreur:
            return False, [str(erreur)]

    def get_id(self):
        return str(self.id)

    @login.user_loader
    def get_user_by_id(id):
        """
        Callback Flask-Login reconstituant un utilisateur depuis son id de session.

        Comportements :
        - Enregistré auprès de l'instance LoginManager via @login.user_loader
        - Convertit l'id (str) en entier avant la requête
        - Retourne None implicitement si aucun utilisateur n'est trouvé (comportement Query.get)

        Retourne :
        - User | None : l'objet User correspondant, ou None si introuvable

        Dépendances :
        - flask_login : LoginManager (login)
        - models      : User
        """
        return User.query.get(int(id))

    
    @staticmethod
    def connexion(email, password):
        try:
            utilisateur = User.query.filter_by(email=email).first()
            if not utilisateur:
                return False, "Email introuvable"
            if not check_password_hash(utilisateur.password, password):
                return False, "Mot de passe incorrect"
            login_user(utilisateur)                # ← établit la session Flask-Login
            return True, utilisateur
        except Exception as e:
            return False, f"Erreur interne: {str(e)}"
        
class Historique(db.Model):
    __tablename__ = 'historique'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_user = db.Column(db.String(100), nullable=False)
    nom_user = db.Column(db.String(100), nullable=False)  
    result_author = db.Column(db.String(100), nullable=False)
    result_title = db.Column(db.String(200), nullable=False)
    result_institution = db.Column(db.String(100), nullable=False)
    result_date_min = db.Column(db.String(100), nullable=False)
    result_typologie = db.Column(db.String(100), nullable=False)
    result_langue = db.Column(db.String(100), nullable=False)
    result_sujet_rameau = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.String(100), nullable=False)
    
    def to_dict(self):
        return {
            "auteur":        self.result_author,
            "titre":         self.result_title,
            "institution":   self.result_institution,
            "langue":        self.result_langue,
            "sujet_rameau":  self.result_sujet_rameau,
            "date_min":      self.result_date_min,
            "typologie":      self.result_typologie,
            "date":          self.timestamp,
        }        

# ----------------------------------------------------------------
# def_table_institution
# ----------------------------------------------------------------
class DefTableInstitution(db.Model):
    __tablename__ = 'def_table_institution'

    id  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.Text, nullable=False)

    # Relations inverses
    publications = db.relationship('DefPublication', backref='institution', lazy=True)

    def __repr__(self):
        return f'<def_table_institution {self.nom}>'


# ----------------------------------------------------------------
# def_auteur
# ----------------------------------------------------------------
class DefAuteur(db.Model):
    __tablename__ = 'def_auteur'

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    auteur_nom    = db.Column(db.String)
    auteur_prenom = db.Column(db.String)

    # Relations inverses
    publications = db.relationship('DefPublication', backref='auteur', lazy=True)

    def __repr__(self):
        return f'<def_auteur {self.auteur_nom} {self.auteur_prenom}>'


# ----------------------------------------------------------------
# def_publication
# ----------------------------------------------------------------
class DefPublication(db.Model):
    __tablename__ = 'def_publication'

    id              = db.Column(db.String, primary_key=True)   # PK varchar dans le dump
    typologie       = db.Column(db.String)
    statut          = db.Column(db.String)
    linkagorha      = db.Column(db.String)                     # corrigé : linkagorha (pas linkaghora)
    linkpublication = db.Column(db.String)
    langue          = db.Column(db.String)
    date_publication = db.Column(db.Text)
    titre           = db.Column(db.Text)

    # Clés étrangères
    id_institution  = db.Column(db.Integer, db.ForeignKey('def_table_institution.id'))
    id_auteur       = db.Column(db.Integer, db.ForeignKey('def_auteur.id'))

    # Relations inverses
    liaisons_sujets = db.relationship('DefLiaisonSujets', backref='publication', lazy=True)

    def __repr__(self):
        return f'<def_publication {self.id} — {self.titre}>'


# ----------------------------------------------------------------
# def_liaison_sujets  (table pivot centrale)
# ----------------------------------------------------------------
class DefLiaisonSujets(db.Model):
    __tablename__ = 'def_liaison_sujets'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    qid            = db.Column(db.String)
    labelfr        = db.Column(db.String)
    rameau         = db.Column(db.String)
    qid_non_matche = db.Column(db.String)

    # Clés étrangères
    id_publication           = db.Column(db.String,  db.ForeignKey('def_publication.id'))
    qid_archaeological_sites = db.Column(db.String,  db.ForeignKey('wikidata_archaeological_sites.qid'))
    qid_persons              = db.Column(db.String,  db.ForeignKey('wikidata_persons.qid'))
    qid_places               = db.Column(db.String,  db.ForeignKey('wikidata_places.qid'))
    qid_concepts             = db.Column(db.String,  db.ForeignKey('wikidata_concepts.qid'))
    qid_organizations        = db.Column(db.String,  db.ForeignKey('wikidata_organizations.qid'))
    qid_art_movements        = db.Column(db.String,  db.ForeignKey('wikidata_art_movements.qid'))
    qid_time_periods         = db.Column(db.String,  db.ForeignKey('wikidata_time_periods.qid'))

    def __repr__(self):
        return f'<def_liaison_sujets {self.id} — {self.labelfr}>'


# ----------------------------------------------------------------
# Tables Wikidata
# ----------------------------------------------------------------

class WikidataArchaeologicalSites(db.Model):
    __tablename__ = 'wikidata_archaeological_sites'

    qid         = db.Column(db.String, primary_key=True)
    labelFr     = db.Column(db.String)
    labelEn     = db.Column(db.String)
    description = db.Column(db.String)
    country     = db.Column(db.String)
    coords      = db.Column(db.String)
    period      = db.Column(db.String)

    liaisons = db.relationship('DefLiaisonSujets',
                               foreign_keys='DefLiaisonSujets.qid_archaeological_sites',
                               backref='archaeological_site', lazy=True)

    def __repr__(self):
        return f'<wikidata_archaeological_sites {self.qid} — {self.labelFr}>'


class WikidataPersons(db.Model):
    __tablename__ = 'wikidata_persons'

    qid         = db.Column(db.String, primary_key=True)
    labelFr     = db.Column(db.String)
    labelEn     = db.Column(db.String)
    description = db.Column(db.String)
    birth       = db.Column(db.String)
    death       = db.Column(db.String)

    liaisons = db.relationship('DefLiaisonSujets',
                               foreign_keys='DefLiaisonSujets.qid_persons',
                               backref='person', lazy=True)

    def __repr__(self):
        return f'<wikidata_persons {self.qid} — {self.labelFr}>'


class WikidataPlaces(db.Model):
    __tablename__ = 'wikidata_places'

    qid         = db.Column(db.String, primary_key=True)
    labelFr     = db.Column(db.String)
    labelEn     = db.Column(db.String)
    description = db.Column(db.String)
    country     = db.Column(db.String)
    coords      = db.Column(db.String)

    liaisons = db.relationship('DefLiaisonSujets',
                               foreign_keys='DefLiaisonSujets.qid_places',
                               backref='place', lazy=True)

    def __repr__(self):
        return f'<wikidata_places {self.qid} — {self.labelFr}>'


class WikidataConcepts(db.Model):
    __tablename__ = 'wikidata_concepts'

    qid         = db.Column(db.String, primary_key=True)   # colonne "0" dans le dump => à renommer
    labelFr     = db.Column(db.String)
    labelEn     = db.Column(db.String)
    description = db.Column(db.String)

    liaisons = db.relationship('DefLiaisonSujets',
                               foreign_keys='DefLiaisonSujets.qid_concepts',
                               backref='concept', lazy=True)

    def __repr__(self):
        return f'<wikidata_concepts {self.qid} — {self.labelFr}>'


class WikidataOrganizations(db.Model):
    __tablename__ = 'wikidata_organizations'

    qid         = db.Column(db.String, primary_key=True)
    labelFr     = db.Column(db.String)
    labelEn     = db.Column(db.String)
    description = db.Column(db.String)
    type        = db.Column(db.String)
    country     = db.Column(db.String)

    liaisons = db.relationship('DefLiaisonSujets',
                               foreign_keys='DefLiaisonSujets.qid_organizations',
                               backref='organization', lazy=True)

    def __repr__(self):
        return f'<wikidata_organizations {self.qid} — {self.labelFr}>'


class WikidataArtMovements(db.Model):
    __tablename__ = 'wikidata_art_movements'

    qid         = db.Column(db.String, primary_key=True)   # colonne "0" dans le dump => à renommer
    labelFr     = db.Column(db.String)
    labelEn     = db.Column(db.String)
    description = db.Column(db.String)
    startDate   = db.Column(db.String)
    endDate     = db.Column(db.String)

    liaisons = db.relationship('DefLiaisonSujets',
                               foreign_keys='DefLiaisonSujets.qid_art_movements',
                               backref='art_movement', lazy=True)

    def __repr__(self):
        return f'<wikidata_art_movements {self.qid} — {self.labelFr}>'


class WikidataTimePeriods(db.Model):
    __tablename__ = 'wikidata_time_periods'

    qid         = db.Column(db.String, primary_key=True)   # colonne "0" dans le dump => à renommer
    labelFr     = db.Column(db.String)
    labelEn     = db.Column(db.String)
    description = db.Column(db.String)
    startTime   = db.Column(db.String)
    endTime     = db.Column(db.String)

    liaisons = db.relationship('DefLiaisonSujets',
                               foreign_keys='DefLiaisonSujets.qid_time_periods',
                               backref='time_period', lazy=True)

    def __repr__(self):
        return f'<wikidata_time_periods {self.qid} — {self.labelFr}>'
