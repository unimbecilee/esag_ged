from flask import Blueprint, request, jsonify
from ..db import db_connection
from .auth import token_required
import psycopg2.extras

bp = Blueprint('document_tags', __name__, url_prefix='/api/documents')

@bp.route('/<int:document_id>/tags', methods=['GET'])
@token_required
def get_document_tags(current_user, document_id):
    """
    Récupère tous les tags d'un document
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT t.id, t.nom, t.couleur, t.description
            FROM tag t
            JOIN document_tag dt ON t.id = dt.tag_id
            WHERE dt.document_id = %s
            ORDER BY t.nom
        """, (document_id,))
        
        tags = cursor.fetchall()
        
        tags_data = []
        for tag in tags:
            tags_data.append({
                'id': tag['id'],
                'nom': tag['nom'],
                'couleur': tag['couleur'],
                'description': tag['description']
            })
        
        return jsonify({
            'success': True,
            'tags': tags_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération des tags: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/<int:document_id>/tags', methods=['POST'])
@token_required
def add_tag_to_document(current_user, document_id):
    """
    Ajoute un tag à un document
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        
        if not tag_id:
            return jsonify({
                'success': False,
                'message': 'ID du tag requis'
            }), 400
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Vérifier si l'association existe déjà
        cursor.execute("""
            SELECT id FROM document_tag
            WHERE document_id = %s AND tag_id = %s
        """, (document_id, tag_id))
        
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'Ce tag est déjà associé au document'
            }), 400
        
        # Ajouter l'association
        cursor.execute("""
            INSERT INTO document_tag (document_id, tag_id, created_by, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id
        """, (document_id, tag_id, current_user['id']))
        
        result = cursor.fetchone()
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag ajouté avec succès',
            'association_id': result['id']
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors de l\'ajout du tag: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/<int:document_id>/tags/<int:tag_id>', methods=['DELETE'])
@token_required
def remove_tag_from_document(current_user, document_id, tag_id):
    """
    Retire un tag d'un document
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            DELETE FROM document_tag
            WHERE document_id = %s AND tag_id = %s
            RETURNING id
        """, (document_id, tag_id))
        
        result = cursor.fetchone()
        
        if result:
            conn.commit()
            return jsonify({
                'success': True,
                'message': 'Tag retiré avec succès'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Association tag-document non trouvée'
            }), 404
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la suppression: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/tags', methods=['GET'])
@token_required
def get_all_tags(current_user):
    """
    Récupère tous les tags disponibles
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT t.*, 
                   COUNT(dt.document_id) as usage_count,
                   u.nom as created_by_nom, u.prenom as created_by_prenom
            FROM tag t
            LEFT JOIN document_tag dt ON t.id = dt.tag_id
            LEFT JOIN utilisateur u ON t.created_by = u.id
            GROUP BY t.id, u.nom, u.prenom
            ORDER BY t.nom
        """)
        
        tags = cursor.fetchall()
        
        tags_data = []
        for tag in tags:
            tags_data.append({
                'id': tag['id'],
                'nom': tag['nom'],
                'couleur': tag['couleur'],
                'description': tag['description'],
                'usage_count': tag['usage_count'],
                'created_by': f"{tag['created_by_prenom']} {tag['created_by_nom']}" if tag['created_by_nom'] else None,
                'created_at': tag['created_at'].isoformat() if tag['created_at'] else None
            })
        
        return jsonify({
            'success': True,
            'tags': tags_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/tags', methods=['POST'])
@token_required
def create_tag(current_user):
    """
    Crée un nouveau tag
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        data = request.get_json()
        nom = data.get('nom', '').strip()
        couleur = data.get('couleur', '#3a8bfd')
        description = data.get('description', '').strip()
        
        if not nom:
            return jsonify({
                'success': False,
                'message': 'Le nom du tag est requis'
            }), 400
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Vérifier si le tag existe déjà
        cursor.execute("SELECT id FROM tag WHERE LOWER(nom) = LOWER(%s)", (nom,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': 'Un tag avec ce nom existe déjà'
            }), 400
        
        # Créer le tag
        cursor.execute("""
            INSERT INTO tag (nom, couleur, description, created_by, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id, nom, couleur, description, created_at
        """, (nom, couleur, description, current_user['id']))
        
        tag = cursor.fetchone()
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag créé avec succès',
            'tag': {
                'id': tag['id'],
                'nom': tag['nom'],
                'couleur': tag['couleur'],
                'description': tag['description'],
                'created_at': tag['created_at'].isoformat()
            }
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la création: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/tags/<int:tag_id>', methods=['PUT'])
@token_required
def update_tag(current_user, tag_id):
    """
    Met à jour un tag existant
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        data = request.get_json()
        nom = data.get('nom', '').strip()
        couleur = data.get('couleur')
        description = data.get('description', '').strip()
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Vérifier si le tag existe et appartient à l'utilisateur
        cursor.execute("""
            SELECT created_by FROM tag WHERE id = %s
        """, (tag_id,))
        
        tag = cursor.fetchone()
        if not tag:
            return jsonify({
                'success': False,
                'message': 'Tag non trouvé'
            }), 404
        
        if tag['created_by'] != current_user['id'] and current_user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': 'Vous ne pouvez modifier que vos propres tags'
            }), 403
        
        # Construire la requête de mise à jour
        update_fields = []
        params = []
        
        if nom:
            # Vérifier l'unicité du nom
            cursor.execute("""
                SELECT id FROM tag 
                WHERE LOWER(nom) = LOWER(%s) AND id != %s
            """, (nom, tag_id))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'Un tag avec ce nom existe déjà'
                }), 400
            update_fields.append("nom = %s")
            params.append(nom)
        
        if couleur:
            update_fields.append("couleur = %s")
            params.append(couleur)
        
        if description is not None:
            update_fields.append("description = %s")
            params.append(description)
        
        if not update_fields:
            return jsonify({
                'success': False,
                'message': 'Aucune donnée à mettre à jour'
            }), 400
        
        update_fields.append("updated_at = NOW()")
        params.append(tag_id)
        
        cursor.execute(f"""
            UPDATE tag 
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, nom, couleur, description, updated_at
        """, params)
        
        updated_tag = cursor.fetchone()
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag mis à jour avec succès',
            'tag': {
                'id': updated_tag['id'],
                'nom': updated_tag['nom'],
                'couleur': updated_tag['couleur'],
                'description': updated_tag['description'],
                'updated_at': updated_tag['updated_at'].isoformat()
            }
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la mise à jour: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@token_required
def delete_tag(current_user, tag_id):
    """
    Supprime un tag
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Vérifier si le tag existe et appartient à l'utilisateur
        cursor.execute("""
            SELECT created_by FROM tag WHERE id = %s
        """, (tag_id,))
        
        tag = cursor.fetchone()
        if not tag:
            return jsonify({
                'success': False,
                'message': 'Tag non trouvé'
            }), 404
        
        if tag['created_by'] != current_user['id'] and current_user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': 'Vous ne pouvez supprimer que vos propres tags'
            }), 403
        
        # Supprimer toutes les associations avec les documents
        cursor.execute("DELETE FROM document_tag WHERE tag_id = %s", (tag_id,))
        
        # Supprimer le tag
        cursor.execute("DELETE FROM tag WHERE id = %s RETURNING id", (tag_id,))
        
        result = cursor.fetchone()
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag supprimé avec succès'
        }), 200
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la suppression: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/search-by-tags', methods=['POST'])
@token_required
def search_documents_by_tags(current_user):
    """
    Recherche des documents par tags
    """
    conn = db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        data = request.get_json()
        tag_ids = data.get('tag_ids', [])
        operator = data.get('operator', 'AND')  # AND ou OR
        
        if not tag_ids:
            return jsonify({
                'success': False,
                'message': 'Au moins un tag requis'
            }), 400
        
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if operator.upper() == 'AND':
            # Documents qui ont TOUS les tags
            cursor.execute("""
                SELECT d.*, COUNT(dt.tag_id) as tag_count
                FROM document d
                JOIN document_tag dt ON d.id = dt.document_id
                WHERE dt.tag_id = ANY(%s)
                  AND d.proprietaire_id = %s
                GROUP BY d.id
                HAVING COUNT(dt.tag_id) = %s
                ORDER BY d.derniere_modification DESC
            """, (tag_ids, current_user['id'], len(tag_ids)))
        else:
            # Documents qui ont AU MOINS UN des tags
            cursor.execute("""
                SELECT DISTINCT d.*
                FROM document d
                JOIN document_tag dt ON d.id = dt.document_id
                WHERE dt.tag_id = ANY(%s)
                  AND d.proprietaire_id = %s
                ORDER BY d.derniere_modification DESC
            """, (tag_ids, current_user['id']))
        
        documents = cursor.fetchall()
        
        documents_data = []
        for doc in documents:
            # Récupérer les tags de chaque document
            cursor.execute("""
                SELECT t.id, t.nom, t.couleur
                FROM tag t
                JOIN document_tag dt ON t.id = dt.tag_id
                WHERE dt.document_id = %s
            """, (doc['id'],))
            
            doc_tags = cursor.fetchall()
            
            documents_data.append({
                'id': doc['id'],
                'titre': doc['titre'],
                'categorie': doc['categorie'],
                'mime_type': doc['mime_type'],
                'taille': doc['taille'],
                'date_ajout': doc['date_ajout'].isoformat() if doc['date_ajout'] else None,
                'derniere_modification': doc['derniere_modification'].isoformat() if doc['derniere_modification'] else None,
                'description': doc['description'],
                'tags': [{'id': t['id'], 'nom': t['nom'], 'couleur': t['couleur']} for t in doc_tags]
            })
        
        return jsonify({
            'success': True,
            'documents': documents_data,
            'total': len(documents_data)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la recherche: {str(e)}'
        }), 500
    finally:
        cursor.close()
        conn.close() 