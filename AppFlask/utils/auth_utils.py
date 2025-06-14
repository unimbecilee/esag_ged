import jwt
from flask import request, jsonify, current_app
from functools import wraps
import os

def token_required(f):
    """Décorateur pour vérifier le token JWT dans les requêtes API"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                # Format: "Bearer <token>"
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Format du token invalide'}), 401
        
        if not token:
            return jsonify({'error': 'Token manquant'}), 401

        try:
            # Décoder le token
            secret_key = current_app.config.get('SECRET_KEY') or os.getenv('SECRET_KEY', 'fallback_secret_key')
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            current_user_data = {
                'user_id': data['user_id'],
                'email': data['email'],
                'role': data.get('role', 'user')
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token invalide'}), 401

        return f(current_user_data, *args, **kwargs)
    
    return decorated 