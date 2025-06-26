from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_required, current_user
from AppFlask.db import db_connection
from AppFlask.api.auth import log_user_action
from psycopg2.extras import RealDictCursor
from AppFlask.models.workflow import Workflow
from AppFlask.models.workflow_instance import WorkflowInstance
from AppFlask.models.etape_workflow import EtapeWorkflow
from AppFlask.models.workflow_approbation import WorkflowApprobation
from AppFlask.auth import token_required
import json

# Créez un Blueprint pour les routes de workflow (pages web)
workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

# Blueprint séparé pour les routes API
workflow_api_bp = Blueprint('workflow_api', __name__, url_prefix='/api')

@workflow_bp.route('/')
@login_required
def list_workflows():
    """Page principale de gestion des workflows"""
    return render_template('workflow/workflow_management.html')

@workflow_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_workflow():
    if request.method == 'POST':
        # Logique de création de workflow ici
        # Par exemple, récupérer les données du formulaire:
        # workflow_name = request.form.get('workflow_name')
        # ... autres champs ...
        flash('Workflow créé avec succès!', 'success') # Exemple de message flash
        return redirect(url_for('workflow.list_workflows'))
    return render_template('workflow/create_workflow.html')

@workflow_bp.route('/instance/<int:instance_id>')
@login_required
def view_instance(instance_id):
    """Voir les détails d'une instance de workflow"""
    user_id = session.get('user_id')
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer l'instance avec toutes les informations
        cursor.execute("""
            SELECT wi.*, 
                   w.nom as workflow_nom, w.description as workflow_description,
                   d.titre as document_titre, d.fichier as document_fichier,
                   u.nom as initiateur_nom, u.prenom as initiateur_prenom,
                   e.nom as etape_courante_nom, e.description as etape_description
            FROM workflow_instance wi
            JOIN workflow w ON wi.workflow_id = w.id
            JOIN document d ON wi.document_id = d.id
            JOIN utilisateur u ON wi.initiateur_id = u.id
            LEFT JOIN etapeworkflow e ON wi.etape_courante_id = e.id
            WHERE wi.id = %s
        """, (instance_id,))
        
        instance = cursor.fetchone()
        if not instance:
            flash('Instance de workflow non trouvée', 'error')
            return redirect(url_for('workflow.list_workflows'))
        
        # Récupérer l'historique des approbations
        cursor.execute("""
            SELECT wa.*, e.nom as etape_nom, e.ordre,
                   u.nom as approbateur_nom, u.prenom as approbateur_prenom
            FROM workflow_approbation wa
            JOIN etapeworkflow e ON wa.etape_id = e.id
            JOIN utilisateur u ON wa.approbateur_id = u.id
            WHERE wa.instance_id = %s
            ORDER BY e.ordre, wa.date_decision
        """, (instance_id,))
        
        approbations = cursor.fetchall()
        
        # Récupérer toutes les étapes du workflow
        cursor.execute("""
            SELECT e.*, 
                   COUNT(wa.id) as approbateurs_count,
                   COUNT(wapp.id) as approbations_count
            FROM etapeworkflow e
            LEFT JOIN workflow_approbateur wa ON e.id = wa.etape_id
            LEFT JOIN workflow_approbation wapp ON e.id = wapp.etape_id AND wapp.instance_id = %s
            WHERE e.workflow_id = %s
            GROUP BY e.id
            ORDER BY e.ordre
        """, (instance_id, instance['workflow_id']))
        
        etapes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('workflow/instance_detail.html',
                             instance=instance,
                             approbations=approbations,
                             etapes=etapes)
        
    except Exception as e:
        flash(f'Erreur lors de la récupération de l\'instance: {str(e)}', 'error')
        return redirect(url_for('workflow.list_workflows'))

