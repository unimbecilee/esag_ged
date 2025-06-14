from flask import Flask, request, jsonify, send_from_directory, current_app
from flask_cors import CORS
from AppFlask.routes.auth_routes import auth_bp
from AppFlask.routes.organization_routes import organization_bp
from AppFlask.routes.trash_routes import trash_bp
from AppFlask.routes.history_routes import history_bp
from AppFlask.routes.logs_routes import logs_bp
from AppFlask.routes.settings_routes import settings_bp
from AppFlask.routes.scan_routes import scan_bp
from AppFlask.routes.search_routes import search_bp
from AppFlask.routes.workflow_routes import workflow_bp
# Import des nouveaux blueprints pour les fonctionnalités avancées de gestion documentaire
from AppFlask.routes.document_version_routes import version_bp
from AppFlask.routes.document_comment_routes import comment_bp
from AppFlask.routes.document_subscription_routes import subscription_bp
from AppFlask.routes.document_checkout_routes import checkout_bp
from AppFlask.routes.folder_routes import folder_bp

from AppFlask.services.logging_service import logging_service
from AppFlask.services.maintenance_service import maintenance_service
import logging
import traceback
import atexit
import os

def create_app():
    app = Flask(__name__, static_folder='../frontend/dist', static_url_path='/')
    
    # Configuration de l'upload
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')
    
    # Créer le dossier d'upload s'il n'existe pas
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Middleware pour gérer les erreurs CORS manuellement et les requêtes OPTIONS
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Max-Age', '3600')
            return response

    # Configuration CORS simplifiée pour éviter les problèmes
    CORS(app, 
         origins="http://localhost:3000",
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # Configuration du logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Enregistrement des blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(organization_bp, url_prefix='/api')
    # app.register_blueprint(trash_bp, url_prefix='/api')  # DÉSACTIVÉ - remplacé par trash_unified_bp
    app.register_blueprint(history_bp, url_prefix='/api')
    app.register_blueprint(logs_bp, url_prefix='/api')
    app.register_blueprint(settings_bp, url_prefix='/api')
    app.register_blueprint(scan_bp, url_prefix='/api')
    app.register_blueprint(search_bp, url_prefix='/api')
    app.register_blueprint(workflow_bp, url_prefix='/api')
    
    # Enregistrer les nouveaux blueprints pour les fonctionnalités avancées
    app.register_blueprint(version_bp, url_prefix='/api')
    app.register_blueprint(comment_bp, url_prefix='/api')
    app.register_blueprint(subscription_bp, url_prefix='/api')
    app.register_blueprint(checkout_bp, url_prefix='/api')
    app.register_blueprint(folder_bp, url_prefix='/api')

    # BLUEPRINT DOCUMENTS UNIFIÉ - Remplace tous les anciens blueprints documents conflictuels
    from .api.documents_unified import bp as documents_unified_bp
    app.register_blueprint(documents_unified_bp, url_prefix='/api')

    # Démarrage du service de maintenance
    maintenance_service.start_cleanup_scheduler()
    
    # Enregistrement de l'arrêt du service à la fermeture de l'application
    atexit.register(maintenance_service.stop_cleanup_scheduler)
    
    # Middleware pour logger toutes les requêtes
    @app.before_request
    def log_request_info():
        # Ne pas logger les requêtes OPTIONS pour éviter le bruit
        if request.method != 'OPTIONS':
            logging_service.log_event(
                level='INFO',
                event_type='HTTP_REQUEST',
                message=f"Requête {request.method} vers {request.path}",
                additional_data={
                    'method': request.method,
                    'path': request.path,
                    'args': dict(request.args),
                    'headers': dict(request.headers)
                }
            )
    
    # Middleware pour gérer les erreurs CORS
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin', '')
        if origin == 'http://localhost:3000':
            response.headers.add('Access-Control-Allow-Origin', origin)
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
        
        # Pour les requêtes OPTIONS (preflight), renvoyer 200 OK
        if request.method == 'OPTIONS':
            response.status_code = 200
        
        return response
        
    # Gestion globale des erreurs
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Erreur non gérée: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': 'Une erreur est survenue',
            'error': str(e)
        }), 500

    # Route catch-all pour gérer toutes les requêtes OPTIONS non capturées par les blueprints
    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def api_options(path):
        """Gestionnaire pour toutes les requêtes OPTIONS vers /api/"""
        response = jsonify({'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

    return app