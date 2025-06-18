from flask import Blueprint, request, jsonify, send_from_directory, current_app, session
from flask_login import login_required, current_user
from AppFlask.db import db_connection
from AppFlask.utils.auth_utils import token_required
import os
import json
from datetime import datetime

# Créer le blueprint pour les API de documents
document_api_bp = Blueprint('document_api', __name__)

def has_permission(doc_id, user_id, required_permission='lecture'):
    """Vérifier les permissions de l'utilisateur sur un document"""
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupérer le propriétaire
        cursor.execute("SELECT proprietaire_id FROM document WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()

        if doc is None:
            return False

        # L'utilisateur est propriétaire → tous les droits
        if doc['proprietaire_id'] == int(user_id):
            return True

        # Sinon, vérifier dans la table partage
        cursor.execute("""
            SELECT permissions FROM partage
            WHERE document_id = %s AND utilisateur_id = %s
        """, (doc_id, user_id))
        partage = cursor.fetchone()

        cursor.close()
        conn.close()

        if not partage:
            return False

        # Vérifier les droits
        if required_permission == 'lecture':
            return True
        elif required_permission == 'edition' and partage['permissions'] in ('édition', 'admin'):
            return True
        elif required_permission == 'admin' and partage['permissions'] == 'admin':
            return True

        return False

    except Exception as e:
        print(f"Erreur dans has_permission: {e}")
        return False

@document_api_bp.route('/documents/my', methods=['GET'])
@token_required
def get_my_documents(current_user_data):
    """Récupérer les documents de l'utilisateur connecté"""
    try:
        user_id = current_user_data['user_id']
        dossier_id = request.args.get('dossier_id')
        
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # Base query pour les documents de l'utilisateur
        if dossier_id and dossier_id != 'null':
            query = """
                SELECT d.id, d.titre, d.description, d.date_ajout as date_creation,
                       d.derniere_modification, d.taille, d.categorie as type_document,
                       d.statut,
                       CASE 
                           WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                           WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                           WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                           ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                       END as taille_formatee
                FROM document d 
                WHERE d.proprietaire_id = %s AND d.dossier_id = %s AND (d.statut != 'supprime' OR d.statut IS NULL)
                ORDER BY d.date_ajout DESC
            """
            cursor.execute(query, (user_id, dossier_id))
        else:
            query = """
                SELECT d.id, d.titre, d.description, d.date_ajout as date_creation,
                       d.derniere_modification, d.taille, d.categorie as type_document,
                       d.statut,
                       CASE 
                           WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                           WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                           WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                           ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                       END as taille_formatee
                FROM document d 
                WHERE d.proprietaire_id = %s AND (d.dossier_id IS NULL OR d.dossier_id = 0) AND (d.statut != 'supprime' OR d.statut IS NULL)
                ORDER BY d.date_ajout DESC
            """
            cursor.execute(query, (user_id,))

        documents = cursor.fetchall()
        
        # Convertir les dates en format ISO
        for doc in documents:
            if doc['date_creation']:
                doc['date_creation'] = doc['date_creation'].isoformat() if hasattr(doc['date_creation'], 'isoformat') else str(doc['date_creation'])
            if doc['derniere_modification']:
                doc['derniere_modification'] = doc['derniere_modification'].isoformat() if hasattr(doc['derniere_modification'], 'isoformat') else str(doc['derniere_modification'])

        cursor.close()
        conn.close()

        return jsonify(documents), 200

    except Exception as e:
        print(f"Erreur lors de la récupération des documents: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des documents'}), 500

@document_api_bp.route('/documents/<int:doc_id>/download', methods=['GET'])
@token_required
def download_document_api(current_user_data, doc_id):
    """Télécharger un document via API"""
    try:
        user_id = current_user_data['user_id']
        
        # Vérifier les permissions
        if not has_permission(doc_id, user_id, 'lecture'):
            return jsonify({'error': 'Permission refusée'}), 403

        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT titre, fichier FROM document WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()
        cursor.close()
        conn.close()

        if not doc:
            return jsonify({'error': 'Document non trouvé'}), 404

        # Chemin du fichier
        file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), doc['fichier'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé sur le serveur'}), 404

        return send_from_directory(
            current_app.config.get('UPLOAD_FOLDER', 'uploads'), 
            doc['fichier'], 
            as_attachment=True,
            download_name=doc['titre']
        )

    except Exception as e:
        print(f"Erreur lors du téléchargement: {e}")
        return jsonify({'error': 'Erreur lors du téléchargement'}), 500

@document_api_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@token_required
def delete_document_api(current_user_data, doc_id):
    """Supprimer un document via API"""
    try:
        user_id = current_user_data['user_id']
        
        # Vérifier les permissions
        if not has_permission(doc_id, user_id, 'admin'):
            return jsonify({'error': 'Permission refusée'}), 403

        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Récupérer les infos du document
        cursor.execute("SELECT * FROM document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()

        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404

        # 2. Insérer dans la table trash (copie des infos importantes)
        cursor.execute("""
            INSERT INTO trash (item_id, item_type, item_data, deleted_by, deleted_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (
            doc_id,
            'document',
            json.dumps({
                'titre': document['titre'],
                'fichier': document['fichier'],
                'taille': document['taille'],
                'description': document['description']
            }),
            user_id
        ))

        # 3. Marquer comme supprimé au lieu de supprimer définitivement
        cursor.execute("""
            UPDATE document 
            SET statut = 'supprime', derniere_modification = NOW() 
            WHERE id = %s
        """, (doc_id,))
        
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Document supprimé avec succès'}), 200

    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")
        return jsonify({'error': 'Erreur lors de la suppression'}), 500

@document_api_bp.route('/documents/share', methods=['POST'])
@token_required
def share_document_api(current_user_data):
    """Partager un document via API"""
    try:
        user_id = current_user_data['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400
            
        doc_id = data.get('document_id')
        utilisateur_id = data.get('utilisateur_id')
        permissions = data.get('permissions')

        if not all([doc_id, utilisateur_id, permissions]):
            return jsonify({'error': 'Paramètres manquants'}), 400

        # Vérifier que l'utilisateur a le droit de partager le document
        if not has_permission(doc_id, user_id, 'admin'):
            return jsonify({'error': 'Permission refusée'}), 403

        conn = db_connection()
        cursor = conn.cursor()

        # Vérifier si le partage existe déjà
        cursor.execute("""
            SELECT id FROM partage 
            WHERE document_id = %s AND utilisateur_id = %s
        """, (doc_id, utilisateur_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Mettre à jour les permissions existantes
            cursor.execute("""
                UPDATE partage 
                SET permissions = %s, date_partage = NOW()
                WHERE document_id = %s AND utilisateur_id = %s
            """, (permissions, doc_id, utilisateur_id))
        else:
            # Créer un nouveau partage
            cursor.execute("""
                INSERT INTO partage (document_id, utilisateur_id, permissions, date_partage, partage_par)
                VALUES (%s, %s, %s, NOW(), %s)
            """, (doc_id, utilisateur_id, permissions, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Document partagé avec succès'}), 200

    except Exception as e:
        print(f"Erreur lors du partage: {e}")
        return jsonify({'error': 'Erreur lors du partage'}), 500

@document_api_bp.route('/users', methods=['GET'])
@token_required
def get_users_api(current_user_data):
    """Récupérer la liste des utilisateurs pour le partage"""
    try:
        current_user_id = current_user_data['user_id']
        
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupérer tous les utilisateurs sauf l'utilisateur actuel
        cursor.execute("""
            SELECT id, nom, prenom, email, username
            FROM utilisateur 
            WHERE id != %s AND (statut = 'actif' OR statut IS NULL)
            ORDER BY nom, prenom
        """, (current_user_id,))
        
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(users), 200

    except Exception as e:
        print(f"Erreur lors de la récupération des utilisateurs: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des utilisateurs'}), 500 