from ..app import db

class InstitutionDefinitive(db.Model):
    __tablename__ = 'def_table_institution'
    id = db.Column(db.String(100), primary_key=True)
    nom = db.Column(db.String(100))