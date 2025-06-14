from flask import Blueprint, request, jsonify, g, current_app
from AppFlask.models.document_checkout import DocumentCheckout
from AppFlask.api.auth import token_required, admin_required
from AppFlask.models.history import History
import json

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

@checkout_bp.route('/document/<int:document_id>', methods=['POST'])
@token_required
def check_out_document(document_id):
    """
    Réserve (check-out) un document pour modification exclusive
    """
    try:
        expiration = request.json.get('expiration') if request.json else None
        
        checkout_id, error = DocumentCheckout.check_out(
            document_id=document_id,
            user_id=g.current_user['id'],
            expiration=expiration
        )
        
        if error:
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
        
        # Enregistrer dans l'historique
        History.create(
            action_type='CHECK_OUT',
            entity_type='DOCUMENT',
            entity_id=document_id,
            entity_name=f"Document {document_id}",
            description=f"Réservation du document {document_id}",
            metadata=json.dumps({
                'document_id': document_id,
                'expiration': expiration.isoformat() if expiration else None
            }),
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Document réservé avec succès',
            'data': {'checkout_id': checkout_id}
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la réservation du document: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@checkout_bp.route('/document/<int:document_id>/checkin', methods=['POST'])
@token_required
def check_in_document(document_id):
    """
    Libère (check-in) un document précédemment réservé
    """
    try:
        success, error = DocumentCheckout.check_in(
            document_id=document_id,
            user_id=g.current_user['id']
        )
        
        if error:
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
        
        # Enregistrer dans l'historique
        History.create(
            action_type='CHECK_IN',
            entity_type='DOCUMENT',
            entity_id=document_id,
            entity_name=f"Document {document_id}",
            description=f"Libération du document {document_id}",
            metadata=json.dumps({
                'document_id': document_id
            }),
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Document libéré avec succès'
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la libération du document: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@checkout_bp.route('/document/<int:document_id>/force-checkin', methods=['POST'])
@token_required
@admin_required
def force_check_in_document(document_id):
    """
    Force la libération d'un document (pour les administrateurs)
    """
    try:
        success, error = DocumentCheckout.force_check_in(
            document_id=document_id,
            admin_id=g.current_user['id']
        )
        
        if error:
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
        
        # Enregistrer dans l'historique
        History.create(
            action_type='FORCE_CHECK_IN',
            entity_type='DOCUMENT',
            entity_id=document_id,
            entity_name=f"Document {document_id}",
            description=f"Libération forcée du document {document_id}",
            metadata=json.dumps({
                'document_id': document_id
            }),
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Document libéré de force avec succès'
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la libération forcée du document: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@checkout_bp.route('/document/<int:document_id>/status', methods=['GET'])
@token_required
def get_checkout_status(document_id):
    """
    Récupère le statut de réservation d'un document
    """
    try:
        checkout = DocumentCheckout.get_checkout_status(document_id)
        
        if not checkout:
            return jsonify({
                'status': 'success',
                'data': {
                    'is_checked_out': False
                }
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'is_checked_out': True,
                'checkout': DocumentCheckout.to_dict(checkout)
            }
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération du statut de réservation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@checkout_bp.route('/user', methods=['GET'])
@token_required
def get_user_checkouts():
    """
    Récupère tous les documents réservés par l'utilisateur courant
    """
    try:
        checkouts = DocumentCheckout.get_user_checkouts(g.current_user['id'])
        
        return jsonify({
            'status': 'success',
            'data': [DocumentCheckout.to_dict(checkout) for checkout in checkouts]
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des réservations: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@checkout_bp.route('/document/<int:document_id>/history', methods=['GET'])
@token_required
def get_checkout_history(document_id):
    """
    Récupère l'historique complet des réservations d'un document
    """
    try:
        history = DocumentCheckout.get_checkout_history(document_id)
        
        return jsonify({
            'status': 'success',
            'data': [DocumentCheckout.to_dict(checkout) for checkout in history]
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération de l'historique des réservations: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 