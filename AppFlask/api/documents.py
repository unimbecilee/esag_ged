from flask import Blueprint, request, jsonify, send_from_directory, current_app
from AppFlask.db import db_connection
from .auth import token_required, log_user_action
from psycopg2.extras import RealDictCursor

bp = Blueprint('api_documents', __name__)
import os
import json
from datetime import datetime

def has_permission(doc_id, user_id, required_permission='lecture'):
    """Vérifier les permissions de l'utilisateur sur un document"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer le propriétaire
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

@bp.route('/documents/my', methods=['GET'])
@token_required  
def get_my_documents(current_user):
    """Récupérer les documents de l'utilisateur connecté"""
    try:
        user_id = current_user['id']
        dossier_id = request.args.get('dossier_id')
        
        print(f"🔍 [API DEBUG] user_id: {user_id}, dossier_id reçu: '{dossier_id}'")
        
        # Convertir dossier_id en None si vide ou invalide
        if dossier_id == '' or dossier_id is None:
            dossier_id = None
        else:
            try:
                dossier_id = int(dossier_id)
            except ValueError:
                dossier_id = None
        
        print(f"🔍 [API DEBUG] dossier_id après conversion: {dossier_id}")
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Query pour les documents de l'utilisateur avec filtrage par dossier
        if dossier_id is None:
            # Documents à la racine (sans dossier)
            query = """
                SELECT d.id, d.titre, d.description, d.date_ajout as date_creation,
                       d.derniere_modification, d.taille, d.categorie as type_document,
                       d.dossier_id,
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
            print(f"🔍 [API DEBUG] Requête racine avec user_id: {user_id}")
            cursor.execute(query, (user_id,))
        else:
            # Documents dans un dossier spécifique
            query = """
                SELECT d.id, d.titre, d.description, d.date_ajout as date_creation,
                       d.derniere_modification, d.taille, d.categorie as type_document,
                       d.dossier_id,
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
            print(f"🔍 [API DEBUG] Requête dossier avec user_id: {user_id}, dossier_id: {dossier_id}")
            cursor.execute(query, (user_id, dossier_id))

        documents = cursor.fetchall()
        print(f"🔍 [API DEBUG] Nombre de documents trouvés: {len(documents)}")
        
        for doc in documents:
            print(f"🔍 [API DEBUG] Doc ID: {doc['id']}, Titre: {doc['titre']}, Dossier: {doc['dossier_id']}")
        
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

@bp.route('/documents/<int:doc_id>', methods=['GET'])
@token_required
def get_document_by_id(current_user, doc_id):
    """Récupérer un document spécifique par son ID"""
    try:
        user_id = current_user['id']
        
        # Vérifier les permissions
        if not has_permission(doc_id, user_id, 'lecture'):
            return jsonify({'error': 'Accès non autorisé'}), 403

        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer le document avec les informations du propriétaire
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

        # Convertir les résultats en dictionnaire
        doc_dict = dict(document)
        
        # Formatage des dates
        if doc_dict.get('date_creation'):
            doc_dict['date_creation'] = doc_dict['date_creation'].isoformat()
        if doc_dict.get('derniere_modification'):
            doc_dict['derniere_modification'] = doc_dict['derniere_modification'].isoformat()
        
        return jsonify(doc_dict), 200

    except Exception as e:
        print(f"Erreur lors de la récupération du document: {e}")
        return jsonify({'error': 'Erreur lors de la récupération du document'}), 500

@bp.route('/documents/<int:doc_id>/download', methods=['GET'])
@token_required
def download_document_api(current_user, doc_id):
    """Télécharger un document via API (Cloudinary)"""
    try:
        user_id = current_user['id']
        
        # Vérifier les permissions
        if not has_permission(doc_id, user_id, 'lecture'):
            return jsonify({'error': 'Permission refusée'}), 403

        conn = db_connection()
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

        # Priorité à l'URL Cloudinary, sinon fallback sur fichier local
        if doc.get('cloudinary_url'):
            # Enregistrer l'action de téléchargement
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
            # Fallback sur fichier local
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
        print(f"Erreur lors du téléchargement: {e}")
        return jsonify({'error': 'Erreur lors du téléchargement'}), 500

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
        language = data.get('language', 'fra')  # Français par défaut

        conn = db_connection()
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

        # Simuler l'extraction OCR (fonctionnalité basique)
        # En réalité, il faudrait télécharger le fichier depuis Cloudinary et utiliser Tesseract
        
        # Pour l'instant, retourner un texte simulé
        extracted_text = f"Texte extrait du document '{document['titre']}' (simulation)\n\nCeci est un exemple de texte extrait par OCR depuis le document.\nLangue détectée: {language}\nConfiance: 85.5%"
        confidence = 85.5
        
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
            'document_title': document['titre']
        }), 200

    except Exception as e:
        print(f"Erreur lors de l'extraction OCR: {e}")
        return jsonify({'error': 'Erreur lors de l\'extraction OCR'}), 500

