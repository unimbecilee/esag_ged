from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from AppFlask.db import db_connection
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from psycopg2.extras import RealDictCursor
import logging
import traceback

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
            logger.info("=== Début de la tentative de connexion ===")
            logger.info(f"Headers complets reçus : {dict(request.headers)}")
            logger.info(f"Méthode de requête : {request.method}")
            logger.info(f"Type de contenu : {request.content_type}")
            
            # Récupération des données selon le format
            if request.is_json:
                logger.info("Traitement d'une requête JSON")
                data = request.get_json()
                logger.info(f"Données JSON reçues : {data}")
                email = data.get('email')
                password = data.get('password')
            else:
                logger.info("Traitement d'une requête form-data")
                logger.info(f"Données form reçues : {dict(request.form)}")
                email = request.form.get('email')
                password = request.form.get('password')
            
            logger.info(f"Email reçu : {email}")
            logger.info(f"Mot de passe reçu : {'*' * len(password) if password else 'Non fourni'}")

            if not email or not password:
                logger.warning("Données manquantes dans la requête")
                return jsonify({'message': 'Email et mot de passe requis'}), 400

            conn = db_connection()
            if conn is None:
                logger.error("Échec de la connexion à la base de données")
                return jsonify({'message': 'Erreur de connexion à la base de données'}), 500

            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                logger.info(f"Recherche de l'utilisateur avec l'email : {email}")
                cursor.execute("SELECT * FROM Utilisateur WHERE email = %s", (email,))
                user = cursor.fetchone()
                
                if user:
                    logger.info("Utilisateur trouvé dans la base de données")
                    logger.info(f"Données utilisateur : {user}")
                    
                    # Vérification du mot de passe
                    logger.info("Tentative de vérification du mot de passe")
                    password_check = check_password_hash(user['mot_de_passe'], password)
                    logger.info(f"Résultat de la vérification du mot de passe : {password_check}")
                    
                    if password_check:
                        logger.info("Authentification réussie - Création de la session")
                        user_obj = User(
                            id=user['id'],
                            nom=user['nom'],
                            prenom=user['prenom'],
                            email=user['email'],
                            role=user['role']
                        )
                        login_user(user_obj)
                        session['user_id'] = user['id']
                        session['user_role'] = user['role']

                        response_data = {
                            'message': 'Connexion réussie',
                            'user': {
                                'id': user['id'],
                                'nom': user['nom'],
                                'prenom': user['prenom'],
                                'email': user['email'],
                                'role': user['role']
                            }
                        }
                        logger.info(f"Envoi de la réponse de succès : {response_data}")
                        return jsonify(response_data), 200
                    else:
                        logger.warning("Échec de l'authentification - Mot de passe incorrect")
                        return jsonify({'message': 'Email ou mot de passe incorrect'}), 401
                else:
                    logger.warning(f"Aucun utilisateur trouvé avec l'email : {email}")
                    return jsonify({'message': 'Email ou mot de passe incorrect'}), 401

            except Exception as e:
                logger.error(f"Erreur SQL : {str(e)}")
                logger.error(f"Traceback complet : {traceback.format_exc()}")
                return jsonify({'message': 'Une erreur est survenue lors de la connexion'}), 500
            finally:
                cursor.close()
                conn.close()
                logger.info("Connexion à la base de données fermée")

        except Exception as e:
            logger.error(f"Erreur générale : {str(e)}")
            logger.error(f"Traceback complet : {traceback.format_exc()}")
            return jsonify({'message': 'Une erreur inattendue est survenue'}), 500

    # Pour les requêtes GET, retourner le template HTML
    return render_template('login.html')


# Déconnexion
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Déconnexion réussie', 'success')
    return redirect(url_for('auth.login'))


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
