from flask import Blueprint, request, jsonify, g, current_app
from AppFlask.models.document_comment import DocumentComment
from AppFlask.api.auth import token_required
from AppFlask.models.history import History
from AppFlask.models.document_subscription import DocumentSubscription
import json

comment_bp = Blueprint('comment', __name__, url_prefix='/comments')

@comment_bp.route('/document/<int:document_id>', methods=['GET'])
@token_required
def get_document_comments(document_id):
    """
    Récupère tous les commentaires d'un document
    """
    try:
        comments = DocumentComment.get_comments(document_id)
        return jsonify({
            'status': 'success',
            'data': comments
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des commentaires: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@comment_bp.route('/document/<int:document_id>', methods=['POST'])
@token_required
def add_comment(document_id):
    """
    Ajoute un nouveau commentaire à un document
    """
    try:
        data = request.json
        
        if not data or 'content' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Le contenu du commentaire est requis'
            }), 400
        
        parent_id = data.get('parent_id')
        
        comment_id = DocumentComment.create(
            document_id=document_id,
            content=data['content'],
            created_by=g.current_user['id'],
            parent_id=parent_id
        )
        
        # Enregistrer dans l'historique
        History.create(
            action_type='CREATE_COMMENT',
            entity_type='DOCUMENT',
            entity_id=document_id,
            entity_name=f"Commentaire {comment_id}",
            description=f"Nouveau commentaire ajouté au document {document_id}",
            metadata=json.dumps({
                'document_id': document_id,
                'comment_id': comment_id,
                'parent_id': parent_id,
                'content': data['content'][:100] + ('...' if len(data['content']) > 100 else '')
            }),
            user_id=g.current_user['id']
        )
        
        # Notifier les abonnés
        subscribers = DocumentSubscription.notify_subscribers(
            document_id=document_id,
            event_type='comments',
            event_data={
                'comment_id': comment_id,
                'user_id': g.current_user['id'],
                'user_name': f"{g.current_user['prenom']} {g.current_user['nom']}",
                'content': data['content'][:100] + ('...' if len(data['content']) > 100 else '')
            }
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Commentaire ajouté avec succès',
            'data': {'comment_id': comment_id}
        }), 201
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'ajout du commentaire: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@comment_bp.route('/<int:comment_id>', methods=['GET'])
@token_required
def get_comment(comment_id):
    """
    Récupère un commentaire spécifique
    """
    try:
        comment = DocumentComment.get_comment(comment_id)
        
        if not comment:
            return jsonify({
                'status': 'error',
                'message': 'Commentaire non trouvé'
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': DocumentComment.to_dict(comment)
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération du commentaire: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@comment_bp.route('/<int:comment_id>', methods=['PUT'])
@token_required
def update_comment(comment_id):
    """
    Met à jour un commentaire existant
    """
    try:
        data = request.json
        
        if not data or 'content' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Le contenu du commentaire est requis'
            }), 400
        
        # Récupérer le commentaire pour vérifier le document_id
        comment = DocumentComment.get_comment(comment_id)
        if not comment:
            return jsonify({
                'status': 'error',
                'message': 'Commentaire non trouvé'
            }), 404
        
        success = DocumentComment.update(
            comment_id=comment_id,
            content=data['content'],
            updated_by=g.current_user['id']
        )
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Vous n\'êtes pas autorisé à modifier ce commentaire'
            }), 403
        
        # Enregistrer dans l'historique
        History.create(
            action_type='UPDATE_COMMENT',
            entity_type='DOCUMENT',
            entity_id=comment['document_id'],
            entity_name=f"Commentaire {comment_id}",
            description=f"Mise à jour du commentaire {comment_id}",
            metadata=json.dumps({
                'document_id': comment['document_id'],
                'comment_id': comment_id,
                'content': data['content'][:100] + ('...' if len(data['content']) > 100 else '')
            }),
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Commentaire mis à jour avec succès'
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la mise à jour du commentaire: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@comment_bp.route('/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(comment_id):
    """
    Supprime un commentaire
    """
    try:
        # Récupérer le commentaire pour vérifier le document_id
        comment = DocumentComment.get_comment(comment_id)
        if not comment:
            return jsonify({
                'status': 'error',
                'message': 'Commentaire non trouvé'
            }), 404
        
        success = DocumentComment.delete(
            comment_id=comment_id,
            deleted_by=g.current_user['id']
        )
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Vous n\'êtes pas autorisé à supprimer ce commentaire'
            }), 403
        
        # Enregistrer dans l'historique
        History.create(
            action_type='DELETE_COMMENT',
            entity_type='DOCUMENT',
            entity_id=comment['document_id'],
            entity_name=f"Commentaire {comment_id}",
            description=f"Suppression du commentaire {comment_id}",
            metadata=json.dumps({
                'document_id': comment['document_id'],
                'comment_id': comment_id
            }),
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Commentaire supprimé avec succès'
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la suppression du commentaire: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500