@bp.route('/documents/<int:doc_id>', methods=['DELETE'])
@token_required
def delete_document_api(current_user, doc_id):
    """Supprimer un document via API"""
    try:
        user_id = current_user['id']
        
        # Vérifier les permissions
        if not has_permission(doc_id, user_id, 'admin'):
            return jsonify({'error': 'Permission refusée'}), 403

        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 1. Récupérer les infos du document
        cursor.execute("SELECT * FROM document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()

        if not document:
            cursor.close()
            conn.close()
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
                'fichier': document.get('fichier'),
                'taille': document.get('taille'),
                'description': document.get('description')
            }),
            user_id
        ))

        # 3. Supprimer définitivement le document (pas de colonne statut)
        cursor.execute("DELETE FROM document WHERE id = %s", (doc_id,))
        
        conn.commit()
        cursor.close()
        conn.close()

        # Enregistrer l'action de suppression
        log_user_action(
            user_id, 
            'DOCUMENT_DELETE_API', 
            f"Suppression API du document '{document['titre']}' (ID: {doc_id})",
            request
        )

        return jsonify({'message': 'Document supprimé avec succès'}), 200

    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")
        return jsonify({'error': 'Erreur lors de la suppression'}), 500

@bp.route('/documents/share', methods=['POST'])
@token_required
def share_document_api(current_user):
    """Partager un document via API"""
    try:
        user_id = current_user['id']
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

