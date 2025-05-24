from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, session, current_app, send_file, Response, abort, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from AppFlask.db import db_connection
from AppFlask.utils.cloudinary_storage import upload_file, get_file_url, delete_file
from AppFlask.api.auth import token_required
import mimetypes
import mammoth
import os
import logging
from docx import Document
from io import BytesIO
import traceback
from psycopg2.extras import RealDictCursor
from AppFlask.routes.history_routes import log_action
import json

# Configuration du logging
logger = logging.getLogger(__name__)

document_bp = Blueprint('document', __name__)

@document_bp.app_context_processor
def inject_permissions():
    return dict(has_permission=has_permission)

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'txt', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_document_by_id(doc_id):
    """Récupère un document depuis la base de données par son ID"""
    try:
        conn = db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT id, titre, description, date_ajout, fichier 
                FROM document 
                WHERE id = %s
            """, (doc_id,))
            doc = cursor.fetchone()
            return doc
    except Exception as e:
        print(f"Erreur lors de la récupération du document: {e}")
        return None
    finally:    
        conn.close()
        
def has_permission(doc_id, user_id, required_permission='lecture'):
    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Récupérer le propriétaire
        cursor.execute("SELECT proprietaire_id FROM Document WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()

        if doc is None:
            return False

        # L'utilisateur est propriétaire → tous les droits
        if doc[0] == int(user_id):
            return True

        # Sinon, vérifier dans la table Partage
        cursor.execute("""
            SELECT permissions FROM Partage
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
        elif required_permission == 'edition' and partage[0] in ('édition', 'admin'):
            return True
        elif required_permission == 'admin' and partage[0] == 'admin':
            return True

        return False

    except Exception as e:
        print(f"Erreur dans has_permission: {e}")
        return False

# Upload de document
@document_bp.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné', 'danger')
        return redirect(url_for('document.list_documents'))

    file = request.files['file']
    titre = request.form.get('title') or file.filename
    description = request.form.get('description', '')
    categorie = request.form.get('categorie', '')
    service = request.form.get('service', 'Non défini')

    if file.filename == '' or not allowed_file(file.filename):
        flash('Type de fichier non autorisé ou fichier manquant', 'danger')
        return redirect(url_for('document.list_documents'))

    try:
        filename = secure_filename(file.filename)
        logger.info(f"Début de l'upload pour le fichier: {filename}")
        
        # Lecture du contenu du fichier
        file_content = file.read()
        file_size = len(file_content)
        mime_type = file.content_type or mimetypes.guess_type(filename)[0]

        # Upload vers Cloudinary
        public_id = f"documents/{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        logger.info(f"Tentative d'upload vers Cloudinary avec public_id: {public_id}")
        
        cloudinary_response = upload_file(
            file_content,
            public_id=public_id,
            resource_type="auto"
        )
        logger.info(f"Réponse Cloudinary: {cloudinary_response}")

        conn = db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO document (
                titre,
                description,
                categorie,
                fichier,
                mime_type,
                taille,
                service,
                proprietaire_id,
                date_ajout,
                derniere_modification,
                modifie_par,
                cloudinary_url,
                cloudinary_public_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, %s, %s
            ) RETURNING id
        """
        cursor.execute(query, (
            titre,
            description,
            categorie,
            filename,
            mime_type,
            cloudinary_response['bytes'],
            service,
            session.get('user_id'),
            session.get('user_id'),
            cloudinary_response['url'],
            cloudinary_response['public_id']
        ))
        
        document_id = cursor.fetchone()[0]
        conn.commit()

        # Vérifier que l'insertion a bien fonctionné
        cursor.execute("SELECT cloudinary_url FROM document WHERE id = %s", (document_id,))
        result = cursor.fetchone()
        logger.info(f"URL enregistrée en base: {result[0] if result else 'None'}")

        cursor.close()
        conn.close()

        # Enregistrer l'action
        enregistrer_action(session['user_id'], document_id, 'upload')
        
        flash('Document uploadé avec succès', 'success')
        return redirect(url_for('document.list_documents'))

    except Exception as e:
        logger.error(f"Erreur lors de l'upload: {str(e)}")
        # Si une erreur survient après l'upload Cloudinary mais avant l'enregistrement en base
        if 'cloudinary_response' in locals() and cloudinary_response.get('public_id'):
            try:
                delete_file(cloudinary_response['public_id'])
                logger.info(f"Fichier supprimé de Cloudinary après erreur: {cloudinary_response['public_id']}")
            except Exception as del_error:
                logger.error(f"Erreur lors de la suppression du fichier Cloudinary: {str(del_error)}")
        
        flash(f'Erreur lors de l\'upload du fichier : {str(e)}', 'danger')
        return redirect(url_for('document.list_documents'))

# Ouvrir un pdf
@document_bp.route('/<int:doc_id>')
def open_document(doc_id):
    user_id = current_user.get_id()

    # Vérification des permissions
    if not has_permission(doc_id, user_id, 'lecture') and session.get('user_role') != 'Admin':
        flash("Vous n'avez pas la permission d'accéder à ce document.", "danger")
        return redirect(url_for('document.list_documents'))

    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM document WHERE id = %s
        """, (doc_id,))
        doc = cursor.fetchone()
        cursor.close()
        conn.close()

        if not doc:
            abort(404)

        # Rediriger vers l'URL Cloudinary
        return redirect(doc['cloudinary_url'])

    except Exception as e:
        logger.error(f"Erreur lors de l'ouverture du document: {str(e)}")
        flash("Erreur lors de l'ouverture du document.", "danger")
        return redirect(url_for('document.list_documents'))

