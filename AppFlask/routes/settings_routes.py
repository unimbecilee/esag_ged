from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from AppFlask.db import db_connection
from AppFlask.api.auth import token_required
import logging
from psycopg2.extras import RealDictCursor

# Configuration du logging
logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__, url_prefix='/api')

# Gestionnaire pour les requêtes OPTIONS
@settings_bp.route('/users', methods=['OPTIONS'])
@settings_bp.route('/settings/profile', methods=['OPTIONS'])
@settings_bp.route('/settings/password', methods=['OPTIONS'])
@settings_bp.route('/settings', methods=['OPTIONS'])
def handle_settings_options():
    return '', 200

@settings_bp.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    try:
        # Vérifier si l'utilisateur est admin
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403

        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                id, 
                nom as username,
                prenom,
                email, 
                role,
                status,
                TO_CHAR(date_creation AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as date_creation
            FROM utilisateur 
            ORDER BY date_creation DESC
        """)
        
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(users)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des utilisateurs: {str(e)}")
        return jsonify({'message': 'Une erreur est survenue'}), 500

@settings_bp.route('/settings/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
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

@settings_bp.route('/api/auth/password', methods=['PUT'])
@token_required
def api_update_password(current_user):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Aucune donnée reçue'}), 400
            
        ancien_mdp = data.get('ancien_mdp')
        nouveau_mdp = data.get('nouveau_mdp')
        confirmer_mdp = data.get('confirmer_mdp')
        
        logger.info(f"Tentative de modification du mot de passe pour l'utilisateur {current_user.get('email')}")
        
        # Vérification des champs
        if not all([ancien_mdp, nouveau_mdp, confirmer_mdp]):
            return jsonify({'message': 'Tous les champs sont requis'}), 400
            
        if nouveau_mdp != confirmer_mdp:
            return jsonify({'message': 'Les nouveaux mots de passe ne correspondent pas'}), 400
            
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier l'ancien mot de passe
        cursor.execute("SELECT mot_de_passe FROM utilisateur WHERE id = %s", (current_user['id'],))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
            
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
        
        logger.info(f"Mot de passe modifié avec succès pour l'utilisateur {current_user.get('email')}")
        return jsonify({'message': 'Mot de passe modifié avec succès'})
            
    except Exception as e:
        logger.error(f"Erreur lors de la modification du mot de passe: {str(e)}")
        return jsonify({'message': 'Une erreur est survenue'}), 500

# Endpoint pour les paramètres généraux
@settings_bp.route('/settings', methods=['GET'])
@token_required
def get_settings(current_user):
    try:
        # Vérifier si une table de paramètres existe dans la base de données
        # Si non, retourner des paramètres par défaut
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si la table existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'parametres'
            );
        """)
        
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            # Créer la table si elle n'existe pas
            logger.info("Création de la table parametres")
            cursor.execute("""
                CREATE TABLE parametres (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES utilisateur(id),
                    email_notifications BOOLEAN DEFAULT true,
                    langue VARCHAR(10) DEFAULT 'fr',
                    theme VARCHAR(20) DEFAULT 'dark',
                    taille_max_fichier INTEGER DEFAULT 10,
                    retention_corbeille INTEGER DEFAULT 30,
                    format_date VARCHAR(20) DEFAULT 'DD/MM/YYYY',
                    fuseau_horaire VARCHAR(50) DEFAULT 'Europe/Paris',
                    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        
        # Vérifier si l'utilisateur a des paramètres
        cursor.execute("""
            SELECT * FROM parametres WHERE user_id = %s
        """, (current_user['id'],))
        
        settings = cursor.fetchone()
        
        if not settings:
            # Créer des paramètres par défaut pour l'utilisateur
            cursor.execute("""
                INSERT INTO parametres (user_id, email_notifications, langue, theme, 
                                      taille_max_fichier, retention_corbeille, format_date, fuseau_horaire)
                VALUES (%s, true, 'fr', 'dark', 10, 30, 'DD/MM/YYYY', 'Europe/Paris')
                RETURNING *;
            """, (current_user['id'],))
            conn.commit()
            settings = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Retourner les paramètres sans l'id et user_id
        settings_response = {
            'email_notifications': settings['email_notifications'],
            'langue': settings['langue'],
            'theme': settings['theme'],
            'taille_max_fichier': settings['taille_max_fichier'],
            'retention_corbeille': settings['retention_corbeille'],
            'format_date': settings['format_date'],
            'fuseau_horaire': settings['fuseau_horaire']
        }
        
        return jsonify(settings_response)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des paramètres: {str(e)}")
        return jsonify({
            'email_notifications': True,
            'langue': 'fr',
            'theme': 'dark',
            'taille_max_fichier': 10,
            'retention_corbeille': 30,
            'format_date': 'DD/MM/YYYY',
            'fuseau_horaire': 'Europe/Paris'
        })

@settings_bp.route('/settings', methods=['PUT'])
@token_required
def update_settings(current_user):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Aucune donnée reçue'}), 400
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'utilisateur a des paramètres
        cursor.execute("""
            SELECT * FROM parametres WHERE user_id = %s
        """, (current_user['id'],))
        
        settings_exist = cursor.fetchone()
        
        if settings_exist:
            # Mettre à jour les paramètres existants
            cursor.execute("""
                UPDATE parametres SET 
                    email_notifications = %s,
                    langue = %s,
                    theme = %s,
                    taille_max_fichier = %s,
                    retention_corbeille = %s,
                    format_date = %s,
                    fuseau_horaire = %s,
                    date_modification = CURRENT_TIMESTAMP
                WHERE user_id = %s
                RETURNING *;
            """, (
                data.get('email_notifications', True),
                data.get('langue', 'fr'),
                data.get('theme', 'dark'),
                data.get('taille_max_fichier', 10),
                data.get('retention_corbeille', 30),
                data.get('format_date', 'DD/MM/YYYY'),
                data.get('fuseau_horaire', 'Europe/Paris'),
                current_user['id']
            ))
        else:
            # Créer des paramètres pour l'utilisateur
            cursor.execute("""
                INSERT INTO parametres (user_id, email_notifications, langue, theme, 
                                      taille_max_fichier, retention_corbeille, format_date, fuseau_horaire)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *;
            """, (
                current_user['id'],
                data.get('email_notifications', True),
                data.get('langue', 'fr'),
                data.get('theme', 'dark'),
                data.get('taille_max_fichier', 10),
                data.get('retention_corbeille', 30),
                data.get('format_date', 'DD/MM/YYYY'),
                data.get('fuseau_horaire', 'Europe/Paris')
            ))
        
        conn.commit()
        updated_settings = cursor.fetchone()
        cursor.close()
        conn.close()
        
        # Retourner les paramètres mis à jour
        settings_response = {
            'email_notifications': updated_settings['email_notifications'],
            'langue': updated_settings['langue'],
            'theme': updated_settings['theme'],
            'taille_max_fichier': updated_settings['taille_max_fichier'],
            'retention_corbeille': updated_settings['retention_corbeille'],
            'format_date': updated_settings['format_date'],
            'fuseau_horaire': updated_settings['fuseau_horaire']
        }
        
        return jsonify(settings_response)
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des paramètres: {str(e)}")
        return jsonify({'message': 'Une erreur est survenue'}), 500