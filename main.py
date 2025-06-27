import os
import logging
from AppFlask import create_app
from AppFlask.routes import (
    auth_routes,
    document_routes,
    scan_routes,
    search_routes,
    trash_routes,
    dashboard_routes,
    workflow_routes,
    organization_routes,
    api_routes
)

# Configuration du logging pour Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

app.config['UPLOAD_FOLDER'] = "uploads/"

# Route de health check pour Railway
@app.route('/')
def health_check():
    """Health check endpoint pour Railway"""
    return {'status': 'healthy', 'message': 'ESAG GED API is running'}, 200

@app.route('/health')
def health():
    """Alternative health check endpoint"""
    return {'status': 'healthy', 'service': 'ESAG GED'}, 200

if __name__ == '__main__':
    try:
        # Configuration pour le déploiement
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') != 'production'
        
        logger.info(f"Starting ESAG GED on port {port}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
        
        app.run(host='0.0.0.0', port=port, debug=debug)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
