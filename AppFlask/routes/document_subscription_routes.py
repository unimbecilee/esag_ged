from flask import Blueprint, request, jsonify, g, current_app
from AppFlask.models.document_subscription import DocumentSubscription
from AppFlask.api.auth import token_required
from AppFlask.models.history import History
import json

subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscriptions')

@subscription_bp.route('/document/<int:document_id>', methods=['POST'])
@token_required
def subscribe_to_document(document_id):
    """
    S'abonne à un document pour recevoir des notifications
    """
    try:
        data = request.json or {}
        
        # Valeurs par défaut
        notify_new_version = data.get('notify_new_version', True)
        notify_metadata_change = data.get('notify_metadata_change', True)
        notify_comments = data.get('notify_comments', True)
        notify_workflow = data.get('notify_workflow', True)
        
        subscription_id = DocumentSubscription.create(
            document_id=document_id,
            user_id=g.current_user['id'],
            notify_new_version=notify_new_version,
            notify_metadata_change=notify_metadata_change,
            notify_comments=notify_comments,
            notify_workflow=notify_workflow
        )
        
        # Enregistrer dans l'historique
        History.create(
            action_type='SUBSCRIBE',
            entity_type='DOCUMENT',
            entity_id=document_id,
            entity_name=f"Document {document_id}",
            description=f"Abonnement aux notifications du document {document_id}",
            metadata=json.dumps({
                'document_id': document_id,
                'notify_new_version': notify_new_version,
                'notify_metadata_change': notify_metadata_change,
                'notify_comments': notify_comments,
                'notify_workflow': notify_workflow
            }),
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Abonnement créé avec succès',
            'data': {'subscription_id': subscription_id}
        }), 201
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la création de l'abonnement: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@subscription_bp.route('/document/<int:document_id>', methods=['GET'])
@token_required
def get_document_subscription(document_id):
    """
    Récupère l'abonnement de l'utilisateur courant à un document
    """
    try:
        subscription = DocumentSubscription.get_subscription(document_id, g.current_user['id'])
        
        if not subscription:
            return jsonify({
                'status': 'success',
                'data': {
                    'is_subscribed': False
                }
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'is_subscribed': True,
                'subscription': DocumentSubscription.to_dict(subscription)
            }
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération de l'abonnement: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@subscription_bp.route('/document/<int:document_id>', methods=['DELETE'])
@token_required
def unsubscribe_from_document(document_id):
    """
    Se désabonne d'un document
    """
    try:
        success = DocumentSubscription.delete(document_id, g.current_user['id'])
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Aucun abonnement trouvé'
            }), 404
        
        # Enregistrer dans l'historique
        History.create(
            action_type='UNSUBSCRIBE',
            entity_type='DOCUMENT',
            entity_id=document_id,
            entity_name=f"Document {document_id}",
            description=f"Désabonnement des notifications du document {document_id}",
            metadata=json.dumps({
                'document_id': document_id
            }),
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Désabonnement effectué avec succès'
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors du désabonnement: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@subscription_bp.route('/user', methods=['GET'])
@token_required
def get_user_subscriptions():
    """
    Récupère tous les abonnements de l'utilisateur courant
    """
    try:
        subscriptions = DocumentSubscription.get_user_subscriptions(g.current_user['id'])
        
        return jsonify({
            'status': 'success',
            'data': [DocumentSubscription.to_dict(subscription) for subscription in subscriptions]
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des abonnements: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@subscription_bp.route('/document/<int:document_id>/subscribers', methods=['GET'])
@token_required
def get_document_subscribers(document_id):
    """
    Récupère tous les utilisateurs abonnés à un document
    """
    try:
        event_type = request.args.get('event_type')
        subscribers = DocumentSubscription.get_document_subscribers(document_id, event_type)
        
        return jsonify({
            'status': 'success',
            'data': [DocumentSubscription.to_dict(subscriber) for subscriber in subscribers]
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des abonnés: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 