@workflow_bp.route('/approve/<int:instance_id>', methods=['POST'])
@login_required
def approve_instance(instance_id):
    """Approuver une étape de workflow"""
    user_id = session.get('user_id')
    commentaire = request.form.get('commentaire', '')
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer l'instance et l'étape courante
        cursor.execute("""
            SELECT wi.*, e.nom as etape_nom, d.titre as document_titre
            FROM workflow_instance wi
            JOIN etapeworkflow e ON wi.etape_courante_id = e.id
            JOIN document d ON wi.document_id = d.id
            WHERE wi.id = %s AND wi.statut = 'EN_COURS'
        """, (instance_id,))
        
        instance = cursor.fetchone()
        if not instance:
            flash('Instance non trouvée ou déjà terminée', 'error')
            return redirect(url_for('workflow.list_workflows'))
        
        # Vérifier que l'utilisateur peut approuver cette étape
        cursor.execute("""
            SELECT 1 FROM workflow_approbateur wa
            WHERE wa.etape_id = %s 
            AND (wa.utilisateur_id = %s 
                 OR (wa.role_id IS NOT NULL AND EXISTS (
                     SELECT 1 FROM role r 
                     JOIN utilisateur u2 ON u2.role = r.nom 
                     WHERE r.id = wa.role_id AND u2.id = %s
                 ))
                 OR wa.organisation_id IN (SELECT organisation_id FROM membre WHERE utilisateur_id = %s))
        """, (instance['etape_courante_id'], user_id, user_id, user_id))
        
        if not cursor.fetchone():
            flash('Vous n\'êtes pas autorisé à approuver cette étape', 'error')
            return redirect(url_for('workflow.view_instance', instance_id=instance_id))
        
        # Enregistrer l'approbation
        cursor.execute("""
            INSERT INTO workflow_approbation (instance_id, etape_id, approbateur_id, decision, commentaire)
            VALUES (%s, %s, %s, 'APPROUVE', %s)
        """, (instance_id, instance['etape_courante_id'], user_id, commentaire))
        
        conn.commit()
        
        # Enregistrer l'action
        log_user_action(
            user_id,
            'WORKFLOW_APPROVE',
            f"Approbation de l'étape '{instance['etape_nom']}' pour le document '{instance['document_titre']}'",
            request
        )
        
        flash('Étape approuvée avec succès', 'success')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        flash(f'Erreur lors de l\'approbation: {str(e)}', 'error')
    
    return redirect(url_for('workflow.view_instance', instance_id=instance_id))

@workflow_bp.route('/reject/<int:instance_id>', methods=['POST'])
@login_required
def reject_instance(instance_id):
    """Rejeter une étape de workflow"""
    user_id = session.get('user_id')
    commentaire = request.form.get('commentaire', '')
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer l'instance et l'étape courante
        cursor.execute("""
            SELECT wi.*, e.nom as etape_nom, d.titre as document_titre
            FROM workflow_instance wi
            JOIN etapeworkflow e ON wi.etape_courante_id = e.id
            JOIN document d ON wi.document_id = d.id
            WHERE wi.id = %s AND wi.statut = 'EN_COURS'
        """, (instance_id,))
        
        instance = cursor.fetchone()
        if not instance:
            flash('Instance non trouvée ou déjà terminée', 'error')
            return redirect(url_for('workflow.list_workflows'))
        
        # Enregistrer le rejet
        cursor.execute("""
            INSERT INTO workflow_approbation (instance_id, etape_id, approbateur_id, decision, commentaire)
            VALUES (%s, %s, %s, 'REJETE', %s)
        """, (instance_id, instance['etape_courante_id'], user_id, commentaire))
        
        # Marquer l'instance comme rejetée
        cursor.execute("""
            UPDATE workflow_instance 
            SET statut = 'REJETE', date_fin = NOW()
            WHERE id = %s
        """, (instance_id,))
        
        conn.commit()
        
        # Enregistrer l'action
        log_user_action(
            user_id,
            'WORKFLOW_REJECT',
            f"Rejet de l'étape '{instance['etape_nom']}' pour le document '{instance['document_titre']}'",
            request
        )
        
        flash('Workflow rejeté', 'warning')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        flash(f'Erreur lors du rejet: {str(e)}', 'error')
    
    return redirect(url_for('workflow.view_instance', instance_id=instance_id))

@workflow_api_bp.route('/workflows', methods=['GET'])
@token_required
def get_workflows(current_user):
    """Récupérer tous les workflows"""
    try:
        workflows = Workflow.get_all()
        return jsonify(workflows), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/workflows/<int:workflow_id>', methods=['GET'])
