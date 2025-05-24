from flask import jsonify, request
from AppFlask.api import api_bp
from AppFlask.db import db_connection
from werkzeug.security import check_password_hash, generate_password_hash
from psycopg2.extras import RealDictCursor
import jwt
from datetime import datetime, timedelta
from functools import wraps
import os
import string
import random
import logging
import traceback

# Clé secrète pour JWT
SECRET_KEY = os.getenv('SECRET_KEY', 'votre_cle_secrete_ici')
MODE = os.getenv('MODE', 'prod')

# Configuration de l'administrateur par défaut
DEFAULT_ADMIN_EMAIL = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@esag.com')
DEFAULT_ADMIN_NOM = os.getenv('DEFAULT_ADMIN_NOM', 'Admin')
DEFAULT_ADMIN_PRENOM = os.getenv('DEFAULT_ADMIN_PRENOM', 'ESAG')
DEFAULT_ADMIN_PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', None)  # Si None, un mot de passe sera généré


# Fonction d'initialisation de l'administrateur
# Commentée car l'administrateur existe déjà dans la base de données
# def init_admin():
#     """Vérifie si un administrateur existe déjà dans la base de données et en crée un si nécessaire."""
#     conn = db_connection()
#     if not conn:
#         logging.error("Erreur de connexion à la base de données lors de l'initialisation de l'administrateur")
#         return
#     
#     try:
#         cursor = conn.cursor(cursor_factory=RealDictCursor)
#         # Vérifier si un administrateur existe déjà
#         cursor.execute("SELECT COUNT(*) AS count FROM Utilisateur WHERE role = 'admin'")
#         admin_count_result = cursor.fetchone()
#         admin_count = admin_count_result['count'] if admin_count_result else 0
#         
#         if admin_count == 0:
#             # Aucun administrateur trouvé, on en crée un
#             password = DEFAULT_ADMIN_PASSWORD or generate_password()
#             hashed_password = generate_password_hash(password)
#             
#             cursor.execute("""
#                 INSERT INTO Utilisateur (email, nom, prenom, mot_de_passe, role)
#                 VALUES (%s, %s, %s, %s, 'Admin')
#                 RETURNING id
#             """, (DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_NOM, DEFAULT_ADMIN_PRENOM, hashed_password))
#             
#             admin_id_result = cursor.fetchone()
#             admin_id = admin_id_result['id'] if admin_id_result else None
#             conn.commit()
#             
#             logging.info(f"Administrateur par défaut créé avec l'ID {admin_id}")
#             if DEFAULT_ADMIN_PASSWORD is None:
#                 logging.info(f"Mot de passe généré pour l'administrateur: {password}")
#                 print(f"\n=== IMPORTANT ===\nAdministrateur par défaut créé:\nEmail: {DEFAULT_ADMIN_EMAIL}\nMot de passe: {password}\n================\n")
#         else:
#             logging.info("Un administrateur existe déjà dans la base de données")
#     
#     except Exception as e:
#         conn.rollback()
#         error_type = type(e).__name__
#         error_details = str(e)
#         detailed_error_message = f"Erreur lors de l'initialisation de l'administrateur: Type={error_type}, Details='{error_details}'"
#         logging.error(detailed_error_message)
#         # Log supplémentaire si le message d'erreur est littéralement "0"
#         if error_details == "0":
#             logging.warning("Le message d'erreur de l'exception est '0'. Vérifiez la cause sous-jacente.")
#         # Pour débogage, loggons également la trace de la pile
#         logging.exception("Trace complète de l'erreur d'initialisation de l'administrateur:")
#     finally:
#         cursor.close()
#         conn.close()

# Fonction vide pour remplacer init_admin
def init_admin():
    """Fonction vide pour compatibilité avec le code existant."""
    logging.info("Fonction init_admin désactivée car l'administrateur existe déjà.")
    pass

# Gestion des requêtes OPTIONS
@api_bp.route('/auth/create-admin', methods=['OPTIONS'])
def handle_create_admin_options():
    return '', 200

@api_bp.route('/users', methods=['OPTIONS'])
def handle_users_options():
    return '', 200

@api_bp.route('/auth/me', methods=['OPTIONS'])
def handle_auth_me_options():
    return '', 200

@api_bp.route('/auth/login', methods=['OPTIONS'])
def handle_auth_login_options():
    return '', 200

