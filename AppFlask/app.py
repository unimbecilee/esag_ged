from AppFlask.routes.auth_routes import auth_bp
from AppFlask.routes.document_routes import document_bp
from AppFlask.routes.organization_routes import organization_bp
from AppFlask.routes.trash_routes import trash_bp
from AppFlask.routes.history_routes import history_bp

def create_app():
    app = Flask(__name__)
    # ... existing configuration code ...

    app.register_blueprint(auth_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(organization_bp)
    app.register_blueprint(trash_bp)
    app.register_blueprint(history_bp)

    # ... rest of the code ... 