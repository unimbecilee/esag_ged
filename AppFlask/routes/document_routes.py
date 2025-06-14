from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, session, current_app, send_file, Response, abort
from flask_login import login_required
from werkzeug.utils import secure_filename
from datetime import datetime
from AppFlask.db import db_connection
from flask_login import current_user
from AppFlask.api.auth import log_user_action
from AppFlask.services.notification_service import notification_service
import mimetypes
import mammoth
import os
import json
from docx import Document
from io import BytesIO


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
        cursor = conn.cursor(dictionary=True)

        # Récupérer le propriétaire
        cursor.execute("SELECT proprietaire_id FROM Document WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()

        if doc is None:
            return False

        # L'utilisateur est propriétaire → tous les droits
        if doc['proprietaire_id'] == int(user_id):
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
        elif required_permission == 'edition' and partage['permissions'] in ('édition', 'admin'):
            return True
        elif required_permission == 'admin' and partage['permissions'] == 'admin':
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
    title = request.form.get('title') or file.filename  # Par défaut, on peut utiliser le nom du fichier
    description = request.form.get('description')
    categorie = request.form.get('categorie')
    dossier_id = request.form.get('dossier_id')  # Récupérer l'ID du dossier s'il est fourni
    
    # Convertir en entier si présent, sinon None
    if dossier_id:
        try:
            dossier_id = int(dossier_id)
        except ValueError:
            dossier_id = None

    if file.filename == '' or not allowed_file(file.filename):
        flash('Type de fichier non autorisé ou fichier manquant', 'danger')
        return redirect(url_for('document.list_documents'))

    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

        file.save(filepath)

        # Infos supplémentaires
        file_size = os.path.getsize(filepath)
        mime_type = mimetypes.guess_type(filepath)[0]

        conn = db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO Document (titre, fichier, description, categorie, taille, mime_type, date_ajout, proprietaire_id, dossier_id)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s)
        """
        cursor.execute(query, (
            title,
            unique_filename,
            description,
            categorie,
            file_size,
            mime_type,
            session.get('user_id'),  # Assure-toi que l'utilisateur est connecté
            dossier_id
        ))
        conn.commit()

        # Récupérer l'ID du document inséré
        cursor.execute("SELECT lastval()")
        document_id = cursor.fetchone()[0]
        
        # Envoyer les notifications
        try:
            notification_service.notify_document_uploaded(document_id, session.get('user_id'))
            print(f"✅ Notifications envoyées pour le document {document_id}")
        except Exception as e:
            print(f"⚠️ Erreur notification upload: {str(e)}")
        cursor.close()
        conn.close()

        # Récupérer l'ID du document inséré
        cursor.execute("SELECT lastval()")
        document_id = cursor.fetchone()[0]
        conn.commit()
        
        # Enregistrer l'action avec le nouveau système
        log_user_action(
            session['user_id'], 
            'DOCUMENT_UPLOAD', 
            f"Upload du document '{title}' (ID: {document_id})",
            request
        )
        
        flash('Fichier uploadé avec succès', 'success')
        return redirect(url_for('document.list_documents'))

    except Exception as e:
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

    doc = get_document_by_id(doc_id)
    if not doc:
        abort(404)

    # Enregistrer l'action de consultation
    log_user_action(
        user_id, 
        'DOCUMENT_VIEW', 
        f"Consultation du document '{doc['titre']}' (ID: {doc_id})",
        request
    )

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], doc['fichier'])
    file_ext = doc['fichier'].rsplit('.', 1)[-1].lower()

    if not os.path.exists(file_path):
        abort(404)

    # Comportement selon le type de fichier
    if file_ext == "pdf":
        return send_file(file_path, mimetype="application/pdf")
    elif file_ext == "txt":
        with open(file_path, 'r', encoding="utf-8") as f:
            content = f.read()
        return render_template('view_text.html', content=content, title=doc['titre'])
    elif file_ext in {"docx", "doc"}:
        try:
            with open(file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value
            return render_template('view_word.html', content=html_content, title=doc['titre'])
        except Exception:
            abort(500)
    elif file_ext == "xlsx":
        try:
            df = pd.read_excel(file_path)
            table_html = df.to_html(classes="table table-striped", index=False)
            return render_template("view_excel.html", table=table_html, title=doc['titre'])
        except Exception as e:
            flash(f"Erreur lors de la lecture du fichier Excel : {e}", "danger")
            return redirect(url_for('document.list_documents'))
    elif file_ext in {"png", "jpg", "jpeg"}:
        return render_template("view_image.html", image_url=url_for('static', filename=f"uploads/{doc['fichier']}"), title=doc['titre'])

    # Autres formats non supportés
    flash("Ce type de document n'est pas encore pris en charge.", "warning")
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
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupérer le dossier courant si spécifié
        dossier_id = request.args.get('dossier_id')
        if dossier_id:
            try:
                dossier_id = int(dossier_id)
            except ValueError:
                dossier_id = None
        
        # Récupérer les informations du dossier courant si spécifié
        current_folder = None
        breadcrumb = []
        if dossier_id:
            cursor.execute("""
                SELECT d.*, u.nom as proprietaire_nom, u.prenom as proprietaire_prenom
                FROM dossier d
                LEFT JOIN Utilisateur u ON d.proprietaire_id = u.id
                WHERE d.id = %s
            """, (dossier_id,))
            current_folder = cursor.fetchone()
            
            # Récupérer le fil d'Ariane
            if current_folder and current_folder.get('chemin'):
                path = current_folder['chemin']
                folder_ids = [int(id) for id in path.strip('/').split('/')]
                
                placeholders = ', '.join(['%s'] * len(folder_ids))
                query = f"""
                    SELECT id, titre
                    FROM dossier
                    WHERE id IN ({placeholders})
                    ORDER BY POSITION(id::text IN %s)
                """
                
                position_str = '/' + '/'.join(str(id) for id in folder_ids) + '/'
                cursor.execute(query, folder_ids + [position_str])
                breadcrumb = cursor.fetchall()

        # Récupérer les sous-dossiers
        cursor.execute("""
            SELECT d.*, u.nom as proprietaire_nom, u.prenom as proprietaire_prenom,
                   (SELECT COUNT(*) FROM dossier WHERE parent_id = d.id) as sous_dossiers_count,
                   (SELECT COUNT(*) FROM document WHERE dossier_id = d.id) as documents_count
            FROM dossier d
            LEFT JOIN Utilisateur u ON d.proprietaire_id = u.id
            WHERE d.parent_id IS %s
            ORDER BY d.titre
        """, (dossier_id,))
        subfolders = cursor.fetchall()

        # 🔹 Filtrage optionnel par catégorie
        categorie = request.args.get('categorie')
        if categorie:
            query = """
                SELECT * FROM Document
                WHERE (proprietaire_id = %s OR id IN (
                    SELECT document_id FROM Partage WHERE utilisateur_id = %s
                )) AND categorie = %s AND dossier_id IS %s
            """
            cursor.execute(query, (user_id, user_id, categorie, dossier_id))
        else:
            query = """
                SELECT * FROM Document
                WHERE (proprietaire_id = %s OR id IN (
                    SELECT document_id FROM Partage WHERE utilisateur_id = %s
                )) AND dossier_id IS %s
            """
            cursor.execute(query, (user_id, user_id, dossier_id))

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
            user_role=session.get('user_role'),
            subfolders=subfolders,
            current_folder=current_folder,
            breadcrumb=breadcrumb,
            dossier_id=dossier_id
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

        # Enregistrer l'action de téléchargement
        log_user_action(
            session.get('user_id'), 
            'DOCUMENT_DOWNLOAD', 
            f"Téléchargement du document '{titre}' (ID: {doc_id})",
            request
        )

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
            session.get('user_id')
        ))

        # 3. Supprimer de la table Document
        cursor.execute("DELETE FROM Document WHERE id = %s", (doc_id,))
        conn.commit()
        
        # Enregistrer l'action avec le nouveau système
        log_user_action(
            session['user_id'], 
            'DOCUMENT_DELETE', 
            f"Suppression du document '{document['titre']}' (ID: {doc_id})",
            request
        )

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
        
        # Enregistrer l'action avec le nouveau système
        log_user_action(
            session['user_id'], 
            'DOCUMENT_SHARE', 
            f"Partage du document (ID: {doc_id}) avec l'utilisateur {utilisateur_id}",
            request
        )

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
        SELECT h.id, u.nom, u.prenom, d.titre, h.action, h.date_action
        FROM Historique h
        JOIN Utilisateur u ON h.utilisateur_id = u.id
        JOIN Document d ON h.document_id = d.id
        ORDER BY h.date_action DESC
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
        
        # Enregistrer l'action avec le nouveau système
        log_user_action(
            session['user_id'], 
            'DOCUMENT_EDIT', 
            f"Modification du document '{new_title}' (ID: {doc_id})",
            request
        )

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
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Historique (utilisateur_id, document_id, action)
        VALUES (%s, %s, %s)
    """, (utilisateur_id, document_id, action))
    conn.commit()
    cursor.close()
    conn.close()

