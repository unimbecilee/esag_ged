from datetime import datetime
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
import json
from typing import List, Dict, Optional

class WorkflowInstance:
    def __init__(self, id=None, workflow_id=None, document_id=None, initiateur_id=None,
                 etape_courante_id=None, statut=None, date_debut=None, date_fin=None, 
                 commentaire=None):
        self.id = id
        self.workflow_id = workflow_id
        self.document_id = document_id
        self.initiateur_id = initiateur_id
        self.etape_courante_id = etape_courante_id
        self.statut = statut
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.commentaire = commentaire

    @staticmethod
    def create(workflow_id: int, document_id: int, initiateur_id: int, 
               commentaire: str = None) -> int:
        """Créer une nouvelle instance de workflow"""
        conn = db_connection()
        if not conn:
            raise Exception("Erreur de connexion à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Obtenir la première étape du workflow
            cursor.execute("""
                SELECT id FROM etapeworkflow 
                WHERE workflow_id = %s 
                ORDER BY ordre 
                LIMIT 1
            """, (workflow_id,))
            
            premiere_etape = cursor.fetchone()
            if not premiere_etape:
                raise Exception("Le workflow n'a pas d'étapes définies")
            
            # Créer l'instance
            cursor.execute("""
                INSERT INTO workflow_instance 
                (workflow_id, document_id, initiateur_id, etape_courante_id, statut, commentaire)
                VALUES (%s, %s, %s, %s, 'EN_COURS', %s)
                RETURNING id
            """, (workflow_id, document_id, initiateur_id, premiere_etape['id'], commentaire))
            
            instance_id = cursor.fetchone()['id']
            
            # Mettre à jour le statut du document
            cursor.execute("""
                UPDATE document SET statut = 'EN_VALIDATION'
                WHERE id = %s
            """, (document_id,))
            
            # Envoyer des notifications aux approbateurs de la première étape
            WorkflowInstance._notify_approvers(cursor, instance_id, premiere_etape['id'], document_id)
            
            conn.commit()
            return instance_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(instance_id: int) -> Optional[Dict]:
        """Récupérer une instance par ID"""
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT wi.*, 
                       w.nom as workflow_nom,
                       d.titre as document_titre,
                       u.nom as initiateur_nom, u.prenom as initiateur_prenom,
                       e.nom as etape_courante_nom
                FROM workflow_instance wi
                LEFT JOIN workflow w ON wi.workflow_id = w.id
                LEFT JOIN document d ON wi.document_id = d.id
                LEFT JOIN utilisateur u ON wi.initiateur_id = u.id
                LEFT JOIN etapeworkflow e ON wi.etape_courante_id = e.id
                WHERE wi.id = %s
            """, (instance_id,))
            
            return cursor.fetchone()
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_document(document_id: int) -> List[Dict]:
        """Récupérer toutes les instances pour un document"""
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT wi.*, 
                       w.nom as workflow_nom,
                       u.nom as initiateur_nom, u.prenom as initiateur_prenom,
                       e.nom as etape_courante_nom
                FROM workflow_instance wi
                LEFT JOIN workflow w ON wi.workflow_id = w.id
                LEFT JOIN utilisateur u ON wi.initiateur_id = u.id
                LEFT JOIN etapeworkflow e ON wi.etape_courante_id = e.id
                WHERE wi.document_id = %s
                ORDER BY wi.date_debut DESC
            """, (document_id,))
            
            return cursor.fetchall()
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_pending_approvals(user_id: int) -> List[Dict]:
        """Récupérer les approbations en attente pour un utilisateur"""
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT wi.*, 
                       w.nom as workflow_nom,
                       d.titre as document_titre,
                       u.nom as initiateur_nom, u.prenom as initiateur_prenom,
                       e.nom as etape_courante_nom,
                       e.id as etape_id,
                       wi.date_debut as date_echeance,
                       CASE 
                           WHEN wi.date_debut > NOW() - INTERVAL '7 days' THEN 'normal'
                           WHEN wi.date_debut > NOW() - INTERVAL '14 days' THEN 'medium'
                           ELSE 'high'
                       END as priorite,
                       COALESCE(wi.commentaire, 'Validation requise') as description
                FROM workflow_instance wi
                JOIN workflow w ON wi.workflow_id = w.id
                JOIN document d ON wi.document_id = d.id
                JOIN utilisateur u ON wi.initiateur_id = u.id
                JOIN etapeworkflow e ON wi.etape_courante_id = e.id
                JOIN workflow_approbateur wa ON e.id = wa.etape_id
                WHERE wi.statut = 'EN_COURS'
                AND (
                    wa.utilisateur_id = %s 
                    OR (wa.role_id IS NOT NULL AND EXISTS (
                        SELECT 1 FROM role r 
                        JOIN utilisateur u2 ON u2.role = r.nom 
                        WHERE r.id = wa.role_id AND u2.id = %s
                    ))
                    OR wa.organisation_id IN (SELECT organisation_id FROM membre WHERE utilisateur_id = %s)
                )
                AND NOT EXISTS (
                    SELECT 1 FROM workflow_approbation 
                    WHERE instance_id = wi.id 
                    AND etape_id = e.id 
                    AND approbateur_id = %s
                )
                ORDER BY wi.date_debut ASC
            """, (user_id, user_id, user_id, user_id))
            
            # Récupérer les données et les convertir en liste de dictionnaires
            results = cursor.fetchall()
            
            # Convertir en liste de dictionnaires Python standard
            approvals = []
            for row in results:
                approval = dict(row)
                approvals.append(approval)
                
            return approvals
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def approve_step(instance_id: int, etape_id: int, approbateur_id: int, 
                    commentaire: str = None) -> bool:
        """Approuver une étape"""
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Enregistrer l'approbation
            cursor.execute("""
                INSERT INTO workflow_approbation 
                (instance_id, etape_id, approbateur_id, decision, commentaire)
                VALUES (%s, %s, %s, 'APPROUVE', %s)
            """, (instance_id, etape_id, approbateur_id, commentaire))
            
            # Vérifier si l'étape est complètement approuvée
            is_step_complete = WorkflowInstance._check_step_completion(cursor, instance_id, etape_id)
            
            if is_step_complete:
                # Passer à l'étape suivante ou terminer le workflow
                WorkflowInstance._advance_to_next_step(cursor, instance_id)
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def reject_step(instance_id: int, etape_id: int, approbateur_id: int, 
                   commentaire: str = None) -> bool:
        """Rejeter une étape"""
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Enregistrer le rejet
            cursor.execute("""
                INSERT INTO workflow_approbation 
                (instance_id, etape_id, approbateur_id, decision, commentaire)
                VALUES (%s, %s, %s, 'REJETE', %s)
            """, (instance_id, etape_id, approbateur_id, commentaire))
            
            # Récupérer l'ID du document
            cursor.execute("""
                SELECT document_id FROM workflow_instance WHERE id = %s
            """, (instance_id,))
            document_id = cursor.fetchone()[0]
            
            # Marquer l'instance comme rejetée
            cursor.execute("""
                UPDATE workflow_instance 
                SET statut = 'REJETE', date_fin = NOW()
                WHERE id = %s
            """, (instance_id,))
            
            # Mettre à jour le statut du document
            cursor.execute("""
                UPDATE document SET statut = 'REJETE'
                WHERE id = %s
            """, (document_id,))
            
            # Notifier l'initiateur du rejet
            WorkflowInstance._notify_rejection(cursor, instance_id, etape_id, document_id)
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def _check_step_completion(cursor, instance_id: int, etape_id: int) -> bool:
        """Vérifier si une étape est complètement approuvée"""
        
        # Obtenir le type d'approbation de l'étape
        cursor.execute("""
            SELECT type_approbation FROM etapeworkflow WHERE id = %s
        """, (etape_id,))
        
        etape = cursor.fetchone()
        if not etape:
            return False
        
        type_approbation = etape['type_approbation']
        
        # Pour une approbation simple, une seule approbation suffit
        if type_approbation == 'SIMPLE':
            return True
        
        # Pour une approbation multiple, vérifier si tous les approbateurs ont approuvé
        elif type_approbation == 'MULTIPLE' or type_approbation == 'PARALLELE':
            # Compter le nombre d'approbateurs requis
            cursor.execute("""
                SELECT COUNT(*) as total FROM workflow_approbateur WHERE etape_id = %s
            """, (etape_id,))
            
            total_approbateurs = cursor.fetchone()['total']
            
            # Compter le nombre d'approbations
            cursor.execute("""
                SELECT COUNT(*) as approvals FROM workflow_approbation 
                WHERE instance_id = %s AND etape_id = %s AND decision = 'APPROUVE'
            """, (instance_id, etape_id))
            
            total_approvals = cursor.fetchone()['approvals']
            
            return total_approvals >= total_approbateurs
        
        return False

    @staticmethod
    def _advance_to_next_step(cursor, instance_id: int):
        """Passer à l'étape suivante ou terminer le workflow"""
        
        # Récupérer l'étape courante et le workflow
        cursor.execute("""
            SELECT wi.etape_courante_id, wi.workflow_id, wi.document_id, w.nom as workflow_nom
            FROM workflow_instance wi
            JOIN workflow w ON wi.workflow_id = w.id
            WHERE wi.id = %s
        """, (instance_id,))
        
        instance = cursor.fetchone()
        if not instance:
            return
        
        etape_courante_id = instance['etape_courante_id']
        workflow_id = instance['workflow_id']
        document_id = instance['document_id']
        workflow_nom = instance['workflow_nom']
        
        # Trouver l'étape suivante
        cursor.execute("""
            SELECT id FROM etapeworkflow 
            WHERE workflow_id = %s AND ordre > (
                SELECT ordre FROM etapeworkflow WHERE id = %s
            )
            ORDER BY ordre 
            LIMIT 1
        """, (workflow_id, etape_courante_id))
        
        next_step = cursor.fetchone()
        
        if next_step:
            # Passer à l'étape suivante
            cursor.execute("""
                UPDATE workflow_instance 
                SET etape_courante_id = %s
                WHERE id = %s
            """, (next_step['id'], instance_id))
            
            # Envoyer des notifications aux approbateurs de la prochaine étape
            WorkflowInstance._notify_approvers(cursor, instance_id, next_step['id'], document_id)
            
        else:
            # C'était la dernière étape, terminer le workflow
            cursor.execute("""
                UPDATE workflow_instance 
                SET statut = 'APPROUVE', date_fin = NOW()
                WHERE id = %s
            """, (instance_id,))
            
            # Mettre à jour le statut du document
            cursor.execute("""
                UPDATE document SET statut = 'APPROUVE'
                WHERE id = %s
            """, (document_id,))
            
            # Si c'est un workflow d'archivage, archiver le document
            if workflow_nom == 'Archivage automatique':
                WorkflowInstance._archive_document(cursor, document_id)
            
            # Notifier l'initiateur que le workflow est terminé
            WorkflowInstance._notify_completion(cursor, instance_id, document_id)

    @staticmethod
    def _archive_document(cursor, document_id: int):
        """Archiver un document après approbation du workflow d'archivage"""
        try:
            # Vérifier si la colonne 'est_archive' existe dans la table document
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'document' AND column_name = 'est_archive'
            """)
            
            column_exists = cursor.fetchone()
            
            if column_exists:
                # Marquer le document comme archivé
                cursor.execute("""
                    UPDATE document 
                    SET est_archive = TRUE, 
                        date_archivage = NOW()
                    WHERE id = %s
                """, (document_id,))
            else:
                # Ajouter une entrée dans la table archive si elle existe
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_name = 'archive'
                """)
                
                table_exists = cursor.fetchone()
                
                if table_exists:
                    cursor.execute("""
                        INSERT INTO archive (document_id, date_archivage, statut)
                        VALUES (%s, NOW(), 'ARCHIVE')
                    """, (document_id,))
                else:
                    # Si aucune structure d'archivage n'existe, juste mettre à jour le statut
                    cursor.execute("""
                        UPDATE document 
                        SET statut = 'ARCHIVE'
                        WHERE id = %s
                    """, (document_id,))
            
        except Exception as e:
            # Journaliser l'erreur mais ne pas interrompre le processus
            print(f"Erreur lors de l'archivage du document {document_id}: {e}")

    @staticmethod
    def _notify_approvers(cursor, instance_id: int, etape_id: int, document_id: int):
        """Envoyer des notifications aux approbateurs d'une étape"""
        
        # Récupérer les informations sur l'étape et le document
        cursor.execute("""
            SELECT e.nom as etape_nom, d.titre as document_titre
            FROM etapeworkflow e
            JOIN document d ON d.id = %s
            WHERE e.id = %s
        """, (document_id, etape_id))
        
        info = cursor.fetchone()
        if not info:
            return
        
        etape_nom = info['etape_nom']
        document_titre = info['document_titre']
        
        # Récupérer les approbateurs par utilisateur direct
        cursor.execute("""
            SELECT u.id, u.nom, u.prenom, u.email
            FROM workflow_approbateur wa
            JOIN utilisateur u ON wa.utilisateur_id = u.id
            WHERE wa.etape_id = %s AND wa.utilisateur_id IS NOT NULL
        """, (etape_id,))
        
        direct_approvers = cursor.fetchall()
        
        # Récupérer les approbateurs par rôle
        cursor.execute("""
            SELECT u.id, u.nom, u.prenom, u.email
            FROM workflow_approbateur wa
            JOIN role r ON wa.role_id = r.id
            JOIN utilisateur u ON u.role = r.nom
            WHERE wa.etape_id = %s AND wa.role_id IS NOT NULL
        """, (etape_id,))
        
        role_approvers = cursor.fetchall()
        
        # Récupérer les approbateurs par organisation
        cursor.execute("""
            SELECT u.id, u.nom, u.prenom, u.email
            FROM workflow_approbateur wa
            JOIN membre m ON wa.organisation_id = m.organisation_id
            JOIN utilisateur u ON m.utilisateur_id = u.id
            WHERE wa.etape_id = %s AND wa.organisation_id IS NOT NULL
        """, (etape_id,))
        
        org_approvers = cursor.fetchall()
        
        # Combiner tous les approbateurs (éliminer les doublons)
        all_approvers = {}
        for approver in direct_approvers + role_approvers + org_approvers:
            all_approvers[approver['id']] = approver
        
        # Créer une notification pour chaque approbateur
        message = f"Un document vous a été soumis pour validation: '{document_titre}' - Étape: {etape_nom}"
        
        for approver_id, approver in all_approvers.items():
            cursor.execute("""
                INSERT INTO workflow_notification
                (instance_id, etape_id, utilisateur_id, message, date_creation, lu)
                VALUES (%s, %s, %s, %s, NOW(), FALSE)
            """, (instance_id, etape_id, approver_id, message))
            
            # Si intégration avec le système de notifications général
            try:
                cursor.execute("""
                    INSERT INTO notification
                    (utilisateur_id, type, titre, message, lien, date_creation, lu)
                    VALUES (%s, 'WORKFLOW', 'Document à valider', %s, %s, NOW(), FALSE)
                """, (approver_id, message, f"/workflow?instance={instance_id}"))
            except:
                # La table notification peut ne pas exister
                pass

    @staticmethod
    def _notify_completion(cursor, instance_id: int, document_id: int):
        """Notifier l'initiateur que le workflow est terminé avec succès"""
        
        # Récupérer les informations sur l'instance et le document
        cursor.execute("""
            SELECT wi.initiateur_id, d.titre as document_titre, w.nom as workflow_nom
            FROM workflow_instance wi
            JOIN document d ON d.id = wi.document_id
            JOIN workflow w ON w.id = wi.workflow_id
            WHERE wi.id = %s
        """, (instance_id,))
        
        info = cursor.fetchone()
        if not info:
            return
        
        initiateur_id = info['initiateur_id']
        document_titre = info['document_titre']
        workflow_nom = info['workflow_nom']
        
        # Message différent selon le type de workflow
        if workflow_nom == 'Archivage automatique':
            message = f"Le document '{document_titre}' a été approuvé et archivé avec succès."
        else:
            message = f"Le document '{document_titre}' a été approuvé avec succès."
        
        # Créer une notification pour l'initiateur
        try:
            cursor.execute("""
                INSERT INTO notification
                (utilisateur_id, type, titre, message, lien, date_creation, lu)
                VALUES (%s, 'WORKFLOW', 'Document approuvé', %s, %s, NOW(), FALSE)
            """, (initiateur_id, message, f"/documents/{document_id}"))
        except:
            # La table notification peut ne pas exister
            pass

    @staticmethod
    def _notify_rejection(cursor, instance_id: int, etape_id: int, document_id: int):
        """Notifier l'initiateur que le workflow a été rejeté"""
        
        # Récupérer les informations sur l'instance, l'étape et le document
        cursor.execute("""
            SELECT wi.initiateur_id, e.nom as etape_nom, d.titre as document_titre, w.nom as workflow_nom
            FROM workflow_instance wi
            JOIN etapeworkflow e ON e.id = %s
            JOIN document d ON d.id = wi.document_id
            JOIN workflow w ON w.id = wi.workflow_id
            WHERE wi.id = %s
        """, (etape_id, instance_id))
        
        info = cursor.fetchone()
        if not info:
            return
        
        initiateur_id = info['initiateur_id']
        etape_nom = info['etape_nom']
        document_titre = info['document_titre']
        workflow_nom = info['workflow_nom']
        
        # Message différent selon le type de workflow
        if workflow_nom == 'Archivage automatique':
            message = f"La demande d'archivage du document '{document_titre}' a été rejetée à l'étape '{etape_nom}'."
        else:
            message = f"Le document '{document_titre}' a été rejeté à l'étape '{etape_nom}'."
        
        # Créer une notification pour l'initiateur
        try:
            cursor.execute("""
                INSERT INTO notification
                (utilisateur_id, type, titre, message, lien, date_creation, lu)
                VALUES (%s, 'WORKFLOW', 'Document rejeté', %s, %s, NOW(), FALSE)
            """, (initiateur_id, message, f"/documents/{document_id}"))
        except:
            # La table notification peut ne pas exister
            pass

    @staticmethod
    def cancel(instance_id: int, user_id: int) -> bool:
        """Annuler une instance de workflow"""
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Vérifier que l'utilisateur est l'initiateur ou un admin
            cursor.execute("""
                SELECT wi.initiateur_id, wi.document_id, u.role
                FROM workflow_instance wi
                JOIN utilisateur u ON %s = u.id
                WHERE wi.id = %s
            """, (user_id, instance_id))
            
            result = cursor.fetchone()
            if not result:
                return False
                
            is_initiator = result['initiateur_id'] == user_id
            is_admin = result['role'] == 'admin'
            document_id = result['document_id']
            
            if not (is_initiator or is_admin):
                return False
            
            # Annuler l'instance
            cursor.execute("""
                UPDATE workflow_instance 
                SET statut = 'ANNULE', date_fin = NOW()
                WHERE id = %s
            """, (instance_id,))
            
            # Remettre le document en brouillon
            cursor.execute("""
                UPDATE document SET statut = 'BROUILLON'
                WHERE id = %s
            """, (document_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def to_dict(instance_row) -> Dict:
        """Convertir une ligne d'instance en dictionnaire"""
        return {
            'id': instance_row['id'],
            'workflow_id': instance_row['workflow_id'],
            'workflow_nom': instance_row.get('workflow_nom'),
            'document_id': instance_row['document_id'],
            'document_titre': instance_row.get('document_titre'),
            'initiateur_id': instance_row['initiateur_id'],
            'initiateur_nom': instance_row.get('initiateur_nom'),
            'initiateur_prenom': instance_row.get('initiateur_prenom'),
            'etape_courante_id': instance_row['etape_courante_id'],
            'etape_courante_nom': instance_row.get('etape_courante_nom'),
            'statut': instance_row['statut'],
            'date_debut': instance_row['date_debut'].isoformat() if instance_row['date_debut'] else None,
            'date_fin': instance_row['date_fin'].isoformat() if instance_row.get('date_fin') else None,
            'commentaire': instance_row['commentaire']
        }

    @staticmethod
    def get_all(limit: int = None, offset: int = 0) -> List[Dict]:
        """Récupérer toutes les instances de workflow avec pagination optionnelle"""
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT wi.*, 
                       w.nom as workflow_nom,
                       d.titre as document_titre,
                       u.nom as initiateur_nom, u.prenom as initiateur_prenom,
                       e.nom as etape_courante_nom
                FROM workflow_instance wi
                LEFT JOIN workflow w ON wi.workflow_id = w.id
                LEFT JOIN document d ON wi.document_id = d.id
                LEFT JOIN utilisateur u ON wi.initiateur_id = u.id
                LEFT JOIN etapeworkflow e ON wi.etape_courante_id = e.id
                ORDER BY wi.date_debut DESC
            """
            
            if limit is not None:
                query += " LIMIT %s OFFSET %s"
                cursor.execute(query, (limit, offset))
            else:
                cursor.execute(query)
            
            return cursor.fetchall()
            
        finally:
            cursor.close()
            conn.close() 