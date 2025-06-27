import os
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



app = create_app()

app.config['UPLOAD_FOLDER'] = "uploads/"

if __name__ == '__main__':
    # Configuration pour le déploiement
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
