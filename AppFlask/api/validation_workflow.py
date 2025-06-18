"""
API endpoints pour le workflow de validation de documents
"""

from flask import Blueprint, request, jsonify, current_app
from AppFlask.api.auth import token_required
from AppFlask.services.validation_workflow_service import ValidationWorkflowService
from typing import Dict, Any
import json

bp = Blueprint('validation_workflow', __name__)
validation_service = ValidationWorkflowService()

@bp.route('/validation-workflow/start', methods=['POST'])
@token_required
def start_validation_workflow(current_user: Dict[str, Any]) -> tuple:
    """
    Démarre un workflow de validation pour un document
    
    Body:
    {
        "document_id": int,
        "commentaire": str (optionnel)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Données manquantes'
            }), 400
        
        document_id = data.get('document_id')
        if not document_id:
            return jsonify({
                'success': False,
                'message': 'document_id est requis'
            }), 400
        
        commentaire = data.get('commentaire', '')
        
        # Démarrer le workflow
        result = validation_service.start_validation_workflow(
            document_id=document_id,
            initiateur_id=current_user['id'],
            commentaire=commentaire
        )
        
        current_app.logger.info(
            f"Workflow de validation démarré par l'utilisateur {current_user['id']} "
            f"pour le document {document_id}"
        )
        
        return jsonify({
            'success': True,
            'data': result
        }), 201
        
    except ValueError as e:
        current_app.logger.warning(f"Données invalides pour démarrer le workflow: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors du démarrage du workflow: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/validation-workflow/approve', methods=['POST'])
@token_required
def process_approval(current_user: Dict[str, Any]) -> tuple:
    """
    Traite une approbation ou un rejet d'étape de workflow
    
    Body:
    {
        "instance_id": int,
        "etape_id": int,
        "decision": "APPROUVE" | "REJETE",
        "commentaire": str (optionnel)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Données manquantes'
            }), 400
        
        # Validation des données requises
        required_fields = ['instance_id', 'etape_id', 'decision']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'{field} est requis'
                }), 400
        
        instance_id = data['instance_id']
        etape_id = data['etape_id']
        decision = data['decision'].upper()
        commentaire = data.get('commentaire', '')
        
        # Valider la décision
        if decision not in ['APPROUVE', 'REJETE']:
            return jsonify({
                'success': False,
                'message': 'decision doit être "APPROUVE" ou "REJETE"'
            }), 400
        
        # Traiter l'approbation
        result = validation_service.process_approval(
            instance_id=instance_id,
            etape_id=etape_id,
            approbateur_id=current_user['id'],
            decision=decision,
            commentaire=commentaire
        )
        
        current_app.logger.info(
            f"Approbation traitée par l'utilisateur {current_user['id']} "
            f"pour l'instance {instance_id}: {decision}"
        )
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except ValueError as e:
        current_app.logger.warning(f"Données invalides pour l'approbation: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors du traitement de l'approbation: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/validation-workflow/pending', methods=['GET'])
@token_required
def get_pending_approvals(current_user: Dict[str, Any]) -> tuple:
    """
    Récupère les approbations en attente pour l'utilisateur connecté
    """
    try:
        pending_approvals = validation_service.get_pending_approvals(current_user['id'])
        
        return jsonify({
            'success': True,
            'data': pending_approvals,
            'count': len(pending_approvals)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des approbations en attente: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/validation-workflow/instance/<int:instance_id>', methods=['GET'])
@token_required
def get_workflow_instance_details(current_user: Dict[str, Any], instance_id: int) -> tuple:
    """
    Récupère les détails d'une instance de workflow
    """
    try:
        details = validation_service.get_workflow_instance_details(instance_id)
        
        if not details:
            return jsonify({
                'success': False,
                'message': 'Instance de workflow non trouvée'
            }), 404
        
        return jsonify({
            'success': True,
            'data': details
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des détails de l'instance: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/validation-workflow/document/<int:document_id>/status', methods=['GET'])
@token_required
def get_document_workflow_status(current_user: Dict[str, Any], document_id: int) -> tuple:
    """
    Récupère le statut du workflow pour un document donné
    """
    try:
        from AppFlask.db import db_connection
        from psycopg2.extras import RealDictCursor
        
        conn = db_connection()
        if not conn:
            raise Exception("Impossible de se connecter à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer l'instance de workflow active pour ce document
            cursor.execute("""
                SELECT wi.*, e.nom as etape_courante_nom,
                       d.statut as document_statut
                FROM workflow_instance wi
                JOIN document d ON wi.document_id = d.id
                LEFT JOIN etapeworkflow e ON wi.etape_courante_id = e.id
                WHERE wi.document_id = %s
                ORDER BY wi.date_debut DESC
                LIMIT 1
            """, (document_id,))
            
            instance = cursor.fetchone()
            
            if not instance:
                return jsonify({
                    'success': True,
                    'data': {
                        'has_workflow': False,
                        'document_id': document_id
                    }
                }), 200
            
            return jsonify({
                'success': True,
                'data': {
                    'has_workflow': True,
                    'instance_id': instance['id'],
                    'statut': instance['statut'],
                    'etape_courante_nom': instance['etape_courante_nom'],
                    'document_statut': instance['document_statut'],
                    'date_creation': instance['date_debut'].isoformat() if instance['date_debut'] else None,
                    'date_fin': instance['date_fin'].isoformat() if instance['date_fin'] else None
                }
            }), 200
            
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération du statut du workflow: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/validation-workflow/statistics', methods=['GET'])
@token_required
def get_workflow_statistics(current_user: Dict[str, Any]) -> tuple:
    """
    Récupère les statistiques des workflows de validation
    """
    try:
        from AppFlask.db import db_connection
        from psycopg2.extras import RealDictCursor
        
        conn = db_connection()
        if not conn:
            raise Exception("Impossible de se connecter à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Statistiques générales avec les bons statuts enum
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_instances,
                    COUNT(CASE WHEN wi.statut = 'EN_COURS' THEN 1 END) as en_cours,
                    COUNT(CASE WHEN wi.statut = 'TERMINE' THEN 1 END) as approuves,
                    COUNT(CASE WHEN wi.statut = 'REJETE' THEN 1 END) as rejetes,
                    COUNT(CASE WHEN wi.statut = 'ANNULE' THEN 1 END) as annules
                FROM workflow_instance wi
            """)
            
            stats = cursor.fetchone()
            
            # Statistiques par utilisateur (si admin)
            user_stats = []
            if current_user.get('role') == 'Admin':
                cursor.execute("""
                    SELECT u.nom, u.prenom, u.role,
                           COUNT(wi.id) as workflows_inities,
                           COUNT(wa.id) as approbations_donnees
                    FROM utilisateur u
                    LEFT JOIN workflow_instance wi ON u.id = wi.initiateur_id
                    LEFT JOIN workflow_approbation wa ON u.id = wa.approbateur_id
                    GROUP BY u.id, u.nom, u.prenom, u.role
                    ORDER BY workflows_inities DESC, approbations_donnees DESC
                """)
                
                user_stats = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'data': {
                    'general': dict(stats) if stats else {},
                    'users': [dict(u) for u in user_stats]
                }
            }), 200
            
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500 