from flask import Flask, request
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
from psycopg2.extras import RealDictCursor
import os

# Importation des Blueprints
from AppFlask.routes.auth_routes import auth_bp, User  # importer User ici
from AppFlask.routes.scan_routes import scan_bp
from AppFlask.routes.search_routes import search_bp
# from AppFlask.routes.trash_routes import trash_bp  # DÉSACTIVÉ - remplacé par trash_unified_bp
from AppFlask.routes.dashboard_routes import dashboard_bp
from AppFlask.routes.workflow_routes import workflow_bp, workflow_api_bp
from AppFlask.routes.organization_routes import organization_bp

from AppFlask.routes.folder_routes import folder_bp
from AppFlask.routes.history_routes import history_bp
from AppFlask.routes.settings_routes import settings_bp
from AppFlask.routes.api_routes import api_bp
from AppFlask.db import db_connection

# Import du blueprint unifié pour les documents
from AppFlask.api.documents_unified import bp as documents_unified_bp

# Import du blueprint unifié pour la corbeille
from AppFlask.api.trash_unified import bp as trash_unified_bp

from AppFlask.api import (
    auth_bp as api_auth_bp,
    search_bp as api_search_bp,
    # trash_bp as api_trash_bp,  # DÉSACTIVÉ - remplacé par trash_unified_bp
    scan_bp as api_scan_bp,
)
from AppFlask.api.workflow import bp as api_workflow_bp
from AppFlask.api.email import bp as api_email_bp
from AppFlask.api.notifications import bp as api_notifications_bp
from AppFlask.api.validation_workflow import bp as validation_workflow_bp
from AppFlask.api.auth import init_admin

# Import du service email
from AppFlask.services.email_service import email_service

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuration CORS
    CORS(app, 
         origins=[
            "http://localhost:3000",
            "https://esag-ged.vercel.app",
            "https://*.vercel.app"
         ],
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control", "X-File-Name"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    )

    # Gestion des requêtes OPTIONS (preflight)
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            origin = request.headers.get('Origin')
            if origin == 'http://localhost:3000':
                response = app.make_default_options_response()
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control, X-File-Name'
                response.headers['Access-Control-Max-Age'] = '86400'
                return response

    # Initialisation du LoginManager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Initialisation du service email
    email_service.init_app(app)

    # Création du dossier uploads s'il n'existe pas
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Enregistrement des Blueprints (SANS les anciens blueprints conflictuels)
    app.register_blueprint(auth_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(search_bp)
    # app.register_blueprint(trash_bp)  # DÉSACTIVÉ - remplacé par trash_unified_bp
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(workflow_api_bp)
    app.register_blueprint(organization_bp)
    app.register_blueprint(folder_bp, url_prefix='/api/folders')
    app.register_blueprint(history_bp, url_prefix='/api/history')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(api_bp)
    
    # Enregistrement des blueprints API
    app.register_blueprint(api_auth_bp, url_prefix='/api')
    app.register_blueprint(api_search_bp, url_prefix='/api')
    # app.register_blueprint(api_trash_bp, url_prefix='/api')  # DÉSACTIVÉ - remplacé par trash_unified_bp
    app.register_blueprint(api_scan_bp, url_prefix='/api')
    app.register_blueprint(api_workflow_bp)
    app.register_blueprint(api_email_bp, url_prefix='/api')
    app.register_blueprint(api_notifications_bp, url_prefix='/api')
    
    # ✅ BLUEPRINT VALIDATION WORKFLOW - Nouveau système de workflow de validation
    app.register_blueprint(validation_workflow_bp, url_prefix='/api')

    # ✅ BLUEPRINT DOCUMENTS UNIFIÉ - Remplace TOUS les anciens blueprints documents conflictuels
    app.register_blueprint(documents_unified_bp, url_prefix='/api')
    
    # ✅ BLUEPRINT CORBEILLE UNIFIÉ - Système de corbeille moderne (sans préfixe supplémentaire)
    app.register_blueprint(trash_unified_bp, url_prefix='/api')

    # Initialisation de l'administrateur par défaut
    # Commenté car l'administrateur existe déjà
    #init_admin()

    return app

@login_manager.user_loader
def load_user(user_id):
    # Implémentation spécifique pour charger l'utilisateur depuis PostgreSQL
    try:
        conn = db_connection()
        if conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM utilisateur WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if user_data:
                user = User(user_data['id'], user_data['nom'], user_data['prenom'], user_data['email'])
                user.role = user_data.get('role', 'User')
                return user
    except Exception as e:
        print(f"Erreur lors du chargement de l'utilisateur: {e}")
    
    return None
