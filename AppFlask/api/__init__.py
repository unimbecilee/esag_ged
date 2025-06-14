from flask import Blueprint
from flask_cors import CORS

# Import existing blueprints
from .auth import bp as auth_bp
from .search import bp as search_bp
from .trash import bp as trash_bp
from .scan import bp as scan_bp

# Import new blueprints
from .document_version import bp as document_version_bp
from .document_checkout import bp as document_checkout_bp
from .document_comment import bp as document_comment_bp
from .document_subscription import bp as document_subscription_bp
from .document_tags import bp as document_tags_bp
from .document_operations import bp as document_operations_bp
from .document_processing import bp as document_processing_bp 