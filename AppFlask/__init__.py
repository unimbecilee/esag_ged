from flask import Flask, request
from flask_login import LoginManager
from flask_cors import CORS
from config import Config
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import cloudinary
import logging

# Chargement des variables d'environnement
load_dotenv()

# Importation des Blueprints
from AppFlask.routes.auth_routes import auth_bp, User
from AppFlask.routes.document_routes import document_bp
from AppFlask.routes.scan_routes import scan_bp
from AppFlask.api.search import search_bp
from AppFlask.routes.trash_routes import trash_bp
from AppFlask.routes.dashboard_routes import dashboard_bp
from AppFlask.routes.workflow_routes import workflow_bp
from AppFlask.routes.organization_routes import organization_bp
from AppFlask.routes.history_routes import history_bp
from AppFlask.routes.settings_routes import settings_bp
from AppFlask.db import db_connection
from AppFlask.api import api_bp
from AppFlask.api.auth import init_admin

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuration Cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dhzibf7tu'),
        api_key=os.getenv('CLOUDINARY_API_KEY', '129899192135474'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET', 'NzKdF2R_wCXwBuiz0cp3fvmE8y0')
    )

    # Configuration du logging
    logging.basicConfig(level=logging.INFO)

    # Configuration CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True
        }
    })

    # Initialisation du LoginManager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Création du dossier uploads s'il n'existe pas
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Enregistrement des Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(trash_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(organization_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

# 🔐 Fonction pour que Flask-Login retrouve un utilisateur
@login_manager.user_loader
def load_user(user_id):
    conn = db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, nom, prenom, email, role FROM Utilisateur WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return User(id=user['id'], nom=user['nom'], prenom=user['prenom'], email=user['email'], role=user['role'])
    return None
