"""
Service pour gérer le workflow automatique de validation de documents
Workflow en 2 étapes : Chef de service -> Directeur
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from AppFlask.services.notification_service import NotificationService
from AppFlask.models.history import History
import logging

logger = logging.getLogger(__name__)

class ValidationWorkflowService:
    """Service pour gérer le workflow de validation automatique"""
    
    WORKFLOW_NAME = "Validation Document"
    WORKFLOW_DESCRIPTION = "Workflow automatique de validation en 2 étapes : Chef de service puis Directeur"
    
    # Statuts des instances (selon enum existant)
    STATUS_EN_COURS = "EN_COURS"
    STATUS_APPROUVE = "TERMINE"  # Utilise TERMINE au lieu d'APPROUVE
    STATUS_REJETE = "REJETE"
    STATUS_ANNULE = "ANNULE"
    
    # Décisions d'approbation
    DECISION_APPROUVE = "APPROUVE"
    DECISION_REJETE = "REJETE"
    DECISION_EN_ATTENTE = "EN_ATTENTE"
    
    # Rôles
    ROLE_CHEF_SERVICE = "chef_de_service"
    ROLE_DIRECTEUR = "Admin"  # Utilise Admin comme directeur
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    @staticmethod
    def get_or_create_workflow() -> int:
        """Récupère ou crée le workflow de validation"""
        conn = db_connection()
        if not conn:
            raise Exception("Impossible de se connecter à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Vérifier si le workflow existe
            cursor.execute("""
                SELECT id FROM workflow 
                WHERE nom = %s
            """, (ValidationWorkflowService.WORKFLOW_NAME,))
            
            workflow = cursor.fetchone()
            if workflow:
                return workflow['id']
            
            # Créer le workflow avec le bon statut
            cursor.execute("""
                INSERT INTO workflow (nom, description, date_creation, statut)
                VALUES (%s, %s, NOW(), 'en_cours')
                RETURNING id
            """, (
                ValidationWorkflowService.WORKFLOW_NAME,
                ValidationWorkflowService.WORKFLOW_DESCRIPTION
            ))
            
            workflow_id = cursor.fetchone()['id']
            
            # Créer les étapes
            # Étape 1 : Chef de service
            cursor.execute("""
                INSERT INTO etapeworkflow (workflow_id, nom, description, ordre, type_approbation, delai_max)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                workflow_id,
                "Validation Chef de Service",
                "Validation par le chef de service",
                1,
                "SIMPLE",
                7  # 7 jours
            ))
            
            etape1_id = cursor.fetchone()['id']
            
            # Étape 2 : Directeur
            cursor.execute("""
                INSERT INTO etapeworkflow (workflow_id, nom, description, ordre, type_approbation, delai_max)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                workflow_id,
                "Validation Directeur",
                "Validation finale par le directeur",
                2,
                "SIMPLE",
                7  # 7 jours
            ))
            
            etape2_id = cursor.fetchone()['id']
            
            # Ajouter les approbateurs par rôle (utilise role_id)
            # Récupérer l'ID du rôle chef_de_service
            cursor.execute("SELECT id FROM role WHERE nom = %s", (ValidationWorkflowService.ROLE_CHEF_SERVICE,))
            chef_role = cursor.fetchone()
            if chef_role:
                cursor.execute("""
                    INSERT INTO workflow_approbateur (etape_id, role_id)
                    VALUES (%s, %s)
                """, (etape1_id, chef_role['id']))
            
            # Récupérer l'ID du rôle Admin
            cursor.execute("SELECT id FROM role WHERE nom = %s", (ValidationWorkflowService.ROLE_DIRECTEUR,))
            admin_role = cursor.fetchone()
            if admin_role:
                cursor.execute("""
                    INSERT INTO workflow_approbateur (etape_id, role_id)
                    VALUES (%s, %s)
                """, (etape2_id, admin_role['id']))
            
            conn.commit()
            logger.info(f"Workflow de validation créé avec l'ID {workflow_id}")
            
            return workflow_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def start_validation_workflow(self, document_id: int, initiateur_id: int, commentaire: str = "") -> Dict:
        """Démarre un workflow de validation pour un document"""
        conn = db_connection()
        if not conn:
            raise Exception("Impossible de se connecter à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Vérifier que le document existe
            cursor.execute("SELECT id, titre FROM document WHERE id = %s", (document_id,))
            document = cursor.fetchone()
            if not document:
                raise Exception("Document non trouvé")
            
            # Vérifier qu'il n'y a pas déjà un workflow en cours pour ce document
            cursor.execute("""
                SELECT id FROM workflow_instance 
                WHERE document_id = %s AND statut = %s
            """, (document_id, self.STATUS_EN_COURS))
            
            if cursor.fetchone():
                raise Exception("Un workflow de validation est déjà en cours pour ce document")
            
            # Récupérer ou créer le workflow
            workflow_id = self.get_or_create_workflow()
            
            # Récupérer la première étape
            cursor.execute("""
                SELECT id FROM etapeworkflow 
                WHERE workflow_id = %s 
                ORDER BY ordre 
                LIMIT 1
            """, (workflow_id,))
            
            premiere_etape = cursor.fetchone()
            if not premiere_etape:
                raise Exception("Aucune étape trouvée pour le workflow")
            
            # Créer l'instance de workflow
            cursor.execute("""
                INSERT INTO workflow_instance (
                    workflow_id, document_id, initiateur_id, 
                    etape_courante_id, statut, date_debut, commentaire
                )
                VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                RETURNING id
            """, (
                workflow_id, document_id, initiateur_id,
                premiere_etape['id'], self.STATUS_EN_COURS, commentaire
            ))
            
            instance_id = cursor.fetchone()['id']
            
            # Mettre à jour le statut du document
            cursor.execute("""
                UPDATE document 
                SET statut = 'EN_VALIDATION' 
                WHERE id = %s
            """, (document_id,))
            
            conn.commit()
            
            # Enregistrer dans l'historique (version simplifiée pour éviter les erreurs de colonne)
            try:
                cursor.execute("""
                    INSERT INTO history (action_type, entity_type, entity_id, entity_name, description, user_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (
                    'START_WORKFLOW',
                    'DOCUMENT',
                    document_id,
                    document['titre'],
                    f"Démarrage du workflow de validation",
                    initiateur_id
                ))
                logger.info("Historique enregistré avec succès")
            except Exception as hist_error:
                logger.warning(f"Erreur lors de l'enregistrement de l'historique (non bloquante): {hist_error}")
            
            # Notifier les approbateurs de la première étape
            self._notify_next_approvers(instance_id, premiere_etape['id'])
            
            logger.info(f"Workflow de validation démarré pour le document {document_id}, instance {instance_id}")
            
            return {
                'instance_id': instance_id,
                'workflow_id': workflow_id,
                'etape_courante_id': premiere_etape['id'],
                'status': self.STATUS_EN_COURS,
                'message': 'Workflow de validation démarré avec succès'
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def process_approval(self, instance_id: int, etape_id: int, approbateur_id: int, 
                        decision: str, commentaire: str = "") -> Dict:
        """Traite une approbation ou un rejet"""
        logger.info(f"🔍 Début process_approval: instance_id={instance_id}, etape_id={etape_id}, approbateur_id={approbateur_id}, decision={decision}")
        
        if decision not in [self.DECISION_APPROUVE, self.DECISION_REJETE]:
            raise ValueError("Décision invalide")
        
        conn = db_connection()
        if not conn:
            raise Exception("Impossible de se connecter à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            logger.info("🔍 Curseur créé avec RealDictCursor")
            
            # Récupérer l'instance avec ses informations
            logger.info("🔍 Récupération de l'instance...")
            cursor.execute("""
                SELECT wi.*, d.titre as document_titre,
                       e.nom as etape_nom, e.ordre as etape_ordre
                FROM workflow_instance wi
                JOIN document d ON wi.document_id = d.id
                JOIN etapeworkflow e ON wi.etape_courante_id = e.id
                WHERE wi.id = %s AND wi.statut = %s
            """, (instance_id, self.STATUS_EN_COURS))
            
            instance_result = cursor.fetchone()
            logger.info(f"🔍 Résultat requête instance: type={type(instance_result)}, contenu={instance_result}")
            
            if not instance_result:
                raise Exception("Instance de workflow non trouvée ou déjà terminée")
            
            # Convertir en dictionnaire si nécessaire
            instance = dict(instance_result) if instance_result else None
            logger.info(f"🔍 Instance convertie: type={type(instance)}, keys={list(instance.keys()) if instance else 'None'}")
            
            # Vérifier que l'utilisateur peut approuver cette étape
            logger.info(f"🔍 Vérification des permissions pour user_id={approbateur_id}, etape_id={etape_id}")
            try:
                can_approve = self._can_user_approve_step(approbateur_id, etape_id)
                logger.info(f"🔍 Résultat vérification permissions: {can_approve}")
                if not can_approve:
                    raise Exception("Vous n'êtes pas autorisé à approuver cette étape")
            except Exception as perm_error:
                logger.error(f"🔍 Erreur lors de la vérification des permissions: {perm_error}")
                raise Exception(f"Erreur de vérification des permissions: {perm_error}")
            
            # Vérifier que c'est bien l'étape courante
            if instance['etape_courante_id'] != etape_id:
                raise Exception("Cette étape n'est pas l'étape courante")
            
            # Enregistrer l'approbation
            cursor.execute("""
                INSERT INTO workflow_approbation (
                    instance_id, etape_id, approbateur_id, decision, 
                    date_decision, commentaire
                )
                VALUES (%s, %s, %s, %s, NOW(), %s)
            """, (instance_id, etape_id, approbateur_id, decision, commentaire))
            
            result = {}
            
            if decision == self.DECISION_REJETE:
                logger.info("🔍 Traitement du REJET - Version simplifiée")
                
                # 1. Rejeter l'instance de workflow
                cursor.execute("""
                    UPDATE workflow_instance 
                    SET statut = %s, date_fin = NOW()
                    WHERE id = %s
                """, (self.STATUS_REJETE, instance_id))
                logger.info("🔍 Instance de workflow mise à jour : REJETE")
                
                # 2. Mettre à jour le statut du document à 'REJETE'
                document_id = instance.get('document_id')
                if document_id:
                    cursor.execute("""
                        UPDATE document 
                        SET statut = 'REJETE' 
                        WHERE id = %s
                    """, (document_id,))
                    logger.info(f"🔍 Document {document_id} mis à jour : statut REJETE")
                
                # 3. Préparer le résultat
                result = {
                    'status': self.STATUS_REJETE,
                    'message': 'Document rejeté avec succès',
                    'final': True
                }
                logger.info("🔍 Résultat de rejet préparé")
                
                # 4. Enregistrement dans l'historique (version simplifiée)
                try:
                    document_titre = instance.get('document_titre', 'Document')
                    etape_nom = instance.get('etape_nom', 'Étape')
                    
                    logger.info(f"🔍 Enregistrement historique - doc_id={document_id}, titre={document_titre}")
                    
                    # Utilisation directe de la base de données pour l'historique
                    cursor.execute("""
                        INSERT INTO history (action_type, entity_type, entity_id, entity_name, description, user_id, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        'REJECT_WORKFLOW',
                        'DOCUMENT', 
                        document_id,
                        document_titre,
                        f"Document rejeté à l'étape '{etape_nom}' - {commentaire}",
                        approbateur_id
                    ))
                    logger.info("🔍 Historique enregistré avec succès")
                    
                except Exception as hist_error:
                    logger.warning(f"🔍 Erreur historique (non bloquante): {hist_error}")
                
                # 5. Notification simplifiée (non bloquante)
                try:
                    # Récupérer l'initiateur pour notification
                    cursor.execute("""
                        SELECT initiateur_id FROM workflow_instance WHERE id = %s
                    """, (instance_id,))
                    initiateur_result = cursor.fetchone()
                    
                    if initiateur_result:
                        initiateur_id = initiateur_result.get('initiateur_id') if isinstance(initiateur_result, dict) else initiateur_result[0]
                        
                        # Créer une notification simple (sans colonne data)
                        cursor.execute("""
                            INSERT INTO notifications (user_id, type, title, message, created_at)
                            VALUES (%s, %s, %s, %s, NOW())
                        """, (
                            initiateur_id,
                            'workflow_rejected',
                            'Document rejeté',
                            f"Votre document '{document_titre}' a été rejeté"
                        ))
                        logger.info(f"🔍 Notification envoyée à l'initiateur {initiateur_id}")
                        
                except Exception as notif_error:
                    logger.warning(f"🔍 Erreur notification (non bloquante): {notif_error}")
                
                logger.info("🔍 Rejet traité avec succès")
                
            else:  # APPROUVE
                logger.info("🔍 Traitement de l'APPROBATION - Version simplifiée")
                
                # Chercher l'étape suivante
                cursor.execute("""
                    SELECT ew.id, ew.nom 
                    FROM etapeworkflow ew
                    JOIN etapeworkflow current_ew ON current_ew.workflow_id = ew.workflow_id
                    WHERE current_ew.id = %s AND ew.ordre > current_ew.ordre
                    ORDER BY ew.ordre 
                    LIMIT 1
                """, (etape_id,))
                
                etape_suivante_result = cursor.fetchone()
                logger.info(f"🔍 Étape suivante result: type={type(etape_suivante_result)}, contenu={etape_suivante_result}")
                
                document_id = instance.get('document_id')
                
                if etape_suivante_result:
                    # Récupération sécurisée des données de l'étape suivante
                    if isinstance(etape_suivante_result, dict):
                        etape_suivante_id = etape_suivante_result.get('id')
                        etape_suivante_nom = etape_suivante_result.get('nom', 'Étape suivante')
                    else:
                        etape_suivante_id = etape_suivante_result[0] if etape_suivante_result else None
                        etape_suivante_nom = etape_suivante_result[1] if len(etape_suivante_result) > 1 else 'Étape suivante'
                    
                    logger.info(f"🔍 Étape suivante: ID={etape_suivante_id}, Nom={etape_suivante_nom}")
                    
                    # Passer à l'étape suivante
                    cursor.execute("""
                        UPDATE workflow_instance 
                        SET etape_courante_id = %s
                        WHERE id = %s
                    """, (etape_suivante_id, instance_id))
                    
                    result = {
                        'status': self.STATUS_EN_COURS,
                        'message': f'Étape approuvée, passage à l\'étape suivante : {etape_suivante_nom}',
                        'etape_suivante_id': etape_suivante_id,
                        'final': False
                    }
                    logger.info("🔍 Passage à l'étape suivante effectué")
                    
                    # Notification simplifiée (non bloquante)
                    try:
                        # Récupérer les approbateurs de l'étape suivante
                        cursor.execute("""
                            SELECT DISTINCT u.id, u.email, u.nom, u.prenom
                            FROM workflow_approbateur wa
                            LEFT JOIN role r ON wa.role_id = r.id
                            JOIN utilisateur u ON (
                                (wa.role_id IS NOT NULL AND u.role = r.nom) OR
                                (wa.utilisateur_id IS NOT NULL AND u.id = wa.utilisateur_id)
                            )
                            WHERE wa.etape_id = %s
                        """, (etape_suivante_id,))
                        
                        approbateurs = cursor.fetchall()
                        logger.info(f"🔍 {len(approbateurs)} approbateurs trouvés pour l'étape suivante")
                        
                        # Créer des notifications simples
                        for approbateur in approbateurs:
                            if isinstance(approbateur, dict):
                                approbateur_id = approbateur.get('id')
                                approbateur_nom = f"{approbateur.get('prenom', '')} {approbateur.get('nom', '')}"
                            else:
                                approbateur_id = approbateur[0]
                                approbateur_nom = f"{approbateur[3]} {approbateur[2]}" if len(approbateur) > 3 else "Approbateur"
                            
                            cursor.execute("""
                                INSERT INTO notifications (user_id, type, title, message, created_at)
                                VALUES (%s, %s, %s, %s, NOW())
                            """, (
                                approbateur_id,
                                'workflow_assigned',
                                'Nouvelle approbation requise',
                                f"Le document '{instance.get('document_titre', 'Document')}' nécessite votre approbation"
                            ))
                        
                    except Exception as notif_error:
                        logger.warning(f"🔍 Erreur notification étape suivante (non bloquante): {notif_error}")
                    
                else:
                    # Toutes les étapes sont terminées - approuver définitivement
                    logger.info("🔍 Dernière étape - Approbation finale")
                    
                    cursor.execute("""
                        UPDATE workflow_instance 
                        SET statut = %s, date_fin = NOW()
                        WHERE id = %s
                    """, (self.STATUS_APPROUVE, instance_id))
                    
                    if document_id:
                        cursor.execute("""
                            UPDATE document 
                            SET statut = 'APPROUVE' 
                            WHERE id = %s
                        """, (document_id,))
                        logger.info(f"🔍 Document {document_id} approuvé définitivement")
                    
                    result = {
                        'status': self.STATUS_APPROUVE,
                        'message': 'Document approuvé définitivement',
                        'final': True
                    }
                
                # Enregistrement dans l'historique (version simplifiée)
                try:
                    document_titre = instance.get('document_titre', 'Document')
                    etape_nom = instance.get('etape_nom', 'Étape')
                    
                    cursor.execute("""
                        INSERT INTO history (action_type, entity_type, entity_id, entity_name, description, user_id, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (
                        'APPROVE_WORKFLOW',
                        'DOCUMENT', 
                        document_id,
                        document_titre,
                        f"Étape '{etape_nom}' approuvée - {commentaire}",
                        approbateur_id
                    ))
                    logger.info("🔍 Historique d'approbation enregistré")
                    
                except Exception as hist_error:
                    logger.warning(f"🔍 Erreur historique approbation (non bloquante): {hist_error}")
                
                logger.info("🔍 Approbation traitée avec succès")
            
            conn.commit()
            
            logger.info(f"Approbation traitée pour l'instance {instance_id}: {decision}")
            
            return result
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def _can_user_approve_step(self, user_id: int, etape_id: int) -> bool:
        """Vérifie si un utilisateur peut approuver une étape"""
        logger.info(f"🔍 _can_user_approve_step: user_id={user_id}, etape_id={etape_id}")
        
        conn = db_connection()
        if not conn:
            logger.error("🔍 _can_user_approve_step: Impossible de se connecter à la BD")
            return False
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            logger.info("🔍 _can_user_approve_step: Curseur créé")
            
            # Récupérer le rôle de l'utilisateur
            cursor.execute("SELECT role FROM utilisateur WHERE id = %s", (user_id,))
            user_result = cursor.fetchone()
            logger.info(f"🔍 _can_user_approve_step: user_result type={type(user_result)}, contenu={user_result}")
            
            if not user_result:
                logger.warning(f"🔍 _can_user_approve_step: Utilisateur {user_id} non trouvé")
                return False
            
            # Vérification de type robuste
            if isinstance(user_result, dict):
                user_role = user_result.get('role')
            else:
                user_role = user_result[0] if user_result else None
            
            logger.info(f"🔍 _can_user_approve_step: user_role={user_role}")
            
            # Vérifier si l'utilisateur peut approuver cette étape (par rôle ou directement)
            cursor.execute("""
                SELECT 1 FROM workflow_approbateur wa
                LEFT JOIN role r ON wa.role_id = r.id
                WHERE wa.etape_id = %s 
                AND (r.nom = %s OR wa.utilisateur_id = %s)
            """, (etape_id, user_role, user_id))
            
            result = cursor.fetchone()
            logger.info(f"🔍 _can_user_approve_step: result={result}")
            
            can_approve = result is not None
            logger.info(f"🔍 _can_user_approve_step: can_approve={can_approve}")
            return can_approve
            
        except Exception as e:
            logger.error(f"🔍 _can_user_approve_step: Erreur={e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def _notify_next_approvers(self, instance_id: int, etape_id: int) -> None:
        """Notifie les approbateurs de l'étape suivante"""
        conn = db_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les approbateurs de l'étape
            logger.info(f"🔍 _notify_next_approvers: Recherche des approbateurs pour l'étape {etape_id}")
            cursor.execute("""
                SELECT DISTINCT u.id, u.email, u.nom, u.prenom, u.role
                FROM workflow_approbateur wa
                LEFT JOIN role r ON wa.role_id = r.id
                JOIN utilisateur u ON (
                    (wa.utilisateur_id IS NOT NULL AND u.id = wa.utilisateur_id) OR
                    (wa.role_id IS NOT NULL AND u.role = r.nom)
                )
                WHERE wa.etape_id = %s
            """, (etape_id,))
            
            approbateurs = cursor.fetchall()
            logger.info(f"🔍 _notify_next_approvers: {len(approbateurs)} approbateurs trouvés")
            
            for approbateur in approbateurs:
                logger.info(f"🔍 Approbateur trouvé: {approbateur['nom']} {approbateur['prenom']} ({approbateur['email']}) - Rôle: {approbateur['role']}")
            
            # Envoyer les notifications via le nouveau service
            from AppFlask.services.notification_service import NotificationService
            
            for approbateur in approbateurs:
                try:
                    logger.info(f"🔍 Tentative d'envoi de notification à {approbateur['email']}")
                    result = NotificationService.notify_workflow_assigned(
                        instance_id=instance_id,
                        etape_id=etape_id,
                        assigned_user_id=approbateur['id'],
                        assigner_id=0  # ID système
                    )
                    logger.info(f"🔍 Résultat notification: {result}")
                    if result:
                        logger.info(f"✅ Notification envoyée à {approbateur['email']} pour l'instance {instance_id}")
                    else:
                        logger.warning(f"⚠️ Échec d'envoi de notification à {approbateur['email']}")
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'envoi de notification à {approbateur['email']}: {e}")
                    import traceback
                    logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
        finally:
            cursor.close()
            conn.close()
    
    def get_pending_approvals(self, user_id: int) -> List[Dict]:
        """Récupère les approbations en attente pour un utilisateur"""
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer le rôle de l'utilisateur
            cursor.execute("SELECT role FROM utilisateur WHERE id = %s", (user_id,))
            user_result = cursor.fetchone()
            if not user_result:
                return []
            
            user_role = user_result['role'] if isinstance(user_result, dict) else user_result[0]
            
            # Récupérer les instances en attente d'approbation
            cursor.execute("""
                SELECT DISTINCT wi.id as instance_id, wi.document_id, wi.date_debut,
                       wi.commentaire, d.titre as document_titre, d.fichier,
                       e.id as etape_id, e.nom as etape_nom, e.description as etape_description,
                       u.nom as initiateur_nom, u.prenom as initiateur_prenom
                FROM workflow_instance wi
                JOIN document d ON wi.document_id = d.id
                JOIN etapeworkflow e ON wi.etape_courante_id = e.id
                JOIN workflow_approbateur wa ON e.id = wa.etape_id
                LEFT JOIN role r ON wa.role_id = r.id
                JOIN utilisateur u ON wi.initiateur_id = u.id
                WHERE wi.statut = %s
                AND (r.nom = %s OR wa.utilisateur_id = %s)
                AND NOT EXISTS (
                    SELECT 1 FROM workflow_approbation wapp
                    WHERE wapp.instance_id = wi.id 
                    AND wapp.etape_id = e.id 
                    AND wapp.approbateur_id = %s
                )
                ORDER BY wi.date_debut ASC
            """, (self.STATUS_EN_COURS, user_role, user_id, user_id))
            
            results = cursor.fetchall()
            return [dict(row) for row in results] if results else []
            
        finally:
            cursor.close()
            conn.close()
    
    def get_workflow_instance_details(self, instance_id: int) -> Optional[Dict]:
        """Récupère les détails d'une instance de workflow"""
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer l'instance
            cursor.execute("""
                SELECT wi.*, d.titre as document_titre, d.fichier, d.statut as document_statut,
                       u.nom as initiateur_nom, u.prenom as initiateur_prenom,
                       e.nom as etape_courante_nom, e.description as etape_courante_description
                FROM workflow_instance wi
                JOIN document d ON wi.document_id = d.id
                JOIN utilisateur u ON wi.initiateur_id = u.id
                LEFT JOIN etapeworkflow e ON wi.etape_courante_id = e.id
                WHERE wi.id = %s
            """, (instance_id,))
            
            instance_result = cursor.fetchone()
            if not instance_result:
                return None
            
            instance = dict(instance_result)
            
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
                       wa.decision as statut_etape,
                       wa.date_decision, wa.commentaire as commentaire_approbation,
                       u.nom as approbateur_nom, u.prenom as approbateur_prenom
                FROM etapeworkflow e
                LEFT JOIN workflow_approbation wa ON e.id = wa.etape_id AND wa.instance_id = %s
                LEFT JOIN utilisateur u ON wa.approbateur_id = u.id
                WHERE e.workflow_id = %s
                ORDER BY e.ordre
            """, (instance_id, instance['workflow_id']))
            
            etapes = cursor.fetchall()
            
            return {
                'instance': dict(instance),
                'approbations': [dict(a) for a in approbations],
                'etapes': [dict(e) for e in etapes]
            }
            
        finally:
            cursor.close()
            conn.close() 