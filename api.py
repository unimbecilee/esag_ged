from flask import Flask, request, jsonify, current_app
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration de la base de données MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 5
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 10
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 45
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

db = SQLAlchemy(app)

# Modèles de données
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    nom = db.Column(db.String(100))
    prenom = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, exclude=None):
        data = {
            'id': self.id,
            'email': self.email,
            'nom': self.nom,
            'prenom': self.prenom,
            'role': self.role
        }
        if exclude:
            return {k: v for k, v in data.items() if k not in exclude}
        return data

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    chemin_fichier = db.Column(db.String(255))
    type_document = db.Column(db.String(50))
    statut = db.Column(db.String(20), default='actif')

    def to_dict(self, exclude=None):
        return {
            'id': self.id,
            'titre': self.titre,
            'description': self.description,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'type_document': self.type_document,
            'statut': self.statut
        }

# Routes API
@app.route('/api/documents', methods=['GET'])
def get_documents():
    try:
        documents = Document.query.all()
        return jsonify([doc.to_dict() for doc in documents])
    except Exception as e:
        logger.error('Erreur lors de l\'authentification : %s', str(e), exc_info=True)
        return jsonify({'error': 'Une erreur interne est survenue'}), 500

@app.route('/api/documents/<int:doc_id>', methods=['GET'])
def get_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        return jsonify(document.to_dict())
    except Exception as e:
        logger.error('Erreur lors de l\'authentification : %s', str(e), exc_info=True)
        return jsonify({'error': 'Une erreur interne est survenue'}), 500

@app.route('/api/documents', methods=['POST'])
def create_document():
    try:
        data = request.json
        if not data or 'titre' not in data:
            return jsonify({'error': 'Le titre est requis'}), 400

        nouveau_document = Document(
            titre=data['titre'],
            description=data.get('description', ''),
            type_document=data.get('type_document', ''),
            statut=data.get('statut', 'actif')
        )
        db.session.add(nouveau_document)
        db.session.commit()
        
        return jsonify({
            'id': nouveau_document.id,
            'message': 'Document créé avec succès'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<int:doc_id>', methods=['PUT'])
def update_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'Aucune donnée fournie'}), 400

        document.titre = data.get('titre', document.titre)
        document.description = data.get('description', document.description)
        document.type_document = data.get('type_document', document.type_document)
        document.statut = data.get('statut', document.statut)
        
        db.session.commit()
        return jsonify({'message': 'Document mis à jour avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    try:
        document = Document.query.get_or_404(doc_id)
        db.session.delete(document)
        db.session.commit()
        return jsonify({'message': 'Document supprimé avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Routes d'authentification
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        logger = current_app.logger
        logger.info('Tentative de connexion avec email: %s', data.get('email'))
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email et mot de passe requis'}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user or not check_password_hash(user.password, data['password']):
            logger.warning('Tentative de connexion échouée pour email: %s', data.get('email'))
            return jsonify({'error': 'Identifiants invalides'}), 401

        token = jwt.encode(
            {
                'user_id': user.id,
                'email': user.email,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(days=1)
            },
            app.config.get('SECRET_KEY', 'fallback_secret_' + str(os.urandom(16))),
            algorithm='HS256'
        )

        return jsonify({
            'token': token,
            'user': user.to_dict(exclude=['password'])
        })
    except Exception as e:
        logger.error('Erreur lors de l\'authentification : %s', str(e), exc_info=True)
        return jsonify({'error': 'Une erreur interne est survenue'}), 500

# Initialisation de la base de données
with app.app_context():
    try:
        db.create_all()
        # Créer un utilisateur admin par défaut si aucun utilisateur n'existe
        if not User.query.first():
            admin = User(
                email='admin@esag.com',
                password=generate_password_hash('admin123'),
                nom='Admin',
                prenom='ESAG',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Utilisateur admin créé avec succès")
        print("Base de données initialisée avec succès")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {str(e)}")

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], port=5000)