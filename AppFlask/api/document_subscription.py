from flask import Blueprint, request, jsonify
from ..models.document_subscription import DocumentSubscription
from .auth import token_required

bp = Blueprint('document_subscription', __name__, url_prefix='/api/documents')

@bp.route('/<int:document_id>/subscribe', methods=['POST'])
@token_required
def subscribe_to_document(current_user, document_id):
    """
    S'abonne aux notifications d'un document
    """
    try:
        data = request.get_json() or {}
        notification_types = data.get('notification_types', ['all'])
        
        # Types de notifications valides
        valid_types = ['modification', 'commentaire', 'partage', 'suppression', 'all']
        
        # Valider les types de notifications
        for ntype in notification_types:
            if ntype not in valid_types:
                return jsonify({
                    'success': False,
                    'message': f'Type de notification invalide: {ntype}'
                }), 400
        
        subscription_id = DocumentSubscription.create(document_id, current_user['id'], notification_types)
        
        if subscription_id:
            return jsonify({
                'success': True,
                'message': 'Abonnement créé avec succès',
                'subscription_id': subscription_id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Vous êtes déjà abonné à ce document'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de l\'abonnement: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/unsubscribe', methods=['DELETE'])
@token_required
def unsubscribe_from_document(current_user, document_id):
    """
    Se désabonne des notifications d'un document
    """
    try:
        success = DocumentSubscription.delete(document_id, current_user['id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Désabonnement effectué avec succès'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Vous n\'êtes pas abonné à ce document'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du désabonnement: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/subscription', methods=['GET'])
@token_required
def get_document_subscription(current_user, document_id):
    """
    Récupère l'abonnement de l'utilisateur pour un document
    """
    try:
        subscription = DocumentSubscription.get_subscription(document_id, current_user['id'])
        
        if subscription:
            subscription_dict = DocumentSubscription.to_dict(subscription)
            return jsonify({
                'success': True,
                'subscription': subscription_dict,
                'is_subscribed': True
            }), 200
        else:
            return jsonify({
                'success': True,
                'subscription': None,
                'is_subscribed': False
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la vérification: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/subscription', methods=['PUT'])
@token_required
def update_document_subscription(current_user, document_id):
    """
    Met à jour les préférences d'abonnement
    """
    try:
        data = request.get_json()
        notification_types = data.get('notification_types', ['all'])
        
        # Types de notifications valides
        valid_types = ['modification', 'commentaire', 'partage', 'suppression', 'all']
        
        # Valider les types de notifications
        for ntype in notification_types:
            if ntype not in valid_types:
                return jsonify({
                    'success': False,
                    'message': f'Type de notification invalide: {ntype}'
                }), 400
        
        success = DocumentSubscription.update(document_id, current_user['id'], notification_types)
        
        if success:
            # Récupérer l'abonnement mis à jour
            subscription = DocumentSubscription.get_subscription(document_id, current_user['id'])
            subscription_dict = DocumentSubscription.to_dict(subscription)
            
            return jsonify({
                'success': True,
                'message': 'Préférences mises à jour avec succès',
                'subscription': subscription_dict
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Abonnement non trouvé'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la mise à jour: {str(e)}'
        }), 500

@bp.route('/my-subscriptions', methods=['GET'])
@token_required
def get_my_subscriptions(current_user):
    """
    Récupère tous les abonnements de l'utilisateur
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        subscriptions = DocumentSubscription.get_user_subscriptions(current_user['id'], page, per_page)
        
        subscriptions_data = []
        for subscription in subscriptions:
            subscription_dict = DocumentSubscription.to_dict(subscription)
            subscriptions_data.append(subscription_dict)
        
        return jsonify({
            'success': True,
            'subscriptions': subscriptions_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/subscribers', methods=['GET'])
@token_required
def get_document_subscribers(current_user, document_id):
    """
    Récupère la liste des abonnés d'un document (pour les propriétaires)
    """
    try:
        subscribers = DocumentSubscription.get_document_subscribers(document_id)
        
        subscribers_data = []
        for subscriber in subscribers:
            subscriber_dict = DocumentSubscription.to_dict(subscriber)
            subscribers_data.append(subscriber_dict)
        
        return jsonify({
            'success': True,
            'subscribers': subscribers_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération: {str(e)}'
        }), 500

@bp.route('/notifications', methods=['GET'])
@token_required
def get_my_notifications(current_user):
    """
    Récupère les notifications de l'utilisateur
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        notifications = DocumentSubscription.get_user_notifications(
            current_user['id'], 
            page, 
            per_page, 
            unread_only
        )
        
        return jsonify({
            'success': True,
            'notifications': notifications
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération: {str(e)}'
        }), 500

@bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_as_read(current_user, notification_id):
    """
    Marque une notification comme lue
    """
    try:
        success = DocumentSubscription.mark_notification_as_read(notification_id, current_user['id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notification marquée comme lue'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Notification non trouvée'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la mise à jour: {str(e)}'
        }), 500

@bp.route('/notifications/mark-all-read', methods=['PUT'])
@token_required
def mark_all_notifications_as_read(current_user):
    """
    Marque toutes les notifications comme lues
    """
    try:
        count = DocumentSubscription.mark_all_notifications_as_read(current_user['id'])
        
        return jsonify({
            'success': True,
            'message': f'{count} notifications marquées comme lues'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la mise à jour: {str(e)}'
        }), 500

@bp.route('/notifications/unread-count', methods=['GET'])
@token_required
def get_unread_notifications_count(current_user):
    """
    Récupère le nombre de notifications non lues
    """
    try:
        count = DocumentSubscription.get_unread_notifications_count(current_user['id'])
        
        return jsonify({
            'success': True,
            'unread_count': count
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du comptage: {str(e)}'
        }), 500 