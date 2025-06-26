from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from AppFlask.db import db_connection
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from psycopg2.extras import RealDictCursor
import logging
import traceback
from AppFlask.api.auth import token_required
from AppFlask.services.logging_service import logging_service
import jwt
import datetime
from config import Config

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

# Classe utilisateur compatible avec Flask-Login
class User(UserMixin):
    def __init__(self, id, nom, prenom, email, role):
        self.id = id
        self.nom = nom
        self.prenom = prenom
        self.email = email
        self.role = role

    def get_id(self):
        return str(self.id)


# Route temporaire pour mettre à jour le mot de passe de l'utilisateur test
@auth_bp.route('/update_test_user', methods=['GET'])
def update_test_user():
    try:
        conn = db_connection()
        if conn is None:
            return jsonify({'message': 'Erreur de connexion à la base de données'}), 500

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'utilisateur existe
        cursor.execute("SELECT id FROM Utilisateur WHERE email = %s", ('admin@test.com',))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'message': 'Utilisateur test non trouvé'}), 404
            
        # Mettre à jour le mot de passe avec le hachage Werkzeug
        hashed_password = generate_password_hash('admin123')
        cursor.execute("""
            UPDATE Utilisateur 
            SET mot_de_passe = %s 
            WHERE email = %s
        """, (hashed_password, 'admin@test.com'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Mot de passe de l\'utilisateur test mis à jour avec succès',
            'credentials': {
                'email': 'admin@test.com',
                'password': 'admin123'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'utilisateur test : {str(e)}")
        logger.error(f"Traceback : {traceback.format_exc()}")
        return jsonify({'message': 'Erreur lors de la mise à jour de l\'utilisateur test'}), 500


# Connexion
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            # Récupération des données selon le format
            if request.is_json:
                data = request.get_json()
                email = data.get('email')
                password = data.get('password')
            else:
                email = request.form.get('email')
                password = request.form.get('password')

            if not email or not password:
                logging_service.log_event(
                    level='WARNING',
                    event_type='LOGIN_ATTEMPT',
                    message='Tentative de connexion avec des données manquantes',
                    additional_data={'email': email}
                )
                return jsonify({'message': 'Email et mot de passe requis'}), 400

            conn = db_connection()
            if conn is None:
                logging_service.log_event(
                    level='ERROR',
                    event_type='SYSTEM_ERROR',
                    message='Échec de connexion à la base de données lors de la tentative de connexion'
                )
                return jsonify({'message': 'Erreur de connexion à la base de données'}), 500

            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, mot_de_passe, nom, prenom, role FROM utilisateur WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                # Création du token JWT
                token = jwt.encode({
                    'user_id': user[0],
                    'email': user[1],
                    'role': user[5],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
                }, Config.SECRET_KEY, algorithm='HS256')

                # Log de la connexion réussie
                logger.info(f"Attempting to log LOGIN_SUCCESS for user_id: {user[0]}")
                try:
                    logging_service.log_event(
                        level='INFO',
                        event_type='LOGIN_SUCCESS',
                        user_id=user[0],
                        message=f"Connexion réussie pour {user[3]} {user[4]}",
                        additional_data={
                            'email': user[1],
                            'role': user[5]
                        }
                    )
                    logger.info(f"Call to logging_service.log_event for LOGIN_SUCCESS completed for user_id: {user[0]}")
                except Exception as e_log:
                    logger.error(f"Exception during logging_service.log_event for LOGIN_SUCCESS: {str(e_log)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")

                return jsonify({
                    'token': token,
                    'user': {
                        'id': user[0],
                        'email': user[1],
                        'nom': user[3],
                        'prenom': user[4],
                        'role': user[5]
                    }
                })
            else:
                # Log de la tentative échouée
                logging_service.log_event(
                    level='WARNING',
                    event_type='LOGIN_FAILED',
                    message='Tentative de connexion échouée',
                    additional_data={'email': email}
                )
                return jsonify({'message': 'Email ou mot de passe incorrect'}), 401

        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {str(e)}")
            logging_service.log_event(
                level='ERROR',
                event_type='SYSTEM_ERROR',
                message=f"Erreur lors de la tentative de connexion: {str(e)}"
            )
            return jsonify({'message': 'Une erreur est survenue'}), 500

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return render_template('login.html')


# Déconnexion
@auth_bp.route('/logout')
@token_required
def logout(current_user):
    try:
        # Log de la déconnexion
        logging_service.log_event(
            level='INFO',
            event_type='LOGOUT',
            user_id=current_user['id'],
            message=f"Déconnexion de l'utilisateur {current_user['nom']} {current_user['prenom']}"
        )
        return jsonify({'message': 'Déconnexion réussie'})
    except Exception as e:
        logger.error(f"Erreur lors de la déconnexion: {str(e)}")
        logging_service.log_event(
            level='ERROR',
            event_type='SYSTEM_ERROR',
            message=f"Erreur lors de la déconnexion: {str(e)}",
            user_id=current_user['id']
        )
        return jsonify({'message': 'Une erreur est survenue lors de la déconnexion'}), 500


# Compte utilisateur
@auth_bp.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    user_id = current_user.get_id()

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        numero_tel = request.form['numero_tel']
        service = request.form['service']

        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Utilisateur 
            SET nom = %s, prenom = %s, email = %s, numero_tel = %s, service = %s 
            WHERE id = %s
        """, (nom, prenom, email, numero_tel, service, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Informations mises à jour avec succès', 'success')
        return redirect(url_for('auth.account'))

    conn = db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nom, prenom, email, numero_tel, service FROM Utilisateur WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('account.html', user=user)

# Route de test pour créer un utilisateur
@auth_bp.route('/create_test_user', methods=['GET'])
def create_test_user():
    try:
        conn = db_connection()
        if conn is None:
            return jsonify({'message': 'Erreur de connexion à la base de données'}), 500

        cursor = conn.cursor()
        
        # Hasher le mot de passe (admin123)
        hashed_password = '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT id FROM Utilisateur WHERE email = %s", ('admin@test.com',))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Utilisateur de test existe déjà'}), 200
            
        # Créer l'utilisateur
        cursor.execute("""
            INSERT INTO Utilisateur (email, mot_de_passe, nom, prenom, role)
            VALUES (%s, %s, %s, %s, %s)
        """, ('admin@test.com', hashed_password, 'Admin', 'Test', 'admin'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Utilisateur de test créé avec succès',
            'credentials': {
                'email': 'admin@test.com',
                'password': 'admin123'
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur de test : {str(e)}")
        logger.error(f"Traceback : {traceback.format_exc()}")
        return jsonify({'message': 'Erreur lors de la création de l\'utilisateur de test'}), 500
