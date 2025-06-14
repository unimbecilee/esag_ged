from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
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

# Créez un Blueprint pour les routes de workflow
workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')

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

@workflow_bp.route('/api/workflows', methods=['GET'])
@token_required
def get_workflows(current_user):
    """Récupérer tous les workflows"""
    try:
        workflows = Workflow.get_all()
        return jsonify(workflows), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_bp.route('/api/workflows/<int:workflow_id>', methods=['GET'])
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

@workflow_bp.route('/api/workflows/archivage', methods=['GET'])
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

@workflow_bp.route('/api/workflow-instances', methods=['POST'])
@token_required
def create_workflow_instance(current_user):
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
        
        return jsonify({
            'message': 'Instance de workflow créée avec succès',
            'instance_id': instance_id
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_bp.route('/api/workflow-instances/<int:instance_id>', methods=['GET'])
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

@workflow_bp.route('/api/documents/<int:document_id>/workflow-instances', methods=['GET'])
@token_required
def get_document_workflow_instances(current_user, document_id):
    """Récupérer les instances de workflow pour un document"""
    try:
        instances = WorkflowInstance.get_by_document(document_id)
        return jsonify(instances), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_bp.route('/api/workflow-instances/<int:instance_id>/approve', methods=['POST'])
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
            
        return jsonify({'message': 'Étape approuvée avec succès'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_bp.route('/api/workflow-instances/<int:instance_id>/reject', methods=['POST'])
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
            
        return jsonify({'message': 'Étape rejetée avec succès'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_bp.route('/api/workflow-instances/<int:instance_id>/cancel', methods=['POST'])
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

@workflow_bp.route('/api/pending-approvals', methods=['GET'])
@token_required
def get_pending_approvals(current_user):
    """Récupérer les approbations en attente pour l'utilisateur courant"""
    try:
        approvals = WorkflowInstance.get_pending_approvals(current_user['id'])
        return jsonify(approvals), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@workflow_bp.route('/api/workflows/<int:workflow_id>/etapes', methods=['GET'])
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

# Vous pouvez ajouter d'autres routes liées aux workflows ici
# Par exemple, pour lister les workflows, les modifier, les supprimer, etc.