@bp.route('/users/sharing', methods=['GET'])
@token_required
def get_users_for_sharing(current_user):
    """Récupérer la liste des utilisateurs pour le partage"""
    try:
        current_user_id = current_user['id']
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer tous les utilisateurs sauf l'utilisateur actuel
        cursor.execute("""
            SELECT id, nom, prenom, email, username
            FROM utilisateur 
            WHERE id != %s
            ORDER BY nom, prenom
        """, (current_user_id,))
        
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(users), 200

    except Exception as e:
        print(f"Erreur lors de la récupération des utilisateurs: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des utilisateurs'}), 500

@bp.route('/documents/recent-activities', methods=['GET'])
@token_required
def get_recent_activities(current_user):
    """Récupérer les activités récentes des documents"""
    try:
        user_id = current_user['id']
        limit = request.args.get('limit', 10, type=int)
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les activités récentes liées aux documents
        query = """
            SELECT 
                h.id,
                h.entity_id as document_id,
                h.entity_name as document_title,
                h.action_type as action,
                h.description as action_description,
                h.created_at as timestamp,
                CONCAT(u.prenom, ' ', u.nom) as user,
                d.categorie as document_type,
                CASE 
                    WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                    WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                    WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                    ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                END as size
            FROM history h
            LEFT JOIN utilisateur u ON h.user_id = u.id
            LEFT JOIN document d ON h.entity_id = d.id
            WHERE h.entity_type = 'document' 
            AND (h.user_id = %s OR d.proprietaire_id = %s OR EXISTS (
                SELECT 1 FROM partage p 
                WHERE p.document_id = d.id AND p.utilisateur_id = %s
            ))
            ORDER BY h.created_at DESC
            LIMIT %s
        """
        
        cursor.execute(query, (user_id, user_id, user_id, limit))
        activities = cursor.fetchall()
        
        # Formatter les résultats pour correspondre à l'interface frontend
        formatted_activities = []
        for activity in activities:
            # Mapper les types d'actions pour correspondre au frontend
            action_mapping = {
                'create': 'EDIT',
                'upload': 'EDIT', 
                'view': 'VIEW',
                'download': 'DOWNLOAD',
                'share': 'SHARE',
                'delete': 'DELETE',
                'edit': 'EDIT',
                'update': 'EDIT'
            }
            
            formatted_activity = {
                'id': activity['id'],
                'document_id': activity['document_id'],
                'document_title': activity['document_title'] or 'Document sans titre',
                'document_type': (activity['document_type'] or 'DOC').upper(),
                'action': action_mapping.get(activity['action'], 'VIEW'),
                'action_description': activity['action_description'] or 'Action sur le document',
                'user': activity['user'] or 'Utilisateur inconnu',
                'timestamp': activity['timestamp'].isoformat() if activity['timestamp'] else datetime.now().isoformat(),
                'size': activity['size'] or '0 B'
            }
            formatted_activities.append(formatted_activity)
        
        cursor.close()
        conn.close()
        
        return jsonify({'activities': formatted_activities}), 200
        
    except Exception as e:
        print(f"Erreur lors de la récupération des activités récentes: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des activités récentes'}), 500

@bp.route('/documents/recent-activities', methods=['DELETE'])
@token_required
def clear_recent_activities(current_user):
    """Vider l'historique des activités récentes de l'utilisateur"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        cursor = conn.cursor()
        
        # Supprimer les entrées d'historique de l'utilisateur pour les documents
        cursor.execute("""
            DELETE FROM history 
            WHERE user_id = %s AND entity_type = 'document'
        """, (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Historique des activités supprimé avec succès'}), 200
        
    except Exception as e:
        print(f"Erreur lors de la suppression de l'historique: {e}")
        return jsonify({'error': 'Erreur lors de la suppression de l\'historique'}), 500

@bp.route('/documents/favorites', methods=['GET'])
@token_required
def get_favorite_documents(current_user):
    """Récupérer les documents favoris de l'utilisateur"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les documents favoris avec leurs informations complètes
        query = """
            SELECT 
                d.id,
                d.titre,
                d.categorie as type_document,
                d.date_ajout as date_creation,
                d.derniere_modification,
                d.taille,
                CASE 
                    WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                    WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                    WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                    ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                END as taille_formatee,
                'actif' as statut,
                f.date_ajout as date_favori,
                u.prenom as proprietaire_prenom,
                u.nom as proprietaire_nom
            FROM favoris f
            JOIN document d ON f.document_id = d.id
            JOIN utilisateur u ON d.proprietaire_id = u.id
            WHERE f.utilisateur_id = %s
            ORDER BY f.date_ajout DESC
        """
        
        cursor.execute(query, (user_id,))
        favorites = cursor.fetchall()
        
        # Convertir les dates en format ISO pour la compatibilité frontend
        formatted_favorites = []
        for fav in favorites:
            formatted_fav = dict(fav)
            if formatted_fav['date_creation']:
                formatted_fav['date_creation'] = formatted_fav['date_creation'].isoformat() if hasattr(formatted_fav['date_creation'], 'isoformat') else str(formatted_fav['date_creation'])
            if formatted_fav['derniere_modification']:
                formatted_fav['derniere_modification'] = formatted_fav['derniere_modification'].isoformat() if hasattr(formatted_fav['derniere_modification'], 'isoformat') else str(formatted_fav['derniere_modification'])
            if formatted_fav['date_favori']:
                formatted_fav['date_favori'] = formatted_fav['date_favori'].isoformat() if hasattr(formatted_fav['date_favori'], 'isoformat') else str(formatted_fav['date_favori'])
            formatted_favorites.append(formatted_fav)
        
        cursor.close()
        conn.close()
        
        return jsonify(formatted_favorites), 200
        
    except Exception as e:
        print(f"Erreur lors de la récupération des favoris: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des documents favoris'}), 500

@bp.route('/documents/<int:doc_id>/favorite', methods=['POST'])
@token_required
def add_to_favorites(current_user, doc_id):
    """Ajouter un document aux favoris"""
    try:
        user_id = current_user['id']
        
        # Vérifier que l'utilisateur a accès au document
        if not has_permission(doc_id, user_id, 'lecture'):
            return jsonify({'error': 'Permission refusée'}), 403
        
        conn = db_connection()
        cursor = conn.cursor()
        
        # Vérifier si le document existe
        cursor.execute("SELECT id FROM document WHERE id = %s", (doc_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Document non trouvé'}), 404
        
        # Ajouter aux favoris (avec gestion des doublons)
        try:
            cursor.execute("""
                INSERT INTO favoris (document_id, utilisateur_id)
                VALUES (%s, %s)
                ON CONFLICT (document_id, utilisateur_id) DO NOTHING
            """, (doc_id, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'message': 'Document ajouté aux favoris'}), 200
            
        except Exception as e:
            cursor.close()
            conn.close()
            if 'duplicate key' in str(e):
                return jsonify({'message': 'Document déjà dans les favoris'}), 200
            raise e
            
    except Exception as e:
        print(f"Erreur lors de l'ajout aux favoris: {e}")
        return jsonify({'error': 'Erreur lors de l\'ajout aux favoris'}), 500

@bp.route('/documents/<int:doc_id>/favorite', methods=['DELETE'])
@token_required
def remove_from_favorites(current_user, doc_id):
    """Retirer un document des favoris"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        cursor = conn.cursor()
        
        # Supprimer des favoris
        cursor.execute("""
            DELETE FROM favoris 
            WHERE document_id = %s AND utilisateur_id = %s
        """, (doc_id, user_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Document non trouvé dans les favoris'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Document retiré des favoris'}), 200
        
    except Exception as e:
        print(f"Erreur lors de la suppression des favoris: {e}")
        return jsonify({'error': 'Erreur lors de la suppression des favoris'}), 500

@bp.route('/documents/<int:doc_id>/favorite/status', methods=['GET'])
@token_required
def check_favorite_status(current_user, doc_id):
    """Vérifier si un document est dans les favoris"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
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
        print(f"Erreur lors de la vérification du statut favori: {e}")
        return jsonify({'error': 'Erreur lors de la vérification'}), 500

@bp.route('/documents/search/advanced', methods=['GET'])
@token_required
def advanced_search_documents(current_user):
    """Recherche avancée de documents avec filtres multiples"""
    try:
        user_id = current_user['id']
        user_role = current_user.get('role', 'user')
        
        # Récupération des paramètres de recherche
        document_types = request.args.get('documentTypes', '').split(',') if request.args.get('documentTypes') else []
        owners = request.args.get('owners', '').split(',') if request.args.get('owners') else []
        tags = request.args.get('tags', '').split(',') if request.args.get('tags') else []
        status = request.args.get('status', '').split(',') if request.args.get('status') else []
        start_date = request.args.get('startDate', '')
        end_date = request.args.get('endDate', '')
        min_size = request.args.get('minSize', '0')
        max_size = request.args.get('maxSize', '100')
        has_attachments = request.args.get('hasAttachments', 'false').lower() == 'true'
        is_shared = request.args.get('isShared', 'false').lower() == 'true'
        is_favorite = request.args.get('isFavorite', 'false').lower() == 'true'
        search_term = request.args.get('searchTerm', '')
        content_search = request.args.get('contentSearch', '')
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Construction de la requête SQL dynamique
        base_query = """
            SELECT DISTINCT
                d.id,
                d.titre,
                d.categorie as type_document,
                d.date_ajout as date_creation,
                d.derniere_modification,
                d.taille,
                CASE 
                    WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                    WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                    WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                    ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                END as taille_formatee,
                'actif' as statut,
                u.prenom as proprietaire_prenom,
                u.nom as proprietaire_nom,
                CASE 
                    WHEN f.id IS NOT NULL THEN 1.0
                    ELSE 0.8
                END as relevance_score
            FROM document d
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            LEFT JOIN favoris f ON d.id = f.document_id AND f.utilisateur_id = %s
            LEFT JOIN partage p ON d.id = p.document_id
        """
        
        conditions = []
        params = [user_id]
        
        # Condition de permissions (utilisateur propriétaire ou document partagé)
        if user_role.lower() != 'admin':
            conditions.append("(d.proprietaire_id = %s OR p.utilisateur_id = %s)")
            params.extend([user_id, user_id])
        
        # Filtre par terme de recherche général
        if search_term:
            conditions.append("(LOWER(d.titre) LIKE LOWER(%s) OR LOWER(d.description) LIKE LOWER(%s))")
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
        
        # Filtre par types de documents
        if document_types and document_types != ['']:
            type_conditions = []
            for doc_type in document_types:
                if doc_type:  # Ignore les valeurs vides
                    type_conditions.append("LOWER(d.categorie) LIKE LOWER(%s)")
                    params.append(f"%{doc_type}%")
            if type_conditions:
                conditions.append(f"({' OR '.join(type_conditions)})")
        
        # Filtre par propriétaires
        if owners and owners != ['']:
            owner_conditions = []
            for owner in owners:
                if owner:  # Ignore les valeurs vides
                    owner_conditions.append("(LOWER(u.nom) LIKE LOWER(%s) OR LOWER(u.prenom) LIKE LOWER(%s) OR LOWER(CONCAT(u.prenom, ' ', u.nom)) LIKE LOWER(%s))")
                    owner_pattern = f"%{owner}%"
                    params.extend([owner_pattern, owner_pattern, owner_pattern])
            if owner_conditions:
                conditions.append(f"({' OR '.join(owner_conditions)})")
        
        # Filtre par plage de dates
        if start_date:
            conditions.append("d.date_ajout >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("d.date_ajout <= %s")
            params.append(end_date)
        
        # Filtre par taille (conversion MB en bytes pour la comparaison)
        try:
            min_size_bytes = int(float(min_size) * 1024 * 1024)  # MB vers bytes
            max_size_bytes = int(float(max_size) * 1024 * 1024)  # MB vers bytes
            
            if min_size_bytes > 0:
                conditions.append("d.taille >= %s")
                params.append(min_size_bytes)
            
            if max_size_bytes < 100 * 1024 * 1024:  # Si moins de 100MB
                conditions.append("d.taille <= %s")
                params.append(max_size_bytes)
        except (ValueError, TypeError):
            pass  # Ignore les erreurs de conversion
        
        # Filtre pour les documents partagés
        if is_shared:
            conditions.append("p.id IS NOT NULL")
        
        # Filtre pour les documents favoris
        if is_favorite:
            conditions.append("f.id IS NOT NULL")
        
        # Construire la requête finale
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        else:
            where_clause = " WHERE 1=1"
        
        final_query = base_query + where_clause + " ORDER BY relevance_score DESC, d.date_ajout DESC LIMIT 100"
        
        cursor.execute(final_query, params)
        documents = cursor.fetchall()
        
        # Formater les résultats
        formatted_results = []
        for doc in documents:
            formatted_doc = dict(doc)
            if formatted_doc['date_creation']:
                formatted_doc['date_creation'] = formatted_doc['date_creation'].isoformat() if hasattr(formatted_doc['date_creation'], 'isoformat') else str(formatted_doc['date_creation'])
            if formatted_doc['derniere_modification']:
                formatted_doc['derniere_modification'] = formatted_doc['derniere_modification'].isoformat() if hasattr(formatted_doc['derniere_modification'], 'isoformat') else str(formatted_doc['derniere_modification'])
            formatted_results.append(formatted_doc)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'results': formatted_results,
            'total': len(formatted_results),
            'filters_applied': {
                'document_types': document_types,
                'owners': owners,
                'date_range': {'start': start_date, 'end': end_date},
                'size_range': {'min': min_size, 'max': max_size},
                'is_shared': is_shared,
                'is_favorite': is_favorite,
                'search_term': search_term
            }
        }), 200
        
    except Exception as e:
        print(f"Erreur lors de la recherche avancée: {e}")
        return jsonify({'error': 'Erreur lors de la recherche avancée', 'details': str(e)}), 500

@bp.route('/documents/search/simple', methods=['GET'])
@token_required
def simple_search_documents(current_user):
    """Recherche simple dans les documents"""
    try:
        search_term = request.args.get('search', '').strip()
        if not search_term:
            return jsonify([]), 200

        user_id = current_user['id']
        admin_mode = request.args.get('admin_mode', 'false').lower() == 'true'
        is_admin = current_user.get('role', '').lower() == 'admin'

        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Construction de la requête de base
        if admin_mode and is_admin:
            base_query = """
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
                WHERE (
                    d.titre ILIKE %s 
                    OR d.description ILIKE %s
                    OR u.nom ILIKE %s
                    OR u.prenom ILIKE %s
                )
                ORDER BY d.date_creation DESC
                LIMIT 50
            """
            search_pattern = f'%{search_term}%'
            cursor.execute(base_query, (search_pattern, search_pattern, search_pattern, search_pattern))
        else:
            base_query = """
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
                WHERE (
                    d.titre ILIKE %s 
                    OR d.description ILIKE %s
                ) AND d.proprietaire_id = %s
                ORDER BY d.date_creation DESC
                LIMIT 50
            """
            search_pattern = f'%{search_term}%'
            cursor.execute(base_query, (search_pattern, search_pattern, user_id))

        documents = cursor.fetchall()
        cursor.close()
        conn.close()

        # Formatage des dates
        for doc in documents:
            if doc['date_creation']:
                doc['date_creation'] = doc['date_creation'].isoformat() if hasattr(doc['date_creation'], 'isoformat') else str(doc['date_creation'])
            if doc['derniere_modification']:
                doc['derniere_modification'] = doc['derniere_modification'].isoformat() if hasattr(doc['derniere_modification'], 'isoformat') else str(doc['derniere_modification'])

        return jsonify(documents), 200

    except Exception as e:
        print(f"Erreur lors de la recherche simple: {e}")
        return jsonify({'error': 'Erreur lors de la recherche'}), 500 