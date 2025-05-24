from flask import jsonify, request
from AppFlask.api import api_bp
from AppFlask.db import db_connection
from .auth import token_required

@api_bp.route('/scan', methods=['POST'])
@token_required
def scan_document(current_user):
    # TODO: Implémenter la logique de scan
    return jsonify({'message': 'Fonctionnalité de scan à implémenter'})
 