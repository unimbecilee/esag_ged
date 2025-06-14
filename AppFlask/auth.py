from functools import wraps
from flask import request, jsonify, current_app
import jwt
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Récupérer le token depuis les headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Récupérer le token depuis les cookies si pas dans les headers
        if not token and request.cookies.get('auth_token'):
            token = request.cookies.get('auth_token')
            
        if not token:
            return jsonify({'message': 'Token d\'authentification manquant!'}), 401
        
        try:
            # Décoder le token
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data['user_id']
            
            # Récupérer l'utilisateur depuis la base de données
            conn = db_connection()
            if not conn:
                return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
                
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM utilisateur WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not user_data:
                return jsonify({'message': 'Utilisateur non trouvé!'}), 401
                
            # Créer un objet utilisateur pour passer à la fonction
            current_user = {
                'id': user_data['id'],
                'email': user_data['email'],
                'nom': user_data['nom'],
                'prenom': user_data['prenom'],
                'role': user_data.get('role', 'User'),
                'is_admin': user_data.get('role') == 'Admin'
            }
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré. Veuillez vous reconnecter!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide. Veuillez vous reconnecter!'}), 401
        
        # Passer l'utilisateur à la fonction décorée
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Récupérer le token depuis les headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Récupérer le token depuis les cookies si pas dans les headers
        if not token and request.cookies.get('auth_token'):
            token = request.cookies.get('auth_token')
            
        if not token:
            return jsonify({'message': 'Token d\'authentification manquant!'}), 401
        
        try:
            # Décoder le token
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data['user_id']
            
            # Récupérer l'utilisateur depuis la base de données
            conn = db_connection()
            if not conn:
                return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
                
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM utilisateur WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not user_data:
                return jsonify({'message': 'Utilisateur non trouvé!'}), 401
                
            # Vérifier si l'utilisateur est admin
            if user_data.get('role') != 'Admin':
                return jsonify({'message': 'Accès restreint aux administrateurs!'}), 403
                
            # Créer un objet utilisateur pour passer à la fonction
            current_user = {
                'id': user_data['id'],
                'email': user_data['email'],
                'nom': user_data['nom'],
                'prenom': user_data['prenom'],
                'role': user_data['role'],
                'is_admin': True
            }
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré. Veuillez vous reconnecter!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide. Veuillez vous reconnecter!'}), 401
        
        # Passer l'utilisateur à la fonction décorée
        return f(current_user, *args, **kwargs)
    
    return decorated

def get_current_user_from_token(token):
    """Récupérer l'utilisateur à partir d'un token"""
    if not token:
        return None
    
    try:
        # Décoder le token
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data['user_id']
        
        # Récupérer l'utilisateur depuis la base de données
        conn = db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM utilisateur WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_data:
            return None
            
        # Créer un objet utilisateur
        user = {
            'id': user_data['id'],
            'email': user_data['email'],
            'nom': user_data['nom'],
            'prenom': user_data['prenom'],
            'role': user_data.get('role', 'User'),
            'is_admin': user_data.get('role') == 'Admin'
        }
        
        return user
        
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None 