@document_bp.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# Liste des documents
@document_bp.route('/')
def list_documents():
    if 'user_id' not in session:
        flash('Vous devez être connecté pour voir vos documents.', 'danger')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    user_role = session.get('user_role', '').lower()
    
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # 🔹 Filtrage optionnel par catégorie
        categorie = request.args.get('categorie')
        
        # Construction de la requête de base
        if user_role == 'admin':
            # L'admin voit tous les documents
            base_query = """
                SELECT d.*, u.nom as proprietaire_nom, u.prenom as proprietaire_prenom 
                FROM Document d
                LEFT JOIN Utilisateur u ON d.proprietaire_id = u.id
            """
            if categorie:
                query = base_query + " WHERE categorie = %s"
                cursor.execute(query, (categorie,))
            else:
                cursor.execute(base_query)
        else:
            # Les utilisateurs normaux ne voient que leurs documents et ceux partagés avec eux
            base_query = """
                SELECT d.*, u.nom as proprietaire_nom, u.prenom as proprietaire_prenom 
                FROM Document d
                LEFT JOIN Utilisateur u ON d.proprietaire_id = u.id
                WHERE d.proprietaire_id = %s 
                OR d.id IN (SELECT document_id FROM Partage WHERE utilisateur_id = %s)
            """
            if categorie:
                query = base_query + " AND d.categorie = %s"
                cursor.execute(query, (user_id, user_id, categorie))
            else:
                cursor.execute(base_query, (user_id, user_id))

        documents = cursor.fetchall()

        # 🔹 Utilisateurs (sauf soi-même)
        cursor.execute("SELECT id, nom, prenom FROM Utilisateur WHERE id != %s", (user_id,))
        utilisateurs = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'document_list.html',
            documents=documents,
            utilisateurs=utilisateurs,
            has_permission=has_permission,
            user_id=user_id,
            user_role=user_role
        )
    
    except Exception as e:
        flash(f'Erreur lors de la récupération des documents : {str(e)}', 'danger')
        return redirect(url_for('dashboard.home'))

@document_bp.route('/upload')
def upload_form():
    return render_template('documents.html')

# Téléchargement d'un document
@document_bp.route('/download/<int:doc_id>')
def download_document(doc_id):
    if not has_permission(doc_id, current_user.get_id(), 'lecture'):
        flash("Vous n'avez pas l'autorisation de télécharger ce document.", "danger")
        return redirect(url_for('document.list_documents'))

    conn = db_connection()
    cursor = conn.cursor(dictionary=True)

    # Utilisation correcte de %s pour MySQL
    cursor.execute("SELECT titre FROM document WHERE id=%s", (doc_id,))
    doc = cursor.fetchone()
    cursor.close()
    conn.close()

    if doc:
        titre = doc['titre']  

        # Vérifier si le fichier existe avant d'envoyer
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], titre)
        if not os.path.exists(file_path):
            flash("Le fichier n'existe pas sur le serveur.", "danger")
            return redirect(url_for('document_bp.list_documents'))

        return send_from_directory(current_app.config['UPLOAD_FOLDER'], titre, as_attachment=True)
    
    flash("Document non trouvé.", "danger")
    return redirect(url_for('document_bp.list_documents'))

