from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from AppFlask.db import db_connection
from AppFlask.api.auth import token_required
import logging

# Configuration du logging
logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)

# Gestionnaire pour les requêtes OPTIONS
@settings_bp.route('/settings/profile', methods=['OPTIONS'])
@settings_bp.route('/settings/password', methods=['OPTIONS'])
def handle_settings_options():
    return '', 200

@settings_bp.route('/settings/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                id, 
                nom, 
                prenom, 
                email, 
                role,
                TO_CHAR(date_creation AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as date_creation,
                TO_CHAR(derniere_connexion AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as derniere_connexion
            FROM utilisateur 
            WHERE id = %s
        """, (current_user['id'],))
        
        user_info = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_info:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
            
        return jsonify(user_info)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations utilisateur: {str(e)}")
        return jsonify({'message': 'Une erreur est survenue'}), 500

@settings_bp.route('/settings/password', methods=['PUT'])
@token_required
def update_password(current_user):
    try:
        data = request.get_json()
        ancien_mdp = data.get('ancien_mdp')
        nouveau_mdp = data.get('nouveau_mdp')
        confirmer_mdp = data.get('confirmer_mdp')
        
        # Vérification des champs
        if not all([ancien_mdp, nouveau_mdp, confirmer_mdp]):
            return jsonify({'message': 'Tous les champs sont requis'}), 400
            
        if nouveau_mdp != confirmer_mdp:
            return jsonify({'message': 'Les nouveaux mots de passe ne correspondent pas'}), 400
            
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Vérifier l'ancien mot de passe
        cursor.execute("SELECT mot_de_passe FROM utilisateur WHERE id = %s", (current_user['id'],))
        user = cursor.fetchone()
        
        if not check_password_hash(user['mot_de_passe'], ancien_mdp):
            cursor.close()
            conn.close()
            return jsonify({'message': 'Ancien mot de passe incorrect'}), 400
            
        # Mettre à jour le mot de passe
        nouveau_mdp_hash = generate_password_hash(nouveau_mdp)
        cursor.execute(
            "UPDATE utilisateur SET mot_de_passe = %s WHERE id = %s",
            (nouveau_mdp_hash, current_user['id'])
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Mot de passe modifié avec succès'})
            
    except Exception as e:
        logger.error(f"Erreur lors de la modification du mot de passe: {str(e)}")
        return jsonify({'message': 'Une erreur est survenue'}), 500 