from AppFlask import create_app
from AppFlask.routes import (
    auth_routes,
    document_routes,
    scan_routes,
    search_routes,
    trash_routes,
    dashboard_routes,
    workflow_routes,
    organization_routes
)



app = create_app()

app.config['UPLOAD_FOLDER'] = "uploads/"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
