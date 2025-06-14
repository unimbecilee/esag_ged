from flask import Blueprint, request, jsonify
from ..db import db_connection
from .auth import token_required
import psycopg2.extras
import shutil
import os
from datetime import datetime

bp = Blueprint('document_operations', __name__, url_prefix='/api/documents')

@bp.route('/<int:document_id>/move', methods=['POST'])
@token_required
def move_document(current_user, document_id):
    """
    Déplace un document vers un autre dossier
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        data = request.get_json()
        target_folder_id = data.get('target_folder_id')
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Vérifier que l'utilisateur est propriétaire du document
        cursor.execute("""
            SELECT proprietaire_id, titre, dossier_id 
            FROM document 
            WHERE id = %s
        """, (document_id,))
        
        document = cursor.fetchone()
        if not document:
            return jsonify({
                'success': False,
                'message': 'Document non trouvé'
            }), 404
        
        if document['proprietaire_id'] != current_user['id']:
            return jsonify({
                'success': False,
                'message': 'Vous n\'avez pas les droits pour déplacer ce document'
            }), 403
        
        # Vérifier que le dossier cible existe et appartient à l'utilisateur
        if target_folder_id:
            cursor.execute("""
                SELECT created_by FROM folder 
                WHERE id = %s
            """, (target_folder_id,))
            
            folder = cursor.fetchone()
            if not folder:
                return jsonify({
                    'success': False,
                    'message': 'Dossier cible non trouvé'
                }), 404
            
            if folder['created_by'] != current_user['id']:
                return jsonify({
                    'success': False,
                    'message': 'Vous n\'avez pas accès au dossier cible'
                }), 403
        
        # Déplacer le document
        cursor.execute("""
            UPDATE document 
            SET dossier_id = %s, derniere_modification = %s
            WHERE id = %s
            RETURNING titre
        """, (target_folder_id, datetime.utcnow(), document_id))
        
        result = cursor.fetchone()
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Document "{result["titre"]}" déplacé avec succès'
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors du déplacement: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/<int:document_id>/copy', methods=['POST'])
@token_required
def copy_document(current_user, document_id):
    """
    Copie un document vers un autre dossier
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        data = request.get_json()
        target_folder_id = data.get('target_folder_id')
        new_title = data.get('new_title')  # Optionnel
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Récupérer les informations du document source
        cursor.execute("""
            SELECT * FROM document WHERE id = %s
        """, (document_id,))
        
        source_doc = cursor.fetchone()
        if not source_doc:
            return jsonify({
                'success': False,
                'message': 'Document source non trouvé'
            }), 404
        
        # Vérifier les droits de lecture sur le document source
        # (pour simplifier, on vérifie si c'est le propriétaire ou si c'est partagé)
        if source_doc['proprietaire_id'] != current_user['id']:
            # TODO: Vérifier les permissions de partage
            pass
        
        # Vérifier que le dossier cible existe et appartient à l'utilisateur
        if target_folder_id:
            cursor.execute("""
                SELECT created_by FROM folder 
                WHERE id = %s
            """, (target_folder_id,))
            
            folder = cursor.fetchone()
            if not folder:
                return jsonify({
                    'success': False,
                    'message': 'Dossier cible non trouvé'
                }), 404
            
            if folder['created_by'] != current_user['id']:
                return jsonify({
                    'success': False,
                    'message': 'Vous n\'avez pas accès au dossier cible'
                }), 403
        
        # Préparer le titre de la copie
        copy_title = new_title if new_title else f"Copie de {source_doc['titre']}"
        
        # Copier le fichier physique si nécessaire
        new_file_path = None
        if source_doc['fichier'] and os.path.exists(source_doc['fichier']):
            file_dir = os.path.dirname(source_doc['fichier'])
            file_name, file_ext = os.path.splitext(os.path.basename(source_doc['fichier']))
            new_file_name = f"{file_name}_copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            new_file_path = os.path.join(file_dir, new_file_name)
            
            try:
                shutil.copy2(source_doc['fichier'], new_file_path)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Erreur lors de la copie du fichier: {str(e)}'
                }), 500
        
        # Créer l'enregistrement de la copie
        cursor.execute("""
            INSERT INTO document (
                titre, categorie, fichier, content, mime_type, taille,
                date_ajout, derniere_modification, description,
                proprietaire_id, service, organisation_id, dossier_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s
            ) RETURNING id, titre
        """, (
            copy_title,
            source_doc['categorie'],
            new_file_path,
            source_doc['content'],
            source_doc['mime_type'],
            source_doc['taille'],
            datetime.utcnow(),
            datetime.utcnow(),
            f"Copie de: {source_doc['description']}" if source_doc['description'] else None,
            current_user['id'],
            source_doc['service'],
            source_doc['organisation_id'],
            target_folder_id
        ))
        
        new_doc = cursor.fetchone()
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Document copié avec succès',
            'new_document': {
                'id': new_doc['id'],
                'titre': new_doc['titre']
            }
        }), 201
    except Exception as e:
        conn.rollback()
        # Nettoyer le fichier copié en cas d'erreur
        if new_file_path and os.path.exists(new_file_path):
            try:
                os.remove(new_file_path)
            except:
                pass
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la copie: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/bulk-move', methods=['POST'])
@token_required
def bulk_move_documents(current_user):
    """
    Déplace plusieurs documents vers un dossier
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        data = request.get_json()
        document_ids = data.get('document_ids', [])
        target_folder_id = data.get('target_folder_id')
        
        if not document_ids:
            return jsonify({
                'success': False,
                'message': 'Aucun document sélectionné'
            }), 400
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Vérifier que tous les documents appartiennent à l'utilisateur
        cursor.execute("""
            SELECT id, titre FROM document 
            WHERE id = ANY(%s) AND proprietaire_id = %s
        """, (document_ids, current_user['id']))
        
        user_documents = cursor.fetchall()
        user_doc_ids = [doc['id'] for doc in user_documents]
        
        if len(user_doc_ids) != len(document_ids):
            return jsonify({
                'success': False,
                'message': 'Certains documents ne vous appartiennent pas'
            }), 403
        
        # Vérifier le dossier cible
        if target_folder_id:
            cursor.execute("""
                SELECT created_by FROM folder 
                WHERE id = %s
            """, (target_folder_id,))
            
            folder = cursor.fetchone()
            if not folder:
                return jsonify({
                    'success': False,
                    'message': 'Dossier cible non trouvé'
                }), 404
            
            if folder['created_by'] != current_user['id']:
                return jsonify({
                    'success': False,
                    'message': 'Vous n\'avez pas accès au dossier cible'
                }), 403
        
        # Déplacer tous les documents
        cursor.execute("""
            UPDATE document 
            SET dossier_id = %s, derniere_modification = %s
            WHERE id = ANY(%s)
        """, (target_folder_id, datetime.utcnow(), user_doc_ids))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(user_doc_ids)} document(s) déplacé(s) avec succès'
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors du déplacement: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/bulk-copy', methods=['POST'])
@token_required
def bulk_copy_documents(current_user):
    """
    Copie plusieurs documents vers un dossier
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        data = request.get_json()
        document_ids = data.get('document_ids', [])
        target_folder_id = data.get('target_folder_id')
        
        if not document_ids:
            return jsonify({
                'success': False,
                'message': 'Aucun document sélectionné'
            }), 400
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Récupérer tous les documents à copier
        cursor.execute("""
            SELECT * FROM document WHERE id = ANY(%s)
        """, (document_ids,))
        
        documents = cursor.fetchall()
        
        if len(documents) != len(document_ids):
            return jsonify({
                'success': False,
                'message': 'Certains documents n\'ont pas été trouvés'
            }), 404
        
        # Vérifier le dossier cible
        if target_folder_id:
            cursor.execute("""
                SELECT created_by FROM folder 
                WHERE id = %s
            """, (target_folder_id,))
            
            folder = cursor.fetchone()
            if not folder:
                return jsonify({
                    'success': False,
                    'message': 'Dossier cible non trouvé'
                }), 404
            
            if folder['created_by'] != current_user['id']:
                return jsonify({
                    'success': False,
                    'message': 'Vous n\'avez pas accès au dossier cible'
                }), 403
        
        copied_count = 0
        errors = []
        
        for doc in documents:
            try:
                # Copier le fichier physique si nécessaire
                new_file_path = None
                if doc['fichier'] and os.path.exists(doc['fichier']):
                    file_dir = os.path.dirname(doc['fichier'])
                    file_name, file_ext = os.path.splitext(os.path.basename(doc['fichier']))
                    new_file_name = f"{file_name}_copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
                    new_file_path = os.path.join(file_dir, new_file_name)
                    shutil.copy2(doc['fichier'], new_file_path)
                
                # Créer la copie
                cursor.execute("""
                    INSERT INTO document (
                        titre, categorie, fichier, content, mime_type, taille,
                        date_ajout, derniere_modification, description,
                        proprietaire_id, service, organisation_id, dossier_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s
                    )
                """, (
                    f"Copie de {doc['titre']}",
                    doc['categorie'],
                    new_file_path,
                    doc['content'],
                    doc['mime_type'],
                    doc['taille'],
                    datetime.utcnow(),
                    datetime.utcnow(),
                    f"Copie de: {doc['description']}" if doc['description'] else None,
                    current_user['id'],
                    doc['service'],
                    doc['organisation_id'],
                    target_folder_id
                ))
                
                copied_count += 1
            except Exception as e:
                errors.append(f"Erreur pour '{doc['titre']}': {str(e)}")
                # Nettoyer le fichier en cas d'erreur
                if new_file_path and os.path.exists(new_file_path):
                    try:
                        os.remove(new_file_path)
                    except:
                        pass
        
        conn.commit()
        
        message = f'{copied_count} document(s) copié(s) avec succès'
        if errors:
            message += f'. Erreurs: {"; ".join(errors)}'
        
        return jsonify({
            'success': True,
            'message': message,
            'copied_count': copied_count,
            'errors': errors
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la copie: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close() 