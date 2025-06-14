from flask import Blueprint, request, jsonify
from ..models.document_checkout import DocumentCheckout
from .auth import token_required
from datetime import datetime, timedelta

bp = Blueprint('document_checkout', __name__, url_prefix='/api/documents')

@bp.route('/<int:document_id>/checkout', methods=['POST'])
@token_required
def checkout_document(current_user, document_id):
    """
    Réserve un document pour modification exclusive
    """
    try:
        data = request.get_json() or {}
        duration_hours = data.get('duration_hours', 24)  # Durée par défaut: 24h
        
        # Calculer l'expiration
        expiration = datetime.utcnow() + timedelta(hours=duration_hours)
        
        checkout_id, error = DocumentCheckout.check_out(document_id, current_user['id'], expiration)
        
        if error:
            return jsonify({
                'success': False,
                'message': error
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Document réservé avec succès',
            'checkout_id': checkout_id,
            'expires_at': expiration.isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la réservation: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/checkin', methods=['POST'])
@token_required
def checkin_document(current_user, document_id):
    """
    Libère un document précédemment réservé
    """
    try:
        success, error = DocumentCheckout.check_in(document_id, current_user['id'])
        
        if error:
            return jsonify({
                'success': False,
                'message': error
            }), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Document libéré avec succès'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de la libération'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la libération: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/checkout/status', methods=['GET'])
@token_required
def get_checkout_status(current_user, document_id):
    """
    Récupère le statut de réservation d'un document
    """
    try:
        checkout = DocumentCheckout.get_checkout_status(document_id)
        
        if checkout:
            checkout_dict = DocumentCheckout.to_dict(checkout)
            
            # Vérifier si c'est l'utilisateur courant qui a réservé
            checkout_dict['is_current_user'] = checkout['checked_out_by'] == current_user['id']
            
            # Vérifier si la réservation a expiré
            checkout_dict['is_expired'] = checkout['expiration'] < datetime.utcnow()
            
            return jsonify({
                'success': True,
                'checkout': checkout_dict,
                'is_checked_out': True
            }), 200
        else:
            return jsonify({
                'success': True,
                'checkout': None,
                'is_checked_out': False
            }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la vérification: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/checkout/force-checkin', methods=['POST'])
@token_required
def force_checkin_document(current_user, document_id):
    """
    Force la libération d'un document (pour les administrateurs)
    """
    try:
        # Vérifier les droits administrateur
        if current_user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': 'Droits administrateur requis'
            }), 403
        
        success, error = DocumentCheckout.force_check_in(document_id, current_user['id'])
        
        if error:
            return jsonify({
                'success': False,
                'message': error
            }), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Document libéré de force avec succès'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de la libération forcée'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la libération forcée: {str(e)}'
        }), 500

@bp.route('/my-checkouts', methods=['GET'])
@token_required
def get_my_checkouts(current_user):
    """
    Récupère tous les documents réservés par l'utilisateur courant
    """
    try:
        checkouts = DocumentCheckout.get_user_checkouts(current_user['id'])
        
        checkouts_data = []
        for checkout in checkouts:
            checkout_dict = DocumentCheckout.to_dict(checkout)
            checkout_dict['is_expired'] = checkout['expiration'] < datetime.utcnow()
            checkouts_data.append(checkout_dict)
        
        return jsonify({
            'success': True,
            'checkouts': checkouts_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/checkout/history', methods=['GET'])
@token_required
def get_checkout_history(current_user, document_id):
    """
    Récupère l'historique des réservations d'un document
    """
    try:
        history = DocumentCheckout.get_checkout_history(document_id)
        
        history_data = []
        for item in history:
            history_dict = DocumentCheckout.to_dict(item)
            history_data.append(history_dict)
        
        return jsonify({
            'success': True,
            'history': history_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération de l\'historique: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/checkout/extend', methods=['POST'])
@token_required
def extend_checkout(current_user, document_id):
    """
    Étend la durée de réservation d'un document
    """
    try:
        data = request.get_json() or {}
        additional_hours = data.get('additional_hours', 24)
        
        success = DocumentCheckout.extend_checkout(document_id, current_user['id'], additional_hours)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Réservation étendue de {additional_hours} heures'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Impossible d\'étendre la réservation'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de l\'extension: {str(e)}'
        }), 500

@bp.route('/admin/cleanup-expired', methods=['POST'])
@token_required
def cleanup_expired_checkouts(current_user):
    """
    Nettoie les réservations expirées (pour les administrateurs)
    """
    try:
        # Vérifier les droits administrateur
        if current_user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': 'Droits administrateur requis'
            }), 403
        
        cleaned_count = DocumentCheckout.cleanup_expired_checkouts()
        
        return jsonify({
            'success': True,
            'message': f'{cleaned_count} réservations expirées nettoyées'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du nettoyage: {str(e)}'
        }), 500 