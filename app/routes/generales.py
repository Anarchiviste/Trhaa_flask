from ..app import app, db
from flask import render_template, redirect, url_for, flash, request
from ..models.models import User, DefTableInstitution, DefAuteur, DefPublication, DefLiaisonSujets, WikidataArchaeologicalSites, WikidataPersons, WikidataPlaces, WikidataConcepts, WikidataOrganizations, WikidataArtMovements, WikidataTimePeriods
from sqlalchemy import text, inspect
from ..models.formulaires import AjoutUtilisateur

@app.route('/')
@app.route('/home')
def home():
    return render_template('pages/home.html')

@app.route('/login')
def login():
    return redirect(url_for('home'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = AjoutUtilisateur()

    if form.validate_on_submit():
        statut, donnees = User.compte_utilisateur(    
            nom=form.nom_utilisateur.data,            
            email=form.email_utilisateur.data,        
            password=form.password.data               
            )

        if statut is True:
            flash("Ajout effectué", "success")
            app.logger.info('signin success')

            return redirect(url_for('home'))

        else:
            flash(",".join(donnees), "error")
            app.logger.info('signin no success')
            return render_template('/pages/sign-in.html', form=form)
    
    else:
        app.logger.info('lancement de la page de sign-in')
        return render_template('pages/sign-in.html', form=form)

login.login_view = 'connexion'

