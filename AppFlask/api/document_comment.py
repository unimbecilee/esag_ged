from flask import Blueprint, request, jsonify
from ..models.document_comment import DocumentComment
from .auth import token_required

bp = Blueprint('document_comment', __name__, url_prefix='/api/documents')

@bp.route('/<int:document_id>/comments', methods=['GET'])
@token_required
def get_document_comments(current_user, document_id):
    """
    Récupère tous les commentaires d'un document
    """
    try:
        comments = DocumentComment.get_comments(document_id)
        
        return jsonify({
            'success': True,
            'comments': comments
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération des commentaires: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/comments', methods=['POST'])
@token_required
def add_document_comment(current_user, document_id):
    """
    Ajoute un nouveau commentaire à un document
    """
    try:
        data = request.get_json()
        content = data.get('content')
        parent_id = data.get('parent_id')  # Pour les réponses
        
        if not content or not content.strip():
            return jsonify({
                'success': False,
                'message': 'Le contenu du commentaire est requis'
            }), 400
        
        comment_id = DocumentComment.create(document_id, content.strip(), current_user['id'], parent_id)
        
        if comment_id:
            # Récupérer le commentaire créé avec ses détails
            comment = DocumentComment.get_comment(comment_id)
            comment_dict = DocumentComment.to_dict(comment)
            
            return jsonify({
                'success': True,
                'message': 'Commentaire ajouté avec succès',
                'comment': comment_dict
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de la création du commentaire'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de l\'ajout du commentaire: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/comments/<int:comment_id>', methods=['PUT'])
@token_required
def update_document_comment(current_user, document_id, comment_id):
    """
    Met à jour un commentaire existant
    """
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content or not content.strip():
            return jsonify({
                'success': False,
                'message': 'Le contenu du commentaire est requis'
            }), 400
        
        success = DocumentComment.update(comment_id, content.strip(), current_user['id'])
        
        if success:
            # Récupérer le commentaire mis à jour
            comment = DocumentComment.get_comment(comment_id)
            comment_dict = DocumentComment.to_dict(comment)
            
            return jsonify({
                'success': True,
                'message': 'Commentaire mis à jour avec succès',
                'comment': comment_dict
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Impossible de modifier ce commentaire'
            }), 403
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la mise à jour: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_document_comment(current_user, document_id, comment_id):
    """
    Supprime un commentaire
    """
    try:
        success = DocumentComment.delete(comment_id, current_user['id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Commentaire supprimé avec succès'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Impossible de supprimer ce commentaire'
            }), 403
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la suppression: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/comments/<int:comment_id>/reply', methods=['POST'])
@token_required
def reply_to_comment(current_user, document_id, comment_id):
    """
    Répond à un commentaire spécifique
    """
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content or not content.strip():
            return jsonify({
                'success': False,
                'message': 'Le contenu de la réponse est requis'
            }), 400
        
        # Vérifier que le commentaire parent existe
        parent_comment = DocumentComment.get_comment(comment_id)
        if not parent_comment:
            return jsonify({
                'success': False,
                'message': 'Commentaire parent non trouvé'
            }), 404
        
        reply_id = DocumentComment.create(document_id, content.strip(), current_user['id'], comment_id)
        
        if reply_id:
            # Récupérer la réponse créée
            reply = DocumentComment.get_comment(reply_id)
            reply_dict = DocumentComment.to_dict(reply)
            
            return jsonify({
                'success': True,
                'message': 'Réponse ajoutée avec succès',
                'reply': reply_dict
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de la création de la réponse'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de l\'ajout de la réponse: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/comments/<int:comment_id>', methods=['GET'])
@token_required
def get_single_comment(current_user, document_id, comment_id):
    """
    Récupère un commentaire spécifique avec ses réponses
    """
    try:
        comment = DocumentComment.get_comment(comment_id)
        
        if not comment:
            return jsonify({
                'success': False,
                'message': 'Commentaire non trouvé'
            }), 404
        
        comment_dict = DocumentComment.to_dict(comment)
        
        return jsonify({
            'success': True,
            'comment': comment_dict
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/comments/count', methods=['GET'])
@token_required
def get_comments_count(current_user, document_id):
    """
    Récupère le nombre total de commentaires d'un document
    """
    try:
        count = DocumentComment.get_comments_count(document_id)
        
        return jsonify({
            'success': True,
            'count': count
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du comptage: {str(e)}'
        }), 500

@bp.route('/my-comments', methods=['GET'])
@token_required
def get_my_comments(current_user):
    """
    Récupère tous les commentaires de l'utilisateur courant
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        comments = DocumentComment.get_user_comments(current_user['id'], page, per_page)
        
        return jsonify({
            'success': True,
            'comments': comments
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération: {str(e)}'
        }), 500 