@api_bp.route('/auth/create-admin', methods=['POST'])
def create_admin_account():
    if MODE != 'dev':
        return jsonify({'message': 'Fonctionnalité désactivée en production'}), 403
    
    data = request.get_json()
    required_fields = ['email', 'nom', 'prenom']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Champs obligatoires manquants'}), 400

    conn = db_connection()
    if not conn:
        return jsonify({'message': 'Erreur de base de données'}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Utilisateur WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            return jsonify({'message': 'Email déjà utilisé'}), 400

        generated_password = generate_password()
        hashed_password = generate_password_hash(generated_password)

        cursor.execute("""
            INSERT INTO Utilisateur (email, nom, prenom, mot_de_passe, role)
            VALUES (%s, %s, %s, %s, 'Admin')
            RETURNING id
        """, (data['email'], data['nom'], data['prenom'], hashed_password))
        
        conn.commit()
        return jsonify({
            'message': 'Administrateur créé',
            'password': generated_password,
            'email': data['email']
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


def generate_password(length=12):
    """Génère un mot de passe aléatoire"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Si c'est une requête OPTIONS, on la laisse passer
        if request.method == 'OPTIONS':
            response = jsonify({'message': 'OK'})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response, 200

        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        try:
            token = token.split(' ')[1]  # Enlever 'Bearer '
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            conn = db_connection()
            if conn is None:
                return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT id, email, nom, prenom, mot_de_passe, role FROM Utilisateur WHERE id = %s", (data['user_id'],))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not current_user:
                return jsonify({'message': 'Utilisateur non trouvé'}), 401
            return f(current_user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        except Exception as e:
            return jsonify({'message': f'Erreur de validation du token: {str(e)}'}), 401
    return decorated

@api_bp.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    if current_user['role'].lower() != 'admin':
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    conn = db_connection()
    if conn is None:
        return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, nom, prenom, email, role, service, numero_tel, date_creation 
            FROM utilisateur 
            ORDER BY nom ASC
        """)
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convertir les dates en format ISO pour le frontend
        formatted_users = []
        for user in users:
            user_dict = dict(user)
            if user_dict.get('date_creation'):
                user_dict['date_creation'] = user_dict['date_creation'].isoformat()
            formatted_users.append(user_dict)
        
        return jsonify(formatted_users)
    except Exception as e:
        print(f"Erreur lors de la récupération des utilisateurs: {str(e)}")
        return jsonify({'message': f'Erreur lors de la récupération des utilisateurs: {str(e)}'}), 500

@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email et mot de passe requis'}), 400
    
    conn = db_connection()
    if conn is None:
        return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, email, nom, prenom, mot_de_passe, role FROM Utilisateur WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'message': 'Email ou mot de passe incorrect'}), 401

        print(f"Hash stocké: {user['mot_de_passe']}")
        print(f"Mot de passe tenté: {password}")
        print(f"Résultat vérification: {check_password_hash(user['mot_de_passe'], password)}")
        if check_password_hash(user['mot_de_passe'], password):
            token = jwt.encode({
                'user_id': user['id'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, SECRET_KEY)
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'nom': user['nom'],
                    'prenom': user['prenom'],
                    'email': user['email'],
                    'role': user['role']
                }
            })
        return jsonify({'message': 'Email ou mot de passe incorrect'}), 401
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api_bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({
        'id': current_user['id'],
        'nom': current_user['nom'],
        'prenom': current_user['prenom'],
        'email': current_user['email'],
        'role': current_user['role']
    })