@token_required
def get_workflow(current_user, workflow_id):
    """Récupérer un workflow par ID"""
    try:
        workflow = Workflow.get_by_id(workflow_id)
        if not workflow:
            return jsonify({'message': 'Workflow non trouvé'}), 404
        return jsonify(workflow), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/workflows/archivage', methods=['GET'])
@token_required
def get_archivage_workflow(current_user):
    """Récupérer le workflow d'archivage"""
    try:
        workflows = Workflow.get_all()
        archivage_workflow = next((w for w in workflows if 'archivage' in w['nom'].lower()), None)
        
        if not archivage_workflow:
            return jsonify({'message': 'Workflow d\'archivage non trouvé'}), 404
            
        return jsonify(archivage_workflow), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/workflow-instances', methods=['POST'])
@token_required
def create_new_workflow_instance(current_user):
    """Créer une nouvelle instance de workflow"""
    try:
        data = request.get_json()
        
        if not data or not data.get('workflow_id') or not data.get('document_id'):
            return jsonify({'message': 'Données invalides'}), 400
        
        workflow_id = data.get('workflow_id')
        document_id = data.get('document_id')
        commentaire = data.get('commentaire')
        
        # Vérifier si le workflow existe
        workflow = Workflow.get_by_id(workflow_id)
        if not workflow:
            return jsonify({'message': 'Workflow non trouvé'}), 404
        
        # Créer l'instance
        instance_id = WorkflowInstance.create(
            workflow_id=workflow_id,
            document_id=document_id,
            initiateur_id=current_user['id'],
            commentaire=commentaire
        )
        
        # Déclencher les notifications pour la première étape
        try:
            from AppFlask.services.notification_service import NotificationService
            
            # Récupérer les informations nécessaires pour les notifications
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les détails de l'instance créée
            cursor.execute("""
                SELECT wi.*, d.titre as document_titre, w.nom as workflow_nom,
                       u.nom as initiateur_nom, u.prenom as initiateur_prenom
                FROM workflow_instance wi
                JOIN document d ON wi.document_id = d.id
                JOIN workflow w ON wi.workflow_id = w.id
                JOIN utilisateur u ON wi.initiateur_id = u.id
                WHERE wi.id = %s
            """, (instance_id,))
            
            instance_info = cursor.fetchone()
            
            if instance_info:
                # Récupérer la première étape du workflow
                cursor.execute("""
                    SELECT e.*, u.id as responsable_user_id
                    FROM etapeworkflow e
                    LEFT JOIN utilisateur u ON u.role = CASE 
                        WHEN e.responsable_id IS NOT NULL THEN (SELECT role FROM utilisateur WHERE id = e.responsable_id)
                        ELSE 'chef_de_service'
                    END
                    WHERE e.workflow_id = %s 
                    ORDER BY e.ordre ASC 
                    LIMIT 1
                """, (workflow_id,))
                
                premiere_etape = cursor.fetchone()
                
                if premiere_etape:
                    # Récupérer tous les utilisateurs avec le rôle responsable de la première étape
                    cursor.execute("""
                        SELECT id, nom, prenom FROM utilisateur 
                        WHERE role = 'chef_de_service'
                        AND id != %s
                    """, (current_user['id'],))
                    
                    responsables = cursor.fetchall()
                    
                    # Créer des notifications pour tous les responsables
                    for responsable in responsables:
                        notification_id = NotificationService.create_workflow_notification(
                            user_id=responsable['id'],
                            workflow_instance_id=instance_id,
                            notification_type='WORKFLOW_APPROVAL_REQUIRED',
                            document_id=document_id,
                            document_title=instance_info['document_titre'],
                            workflow_title=instance_info['workflow_nom'],
                            etape_name=premiere_etape['nom'],
                            initiateur_name=f"{instance_info['initiateur_prenom']} {instance_info['initiateur_nom']}",
                            priority=3,
                            send_email=True
                        )
                        
                        if notification_id:
                            current_app.logger.info(f"Notification créée pour {responsable['prenom']} {responsable['nom']} (ID: {notification_id})")
                        else:
                            current_app.logger.warning(f"Échec création notification pour {responsable['prenom']} {responsable['nom']}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            current_app.logger.error(f"Erreur lors de l'envoi des notifications: {str(e)}")
            # Ne pas faire échouer la création de l'instance pour un problème de notification
        
        return jsonify({
            'message': 'Instance de workflow créée avec succès',
            'instance_id': instance_id
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/workflow-instances/<int:instance_id>', methods=['GET'])
@token_required
def get_workflow_instance(current_user, instance_id):
    """Récupérer une instance de workflow par ID"""
    try:
        instance = WorkflowInstance.get_by_id(instance_id)
        if not instance:
            return jsonify({'message': 'Instance non trouvée'}), 404
        return jsonify(instance), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/documents/<int:document_id>/workflow-instances', methods=['GET'])
@token_required
def get_document_workflow_instances(current_user, document_id):
    """Récupérer les instances de workflow pour un document"""
    try:
        instances = WorkflowInstance.get_by_document(document_id)
        return jsonify(instances), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/workflow-instances', methods=['GET'])
@token_required
def get_all_workflow_instances(current_user):
    """Récupérer toutes les instances de workflow avec pagination optionnelle"""
    try:
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)
        
        instances = WorkflowInstance.get_all(limit=limit, offset=offset)
        
        return jsonify([WorkflowInstance.to_dict(i) for i in instances]), 200
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des instances de workflow: {e}")
        return jsonify({'error': str(e)}), 500

@workflow_api_bp.route('/workflow-instances/<int:instance_id>/approve', methods=['POST'])
@token_required
def approve_workflow_step(current_user, instance_id):
    """Approuver une étape de workflow"""
    try:
        data = request.get_json()
        
        if not data or not data.get('etape_id'):
            return jsonify({'message': 'Données invalides'}), 400
        
        etape_id = data.get('etape_id')
        commentaire = data.get('commentaire')
        
        # Approuver l'étape
        success = WorkflowInstance.approve_step(
            instance_id=instance_id,
            etape_id=etape_id,
            approbateur_id=current_user['id'],
            commentaire=commentaire
        )
        
        if not success:
            return jsonify({'message': 'Échec de l\'approbation'}), 400
        
        # Créer des notifications après l'approbation
        try:
            from AppFlask.services.notification_service import NotificationService
            
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les informations de l'instance et de l'étape
            cursor.execute("""
                SELECT wi.*, d.titre as document_titre, w.nom as workflow_nom,
                       u.nom as initiateur_nom, u.prenom as initiateur_prenom,
                       e.nom as etape_nom
                FROM workflow_instance wi
                JOIN document d ON wi.document_id = d.id
                JOIN workflow w ON wi.workflow_id = w.id
                JOIN utilisateur u ON wi.initiateur_id = u.id
                JOIN etapeworkflow e ON e.id = %s
                WHERE wi.id = %s
            """, (etape_id, instance_id))
            
            instance_info = cursor.fetchone()
            
            if instance_info:
                # 1. Notifier l'initiateur de l'approbation
                NotificationService.create_workflow_notification(
                    user_id=instance_info['initiateur_id'],
                    workflow_instance_id=instance_id,
                    notification_type='WORKFLOW_APPROVED',
                    document_id=instance_info['document_id'],
                    document_title=instance_info['document_titre'],
                    workflow_title=instance_info['workflow_nom'],
                    etape_name=instance_info['etape_nom'],
                    priority=2,
                    send_email=True
                )
                
                # 2. Vérifier s'il y a une étape suivante
                cursor.execute("""
                    SELECT e.*, e.ordre as etape_ordre
                    FROM etapeworkflow e
                    WHERE e.workflow_id = %s AND e.ordre > (
                        SELECT ordre FROM etapeworkflow WHERE id = %s
                    )
                    ORDER BY e.ordre ASC
                    LIMIT 1
                """, (instance_info['workflow_id'], etape_id))
                
                etape_suivante = cursor.fetchone()
                
                if etape_suivante:
                    # Il y a une étape suivante, notifier les responsables
                    cursor.execute("""
                        SELECT id, nom, prenom FROM utilisateur 
                        WHERE role = 'chef_de_service'
                        AND id != %s
                    """, (current_user['id'],))
                    
                    responsables_suivants = cursor.fetchall()
                    
                    for responsable in responsables_suivants:
                        NotificationService.create_workflow_notification(
                            user_id=responsable['id'],
                            workflow_instance_id=instance_id,
                            notification_type='WORKFLOW_APPROVAL_REQUIRED',
                            document_id=instance_info['document_id'],
                            document_title=instance_info['document_titre'],
                            workflow_title=instance_info['workflow_nom'],
                            etape_name=etape_suivante['nom'],
                            initiateur_name=f"{instance_info['initiateur_prenom']} {instance_info['initiateur_nom']}",
                            priority=3,
                            send_email=True
                        )
                else:
                    # Workflow terminé, notifier l'initiateur
                    NotificationService.create_workflow_notification(
                        user_id=instance_info['initiateur_id'],
                        workflow_instance_id=instance_id,
                        notification_type='WORKFLOW_COMPLETED',
                        document_id=instance_info['document_id'],
                        document_title=instance_info['document_titre'],
                        workflow_title=instance_info['workflow_nom'],
                        priority=2,
                        send_email=True
                    )
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            current_app.logger.error(f"Erreur notifications approbation: {str(e)}")
            # Ne pas faire échouer l'approbation pour un problème de notification
            
        return jsonify({'message': 'Étape approuvée avec succès'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/workflow-instances/<int:instance_id>/reject', methods=['POST'])
@token_required
def reject_workflow_step(current_user, instance_id):
    """Rejeter une étape de workflow"""
    try:
        data = request.get_json()
        
        if not data or not data.get('etape_id'):
            return jsonify({'message': 'Données invalides'}), 400
        
        etape_id = data.get('etape_id')
        commentaire = data.get('commentaire')
        
        # Rejeter l'étape
        success = WorkflowInstance.reject_step(
            instance_id=instance_id,
            etape_id=etape_id,
            approbateur_id=current_user['id'],
            commentaire=commentaire
        )
        
        if not success:
            return jsonify({'message': 'Échec du rejet'}), 400
        
        # Créer une notification de rejet
        try:
            from AppFlask.services.notification_service import NotificationService
            
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les informations de l'instance
            cursor.execute("""
                SELECT wi.*, d.titre as document_titre, w.nom as workflow_nom,
                       u.nom as initiateur_nom, u.prenom as initiateur_prenom,
                       e.nom as etape_nom
                FROM workflow_instance wi
                JOIN document d ON wi.document_id = d.id
                JOIN workflow w ON wi.workflow_id = w.id
                JOIN utilisateur u ON wi.initiateur_id = u.id
                JOIN etapeworkflow e ON e.id = %s
                WHERE wi.id = %s
            """, (etape_id, instance_id))
            
            instance_info = cursor.fetchone()
            
            if instance_info:
                # Notifier l'initiateur du rejet
                NotificationService.create_workflow_notification(
                    user_id=instance_info['initiateur_id'],
                    workflow_instance_id=instance_id,
                    notification_type='WORKFLOW_REJECTED',
                    document_id=instance_info['document_id'],
                    document_title=instance_info['document_titre'],
                    workflow_title=instance_info['workflow_nom'],
                    etape_name=instance_info['etape_nom'],
                    priority=2,
                    send_email=True
                )
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            current_app.logger.error(f"Erreur notifications rejet: {str(e)}")
            # Ne pas faire échouer le rejet pour un problème de notification
            
        return jsonify({'message': 'Étape rejetée avec succès'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/workflow-instances/<int:instance_id>/cancel', methods=['POST'])
@token_required
def cancel_workflow_instance(current_user, instance_id):
    """Annuler une instance de workflow"""
    try:
        # Annuler l'instance
        success = WorkflowInstance.cancel(
            instance_id=instance_id,
            user_id=current_user['id']
        )
        
        if not success:
            return jsonify({'message': 'Échec de l\'annulation'}), 400
            
        return jsonify({'message': 'Instance annulée avec succès'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/pending-approvals', methods=['GET'])
@token_required
def get_pending_approvals(current_user):
    """Récupérer les approbations en attente pour l'utilisateur courant"""
    try:
        approvals = WorkflowInstance.get_pending_approvals(current_user['id'])
        return jsonify(approvals), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/workflows/<int:workflow_id>/etapes', methods=['GET'])
@token_required
def get_workflow_etapes(current_user, workflow_id):
    """Récupérer les étapes d'un workflow"""
    try:
        current_app.logger.info(f"Récupération des étapes pour le workflow {workflow_id}")
        
        # Vérifier si le workflow existe
        workflow = Workflow.get_by_id(workflow_id)
        if not workflow:
            current_app.logger.warning(f"Workflow {workflow_id} non trouvé")
            return jsonify({'message': 'Workflow non trouvé'}), 404
            
        # Récupérer les étapes
        etapes = Workflow.get_etapes(workflow_id)
        current_app.logger.info(f"Étapes récupérées pour le workflow {workflow_id}: {len(etapes)} étapes trouvées")
        
        return jsonify(etapes), 200
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des étapes du workflow {workflow_id}: {e}")
        return jsonify({'message': str(e)}), 500

@workflow_api_bp.route('/workflow-stats', methods=['GET'])
@token_required
def get_workflow_stats(current_user):
    """Récupérer les statistiques des workflows"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Statistiques générales
        stats = {}
        
        # 1. Nombre total de workflows (modèles)
        cursor.execute("SELECT COUNT(*) as count FROM workflow")
        stats['totalWorkflows'] = cursor.fetchone()['count']
        
        # 2. Instances actives (en cours)
        cursor.execute("SELECT COUNT(*) as count FROM workflow_instance WHERE statut = 'EN_COURS'")
        stats['activeInstances'] = cursor.fetchone()['count']
        
        # 3. Approbations en attente pour l'utilisateur courant
        user_role = current_user.get('role', '')
        cursor.execute("""
            SELECT COUNT(DISTINCT wi.id) as count
            FROM workflow_instance wi
            JOIN etapeworkflow e ON wi.etape_courante_id = e.id
            JOIN workflow_approbateur wa ON e.id = wa.etape_id
            LEFT JOIN role r ON wa.role_id = r.id
            WHERE wi.statut = 'EN_COURS'
            AND (r.nom = %s OR wa.utilisateur_id = %s)
            AND NOT EXISTS (
                SELECT 1 FROM workflow_approbation wapp
                WHERE wapp.instance_id = wi.id 
                AND wapp.etape_id = e.id 
                AND wapp.approbateur_id = %s
            )
        """, (user_role, current_user['id'], current_user['id']))
        stats['pendingApprovals'] = cursor.fetchone()['count']
        
        # 4. Instances terminées aujourd'hui
        cursor.execute("""
            SELECT COUNT(*) as count FROM workflow_instance 
            WHERE statut = 'TERMINE'
            AND DATE(date_fin) = CURRENT_DATE
        """)
        stats['completedToday'] = cursor.fetchone()['count']
        
        # 5. Répartition par statut
        cursor.execute("""
            SELECT statut, COUNT(*) as count 
            FROM workflow_instance 
            GROUP BY statut
        """)
        status_breakdown = {row['statut']: row['count'] for row in cursor.fetchall()}
        stats['statusBreakdown'] = status_breakdown
        
        # 6. Instances récentes (dernières 10)
        cursor.execute("""
            SELECT wi.id, wi.statut, wi.date_debut, wi.date_fin,
                   d.titre as document_titre,
                   w.nom as workflow_nom,
                   e.nom as etape_courante_nom,
                   u.nom as initiateur_nom, u.prenom as initiateur_prenom
            FROM workflow_instance wi
            JOIN document d ON wi.document_id = d.id
            JOIN workflow w ON wi.workflow_id = w.id
            LEFT JOIN etapeworkflow e ON wi.etape_courante_id = e.id
            JOIN utilisateur u ON wi.initiateur_id = u.id
            ORDER BY wi.date_debut DESC
            LIMIT 10
        """)
        recent_instances = [dict(row) for row in cursor.fetchall()]
        stats['recentInstances'] = recent_instances
        
        cursor.close()
        conn.close()
        
        return jsonify(stats), 200
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        return jsonify({'message': str(e)}), 500

# Vous pouvez ajouter d'autres routes liées aux workflows ici
# Par exemple, pour lister les workflows, les modifier, les supprimer, etc.