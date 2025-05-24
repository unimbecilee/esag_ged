from flask import Blueprint, redirect, url_for, flash, render_template, jsonify, request
from flask_login import login_required
from AppFlask.db import db_connection
from AppFlask.api.auth import token_required
import os
import logging
from psycopg2.extras import RealDictCursor
from AppFlask.routes.history_routes import log_action

# Configuration du logging
logger = logging.getLogger(__name__)

trash_bp = Blueprint('trash', __name__)

# Voir la corbeille
@trash_bp.route('/trash')
def view_trash():
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.id AS corbeille_id, d.id AS document_id, d.titre, d.description, c.date_suppression
            FROM Corbeille c
            JOIN Document d ON c.document_id = d.id
        """
        cursor.execute(query)
        trash_docs = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('trash.html', trash_docs=trash_docs)
    except Exception as e:
        flash(f"Erreur lors de la récupération de la corbeille : {str(e)}")
        return redirect('/')

# Restaurer un document
@trash_bp.route('/restore/<int:doc_id>', methods=['POST'])
def restore_document(doc_id):
    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Supprimer le document de la corbeille
        cursor.execute("DELETE FROM Corbeille WHERE document_id = %s", (doc_id,))
        conn.commit()

        flash('Document restauré avec succès')
    except Exception as e:
        flash(f'Erreur lors de la restauration : {str(e)}')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('trash.view_trash'))

# Suppression définitive (route web)
@trash_bp.route('/delete_permanent/<int:doc_id>', methods=['POST'])
def delete_permanently(doc_id):
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # Récupérer le fichier avant suppression
        cursor.execute("SELECT fichier FROM Document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()

        if document:
            file_path = os.path.join('uploads', document['fichier'])
            if os.path.exists(file_path):
                os.remove(file_path)

            # Supprimer le document de la corbeille et de la table Document
            cursor.execute("DELETE FROM Corbeille WHERE document_id = %s", (doc_id,))
            cursor.execute("DELETE FROM Document WHERE id = %s", (doc_id,))
            conn.commit()

            flash('Document supprimé définitivement')
        else:
            flash('Document introuvable')
    except Exception as e:
        flash(f'Erreur lors de la suppression définitive : {str(e)}')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('trash.view_trash'))

@trash_bp.route('/api/trash', methods=['GET'])
@token_required
def get_trash_items(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer tous les éléments dans la corbeille qui n'ont pas été restaurés ou supprimés définitivement
        cursor.execute("""
            SELECT t.*, 
                   u1.prenom || ' ' || u1.nom as deleted_by_name,
                   u2.prenom || ' ' || u2.nom as restored_by_name
            FROM trash t
            LEFT JOIN utilisateur u1 ON t.deleted_by = u1.id
            LEFT JOIN utilisateur u2 ON t.restored_by = u2.id
            WHERE t.restored_at IS NULL 
            AND t.permanent_delete_at IS NULL
            ORDER BY t.deleted_at DESC
        """)
        
        items = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(items)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des éléments de la corbeille: {str(e)}")
        return jsonify({'message': str(e)}), 500

@trash_bp.route('/api/trash/<int:trash_id>/restore', methods=['POST'])
@token_required
def restore_from_trash(current_user, trash_id):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer les informations de l'élément
        cursor.execute("""
            SELECT * FROM trash 
            WHERE id = %s AND restored_at IS NULL AND permanent_delete_at IS NULL
        """, (trash_id,))
        
        trash_item = cursor.fetchone()
        if not trash_item:
            return jsonify({'message': 'Élément non trouvé dans la corbeille'}), 404

        # Restaurer l'élément selon son type
        if trash_item['item_type'] == 'document':
            cursor.execute("""
                INSERT INTO document (
                    id,
                    titre,
                    description,
                    fichier,
                    taille,
                    mime_type,
                    cloudinary_url,
                    cloudinary_public_id,
                    proprietaire_id,
                    date_ajout,
                    derniere_modification,
                    modifie_par
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP,
                    %s
                )
            """, (
                trash_item['item_id'],
                trash_item['item_data']['titre'],
                trash_item['item_data']['description'],
                trash_item['item_data']['fichier'],
                trash_item['item_data']['taille'],
                trash_item['item_data'].get('mime_type'),
                trash_item['item_data'].get('cloudinary_url'),
                trash_item['item_data'].get('cloudinary_public_id'),
                trash_item['deleted_by'],
                current_user['id']
            ))

        # Marquer comme restauré dans la corbeille
        cursor.execute("""
            UPDATE trash 
            SET restored_at = CURRENT_TIMESTAMP,
                restored_by = %s
            WHERE id = %s
        """, (current_user['id'], trash_id))

        conn.commit()
        cursor.close()
        conn.close()

        # Log de l'action de restauration
        log_action(
            user_id=current_user['id'],
            action_type="RESTORE",
            entity_type=trash_item['item_type'].upper(),
            entity_id=trash_item['item_id'],
            entity_name=trash_item['item_data'].get('titre', ''),
            description=f"Restauration depuis la corbeille : {trash_item['item_type']} - {trash_item['item_data'].get('titre', '')}",
            metadata=trash_item['item_data']
        )

        return jsonify({'message': 'Élément restauré avec succès'})

    except Exception as e:
        logger.error(f"Erreur lors de la restauration de l'élément: {str(e)}")
        if conn:
            conn.rollback()
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({'message': str(e)}), 500

@trash_bp.route('/api/trash/<int:trash_id>', methods=['DELETE'])
@token_required
def api_delete_permanently(current_user, trash_id):
    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Marquer comme supprimé définitivement
        cursor.execute("""
            UPDATE trash 
            SET permanent_delete_at = CURRENT_TIMESTAMP,
                permanent_delete_by = %s
            WHERE id = %s AND restored_at IS NULL
            RETURNING item_type, item_id, item_data
        """, (current_user['id'], trash_id))
        
        deleted_item = cursor.fetchone()
        if not deleted_item:
            return jsonify({'message': 'Élément non trouvé ou déjà restauré'}), 404

        conn.commit()
        cursor.close()
        conn.close()

        # Log de l'action de suppression définitive
        log_action(
            user_id=current_user['id'],
            action_type="PERMANENT_DELETE",
            entity_type=deleted_item['item_type'].upper(),
            entity_id=deleted_item['item_id'],
            entity_name=deleted_item['item_data'].get('titre') or deleted_item['item_data'].get('nom'),
            description=f"Suppression définitive : {deleted_item['item_type']} - {deleted_item['item_data'].get('titre') or deleted_item['item_data'].get('nom')}",
            metadata=deleted_item['item_data']
        )

        return jsonify({'message': 'Élément supprimé définitivement'})

    except Exception as e:
        logger.error(f"Erreur lors de la suppression définitive: {str(e)}")
        return jsonify({'message': str(e)}), 500

# Gestionnaire pour les requêtes OPTIONS
@trash_bp.route('/api/trash', methods=['OPTIONS'])
@trash_bp.route('/api/trash/<int:trash_id>/restore', methods=['OPTIONS'])
@trash_bp.route('/api/trash/<int:trash_id>', methods=['OPTIONS'])
def handle_trash_options():
    return '', 200