@api_bp.route('/users', methods=['POST'])
@token_required
def create_user(current_user):
    print(f"Tentative de création d'utilisateur par {current_user['email']}")
    
    if current_user['role'].lower() != 'admin':
        print(f"Accès refusé pour {current_user['email']} - Rôle: {current_user['role']}")
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Aucune donnée reçue'}), 400
            
        print("Données reçues:", data)
        
        required_fields = ['email', 'nom', 'prenom', 'role']
        for field in required_fields:
            if not data.get(field):
                print(f"Champ manquant ou vide: {field}")
                return jsonify({'message': f'Le champ {field} est requis et ne peut pas être vide'}), 400
        
        conn = db_connection()
        if conn is None:
            print("Erreur de connexion à la base de données")
            return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor()
        
        # Vérifier si l'email existe déjà
        cursor.execute("SELECT id FROM utilisateur WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            print(f"Email déjà utilisé: {data['email']}")
            return jsonify({'message': 'Cet email est déjà utilisé'}), 400
        
        # Générer un mot de passe aléatoire
        generated_password = generate_password()
        hashed_password = generate_password_hash(generated_password)
        
        # Insérer le nouvel utilisateur
        try:
            # Mapper le rôle en français
            role_mapping = {
                'user': 'Utilisateur',
                'admin': 'Admin'
            }
            french_role = role_mapping.get(data['role'].lower(), 'Utilisateur')
            
            cursor.execute("""
            INSERT INTO utilisateur (
                email, nom, prenom, mot_de_passe, role, 
                service, numero_tel, organisation_id, date_creation
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, CURRENT_TIMESTAMP)
            RETURNING id, date_creation
            """, (
                data['email'],
                data['nom'],
                data['prenom'],
                hashed_password,
                french_role,
                data.get('categorie', ''),
                data.get('numero_tel', '')
            ))
            
            new_user = cursor.fetchone()
            conn.commit()
            
            print(f"Utilisateur créé avec succès: {data['email']}")
            return jsonify({
                'message': 'Utilisateur créé avec succès',
                'user_id': new_user['id'],
                'date_creation': new_user['date_creation'].isoformat() if new_user['date_creation'] else None,
                'password': generated_password
            }), 201
            
        except Exception as e:
            conn.rollback()
            print(f"Erreur SQL lors de la création de l'utilisateur: {str(e)}")
            return jsonify({'message': 'Erreur lors de la création de l\'utilisateur dans la base de données'}), 500
            
    except Exception as e:
        print(f"Erreur lors de la création de l'utilisateur: {str(e)}")
        return jsonify({'message': 'Une erreur est survenue lors de la création de l\'utilisateur'}), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    if current_user['role'].lower() != 'admin':
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    if current_user['id'] == user_id:
        return jsonify({'message': 'Vous ne pouvez pas supprimer votre propre compte'}), 400
    
    conn = db_connection()
    if conn is None:
        return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Vérifier si l'utilisateur existe
        cursor.execute("SELECT id FROM Utilisateur WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Supprimer l'utilisateur
        cursor.execute("DELETE FROM Utilisateur WHERE id = %s", (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Utilisateur supprimé avec succès'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    if current_user['role'].lower() != 'admin':
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Aucune donnée fournie'}), 400
    
    conn = db_connection()
    if conn is None:
        return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'utilisateur existe
        cursor.execute("SELECT * FROM Utilisateur WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        if 'email' in data and data['email'] != user['email']:
            cursor.execute("SELECT id FROM Utilisateur WHERE email = %s AND id != %s", (data['email'], user_id))
            if cursor.fetchone():
                return jsonify({'message': 'Cet email est déjà utilisé'}), 400
        
        # Préparer les champs à mettre à jour
        update_fields = []
        update_values = []
        
        if 'email' in data:
            update_fields.append("email = %s")
            update_values.append(data['email'])
        
        if 'nom' in data:
            update_fields.append("nom = %s")
            update_values.append(data['nom'])
        
        if 'prenom' in data:
            update_fields.append("prenom = %s")
            update_values.append(data['prenom'])
        
        if 'role' in data:
            update_fields.append("role = %s")
            update_values.append(data['role'])
        
        if 'password' in data:
            update_fields.append("mot_de_passe = %s")
            update_values.append(generate_password_hash(data['password']))
        
        if not update_fields:
            return jsonify({'message': 'Aucun champ à mettre à jour'}), 400
        
        # Ajouter l'ID de l'utilisateur à la fin des valeurs
        update_values.append(user_id)
        
        # Exécuter la mise à jour
        query = f"""
            UPDATE Utilisateur 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        cursor.execute(query, tuple(update_values))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Utilisateur mis à jour avec succès'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api_bp.route('/auth/password', methods=['PUT', 'OPTIONS'])
@token_required
def update_password(current_user):
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()
        ancien_mdp = data.get('ancien_mdp')
        nouveau_mdp = data.get('nouveau_mdp')
        
        if not all([ancien_mdp, nouveau_mdp]):
            return jsonify({'message': 'Tous les champs sont requis'}), 400
            
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