@document_bp.route('/delete/<int:doc_id>', methods=['GET'])
def delete_document(doc_id):
    if not has_permission(doc_id, current_user.get_id(), 'admin'):
        flash("Vous n'avez pas la permission de supprimer ce document.", "danger")
        return redirect(url_for('document.list_documents'))
    
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Récupérer les infos du document
        cursor.execute("SELECT * FROM Document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()

        if not document:
            flash("Document introuvable.", "danger")
            return redirect(url_for('document.list_documents'))

        # 2. Insérer dans la table Corbeille (copie des infos importantes)
        cursor.execute("""
            INSERT INTO Corbeille (document_id, utilisateur_id, date_suppression, titre, fichier, taille, description)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s)
        """, (
            doc_id,
            session.get('user_id'),
            document['titre'],
            document['fichier'],
            document['taille'],
            document['description']
        ))

        # 3. Supprimer de la table Document
        cursor.execute("DELETE FROM Document WHERE id = %s", (doc_id,))
        conn.commit()
        
        # Enregistrer l'action
        enregistrer_action(session['user_id'], doc_id, 'suppression')

        flash("Document déplacé vers la corbeille avec succès.", "success")

    except Exception as e:
        flash(f"Erreur lors de la suppression du document : {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('document.list_documents'))

@document_bp.route('/partager', methods=['POST'])
def share_document():
    try:
        doc_id = request.form.get("document_id")
        utilisateur_id = request.form.get("utilisateur_id")
        permissions = request.form.get("permissions")

        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Partage (document_id, utilisateur_id, permissions)
            VALUES (%s, %s, %s)
        """, (doc_id, utilisateur_id, permissions))

        conn.commit()
        cursor.close()
        conn.close()
        
        # Enregistrer l'action
        enregistrer_action(session['user_id'], doc_id, 'partage')

        flash("Document partagé avec succès", "success")
    except Exception as e:
        flash(f"Erreur : {str(e)}", "danger")

    return redirect(url_for('document.list_documents'))

@document_bp.route('/historique')
@login_required
def view_history(): 
    conn = db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            h.id,
            h.action_type as action,
            h.entity_name as titre,
            h.description,
            u.nom,
            u.prenom,
            CASE
                WHEN h.metadata->>'mime_type' LIKE 'application/pdf' THEN 'PDF'
                WHEN h.metadata->>'mime_type' LIKE 'application/msword' OR 
                     h.metadata->>'mime_type' LIKE 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' THEN 'Word'
                WHEN h.metadata->>'mime_type' LIKE 'application/vnd.ms-excel' OR 
                     h.metadata->>'mime_type' LIKE 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' THEN 'Excel'
                WHEN h.metadata->>'mime_type' LIKE 'image/%' THEN 'Image'
                WHEN h.metadata->>'mime_type' LIKE 'text/plain' THEN 'Texte'
                WHEN h.metadata->>'mime_type' LIKE 'application/zip' OR h.metadata->>'mime_type' LIKE 'application/x-rar-compressed' THEN 'Archive'
                WHEN h.metadata->>'mime_type' LIKE 'video/%' THEN 'Vidéo'
                WHEN h.metadata->>'mime_type' LIKE 'audio/%' THEN 'Audio'
                ELSE 'Autre'
            END as type_document,
            h.created_at as date_action
        FROM history h
        JOIN utilisateur u ON h.user_id = u.id
        WHERE h.entity_type = 'DOCUMENT'
        ORDER BY h.created_at DESC
    """)
    
    historique = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('historique.html', historique=historique)

# Modifier un document
@document_bp.route('/edit/<int:doc_id>', methods=['GET', 'POST'])
def edit_document(doc_id):
    if not has_permission(doc_id, current_user.get_id(), 'edition'):
        flash("Vous n'avez pas la permission de modifier ce document.", "danger")
        return redirect(url_for('document.list_documents'))

    conn = db_connection()
    cursor = conn.cursor(dictionary=True)

    # Récupérer les informations actuelles du document
    cursor.execute("SELECT * FROM document WHERE id = %s", (doc_id,))
    doc = cursor.fetchone()

    if not doc:
        flash('Document non trouvé.', 'danger')
        return redirect(url_for('document.list_documents'))

    # Extraire le nom et l'extension du titre
    title_base, extension = os.path.splitext(doc['titre'])

    if request.method == 'POST':
        new_title_base = request.form['titre']
        new_description = request.form['description']
        new_categorie = request.form['categorie']

        # Recomposer le titre avec l'extension originale
        new_title = f"{new_title_base}{extension}"

        # Mise à jour dans la base
        cursor.execute("""
            UPDATE document
            SET titre = %s, description = %s, categorie = %s, derniere_modification = NOW(), modifie_par = %s
            WHERE id = %s
        """, (new_title, new_description, new_categorie, session.get('user_id'), doc_id))

        conn.commit()
        cursor.close()
        conn.close()
        
         # Enregistrer l'action
        enregistrer_action(session['user_id'], doc_id, 'modification')

        flash('Document modifié avec succès !', 'success')
        return redirect(url_for('document.list_documents'))

    cursor.close()
    conn.close()
    return render_template('edit_document.html', document=doc, title_base=title_base, extension=extension)

@document_bp.route('/shared')
@login_required
def shared_documents():
    user_id = session.get('user_id')

    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupère les documents partagés avec l'utilisateur
        query = """
            SELECT d.*
            FROM Partage p
            JOIN Document d ON p.document_id = d.id
            WHERE p.utilisateur_id = %s
        """
        cursor.execute(query, (user_id,))
        documents = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('shared_documents.html', documents=documents)

    except Exception as e:
        flash(f'Erreur : {str(e)}', 'danger')
        return redirect(url_for('dashboard.home'))

def enregistrer_action(utilisateur_id, document_id, action):
    """
    Fonction dépréciée - Utiliser log_action à la place
    """
    from AppFlask.routes.history_routes import log_action
    
    # Récupérer les informations du document
    conn = db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT titre, mime_type, taille FROM document WHERE id = %s", (document_id,))
    document = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not document:
        return False
        
    # Mapper l'ancien type d'action vers le nouveau
    action_type_map = {
        'upload': 'CREATE',
        'modification': 'UPDATE',
        'suppression': 'DELETE',
        'partage': 'SHARE'
    }
    
    action_type = action_type_map.get(action, action.upper())
    
    # Créer la description appropriée
    description_map = {
        'CREATE': f"Création du document {document['titre']}",
        'UPDATE': f"Modification du document {document['titre']}",
        'DELETE': f"Suppression du document {document['titre']}",
        'SHARE': f"Partage du document {document['titre']}"
    }
    
    return log_action(
        user_id=utilisateur_id,
        action_type=action_type,
        entity_type='DOCUMENT',
        entity_id=document_id,
        entity_name=document['titre'],
        description=description_map.get(action_type, f"Action {action} sur le document {document['titre']}"),
        metadata={
            'mime_type': document['mime_type'],
            'size': document['taille']
        }
    )

# Route API pour l'upload de document
@document_bp.route('/api/documents', methods=['POST'])
@token_required
def api_upload_document(current_user):
    logger.info("=== Début de la requête d'upload de document ===")
    logger.info(f"Utilisateur: {current_user['email']}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Files: {request.files}")
    logger.info(f"Form data: {dict(request.form)}")

    if 'file' not in request.files:
        logger.error("Aucun fichier dans la requête")
        return jsonify({'message': 'Aucun fichier sélectionné'}), 400

    file = request.files['file']
    titre = request.form.get('titre', file.filename)
    description = request.form.get('description', '')
    categorie = request.form.get('type_document', 'AUTRE')
    service = request.form.get('service', 'Non défini')

    if file.filename == '':
        logger.error("Nom de fichier vide")
        return jsonify({'message': 'Aucun fichier sélectionné'}), 400

    try:
        filename = secure_filename(file.filename)
        logger.info(f"Fichier sécurisé: {filename}")
        
        # Lecture du contenu du fichier
        file_content = file.read()
        logger.info(f"Taille du fichier: {len(file_content)} bytes")
        
        # Upload vers Cloudinary
        public_id = f"documents/{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        logger.info(f"Public ID Cloudinary: {public_id}")
        
        # Déterminer le resource_type en fonction de l'extension
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext in ['jpg', 'jpeg', 'png', 'gif']:
            resource_type = 'image'
        elif ext in ['mp4', 'mov']:
            resource_type = 'video'
        else:
            resource_type = 'raw'
        logger.info(f"Type de ressource détecté: {resource_type}")
            
        cloudinary_response = upload_file(
            file_content,
            public_id=public_id,
            resource_type=resource_type
        )
        logger.info(f"Réponse Cloudinary complète: {cloudinary_response}")

        conn = db_connection()
        if not conn:
            logger.error("Impossible de se connecter à la base de données")
            return jsonify({'message': 'Erreur de connexion à la base de données'}), 500

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            INSERT INTO document (
                titre,
                description,
                categorie,
                fichier,
                mime_type,
                taille,
                service,
                proprietaire_id,
                date_ajout,
                derniere_modification,
                modifie_par,
                cloudinary_url,
                cloudinary_public_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s, %s, %s
            ) RETURNING id, cloudinary_url
        """

        logger.info("Tentative d'insertion en base de données")
        logger.info(f"Paramètres: titre={titre}, categorie={categorie}, service={service}")
        
        cursor.execute(query, (
            titre,
            description,
            categorie,
            filename,
            file.content_type,
            cloudinary_response.get('bytes', 0),
            service,
            current_user['id'],
            current_user['id'],
            cloudinary_response.get('url', ''),
            cloudinary_response.get('public_id', '')
        ))
        
        result = cursor.fetchone()
        logger.info(f"Résultat de l'insertion: {result}")
        
        if not result:
            logger.error("Aucun résultat retourné après l'insertion")
            raise Exception("Erreur lors de l'insertion en base de données")
            
        document_id = result['id']
        document_url = result['cloudinary_url']
        conn.commit()
        logger.info("Transaction validée")

        cursor.close()
        conn.close()

        # Enregistrer l'action
        enregistrer_action(current_user['id'], document_id, 'upload')
        logger.info("Action enregistrée")

        # Log de l'action de création
        log_action(
            user_id=current_user['id'],
            action_type="CREATE",
            entity_type="DOCUMENT",
            entity_id=document_id,
            entity_name=titre,
            description=f"Création du document {titre}",
            metadata={
                "type": categorie,
                "size": cloudinary_response.get('bytes', 0),
                "mime_type": file.content_type
            }
        )

        logger.info("=== Fin de l'upload avec succès ===")
        return jsonify({
            'message': 'Document créé avec succès',
            'document_id': document_id,
            'url': document_url
        }), 201

    except Exception as e:
        logger.error(f"Erreur lors de l'upload: {str(e)}")
        logger.error(f"Détails de l'erreur: {traceback.format_exc()}")
        if 'cloudinary_response' in locals() and cloudinary_response.get('public_id'):
            try:
                delete_file(cloudinary_response['public_id'], resource_type=resource_type)
                logger.info(f"Fichier supprimé de Cloudinary après erreur: {cloudinary_response['public_id']}")
            except Exception as del_error:
                logger.error(f"Erreur lors de la suppression du fichier Cloudinary: {str(del_error)}")
        
        if 'conn' in locals() and conn:
            conn.rollback()
            logger.info("Transaction annulée")
            conn.close()
            
        return jsonify({'message': str(e)}), 500

# Route API pour récupérer les documents récents
@document_bp.route('/api/documents/recent', methods=['GET'])
@token_required
def api_recent_documents(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)  # Utilisation de RealDictCursor pour avoir les résultats en dictionnaire

        # Si l'utilisateur est admin, il voit tous les documents
        # Sinon, il ne voit que ses propres documents
        if current_user['role'].lower() == 'admin':
            query = """
                SELECT 
                    d.id, 
                    d.titre, 
                    d.fichier,
                    d.description,
                    d.categorie as type_document,
                    d.taille,
                    CASE 
                        WHEN d.taille IS NULL OR d.taille = 0 THEN '0 B'
                        WHEN d.taille < 1024 THEN ROUND(d.taille::numeric, 2)::text || ' B'
                        WHEN d.taille < 1048576 THEN ROUND((d.taille::numeric/1024), 2)::text || ' KB'
                        WHEN d.taille < 1073741824 THEN ROUND((d.taille::numeric/1048576), 2)::text || ' MB'
                        ELSE ROUND((d.taille::numeric/1073741824), 2)::text || ' GB'
                    END as taille_formatee,
                    TO_CHAR(d.date_ajout, 'DD/MM/YYYY') as date_creation,
                    u.nom as proprietaire_nom,
                    u.prenom as proprietaire_prenom,
                    CASE
                        WHEN d.cloudinary_url IS NOT NULL AND d.cloudinary_url != '' THEN 'DISPONIBLE'
                        ELSE 'NON DISPONIBLE'
                    END as statut
                FROM document d
                LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
                ORDER BY d.date_ajout DESC
                LIMIT 6
            """
            cursor.execute(query)
        else:
            query = """
                SELECT 
                    d.id, 
                    d.titre, 
                    d.fichier,
                    d.description,
                    d.categorie as type_document,
                    d.taille,
                    CASE 
                        WHEN d.taille IS NULL OR d.taille = 0 THEN '0 B'
                        WHEN d.taille < 1024 THEN ROUND(d.taille::numeric, 2)::text || ' B'
                        WHEN d.taille < 1048576 THEN ROUND((d.taille::numeric/1024), 2)::text || ' KB'
                        WHEN d.taille < 1073741824 THEN ROUND((d.taille::numeric/1048576), 2)::text || ' MB'
                        ELSE ROUND((d.taille::numeric/1073741824), 2)::text || ' GB'
                    END as taille_formatee,
                    TO_CHAR(d.date_ajout, 'DD/MM/YYYY') as date_creation,
                    u.nom as proprietaire_nom,
                    u.prenom as proprietaire_prenom,
                    CASE
                        WHEN d.cloudinary_url IS NOT NULL AND d.cloudinary_url != '' THEN 'DISPONIBLE'
                        ELSE 'NON DISPONIBLE'
                    END as statut
                FROM document d
                LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
                WHERE d.proprietaire_id = %s
                ORDER BY d.date_ajout DESC
                LIMIT 6
            """
            cursor.execute(query, (current_user['id'],))

        documents = cursor.fetchall()
        
        logger.info(f"Documents récents récupérés pour {current_user['email']} (rôle: {current_user['role']}): {len(documents)} documents")
        logger.info(f"Données des documents: {documents}")  # Pour le débogage
        
        cursor.close()
        conn.close()
        return jsonify(documents)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents récents: {str(e)}")
        return jsonify({'message': str(e)}), 500

# Route OPTIONS pour les documents de l'utilisateur
@document_bp.route('/api/documents/my', methods=['OPTIONS'])
def api_my_documents_options():
    return '', 200

# Route API pour récupérer les documents de l'utilisateur connecté
@document_bp.route('/api/documents/my', methods=['GET'])
@token_required
def api_my_documents(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        base_query = """
            SELECT 
                d.id,
                d.titre,
                d.description,
                COALESCE(d.categorie, 'Non catégorisé') as type_document,
                d.fichier,
                COALESCE(d.mime_type, 'application/octet-stream') as mime_type,
                COALESCE(d.taille, 0) as taille,
                CASE 
                    WHEN d.taille IS NULL OR d.taille = 0 THEN '0 B'
                    WHEN d.taille < 1024 THEN ROUND(d.taille::numeric, 2)::text || ' B'
                    WHEN d.taille < 1048576 THEN ROUND((d.taille::numeric/1024), 2)::text || ' KB'
                    WHEN d.taille < 1073741824 THEN ROUND((d.taille::numeric/1048576), 2)::text || ' MB'
                    ELSE ROUND((d.taille::numeric/1073741824), 2)::text || ' GB'
                END as taille_formatee,
                COALESCE(TO_CHAR(d.date_ajout AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'), '') as date_creation,
                COALESCE(TO_CHAR(d.derniere_modification AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'), '') as derniere_modification,
                COALESCE(d.service, 'Non défini') as service,
                COALESCE(d.cloudinary_url, '') as cloudinary_url,
                COALESCE(d.cloudinary_public_id, '') as cloudinary_public_id,
                COALESCE(u.nom, '') as proprietaire_nom,
                COALESCE(u.prenom, '') as proprietaire_prenom,
                COALESCE(u.email, '') as proprietaire_email,
                COALESCE(m.nom, '') as modifie_par_nom,
                COALESCE(m.prenom, '') as modifie_par_prenom,
                CASE
                    WHEN LOWER(d.fichier) LIKE '%.pdf' THEN 'PDF'
                    WHEN LOWER(d.fichier) LIKE '%.doc' OR LOWER(d.fichier) LIKE '%.docx' THEN 'Word'
                    WHEN LOWER(d.fichier) LIKE '%.xls' OR LOWER(d.fichier) LIKE '%.xlsx' THEN 'Excel'
                    WHEN LOWER(d.fichier) LIKE '%.jpg' OR LOWER(d.fichier) LIKE '%.jpeg' OR 
                         LOWER(d.fichier) LIKE '%.png' OR LOWER(d.fichier) LIKE '%.gif' THEN 'Image'
                    WHEN LOWER(d.fichier) LIKE '%.txt' THEN 'Texte'
                    WHEN LOWER(d.fichier) LIKE '%.zip' OR LOWER(d.fichier) LIKE '%.rar' THEN 'Archive'
                    WHEN LOWER(d.fichier) LIKE '%.mp4' OR LOWER(d.fichier) LIKE '%.avi' OR 
                         LOWER(d.fichier) LIKE '%.mov' THEN 'Vidéo'
                    WHEN LOWER(d.fichier) LIKE '%.mp3' OR LOWER(d.fichier) LIKE '%.wav' THEN 'Audio'
                    WHEN d.mime_type LIKE 'image/%' THEN 'Image'
                    WHEN d.mime_type = 'application/pdf' THEN 'PDF'
                    WHEN d.mime_type LIKE 'application/msword' OR 
                         d.mime_type LIKE 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' THEN 'Word'
                    WHEN d.mime_type LIKE 'application/vnd.ms-excel' OR 
                         d.mime_type LIKE 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' THEN 'Excel'
                    WHEN d.mime_type LIKE 'text/plain' THEN 'Texte'
                    WHEN d.mime_type LIKE 'application/zip' OR d.mime_type LIKE 'application/x-rar-compressed' THEN 'Archive'
                    WHEN d.mime_type LIKE 'video/%' THEN 'Vidéo'
                    WHEN d.mime_type LIKE 'audio/%' THEN 'Audio'
                    ELSE 'Autre'
                END as type_document,
                CASE
                    WHEN d.cloudinary_url IS NOT NULL AND d.cloudinary_url != '' THEN 'DISPONIBLE'
                    ELSE 'NON DISPONIBLE'
                END as statut
            FROM document d
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            LEFT JOIN utilisateur m ON d.modifie_par = m.id::text
        """

        if current_user['role'].lower() == 'admin':
            query = base_query + " ORDER BY d.date_ajout DESC"
            cursor.execute(query)
        else:
            query = base_query + " WHERE d.proprietaire_id = %s ORDER BY d.date_ajout DESC"
            cursor.execute(query, (current_user['id'],))

        documents = cursor.fetchall()
        
        # Transformation des données
        formatted_documents = []
        for doc in documents:
            # Création d'une copie du document pour éviter de modifier l'original
            formatted_doc = dict(doc)
            
            # Structuration des informations sur le propriétaire
            formatted_doc['proprietaire'] = {
                'nom': formatted_doc.pop('proprietaire_nom', ''),
                'prenom': formatted_doc.pop('proprietaire_prenom', ''),
                'email': formatted_doc.pop('proprietaire_email', '')
            }
            
            # Structuration des informations sur la dernière modification
            formatted_doc['derniere_modification_par'] = {
                'nom': formatted_doc.pop('modifie_par_nom', ''),
                'prenom': formatted_doc.pop('modifie_par_prenom', '')
            }
            
            formatted_documents.append(formatted_doc)
        
        logger.info(f"Documents récupérés pour {current_user['email']} (rôle: {current_user['role']}): {len(formatted_documents)} documents")
        
        cursor.close()
        conn.close()
        return jsonify(formatted_documents)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents: {str(e)}")
        return jsonify({'message': str(e)}), 500

@document_bp.route('/api/documents/shared', methods=['GET'])
@token_required
def api_shared_documents(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT 
                d.id,
                d.titre,
                d.description,
                CASE
                    WHEN LOWER(d.fichier) LIKE '%.pdf' THEN 'PDF'
                    WHEN LOWER(d.fichier) LIKE '%.doc' OR LOWER(d.fichier) LIKE '%.docx' THEN 'Word'
                    WHEN LOWER(d.fichier) LIKE '%.xls' OR LOWER(d.fichier) LIKE '%.xlsx' THEN 'Excel'
                    WHEN LOWER(d.fichier) LIKE '%.jpg' OR LOWER(d.fichier) LIKE '%.jpeg' OR 
                         LOWER(d.fichier) LIKE '%.png' OR LOWER(d.fichier) LIKE '%.gif' THEN 'Image'
                    WHEN LOWER(d.fichier) LIKE '%.txt' THEN 'Texte'
                    WHEN LOWER(d.fichier) LIKE '%.zip' OR LOWER(d.fichier) LIKE '%.rar' THEN 'Archive'
                    WHEN LOWER(d.fichier) LIKE '%.mp4' OR LOWER(d.fichier) LIKE '%.avi' OR 
                         LOWER(d.fichier) LIKE '%.mov' THEN 'Vidéo'
                    WHEN LOWER(d.fichier) LIKE '%.mp3' OR LOWER(d.fichier) LIKE '%.wav' THEN 'Audio'
                    WHEN d.mime_type LIKE 'image/%' THEN 'Image'
                    WHEN d.mime_type = 'application/pdf' THEN 'PDF'
                    WHEN d.mime_type LIKE 'application/msword' OR 
                         d.mime_type LIKE 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' THEN 'Word'
                    WHEN d.mime_type LIKE 'application/vnd.ms-excel' OR 
                         d.mime_type LIKE 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' THEN 'Excel'
                    WHEN d.mime_type LIKE 'text/plain' THEN 'Texte'
                    WHEN d.mime_type LIKE 'application/zip' OR d.mime_type LIKE 'application/x-rar-compressed' THEN 'Archive'
                    WHEN d.mime_type LIKE 'video/%' THEN 'Vidéo'
                    WHEN d.mime_type LIKE 'audio/%' THEN 'Audio'
                    ELSE 'Autre'
                END as type_document,
                COALESCE(d.taille, 0) as taille,
                CASE 
                    WHEN d.taille IS NULL OR d.taille = 0 THEN '0 B'
                    WHEN d.taille < 1024 THEN ROUND(d.taille::numeric, 2)::text || ' B'
                    WHEN d.taille < 1048576 THEN ROUND((d.taille::numeric/1024), 2)::text || ' KB'
                    WHEN d.taille < 1073741824 THEN ROUND((d.taille::numeric/1048576), 2)::text || ' MB'
                    ELSE ROUND((d.taille::numeric/1073741824), 2)::text || ' GB'
                END as taille_formatee,
                COALESCE(TO_CHAR(d.date_ajout AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'), '') as date_creation,
                COALESCE(TO_CHAR(p.date_partage AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'), '') as date_partage,
                d.cloudinary_url,
                COALESCE(u.nom, '') as proprietaire_nom,
                COALESCE(u.prenom, '') as proprietaire_prenom,
                p.permissions,
                CASE
                    WHEN d.cloudinary_url IS NOT NULL AND d.cloudinary_url != '' THEN 'DISPONIBLE'
                    ELSE 'NON DISPONIBLE'
                END as statut
            FROM document d
            JOIN partage p ON d.id = p.document_id
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            WHERE p.utilisateur_id = %s
            ORDER BY p.date_partage DESC
        """
        cursor.execute(query, (current_user['id'],))
        documents = cursor.fetchall()

        logger.info(f"Documents partagés récupérés pour {current_user['email']}: {len(documents)} documents")
        
        cursor.close()
        conn.close()
        return jsonify(documents)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents partagés: {str(e)}")
        return jsonify({'message': str(e)}), 500

@document_bp.route('/api/documents/stats', methods=['GET'])
@token_required
def api_document_stats(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Statistiques globales
        if current_user['role'].lower() == 'admin':
            # Pour l'admin, on compte tous les documents
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(DISTINCT d.id) FILTER (WHERE p.document_id IS NOT NULL) as documents_partages,
                    COALESCE(SUM(d.taille), 0) as taille_totale
                FROM document d
                LEFT JOIN partage p ON d.id = p.document_id
            """)
        else:
            # Pour les utilisateurs normaux, on compte leurs documents et ceux partagés avec eux
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT d.id) as total_documents,
                    COUNT(DISTINCT CASE WHEN p.document_id IS NOT NULL THEN d.id END) as documents_partages,
                    COALESCE(SUM(d.taille), 0) as taille_totale
                FROM document d
                LEFT JOIN partage p ON d.id = p.document_id
                WHERE d.proprietaire_id = %s OR p.utilisateur_id = %s
            """, (current_user['id'], current_user['id']))

        stats = cursor.fetchone()
        
        # Formatage de la taille totale
        taille_totale = stats['taille_totale']
        if taille_totale < 1024:
            espace_utilise = f"{taille_totale} B"
        elif taille_totale < 1048576:
            espace_utilise = f"{round(taille_totale/1024, 2)} KB"
        elif taille_totale < 1073741824:
            espace_utilise = f"{round(taille_totale/1048576, 2)} MB"
        else:
            espace_utilise = f"{round(taille_totale/1073741824, 2)} GB"

        # Statistiques par type de document
        if current_user['role'].lower() == 'admin':
            cursor.execute("""
                SELECT 
                    CASE
                        WHEN LOWER(d.fichier) LIKE '%.pdf' THEN 'PDF'
                        WHEN LOWER(d.fichier) LIKE '%.doc' OR LOWER(d.fichier) LIKE '%.docx' THEN 'Word'
                        WHEN LOWER(d.fichier) LIKE '%.xls' OR LOWER(d.fichier) LIKE '%.xlsx' THEN 'Excel'
                        WHEN LOWER(d.fichier) LIKE '%.jpg' OR LOWER(d.fichier) LIKE '%.jpeg' OR 
                             LOWER(d.fichier) LIKE '%.png' OR LOWER(d.fichier) LIKE '%.gif' THEN 'Image'
                        WHEN LOWER(d.fichier) LIKE '%.txt' THEN 'Texte'
                        WHEN LOWER(d.fichier) LIKE '%.zip' OR LOWER(d.fichier) LIKE '%.rar' THEN 'Archive'
                        WHEN LOWER(d.fichier) LIKE '%.mp4' OR LOWER(d.fichier) LIKE '%.avi' OR 
                             LOWER(d.fichier) LIKE '%.mov' THEN 'Vidéo'
                        WHEN LOWER(d.fichier) LIKE '%.mp3' OR LOWER(d.fichier) LIKE '%.wav' THEN 'Audio'
                        WHEN d.mime_type LIKE 'image/%' THEN 'Image'
                        WHEN d.mime_type = 'application/pdf' THEN 'PDF'
                        WHEN d.mime_type LIKE 'application/msword' OR 
                             d.mime_type LIKE 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' THEN 'Word'
                        WHEN d.mime_type LIKE 'application/vnd.ms-excel' OR 
                             d.mime_type LIKE 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' THEN 'Excel'
                        WHEN d.mime_type LIKE 'text/plain' THEN 'Texte'
                        WHEN d.mime_type LIKE 'application/zip' OR d.mime_type LIKE 'application/x-rar-compressed' THEN 'Archive'
                        WHEN d.mime_type LIKE 'video/%' THEN 'Vidéo'
                        WHEN d.mime_type LIKE 'audio/%' THEN 'Audio'
                        ELSE 'Autre'
                    END as type_document,
                    COUNT(*) as count
                FROM document d
                GROUP BY type_document
                ORDER BY count DESC
            """)
        else:
            cursor.execute("""
                SELECT 
                    CASE
                        WHEN LOWER(d.fichier) LIKE '%.pdf' THEN 'PDF'
                        WHEN LOWER(d.fichier) LIKE '%.doc' OR LOWER(d.fichier) LIKE '%.docx' THEN 'Word'
                        WHEN LOWER(d.fichier) LIKE '%.xls' OR LOWER(d.fichier) LIKE '%.xlsx' THEN 'Excel'
                        WHEN LOWER(d.fichier) LIKE '%.jpg' OR LOWER(d.fichier) LIKE '%.jpeg' OR 
                             LOWER(d.fichier) LIKE '%.png' OR LOWER(d.fichier) LIKE '%.gif' THEN 'Image'
                        WHEN LOWER(d.fichier) LIKE '%.txt' THEN 'Texte'
                        WHEN LOWER(d.fichier) LIKE '%.zip' OR LOWER(d.fichier) LIKE '%.rar' THEN 'Archive'
                        WHEN LOWER(d.fichier) LIKE '%.mp4' OR LOWER(d.fichier) LIKE '%.avi' OR 
                             LOWER(d.fichier) LIKE '%.mov' THEN 'Vidéo'
                        WHEN LOWER(d.fichier) LIKE '%.mp3' OR LOWER(d.fichier) LIKE '%.wav' THEN 'Audio'
                        WHEN d.mime_type LIKE 'image/%' THEN 'Image'
                        WHEN d.mime_type = 'application/pdf' THEN 'PDF'
                        WHEN d.mime_type LIKE 'application/msword' OR 
                             d.mime_type LIKE 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' THEN 'Word'
                        WHEN d.mime_type LIKE 'application/vnd.ms-excel' OR 
                             d.mime_type LIKE 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' THEN 'Excel'
                        WHEN d.mime_type LIKE 'text/plain' THEN 'Texte'
                        WHEN d.mime_type LIKE 'application/zip' OR d.mime_type LIKE 'application/x-rar-compressed' THEN 'Archive'
                        WHEN d.mime_type LIKE 'video/%' THEN 'Vidéo'
                        WHEN d.mime_type LIKE 'audio/%' THEN 'Audio'
                        ELSE 'Autre'
                    END as type_document,
                    COUNT(*) as count
                FROM document d
                LEFT JOIN partage p ON d.id = p.document_id
                WHERE d.proprietaire_id = %s OR p.utilisateur_id = %s
                GROUP BY type_document
                ORDER BY count DESC
            """, (current_user['id'], current_user['id']))

        types_count = cursor.fetchall()
        documents_par_type = {row['type_document']: row['count'] for row in types_count}

        cursor.close()
        conn.close()

        return jsonify({
            'total_documents': stats['total_documents'],
            'documents_partages': stats['documents_partages'],
            'espace_utilise': espace_utilise,
            'documents_par_type': documents_par_type
        })

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
        return jsonify({'message': str(e)}), 500

@document_bp.route('/api/documents/search', methods=['GET', 'OPTIONS'])
@token_required
def search_documents(current_user):
    try:
        if request.method == 'OPTIONS':
            return '', 200

        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])

        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        results = []

        # Recherche dans les documents
        cursor.execute("""
            SELECT 
                'document' as type,
                id,
                titre,
                CASE
                    WHEN LOWER(fichier) LIKE '%.pdf' THEN 'PDF'
                    WHEN LOWER(fichier) LIKE '%.doc' OR LOWER(fichier) LIKE '%.docx' THEN 'Word'
                    WHEN LOWER(fichier) LIKE '%.xls' OR LOWER(fichier) LIKE '%.xlsx' THEN 'Excel'
                    WHEN LOWER(fichier) LIKE '%.jpg' OR LOWER(fichier) LIKE '%.jpeg' OR 
                         LOWER(fichier) LIKE '%.png' OR LOWER(fichier) LIKE '%.gif' THEN 'Image'
                    WHEN LOWER(fichier) LIKE '%.txt' THEN 'Texte'
                    ELSE 'Autre'
                END as type_document,
                CASE 
                    WHEN taille < 1024 THEN CONCAT(ROUND(taille::numeric, 2)::text, ' B')
                    WHEN taille < 1048576 THEN CONCAT(ROUND((taille::numeric/1024), 2)::text, ' KB')
                    WHEN taille < 1073741824 THEN CONCAT(ROUND((taille::numeric/1048576), 2)::text, ' MB')
                    ELSE CONCAT(ROUND((taille::numeric/1073741824), 2)::text, ' GB')
                END as taille_formatee,
                TO_CHAR(date_ajout, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as date_creation
            FROM document 
            WHERE 
                (LOWER(titre) LIKE LOWER(%s) OR 
                LOWER(description) LIKE LOWER(%s)) AND
                (proprietaire_id = %s OR 
                id IN (SELECT document_id FROM partage WHERE utilisateur_id = %s) OR
                %s)
            LIMIT 5
        """, (f"%{query}%", f"%{query}%", current_user['id'], current_user['id'], current_user['role'].lower() == 'admin'))
        
        document_results = cursor.fetchall()
        results.extend(document_results)

        cursor.close()
        conn.close()

        return jsonify(results)

    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {str(e)}")
        return jsonify({'message': str(e)}), 500

# Gestionnaire pour les requêtes OPTIONS
@document_bp.route('/api/documents/<int:doc_id>', methods=['OPTIONS'])
def handle_document_options(doc_id):
    return '', 200

# Suppression d'un document
@document_bp.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@token_required
def delete_document_api(current_user, doc_id):
    conn = None
    cursor = None
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Vérifier les droits de l'utilisateur
        if current_user['role'].lower() != 'admin':
            cursor.execute("SELECT proprietaire_id FROM document WHERE id = %s", (doc_id,))
            doc = cursor.fetchone()
            if not doc or str(doc['proprietaire_id']) != str(current_user['id']):
                return jsonify({'message': "Vous n'avez pas la permission de supprimer ce document."}), 403

        # Récupérer les informations du document
        cursor.execute("""
            SELECT * FROM document WHERE id = %s
        """, (doc_id,))
        document = cursor.fetchone()

        if not document:
            return jsonify({'message': "Document introuvable."}), 404

        # Préparer les données JSON pour la table trash
        item_data = {
            'titre': document['titre'],
            'fichier': document['fichier'],
            'description': document['description'],
            'taille': document['taille'],
            'mime_type': document.get('mime_type'),
            'cloudinary_url': document.get('cloudinary_url'),
            'cloudinary_public_id': document.get('cloudinary_public_id')
        }

        # Sauvegarder dans la table trash
        cursor.execute("""
            INSERT INTO trash (
                item_id,
                item_type,
                item_data,
                deleted_by,
                deleted_at
            ) VALUES (
                %s, %s, %s::jsonb, %s, CURRENT_TIMESTAMP
            )
        """, (
            doc_id,
            'document',
            json.dumps(item_data),
            current_user['id']
        ))

        # Supprimer le document
        cursor.execute("DELETE FROM document WHERE id = %s", (doc_id,))

        # Enregistrer l'action
        from AppFlask.routes.history_routes import log_action
        log_action(
            user_id=current_user['id'],
            action_type='DELETE',
            entity_type='DOCUMENT',
            entity_id=doc_id,
            entity_name=document['titre'],
            description=f"Suppression du document {document['titre']}",
            metadata={
                'size': document['taille'],
                'mime_type': document.get('mime_type', 'unknown')
            }
        )

        conn.commit()
        return jsonify({
            'message': "Document déplacé vers la corbeille avec succès.",
            'document_id': doc_id
        }), 200

    except Exception as e:
        logger.error(f"Erreur lors de la suppression du document: {str(e)}")
        if conn:
            conn.rollback()
        return jsonify({'message': "Erreur lors de la suppression du document."}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

