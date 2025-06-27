from flask import Blueprint, jsonify, request, current_app
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
import bcrypt
import traceback

def log_user_action(user_id, action_type, description, request_obj=None):
    """Enregistrer une action utilisateur dans l'historique"""
    try:
        conn = db_connection()
        if not conn:
            print("Erreur: Impossible de se connecter à la base de données pour log_user_action")
            return
            
        cursor = conn.cursor()
        
        # Enregistrer dans la table history seulement si user_id n'est pas None
        if user_id is not None:
            cursor.execute("""
                INSERT INTO history (action_type, entity_type, entity_id, entity_name, description, user_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (action_type, 'user', user_id, 'Action utilisateur', description, user_id))
        
        # Si request disponible, enregistrer aussi dans system_logs
        if request_obj:
            level = 'WARNING' if 'FAILED' in action_type else 'INFO'
            cursor.execute("""
                INSERT INTO system_logs (timestamp, level, event_type, user_id, ip_address, 
                                       request_path, request_method, message, additional_data)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
            """, (level, action_type, user_id, 
                  request_obj.remote_addr or '127.0.0.1',
                  request_obj.path, request_obj.method, description, '{}'))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Action enregistrée: {action_type} pour user_id={user_id}")
        
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'action: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals() and conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass

# Blueprint for auth endpoints
bp = Blueprint('api_auth', __name__)

# Clé secrète pour JWT
SECRET_KEY = current_app.config.get('SECRET_KEY') if current_app else os.getenv('SECRET_KEY', 'votre_cle_secrete_ici')
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
@bp.route('/auth/create-admin', methods=['OPTIONS'])
def handle_create_admin_options():
    return '', 200

@bp.route('/users', methods=['OPTIONS'])
def handle_users_options():
    return '', 200

@bp.route('/auth/me', methods=['OPTIONS'])
def handle_auth_me_options():
    return '', 200

@bp.route('/login', methods=['OPTIONS'])
def handle_auth_login_options():
    return '', 200

@bp.route('/folders', methods=['OPTIONS'])
def handle_folders_options():
    """Gère les requêtes OPTIONS pour les routes de dossiers"""
    response = jsonify({'message': 'OK'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response, 200

@bp.route('/auth/create-admin', methods=['POST'])
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
        cursor.execute("SELECT id FROM utilisateur WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            return jsonify({'message': 'Email déjà utilisé'}), 400

        generated_password = generate_password()
        hashed_password = generate_password_hash(generated_password)

        cursor.execute("""
            INSERT INTO utilisateur (email, nom, prenom, mot_de_passe, role)
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
            cursor.execute("SELECT id, email, nom, prenom, mot_de_passe, role FROM utilisateur WHERE id = %s", (data['user_id'],))
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

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
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
            cursor.execute("SELECT id, email, nom, prenom, mot_de_passe, role FROM utilisateur WHERE id = %s", (data['user_id'],))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not current_user:
                return jsonify({'message': 'Utilisateur non trouvé'}), 401
            
            if current_user['role'].lower() != 'admin':
                return jsonify({'message': 'Accès administrateur requis'}), 403
                
            return f(current_user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        except Exception as e:
            return jsonify({'message': f'Erreur de validation du token: {str(e)}'}), 401
    return decorated

@bp.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    print(f"Tentative de récupération des utilisateurs par {current_user['email']} (rôle: {current_user['role']})")
    
    if current_user['role'].lower() != 'admin':
        print(f"Accès refusé: {current_user['email']} n'est pas admin")
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    conn = db_connection()
    if conn is None:
        print("Erreur: Impossible de se connecter à la base de données")
        return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        print("Exécution de la requête SQL pour récupérer les utilisateurs")
        
        query = """
            SELECT id, nom, prenom, email, role, categorie, numero_tel, 
                   date_creation
            FROM utilisateur 
            ORDER BY nom ASC
        """
        
        print(f"Requête SQL: {query}")
        cursor.execute(query)
        users = cursor.fetchall()
        print(f"Nombre d'utilisateurs récupérés: {len(users)}")
        
        cursor.close()
        conn.close()
        
        # Convertir les dates en format ISO pour le frontend
        formatted_users = []
        for user in users:
            user_dict = dict(user)
            if user_dict.get('date_creation'):
                user_dict['date_creation'] = user_dict['date_creation'].isoformat() if hasattr(user_dict['date_creation'], 'isoformat') else str(user_dict['date_creation'])
            formatted_users.append(user_dict)
        
        print(f"Utilisateurs formatés: {formatted_users}")
        return jsonify(formatted_users)
    except Exception as e:
        print(f"Erreur lors de la récupération des utilisateurs: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Erreur lors de la récupération des utilisateurs: {str(e)}'}), 500

@bp.route('/login', methods=['POST'])
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
        cursor.execute("SELECT id, email, nom, prenom, mot_de_passe, role FROM utilisateur WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            # Enregistrer la tentative de connexion échouée pour email inexistant
            log_user_action(
                None, 
                'LOGIN_FAILED', 
                f"Tentative de connexion échouée pour l'email inexistant: {email}",
                request
            )
            cursor.close()
            conn.close()
            return jsonify({'message': 'Email ou mot de passe incorrect'}), 401

        print(f"Hash stocké: {user['mot_de_passe']}")
        print(f"Mot de passe tenté: {password}")
        print(f"Résultat vérification: {check_password_hash(user['mot_de_passe'], password)}")
        
        if check_password_hash(user['mot_de_passe'], password):
            token = jwt.encode({
                'user_id': user['id'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            # Enregistrer la connexion réussie
            log_user_action(
                user['id'], 
                'LOGIN_SUCCESS', 
                f"Connexion réussie pour {user['prenom']} {user['nom']} ({user['email']})",
                request
            )
            
            cursor.close()
            conn.close()
            return jsonify({
                'access_token': token,
                'user': {
                    'id': user['id'],
                    'nom': user['nom'],
                    'prenom': user['prenom'],
                    'email': user['email'],
                    'role': user['role']
                }
            })
        else:
            # Enregistrer l'échec de mot de passe
            log_user_action(
                user['id'], 
                'LOGIN_FAILED', 
                f"Tentative de connexion avec mot de passe incorrect pour {user['email']}",
                request
            )
            cursor.close()
            conn.close()
            return jsonify({'message': 'Email ou mot de passe incorrect'}), 401
            
    except Exception as e:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print(f"Erreur lors de la connexion: {e}")
        return jsonify({'message': str(e)}), 500

@bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({
        'id': current_user['id'],
        'nom': current_user['nom'],
        'prenom': current_user['prenom'],
        'email': current_user['email'],
        'role': current_user['role']
    })

@bp.route('/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """Route de déconnexion pour enregistrer l'action"""
    # Enregistrer la déconnexion
    log_user_action(
        current_user['id'], 
        'LOGOUT', 
        f"Déconnexion de {current_user['prenom']} {current_user['nom']} ({current_user['email']})",
        request
    )
    
    return jsonify({'message': 'Déconnexion réussie'})

@bp.route('/users', methods=['POST'])
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
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'email existe déjà
        cursor.execute("SELECT id FROM utilisateur WHERE email = %s", (data['email'],))
        existing_user = cursor.fetchone()
        if existing_user:
            # Option: Si le paramètre replace_if_exists est à true, on supprime l'utilisateur existant
            if data.get('replace_if_exists'):
                try:
                    print(f"Suppression de l'utilisateur existant avec l'email {data['email']}")
                    # Avec RealDictCursor, existing_user est un dictionnaire
                    user_id = existing_user['id'] if isinstance(existing_user, dict) else existing_user[0]
                    
                    # Supprimer les références dans d'autres tables
                    cursor.execute("UPDATE trash SET deleted_by = NULL WHERE deleted_by = %s", (user_id,))
                    cursor.execute("UPDATE trash SET restored_by = NULL WHERE restored_by = %s", (user_id,))
                    cursor.execute("UPDATE document SET proprietaire_id = NULL WHERE proprietaire_id = %s", (user_id,))
                    cursor.execute("UPDATE historique SET utilisateur_id = NULL WHERE utilisateur_id = %s", (user_id,))
                    
                    # Supprimer l'utilisateur
                    cursor.execute("DELETE FROM utilisateur WHERE id = %s", (user_id,))
                    conn.commit()
                    print(f"Utilisateur existant supprimé avec succès")
                except Exception as e:
                    conn.rollback()
                    print(f"Erreur lors de la suppression de l'utilisateur existant: {str(e)}")
                    cursor.close()
                    conn.close()
                    return jsonify({'message': f"Impossible de remplacer l'utilisateur existant: {str(e)}"}), 500
            else:
                pass
            cursor.close()
            conn.close()
            print(f"Email déjà utilisé: {data['email']}")
            return jsonify({'message': 'Cet email est déjà utilisé'}), 400
        
        # Générer un mot de passe aléatoire
        generated_password = generate_password()
        hashed_password = generate_password_hash(generated_password)
        
        # Utiliser le rôle spécifié dans la requête
        # La contrainte accepte maintenant tous les rôles définis dans le frontend
        role_value = data['role']
        print(f"Utilisation du rôle spécifié dans la requête: '{role_value}'")
        
        # Insérer le nouvel utilisateur avec un minimum de champs
        try:
            # Afficher la requête SQL pour le débogage
            query = """
            INSERT INTO utilisateur (email, nom, prenom, mot_de_passe, role)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """
            values = (
                data['email'],
                data['nom'],
                data['prenom'],
                hashed_password,
                role_value
            )
            print(f"Exécution de la requête: {query} avec les valeurs: {data['email']}, {data['nom']}, {data['prenom']}, [MOT_DE_PASSE_MASQUÉ], {role_value}")
            
            cursor.execute(query, values)
            
            new_user = cursor.fetchone()
            print(f"Type de résultat de l'insertion: {type(new_user).__name__}, valeur: {new_user}")
            
            if not new_user:
                conn.rollback()
                print("Erreur: Aucun ID retourné après l'insertion")
                return jsonify({'message': 'Erreur lors de la création de l\'utilisateur: aucun ID retourné'}), 500
                
            conn.commit()
            
            # Récupérer l'ID de l'utilisateur créé de manière sécurisée
            user_id = None
            try:
                # Avec RealDictCursor, le résultat est un dictionnaire avec la colonne 'id'
                if isinstance(new_user, dict) and 'id' in new_user:
                    user_id = new_user['id']
                    print(f"ID extrait du dictionnaire: {user_id}")
                # Essayer différentes approches pour extraire l'ID
                elif isinstance(new_user, (list, tuple)) and len(new_user) > 0:
                    user_id = new_user[0]
                    print(f"ID extrait via indexation: {user_id}")
                elif hasattr(new_user, 'items') and callable(getattr(new_user, 'items')):  # Dict-like
                    user_id = list(new_user.values())[0] if new_user else None
                    print(f"ID extrait via values(): {user_id}")
                elif hasattr(new_user, '__getitem__'):
                    try:
                        user_id = new_user[0]
                        print(f"ID extrait via __getitem__: {user_id}")
                    except (IndexError, TypeError, KeyError):
                        pass
                
                # Si toutes les approches échouent, essayer de convertir en chaîne
                if user_id is None and new_user is not None:
                    try:
                        user_id = int(str(new_user).strip('()').split(',')[0])
                        print(f"ID extrait via conversion de chaîne: {user_id}")
                    except (ValueError, IndexError):
                        pass
                
                print(f"Utilisateur créé avec succès: {data['email']} avec le rôle '{role_value}', ID: {user_id}")
            except Exception as e:
                print(f"Avertissement: Impossible d'extraire l'ID utilisateur du résultat: {new_user}, erreur: {str(e)}")
                # Continuer même si on ne peut pas extraire l'ID
            
            # Enregistrer l'action de création d'utilisateur
            log_user_action(
                current_user['id'], 
                'USER_CREATE', 
                f"Création de l'utilisateur {data['prenom']} {data['nom']} ({data['email']}) avec le rôle '{role_value}'",
                request
            )
            
            # 📧 ENVOYER L'EMAIL DE BIENVENUE
            email_sent = False
            try:
                from AppFlask.services.email_service import email_service
                
                # Préparer les données pour le template
                email_data = {
                    'user_name': f"{data['prenom']} {data['nom']}",
                    'user_email': data['email'],
                    'user_role': role_value,
                    'generated_password': generated_password,
                    'login_url': 'http://localhost:3000/login'
                }
                
                # Envoyer l'email de bienvenue
                email_sent = email_service.send_template_email(
                    to=[data['email']],
                    template_name='welcome',
                    subject='Bienvenue sur ESAG GED - Votre compte a été créé',
                    template_data=email_data
                )
                
                if email_sent:
                    print(f"✅ Email de bienvenue envoyé à {data['email']}")
                else:
                    print(f"⚠️ Échec de l'envoi de l'email de bienvenue à {data['email']}")
                    
            except Exception as email_error:
                print(f"❌ Erreur lors de l'envoi de l'email de bienvenue: {str(email_error)}")
                # L'utilisateur est créé même si l'email échoue
            
            return jsonify({
                'message': 'Utilisateur créé avec succès',
                'user_id': user_id,
                'email_sent': email_sent
            }), 201
            
        except Exception as e:
            conn.rollback()
            print(f"Erreur SQL lors de la création de l'utilisateur: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'message': f'Erreur lors de la création de l\'utilisateur dans la base de données: {str(e)}'}), 500
            
    except Exception as e:
        print(f"Erreur lors de la création de l'utilisateur: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Une erreur est survenue lors de la création de l\'utilisateur: {str(e)}'}), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

@bp.route('/users/<int:user_id>', methods=['DELETE'])
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'utilisateur existe
        cursor.execute("SELECT nom, prenom, email FROM utilisateur WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        print(f"Tentative de suppression définitive de l'utilisateur {user_id}: {user['prenom']} {user['nom']}")
        
        # Identifier les tables qui ont une référence à l'utilisateur dans la table trash
        # Nous nous concentrons uniquement sur les colonnes connues pour exister
        known_references = [
            {"table": "trash", "column": "deleted_by"},
            {"table": "trash", "column": "restored_by"},
            {"table": "document", "column": "proprietaire_id"},
            {"table": "historique", "column": "utilisateur_id"}
        ]
        
        # Mettre à jour les références dans les tables
        for ref in known_references:
            table = ref["table"]
            column = ref["column"]
            
            # Utiliser une nouvelle connexion pour chaque opération pour éviter les problèmes de transaction
            update_conn = db_connection()
            if update_conn is None:
                print(f"Impossible de se connecter à la base de données pour mettre à jour {table}.{column}")
                continue
                
            update_cursor = None
            try:
                update_cursor = update_conn.cursor(cursor_factory=RealDictCursor)
                
                # Vérifier s'il y a des références
                update_cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} = %s", (user_id,))
                count = update_cursor.fetchone()['count']
                
                if count > 0:
                    # Mettre à jour les références pour utiliser NULL
                    update_cursor.execute(f"""
                        UPDATE {table} 
                        SET {column} = NULL 
                        WHERE {column} = %s
                    """, (user_id,))
                    
                    update_conn.commit()
                    print(f"Mise à jour de {count} références dans la table {table}.{column} de l'utilisateur {user_id} vers NULL")
            except Exception as e:
                if update_conn:
                    update_conn.rollback()
                print(f"Erreur lors de la mise à jour des références dans {table}.{column}: {str(e)}")
            finally:
                if update_cursor:
                    update_cursor.close()
                if update_conn:
                    update_conn.close()
        
        # Maintenant que toutes les références ont été mises à jour, supprimer l'utilisateur
        delete_conn = db_connection()
        if delete_conn is None:
            return jsonify({'message': 'Erreur de connexion à la base de données pour la suppression'}), 500
            
        delete_cursor = None
        try:
            delete_cursor = delete_conn.cursor()
            
            # Supprimer l'utilisateur définitivement
            delete_cursor.execute("DELETE FROM utilisateur WHERE id = %s", (user_id,))
            
            delete_conn.commit()
            
            # Log l'action
            log_user_action(
                current_user['id'],
                'USER_DELETE',
                f"Suppression définitive de l'utilisateur {user['prenom']} {user['nom']} ({user['email']})",
                request
            )
            
            print(f"Utilisateur {user_id} supprimé avec succès")
            
            return jsonify({'message': 'Utilisateur supprimé définitivement avec succès'})
        except Exception as e:
            if delete_conn:
                delete_conn.rollback()
            print(f"Erreur lors de la suppression de l'utilisateur: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'message': f"Erreur lors de la suppression: {str(e)}"}), 500
        finally:
            if delete_cursor:
                delete_cursor.close()
            if delete_conn:
                delete_conn.close()
    except Exception as e:
        print(f"Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f"Erreur générale: {str(e)}"}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

@bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    print(f"Tentative de mise à jour de l'utilisateur {user_id} par {current_user['email']}")
    
    if current_user['role'].lower() != 'admin':
        print(f"Accès refusé pour {current_user['email']} - Rôle: {current_user['role']}")
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Aucune donnée reçue'}), 400
        print("Données reçues:", data)
        
        conn = db_connection()
        if conn is None:
            return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'utilisateur existe
        cursor.execute("SELECT * FROM utilisateur WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        if 'email' in data and data['email'] != user['email']:
            cursor.execute("SELECT id FROM utilisateur WHERE email = %s AND id != %s", (data['email'], user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'message': 'Cet email est déjà utilisé par un autre utilisateur'}), 400
        
        # Construire la requête de mise à jour
        update_fields = []
        update_values = []
        
        if 'nom' in data:
            update_fields.append("nom = %s")
            update_values.append(data['nom'])
        
        if 'prenom' in data:
            update_fields.append("prenom = %s")
            update_values.append(data['prenom'])
        
        if 'email' in data:
            update_fields.append("email = %s")
            update_values.append(data['email'])
        
        if 'role' in data:
            update_fields.append("role = %s")
            update_values.append(data['role'])
            print(f"Mise à jour du rôle: '{data['role']}'")
        
        if not update_fields:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Aucun champ à mettre à jour'}), 400
        
        # Exécuter la requête de mise à jour
        query = f"UPDATE utilisateur SET {', '.join(update_fields)} WHERE id = %s"
        update_values.append(user_id)
        
        try:
            print(f"Exécution de la requête: {query} avec les valeurs: {update_values}")
            cursor.execute(query, update_values)
            conn.commit()
            # Enregistrer l'action de mise à jour
            log_user_action(
                current_user['id'], 
                'USER_UPDATE', 
                f"Mise à jour de l'utilisateur {user_id}", 
                request
            )
            return jsonify({'message': 'Utilisateur mis à jour avec succès'}), 200
        except Exception as e:
            conn.rollback()
            print(f"Erreur SQL lors de la mise à jour: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'message': f'Erreur SQL lors de la mise à jour: {str(e)}'}), 500
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Erreur lors de la mise à jour de l'utilisateur: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Une erreur est survenue lors de la mise à jour de l\'utilisateur: {str(e)}'}), 500

@bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """Réinitialiser le mot de passe d'un utilisateur"""
    try:
        data = request.get_json()
        if not data or not data.get('email'):
            return jsonify({'message': 'Email requis'}), 400
        
        email = data['email']
        
        conn = db_connection()
        if conn is None:
            return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'utilisateur existe
        cursor.execute("SELECT id, nom, prenom, email FROM utilisateur WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            # Pour des raisons de sécurité, on ne révèle pas si l'email existe
            return jsonify({'message': 'Si cet email existe, un nouveau mot de passe a été envoyé'}), 200
        
        # Générer un nouveau mot de passe
        new_password = generate_password()
        hashed_password = generate_password_hash(new_password)
        
        # Mettre à jour le mot de passe
        cursor.execute("""
            UPDATE utilisateur 
            SET mot_de_passe = %s 
            WHERE id = %s
        """, (hashed_password, user['id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # 📧 ENVOYER L'EMAIL DE RÉINITIALISATION
        try:
            from AppFlask.services.email_service import email_service
            
            # Préparer les données pour le template
            email_data = {
                'user_name': f"{user['prenom']} {user['nom']}",
                'user_email': user['email'],
                'new_password': new_password,
                'login_url': 'http://localhost:3000/login'
            }
            
            # Envoyer l'email de réinitialisation
            email_sent = email_service.send_template_email(
                to=[user['email']],
                template_name='password_reset',
                subject='Réinitialisation de votre mot de passe - ESAG GED',
                template_data=email_data
            )
            
            if email_sent:
                logger.info(f"✅ Email de réinitialisation envoyé à {user['email']}")
            else:
                logger.warning(f"⚠️ Échec de l'envoi de l'email de réinitialisation à {user['email']}")
                
        except Exception as email_error:
            logger.error(f"❌ Erreur lors de l'envoi de l'email de réinitialisation: {str(email_error)}")
        
        # Enregistrer l'action
        log_user_action(
            user['id'], 
            'PASSWORD_RESET', 
            f"Réinitialisation du mot de passe pour {user['email']}",
            request
        )
        
        return jsonify({
            'message': 'Si cet email existe, un nouveau mot de passe a été envoyé',
            'email_sent': email_sent if 'email_sent' in locals() else False
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation du mot de passe: {str(e)}")
        return jsonify({'message': 'Une erreur est survenue'}), 500

@bp.route('/auth/request-password-reset', methods=['POST'])
@token_required
def admin_reset_user_password(current_user):
    """Réinitialiser le mot de passe d'un utilisateur (admin seulement)"""
    try:
        # Vérifier les permissions admin
        if current_user['role'].lower() != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403
        
        data = request.get_json()
        if not data or not data.get('user_id'):
            return jsonify({'message': 'ID utilisateur requis'}), 400
        
        user_id = data['user_id']
        
        conn = db_connection()
        if conn is None:
            return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les informations de l'utilisateur
        cursor.execute("SELECT id, nom, prenom, email FROM utilisateur WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Générer un nouveau mot de passe
        new_password = generate_password()
        hashed_password = generate_password_hash(new_password)
        
        # Mettre à jour le mot de passe
        cursor.execute("""
            UPDATE utilisateur 
            SET mot_de_passe = %s 
            WHERE id = %s
        """, (hashed_password, user['id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # 📧 ENVOYER L'EMAIL DE RÉINITIALISATION
        try:
            from AppFlask.services.email_service import email_service
            
            # Préparer les données pour le template
            email_data = {
                'user_name': f"{user['prenom']} {user['nom']}",
                'user_email': user['email'],
                'new_password': new_password,
                'admin_name': f"{current_user['prenom']} {current_user['nom']}",
                'login_url': 'http://localhost:3000/login'
            }
            
            # Envoyer l'email de réinitialisation
            email_sent = email_service.send_template_email(
                to=[user['email']],
                template_name='password_reset',
                subject='Votre mot de passe a été réinitialisé - ESAG GED',
                template_data=email_data
            )
            
            if email_sent:
                logger.info(f"✅ Email de réinitialisation envoyé à {user['email']} par l'admin {current_user['email']}")
            else:
                logger.warning(f"⚠️ Échec de l'envoi de l'email de réinitialisation à {user['email']}")
                
        except Exception as email_error:
            logger.error(f"❌ Erreur lors de l'envoi de l'email de réinitialisation: {str(email_error)}")
        
        # Enregistrer l'action
        log_user_action(
            current_user['id'], 
            'ADMIN_PASSWORD_RESET', 
            f"Réinitialisation du mot de passe de {user['email']} par l'admin {current_user['email']}",
            request
        )
        
        return jsonify({
            'message': f'Mot de passe réinitialisé pour {user["email"]}',
            'new_password': new_password,
            'email_sent': email_sent if 'email_sent' in locals() else False
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation du mot de passe: {str(e)}")
        return jsonify({'message': 'Une erreur est survenue'}), 500

@bp.route('/users/<int:user_id>/status', methods=['PUT'])
@token_required
def update_user_status(current_user, user_id):
    """Mettre à jour le statut d'un utilisateur (actif/inactif)"""
    if current_user['role'].lower() != 'admin':
        return jsonify({'message': 'Accès non autorisé'}), 403
    
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'message': 'Statut requis'}), 400
    
    status = data['status']
    if status not in ['active', 'inactive']:
        return jsonify({'message': 'Statut invalide. Valeurs acceptées: active, inactive'}), 400
    
    conn = db_connection()
    if conn is None:
        return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'utilisateur existe
        cursor.execute("SELECT id, nom, prenom, email FROM utilisateur WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Utilisateur non trouvé'}), 404
        
        # Mettre à jour le statut
        cursor.execute("""
            UPDATE utilisateur 
            SET status = %s
            WHERE id = %s
        """, (status, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log l'action
        action_type = 'USER_ACTIVATE' if status == 'active' else 'USER_DEACTIVATE'
        log_user_action(
            current_user['id'],
            action_type,
            f"{'Activation' if status == 'active' else 'Désactivation'} de l'utilisateur {user['prenom']} {user['nom']} ({user['email']})",
            request
        )
        
        return jsonify({
            'message': f"L'utilisateur a été {'activé' if status == 'active' else 'désactivé'} avec succès",
            'status': status
        }), 200
        
    except Exception as e:
        print(f"Erreur lors de la mise à jour du statut de l'utilisateur: {str(e)}")
        return jsonify({'message': str(e)}), 500

@bp.route('/users/<int:user_id>', methods=['OPTIONS'])
def handle_user_id_options(user_id):
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,DELETE')
    return response

@bp.route('/users/<int:user_id>/status', methods=['OPTIONS'])
def handle_user_status_options(user_id):
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'PUT')
    return response