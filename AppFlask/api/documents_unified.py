from flask import Blueprint, request, jsonify, send_from_directory, current_app
from AppFlask.db import db_connection
from AppFlask.api.auth import token_required, log_user_action
from psycopg2.extras import RealDictCursor
import os
import json
from datetime import datetime
from AppFlask.services.notification_service import notification_service
from AppFlask.utils.trash_manager import move_document_to_trash

# Blueprint unifié pour tous les documents
bp = Blueprint('documents_unified', __name__)

def has_permission(doc_id, user_id, required_permission='lecture'):
    """Vérifier les permissions de l'utilisateur sur un document"""
    try:
        conn = db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer le document et vérifier qu'il existe
        cursor.execute("SELECT proprietaire_id FROM document WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()

        if doc is None:
            cursor.close()
            conn.close()
            return False

        # L'utilisateur est propriétaire → tous les droits
        if doc['proprietaire_id'] == int(user_id):
            cursor.close()
            conn.close()
            return True

        # Vérifier si l'utilisateur est admin
        cursor.execute("SELECT role FROM utilisateur WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user and user.get('role', '').lower() == 'admin':
            cursor.close()
            conn.close()
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

        # Vérifier les droits selon le niveau requis
        permissions = partage['permissions']
        if required_permission == 'lecture':
            return True
        elif required_permission == 'edition' and permissions in ('édition', 'admin'):
            return True
        elif required_permission == 'admin' and permissions == 'admin':
            return True

        return False

    except Exception as e:
        print(f"🚨 Erreur dans has_permission: {e}")
        return False

# ================================
# ROUTES PRINCIPALES
# ================================

@bp.route('/documents/my', methods=['GET'])
@token_required  
def get_my_documents(current_user):
    """Récupérer les documents de l'utilisateur connecté"""
    try:
        user_id = current_user['id']
        dossier_id = request.args.get('dossier_id')
        admin_mode = request.args.get('admin_mode', 'false').lower() == 'true'
        
        print(f"🔍 [API DEBUG] user_id: {user_id}, dossier_id: '{dossier_id}', admin_mode: {admin_mode}")
        
        # Convertir dossier_id
        if dossier_id == '' or dossier_id == 'None':
            dossier_id = None
        else:
            try:
                dossier_id = int(dossier_id) if dossier_id else None
            except ValueError:
                dossier_id = None
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Vérifier si l'utilisateur est admin
        cursor.execute("SELECT role FROM utilisateur WHERE id = %s", (user_id,))
        user_info = cursor.fetchone()
        is_admin = user_info and user_info.get('role', '').lower() == 'admin'

        # Construire la requête selon le mode
        if admin_mode and is_admin:
            # Mode admin : voir tous les documents
            if dossier_id is None:
                query = """
                    SELECT d.id, d.titre, d.description, d.date_ajout as date_creation,
                           d.derniere_modification, d.taille, d.categorie as type_document,
                           d.dossier_id, d.cloudinary_url,
                           CASE 
                               WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                               WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                               WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                               ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                           END as taille_formatee
                    FROM document d 
                    WHERE d.dossier_id IS NULL
                    ORDER BY d.date_ajout DESC
                """
                cursor.execute(query)
            else:
                query = """
                    SELECT d.id, d.titre, d.description, d.date_ajout as date_creation,
                           d.derniere_modification, d.taille, d.categorie as type_document,
                           d.dossier_id, d.cloudinary_url,
                           CASE 
                               WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                               WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                               WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                               ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                           END as taille_formatee
                    FROM document d 
                    WHERE d.dossier_id = %s
                    ORDER BY d.date_ajout DESC
                """
                cursor.execute(query, (dossier_id,))
        else:
            # Mode normal : seulement les documents de l'utilisateur
            if dossier_id is None:
                query = """
                    SELECT d.id, d.titre, d.description, d.date_ajout as date_creation,
                           d.derniere_modification, d.taille, d.categorie as type_document,
                           d.dossier_id, d.cloudinary_url,
                           CASE 
                               WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                               WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                               WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                               ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                           END as taille_formatee
                    FROM document d 
                    WHERE d.proprietaire_id = %s AND d.dossier_id IS NULL
                    ORDER BY d.date_ajout DESC
                """
                cursor.execute(query, (user_id,))
            else:
                query = """
                    SELECT d.id, d.titre, d.description, d.date_ajout as date_creation,
                           d.derniere_modification, d.taille, d.categorie as type_document,
                           d.dossier_id, d.cloudinary_url,
                           CASE 
                               WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                               WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                               WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                               ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                           END as taille_formatee
                    FROM document d 
                    WHERE d.proprietaire_id = %s AND d.dossier_id = %s
                    ORDER BY d.date_ajout DESC
                """
                cursor.execute(query, (user_id, dossier_id))

        documents = cursor.fetchall()
        
        # Convertir les dates
        for doc in documents:
            if doc['date_creation']:
                doc['date_creation'] = doc['date_creation'].isoformat() if hasattr(doc['date_creation'], 'isoformat') else str(doc['date_creation'])
            if doc['derniere_modification']:
                doc['derniere_modification'] = doc['derniere_modification'].isoformat() if hasattr(doc['derniere_modification'], 'isoformat') else str(doc['derniere_modification'])

        cursor.close()
        conn.close()

        return jsonify(documents), 200

    except Exception as e:
        print(f"🚨 Erreur lors de la récupération des documents: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des documents'}), 500

@bp.route('/documents/<int:doc_id>', methods=['GET'])
@token_required
def get_document_by_id(current_user, doc_id):
    """Récupérer un document spécifique par son ID"""
    try:
        user_id = current_user['id']
        
        print(f"🔍 [API DEBUG] Récupération document {doc_id} par utilisateur {user_id}")
        
        # Vérifier les permissions avec debug
        has_perm = has_permission(doc_id, user_id, 'lecture')
        print(f"🔍 [API DEBUG] Permission lecture pour doc {doc_id}: {has_perm}")
        
        if not has_perm:
            return jsonify({'error': 'Accès non autorisé'}), 403

        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer le document avec toutes les informations
        cursor.execute("""
            SELECT d.*, 
                   u.nom as proprietaire_nom, 
                   u.prenom as proprietaire_prenom,
                   CASE 
                       WHEN d.taille IS NULL THEN 'Inconnue'
                       WHEN d.taille < 1024 THEN CONCAT(d.taille, ' B')
                       WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille / 1024.0, 2), ' KB')
                       WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille / 1048576.0, 2), ' MB')
                       ELSE CONCAT(ROUND(d.taille / 1073741824.0, 2), ' GB')
                   END as taille_formatee
            FROM document d
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            WHERE d.id = %s
        """, (doc_id,))
        
        document = cursor.fetchone()
        cursor.close()
        conn.close()

        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404

        # Convertir en dictionnaire
        doc_dict = dict(document)
        
        # Formatage des dates
        if doc_dict.get('date_ajout'):
            doc_dict['date_creation'] = doc_dict['date_ajout'].isoformat() if hasattr(doc_dict['date_ajout'], 'isoformat') else str(doc_dict['date_ajout'])
        if doc_dict.get('derniere_modification'):
            doc_dict['derniere_modification'] = doc_dict['derniere_modification'].isoformat() if hasattr(doc_dict['derniere_modification'], 'isoformat') else str(doc_dict['derniere_modification'])
        
        print(f"✅ [API DEBUG] Document {doc_id} récupéré avec succès")
        return jsonify(doc_dict), 200

    except Exception as e:
        print(f"🚨 Erreur lors de la récupération du document {doc_id}: {e}")
        return jsonify({'error': 'Erreur lors de la récupération du document'}), 500

@bp.route('/documents/<int:doc_id>/download', methods=['GET'])
@token_required
def download_document_api(current_user, doc_id):
    """Télécharger un document via API (Cloudinary)"""
    try:
        user_id = current_user['id']
        
        print(f"🔍 [API DEBUG] Téléchargement document {doc_id} par utilisateur {user_id}")
        
        # Vérifier les permissions
        if not has_permission(doc_id, user_id, 'lecture'):
            return jsonify({'error': 'Permission refusée'}), 403

        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer l'URL Cloudinary du document
        cursor.execute("""
            SELECT titre, fichier, cloudinary_url, mime_type 
            FROM document 
            WHERE id = %s
        """, (doc_id,))
        doc = cursor.fetchone()
        cursor.close()
        conn.close()

        if not doc:
            return jsonify({'error': 'Document non trouvé'}), 404

        # Priorité à l'URL Cloudinary
        if doc.get('cloudinary_url'):
            # Enregistrer l'action
            log_user_action(
                user_id, 
                'DOCUMENT_DOWNLOAD_API', 
                f"Téléchargement API du document '{doc['titre']}' (ID: {doc_id})",
                request
            )
            
            # Redirection vers Cloudinary
            from flask import redirect
            return redirect(doc['cloudinary_url'])
        
        elif doc.get('fichier'):
            # Fallback vers fichier local
            file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), doc['fichier'])
            
            if not os.path.exists(file_path):
                return jsonify({'error': 'Fichier non trouvé sur le serveur'}), 404

            log_user_action(
                user_id, 
                'DOCUMENT_DOWNLOAD_API', 
                f"Téléchargement API du document '{doc['titre']}' (ID: {doc_id})",
                request
            )

            return send_from_directory(
                current_app.config.get('UPLOAD_FOLDER', 'uploads'), 
                doc['fichier'], 
                as_attachment=True,
                download_name=doc['titre']
            )
        else:
            return jsonify({'error': 'Aucun fichier associé à ce document'}), 404

    except Exception as e:
        print(f"🚨 Erreur lors du téléchargement du document {doc_id}: {e}")
        return jsonify({'error': 'Erreur lors du téléchargement'}), 500

@bp.route('/documents/recent-activities', methods=['GET'])
@token_required
def get_recent_activities(current_user):
    """Récupérer les activités récentes de l'utilisateur"""
    try:
        user_id = current_user['id']
        
        print(f"🔍 [RECENT DEBUG] Récupération activités pour user_id: {user_id}")
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les documents récemment ajoutés par l'utilisateur
        query = """
            SELECT d.id as document_id, d.titre as document_title, d.categorie as document_type,
                   'UPLOAD' as action, 'Document uploadé' as action_description,
                   u.prenom || ' ' || u.nom as user, d.date_ajout as timestamp,
                   CASE 
                       WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                       WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                       WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                       ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                   END as size
            FROM document d
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            WHERE d.proprietaire_id = %s
            ORDER BY d.date_ajout DESC
            LIMIT 20
        """
        
        cursor.execute(query, (user_id,))
        activities = cursor.fetchall()
        
        # Convertir les dates
        for activity in activities:
            if activity['timestamp']:
                activity['timestamp'] = activity['timestamp'].isoformat() if hasattr(activity['timestamp'], 'isoformat') else str(activity['timestamp'])
        
        cursor.close()
        conn.close()
        
        print(f"🔍 [RECENT DEBUG] {len(activities)} activités trouvées")
        return jsonify({'activities': activities}), 200
        
    except Exception as e:
        print(f"🚨 Erreur lors de la récupération des activités récentes: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des activités récentes'}), 500

@bp.route('/documents/favorites', methods=['GET'])
@token_required
def get_favorite_documents(current_user):
    """Récupérer les documents favoris de l'utilisateur"""
    try:
        user_id = current_user['id']
        
        print(f"🔍 [FAVORITES DEBUG] Récupération favoris pour user_id: {user_id}")
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les documents favoris avec leurs informations complètes
        query = """
            SELECT d.id, d.titre, d.description, d.date_ajout as date_creation,
                   d.derniere_modification, d.taille, d.categorie as type_document,
                   d.dossier_id, d.cloudinary_url,
                   CASE 
                       WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                       WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                       WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                       ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                   END as taille_formatee,
                   u.prenom || ' ' || u.nom as proprietaire_nom,
                   f.date_ajout as date_favori,
                   'actif' as statut
            FROM favoris f
            JOIN document d ON f.document_id = d.id
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            WHERE f.utilisateur_id = %s 
            ORDER BY f.date_ajout DESC
        """
        
        cursor.execute(query, (user_id,))
        favorites = cursor.fetchall()
        
        # Convertir les dates
        for favorite in favorites:
            if favorite['date_creation']:
                favorite['date_creation'] = favorite['date_creation'].isoformat() if hasattr(favorite['date_creation'], 'isoformat') else str(favorite['date_creation'])
            if favorite['derniere_modification']:
                favorite['derniere_modification'] = favorite['derniere_modification'].isoformat() if hasattr(favorite['derniere_modification'], 'isoformat') else str(favorite['derniere_modification'])
            if favorite.get('date_favori'):
                favorite['date_favori'] = favorite['date_favori'].isoformat() if hasattr(favorite['date_favori'], 'isoformat') else str(favorite['date_favori'])
        
        cursor.close()
        conn.close()
        
        print(f"🔍 [FAVORITES DEBUG] {len(favorites)} favoris trouvés")
        return jsonify(favorites), 200
        
    except Exception as e:
        print(f"🚨 Erreur lors de la récupération des favoris: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des favoris'}), 500

@bp.route('/documents/<int:doc_id>/favorite', methods=['POST'])
@token_required
def add_to_favorites(current_user, doc_id):
    """Ajouter un document aux favoris"""
    try:
        user_id = current_user['id']
        
        print(f"🔍 [FAVORITES ADD] User {user_id} ajoute document {doc_id} aux favoris")
        
        # Vérifier que l'utilisateur a accès au document
        if not has_permission(doc_id, user_id, 'lecture'):
            return jsonify({'error': 'Permission refusée'}), 403
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si le document existe
        cursor.execute("SELECT id, titre FROM document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()
        if not document:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Document non trouvé'}), 404
        
        # Extraire le titre du document en toute sécurité
        doc_title = document['titre'] if document and 'titre' in document else f"Document {doc_id}"
        
        # Ajouter aux favoris (avec gestion des doublons)
        cursor.execute("""
            INSERT INTO favoris (document_id, utilisateur_id)
            VALUES (%s, %s)
            ON CONFLICT (document_id, utilisateur_id) DO NOTHING
        """, (doc_id, user_id))
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        # Enregistrer l'action
        try:
            log_user_action(
                user_id,
                'DOCUMENT_FAVORITE_ADD',
                f"Ajout aux favoris du document '{doc_title}' (ID: {doc_id})",
                request
            )
        except Exception as log_error:
            print(f"⚠️ Erreur lors du logging: {log_error}")
        
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            print(f"✅ [FAVORITES ADD] Document {doc_id} ajouté aux favoris de l'utilisateur {user_id}")
            return jsonify({'message': 'Document ajouté aux favoris', 'is_favorite': True}), 200
        else:
            print(f"ℹ️ [FAVORITES ADD] Document {doc_id} déjà dans les favoris de l'utilisateur {user_id}")
            return jsonify({'message': 'Document déjà dans les favoris', 'is_favorite': True}), 200
            
    except Exception as e:
        print(f"🚨 Erreur lors de l'ajout aux favoris: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de l\'ajout aux favoris'}), 500

@bp.route('/documents/<int:doc_id>/favorite', methods=['DELETE'])
@token_required
def remove_from_favorites(current_user, doc_id):
    """Retirer un document des favoris"""
    try:
        user_id = current_user['id']
        
        print(f"🔍 [FAVORITES REMOVE] User {user_id} retire document {doc_id} des favoris")
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor()
        
        # Récupérer le titre du document pour les logs
        cursor.execute("SELECT titre FROM document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()
        doc_title = document[0] if document else f"Document {doc_id}"
        
        # Supprimer des favoris
        cursor.execute("""
            DELETE FROM favoris 
            WHERE document_id = %s AND utilisateur_id = %s
        """, (doc_id, user_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Document non trouvé dans les favoris', 'is_favorite': False}), 404
        
        conn.commit()
        
        # Enregistrer l'action
        log_user_action(
            user_id,
            'DOCUMENT_FAVORITE_REMOVE',
            f"Suppression des favoris du document '{doc_title}' (ID: {doc_id})",
            request
        )
        
        cursor.close()
        conn.close()
        
        print(f"✅ [FAVORITES REMOVE] Document {doc_id} retiré des favoris de l'utilisateur {user_id}")
        return jsonify({'message': 'Document retiré des favoris', 'is_favorite': False}), 200
        
    except Exception as e:
        print(f"🚨 Erreur lors de la suppression des favoris: {e}")
        return jsonify({'error': 'Erreur lors de la suppression des favoris'}), 500

@bp.route('/documents/<int:doc_id>/favorite/status', methods=['GET'])
@token_required
def check_favorite_status(current_user, doc_id):
    """Vérifier si un document est dans les favoris"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM favoris 
            WHERE document_id = %s AND utilisateur_id = %s
        """, (doc_id, user_id))
        
        is_favorite = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        
        return jsonify({'is_favorite': is_favorite}), 200
        
    except Exception as e:
        print(f"🚨 Erreur lors de la vérification du statut favori: {e}")
        return jsonify({'error': 'Erreur lors de la vérification'}), 500

@bp.route('/documents/<int:doc_id>/ocr', methods=['POST'])
@token_required
def extract_ocr_text(current_user, doc_id):
    """Extraire le texte d'un document via OCR"""
    try:
        user_id = current_user['id']
        
        # Vérifier les permissions
        if not has_permission(doc_id, user_id, 'lecture'):
            return jsonify({'error': 'Accès non autorisé'}), 403

        # Récupérer les paramètres
        data = request.get_json() or {}
        language = data.get('language', 'fra')

        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer les informations du document
        cursor.execute("""
            SELECT titre, fichier, cloudinary_url, mime_type 
            FROM document 
            WHERE id = %s
        """, (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        conn.close()

        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404

        # Vérifier si le document supporte l'OCR
        if not document['mime_type'] or not document['mime_type'].startswith(('image/', 'application/pdf')):
            return jsonify({'error': 'Ce type de document ne supporte pas l\'OCR'}), 400

        # Texte simulé selon la langue
        language_texts = {
            'fra': f"Texte extrait du document '{document['titre']}' (simulation)\n\nCeci est un exemple de texte extrait par OCR depuis le document.\nLangue détectée: Français\nConfiance: 87.3%\n\nContenu analysé:\n- Format: {document['mime_type']}\n- Source: Cloudinary\n- Extraction réussie",
            'eng': f"Text extracted from document '{document['titre']}' (simulation)\n\nThis is an example of OCR extracted text from the document.\nDetected language: English\nConfidence: 87.3%\n\nAnalyzed content:\n- Format: {document['mime_type']}\n- Source: Cloudinary\n- Extraction successful",
            'spa': f"Texto extraído del documento '{document['titre']}' (simulación)\n\nEste es un ejemplo de texto extraído por OCR del documento.\nIdioma detectado: Español\nConfianza: 87.3%\n\nContenido analizado:\n- Formato: {document['mime_type']}\n- Fuente: Cloudinary\n- Extracción exitosa"
        }
        
        extracted_text = language_texts.get(language, language_texts['fra'])
        confidence = 87.3
        
        # Enregistrer l'action
        log_user_action(
            user_id,
            'DOCUMENT_OCR',
            f"Extraction OCR du document '{document['titre']}' (ID: {doc_id}) en {language}",
            request
        )

        return jsonify({
            'success': True,
            'text': extracted_text,
            'confidence': confidence,
            'language': language,
            'document_title': document['titre'],
            'pages_processed': 1,
            'processing_time': 1.8
        }), 200

    except Exception as e:
        print(f"🚨 Erreur lors de l'extraction OCR: {e}")
        return jsonify({'error': 'Erreur lors de l\'extraction OCR'}), 500 

@bp.route('/documents/upload', methods=['POST'])
@token_required
def upload_document_with_notifications(current_user):
    """Upload d'un document avec notifications automatiques"""
    try:
        print("🔍 Début de la fonction upload_document_with_notifications")
        if 'file' not in request.files:
            print("❌ Aucun fichier fourni dans la requête")
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            print("❌ Nom de fichier vide")
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        # Récupérer les métadonnées
        title = request.form.get('titre', file.filename)
        description = request.form.get('description', '')
        categorie = request.form.get('type_document', 'Document')
        service = request.form.get('service', 'GED')
        dossier_id = request.form.get('dossier_id')
        mime_type = request.form.get('mime_type', 'application/octet-stream')
        
        print(f"📄 Métadonnées reçues: titre={title}, description={description}, categorie={categorie}, service={service}, dossier_id={dossier_id}, mime_type={mime_type}")
        
        # Convertir dossier_id
        if dossier_id:
            try:
                dossier_id = int(dossier_id)
                print(f"📁 dossier_id converti en entier: {dossier_id}")
            except ValueError:
                print(f"⚠️ Impossible de convertir dossier_id en entier: {dossier_id}")
                dossier_id = None
        
        # Sauvegarder le fichier (logique simplifiée)
        filename = file.filename
        file_size = len(file.read())  # Calculer la taille du fichier
        file.seek(0)  # Réinitialiser le pointeur du fichier après avoir lu sa taille
        
        print(f"📊 Taille du fichier: {file_size} octets")
        
        # Upload du fichier vers Cloudinary
        from AppFlask.utils.cloudinary_storage import upload_file
        try:
            print("🔄 Début de l'upload vers Cloudinary")
            cloudinary_result = upload_file(file, resource_type="auto")
            cloudinary_url = cloudinary_result.get('secure_url')
            cloudinary_public_id = cloudinary_result.get('public_id')
            print(f"✅ Upload Cloudinary réussi: URL={cloudinary_url}, Public ID={cloudinary_public_id}")
        except Exception as cloud_error:
            print(f"❌ Erreur lors de l'upload vers Cloudinary: {str(cloud_error)}")
            return jsonify({'error': 'Erreur lors de l\'upload vers Cloudinary'}), 500
        
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        print("✅ Connexion à la base de données établie")
        cursor = conn.cursor()
        
        # Insérer le document
        insert_query = """
            INSERT INTO document (titre, fichier, description, categorie, taille, 
                                date_ajout, proprietaire_id, dossier_id, mime_type, 
                                cloudinary_url, cloudinary_public_id)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        query_params = (title, filename, description, categorie, file_size, 
                       current_user['id'], dossier_id, mime_type,
                       cloudinary_url, cloudinary_public_id)
        print(f"🔄 Exécution de la requête SQL: {insert_query}")
        print(f"🔄 Paramètres: {query_params}")
        
        try:
            cursor.execute(insert_query, query_params)
            result = cursor.fetchone()
            document_id = result['id'] if isinstance(result, dict) else result[0]
            print(f"✅ Document inséré avec succès, ID: {document_id}")
            conn.commit()
        except Exception as db_error:
            print(f"❌ Erreur lors de l'insertion en base de données: {str(db_error)}")
            conn.rollback()
            raise db_error
        
        # Envoyer les notifications
        try:
            notification_service.notify_document_uploaded(document_id, current_user['id'])
            log_user_action(current_user['id'], 'DOCUMENT_UPLOAD', 
                          f"Upload du document '{title}' (ID: {document_id})", request)
            print("✅ Notifications envoyées avec succès")
        except Exception as e:
            print(f"⚠️ Erreur notification upload: {str(e)}")
        
        cursor.close()
        conn.close()
        print("✅ Fin de la fonction upload_document_with_notifications")
        
        return jsonify({
            'message': 'Document uploadé avec succès',
            'document_id': document_id,
            'title': title,
            'url': cloudinary_url
        }), 201
        
    except Exception as e:
        print(f"❌ Erreur upload document: {str(e)}")
        print(f"❌ Type d'erreur: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Erreur lors de l\'upload'}), 500

@bp.route('/documents/<int:doc_id>/share', methods=['POST'])
@token_required
def share_document_with_notifications(current_user, doc_id):
    """Partager un document avec notifications"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'ID utilisateur requis'}), 400
        
        shared_with_user_id = data['user_id']
        permissions = data.get('permissions', 'lecture')
        
        # Vérifier les permissions
        if not has_permission(doc_id, current_user['id'], 'admin'):
            return jsonify({'error': 'Permission insuffisante'}), 403
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor()
        
        # Partager le document
        cursor.execute("""
            INSERT INTO partage (document_id, utilisateur_id, permissions, date_partage)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (document_id, utilisateur_id) 
            DO UPDATE SET permissions = EXCLUDED.permissions, date_partage = NOW()
        """, (doc_id, shared_with_user_id, permissions))
        
        conn.commit()
        
        # Envoyer la notification
        try:
            notification_service.notify_document_shared(doc_id, shared_with_user_id, current_user['id'])
            log_user_action(current_user['id'], 'DOCUMENT_SHARE', 
                          f"Partage du document {doc_id} avec l'utilisateur {shared_with_user_id}", request)
        except Exception as e:
            print(f"⚠️ Erreur notification partage: {str(e)}")
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Document partagé avec succès'}), 200
        
    except Exception as e:
        print(f"❌ Erreur partage document: {str(e)}")
        return jsonify({'error': 'Erreur lors du partage'}), 500

# ================================
# ROUTES ABONNEMENTS NOTIFICATIONS
# ================================

@bp.route('/documents/<int:doc_id>/subscription', methods=['GET'])
@token_required
def get_document_subscription(current_user, doc_id):
    """Vérifier l'abonnement aux notifications d'un document"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier l'abonnement
        cursor.execute("""
            SELECT * FROM document_subscriptions 
            WHERE user_id = %s AND document_id = %s
        """, (user_id, doc_id))
        
        subscription = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'is_subscribed': subscription is not None,
            'subscription': dict(subscription) if subscription else None
        }), 200
        
    except Exception as e:
        print(f"🚨 Erreur vérification abonnement: {e}")
        return jsonify({'error': 'Erreur lors de la vérification'}), 500

@bp.route('/documents/<int:doc_id>/subscribe', methods=['POST'])
@token_required
def subscribe_to_document(current_user, doc_id):
    """S'abonner aux notifications d'un document"""
    try:
        user_id = current_user['id']
        data = request.get_json() or {}
        notification_types = data.get('notification_types', ['all'])
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor()
        
        # Créer ou mettre à jour l'abonnement
        cursor.execute("""
            INSERT INTO document_subscriptions 
            (user_id, document_id, notification_types, is_active, created_at)
            VALUES (%s, %s, %s, true, NOW())
            ON CONFLICT (user_id, document_id) 
            DO UPDATE SET 
                notification_types = EXCLUDED.notification_types,
                is_active = true,
                updated_at = NOW()
        """, (user_id, doc_id, notification_types))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Abonnement créé avec succès'}), 201
        
    except Exception as e:
        print(f"🚨 Erreur abonnement: {e}")
        return jsonify({'error': 'Erreur lors de l\'abonnement'}), 500

@bp.route('/documents/<int:doc_id>/subscription', methods=['PUT'])
@token_required
def update_document_subscription(current_user, doc_id):
    """Mettre à jour l'abonnement aux notifications d'un document"""
    try:
        user_id = current_user['id']
        data = request.get_json() or {}
        notification_types = data.get('notification_types', ['all'])
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor()
        
        # Mettre à jour l'abonnement
        cursor.execute("""
            UPDATE document_subscriptions 
            SET notification_types = %s, updated_at = NOW()
            WHERE user_id = %s AND document_id = %s
        """, (notification_types, user_id, doc_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Abonnement non trouvé'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Abonnement mis à jour avec succès'}), 200
        
    except Exception as e:
        print(f"🚨 Erreur mise à jour abonnement: {e}")
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 500

@bp.route('/documents/<int:doc_id>/unsubscribe', methods=['DELETE'])
@token_required
def unsubscribe_from_document(current_user, doc_id):
    """Se désabonner des notifications d'un document"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor()
        
        # Supprimer l'abonnement
        cursor.execute("""
            DELETE FROM document_subscriptions 
            WHERE user_id = %s AND document_id = %s
        """, (user_id, doc_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Abonnement non trouvé'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Désabonnement effectué avec succès'}), 200
        
    except Exception as e:
        print(f"🚨 Erreur désabonnement: {e}")
        return jsonify({'error': 'Erreur lors du désabonnement'}), 500

@bp.route('/documents/my-subscriptions', methods=['GET'])
@token_required
def get_my_subscriptions(current_user):
    """Récupérer tous les abonnements de l'utilisateur"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les abonnements avec les informations des documents
        cursor.execute("""
            SELECT ds.*, d.titre as document_title
            FROM document_subscriptions ds
            JOIN document d ON ds.document_id = d.id
            WHERE ds.user_id = %s
            ORDER BY ds.created_at DESC
        """, (user_id,))
        
        subscriptions = cursor.fetchall()
        
        # Convertir les dates
        for sub in subscriptions:
            if sub['created_at']:
                sub['created_at'] = sub['created_at'].isoformat() if hasattr(sub['created_at'], 'isoformat') else str(sub['created_at'])
            if sub['updated_at']:
                sub['updated_at'] = sub['updated_at'].isoformat() if hasattr(sub['updated_at'], 'isoformat') else str(sub['updated_at'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'subscriptions': [dict(sub) for sub in subscriptions]
        }), 200
        
    except Exception as e:
        print(f"🚨 Erreur récupération abonnements: {e}")
        return jsonify({'error': 'Erreur lors de la récupération'}), 500

@bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@token_required
def delete_document(current_user, doc_id):
    """Supprimer un document (déplacer vers la corbeille)"""
    try:
        from AppFlask.utils.trash_manager import move_document_to_trash
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier que le document existe et appartient à l'utilisateur ou que l'utilisateur est admin
        cursor.execute("""
            SELECT * FROM document 
            WHERE id = %s AND (proprietaire_id = %s OR %s = true)
        """, (doc_id, current_user['id'], current_user['role'].lower() == 'admin'))
        
        document = cursor.fetchone()
        if not document:
            return jsonify({'message': 'Document non trouvé ou accès refusé'}), 404
        
        cursor.close()
        conn.close()
        
        # Déplacer vers la corbeille au lieu de supprimer définitivement
        deletion_reason = request.json.get('reason', 'Suppression par l\'utilisateur') if request.is_json else 'Suppression par l\'utilisateur'
        success = move_document_to_trash(doc_id, current_user['id'], deletion_reason)
        
        if not success:
            return jsonify({'message': 'Erreur lors du déplacement vers la corbeille'}), 500
        
        # Log de l'action
        log_user_action(
            current_user['id'],
            'MOVE_TO_TRASH',
            f"Document déplacé vers la corbeille: {document['titre']}",
            request
        )
        
        return jsonify({'message': 'Document déplacé vers la corbeille avec succès'}), 200
        
    except Exception as e:
        print(f"🚨 Erreur suppression document: {e}")
        return jsonify({'message': 'Erreur lors de la suppression du document'}), 500
