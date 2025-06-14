#!/usr/bin/env python3
"""
Service de notifications complet pour ESAG GED
Gestion des notifications en temps réel et par email
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from jinja2 import Template
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from AppFlask.services.email_service import email_service

logger = logging.getLogger(__name__)

class NotificationService:
    """Service complet pour la gestion des notifications"""
    
    @staticmethod
    def create_notification(
        user_id: int,
        title: str,
        message: str,
        notification_type: str = 'info',
        document_id: int = None,
        workflow_id: int = None,
        created_by_id: int = None,
        priority: int = 1,
        expires_at: datetime = None,
        metadata: Dict[str, Any] = None,
        send_email: bool = True
    ) -> Optional[int]:
        """
        Créer une nouvelle notification
        
        Args:
            user_id: ID de l'utilisateur destinataire
            title: Titre de la notification
            message: Message de la notification
            notification_type: Type de notification
            document_id: ID du document associé (optionnel)
            workflow_id: ID du workflow associé (optionnel)
            created_by_id: ID de l'utilisateur créateur (optionnel)
            priority: Priorité (1=basse, 2=normale, 3=haute, 4=urgente)
            expires_at: Date d'expiration (optionnel)
            metadata: Métadonnées supplémentaires (optionnel)
            send_email: Envoyer aussi par email
        
        Returns:
            ID de la notification créée ou None en cas d'erreur
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Vérifier les préférences de l'utilisateur
            cursor.execute("""
                SELECT app_notifications, email_notifications
                FROM user_notification_preferences
                WHERE user_id = %s
            """, (user_id,))
            
            preferences = cursor.fetchone()
            
            # Si l'utilisateur a désactivé les notifications app, ne pas créer
            if preferences and not preferences.get('app_notifications', True):
                logger.info(f"Notifications app désactivées pour l'utilisateur {user_id}")
                cursor.close()
                conn.close()
                return None
            
            # Créer la notification en base
            cursor.execute("""
                INSERT INTO notifications 
                (user_id, title, message, type, document_id, workflow_id, 
                 created_by_id, priority, expires_at, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (
                user_id, title, message, notification_type, document_id,
                workflow_id, created_by_id, priority, expires_at,
                metadata or {}
            ))
            
            notification_id = cursor.fetchone()['id']
            conn.commit()
            
            # Log de la création
            NotificationService._log_notification_action(
                notification_id, user_id, 'created', 'app', 'success'
            )
            
            # Envoyer par email si demandé et autorisé
            if send_email and preferences and preferences.get('email_notifications', True):
                email_sent = NotificationService._send_notification_email(
                    user_id, title, message, notification_type, metadata or {}
                )
                
                if email_sent:
                    NotificationService._log_notification_action(
                        notification_id, user_id, 'sent', 'email', 'success'
                    )
                else:
                    NotificationService._log_notification_action(
                        notification_id, user_id, 'sent', 'email', 'failed'
                    )
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Notification créée (ID: {notification_id}) pour utilisateur {user_id}")
            return notification_id
            
        except Exception as e:
            logger.error(f"❌ Erreur création notification: {str(e)}")
            return None
    
    @staticmethod
    def create_bulk_notifications(
        user_ids: List[int],
        title: str,
        message: str,
        notification_type: str = 'info',
        document_id: int = None,
        workflow_id: int = None,
        created_by_id: int = None,
        priority: int = 1,
        send_email: bool = True,
        exclude_user_id: int = None
    ) -> int:
        """
        Créer des notifications pour plusieurs utilisateurs
        
        Returns:
            Nombre de notifications créées
        """
        created_count = 0
        
        # Filtrer l'utilisateur exclu
        if exclude_user_id:
            user_ids = [uid for uid in user_ids if uid != exclude_user_id]
        
        for user_id in user_ids:
            notification_id = NotificationService.create_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                document_id=document_id,
                workflow_id=workflow_id,
                created_by_id=created_by_id,
                priority=priority,
                send_email=send_email
            )
            
            if notification_id:
                created_count += 1
        
        logger.info(f"✅ {created_count}/{len(user_ids)} notifications créées en masse")
        return created_count
    
    @staticmethod
    def notify_document_uploaded(document_id: int, uploader_id: int) -> bool:
        """Notifier l'ajout d'un nouveau document"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les infos du document et de l'uploader
            cursor.execute("""
                SELECT d.titre, d.type_document, d.proprietaire_id,
                       u.nom as uploader_nom, u.prenom as uploader_prenom
                FROM document d
                JOIN utilisateur u ON d.proprietaire_id = u.id
                WHERE d.id = %s
            """, (document_id,))
            
            document = cursor.fetchone()
            if not document:
                return False
            
            # Récupérer les utilisateurs à notifier
            users_to_notify = NotificationService._get_document_subscribers(
                document_id, exclude_user_id=uploader_id
            )
            
            # Ajouter les admins
            cursor.execute("""
                SELECT id FROM utilisateur 
                WHERE role = 'Admin' AND id != %s
            """, (uploader_id,))
            
            admins = [admin['id'] for admin in cursor.fetchall()]
            users_to_notify.extend(admins)
            
            # Supprimer les doublons
            users_to_notify = list(set(users_to_notify))
            
            cursor.close()
            conn.close()
            
            # Créer les notifications
            title = "Nouveau document ajouté"
            message = f'Le document "{document["titre"]}" a été ajouté par {document["uploader_prenom"]} {document["uploader_nom"]}'
            
            created_count = NotificationService.create_bulk_notifications(
                user_ids=users_to_notify,
                title=title,
                message=message,
                notification_type='document_uploaded',
                document_id=document_id,
                created_by_id=uploader_id,
                priority=2,
                send_email=True
            )
            
            return created_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur notification document uploadé: {str(e)}")
            return False
    
    @staticmethod
    def notify_document_shared(document_id: int, shared_with_user_id: int, shared_by_user_id: int) -> bool:
        """Notifier le partage d'un document"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les infos
            cursor.execute("""
                SELECT d.titre,
                       u1.nom as shared_by_nom, u1.prenom as shared_by_prenom,
                       u2.nom as shared_with_nom, u2.prenom as shared_with_prenom
                FROM document d,
                     utilisateur u1,
                     utilisateur u2
                WHERE d.id = %s 
                AND u1.id = %s 
                AND u2.id = %s
            """, (document_id, shared_by_user_id, shared_with_user_id))
            
            info = cursor.fetchone()
            if not info:
                return False
            
            cursor.close()
            conn.close()
            
            # Créer la notification
            title = "Document partagé avec vous"
            message = f'{info["shared_by_prenom"]} {info["shared_by_nom"]} a partagé le document "{info["titre"]}" avec vous'
            
            notification_id = NotificationService.create_notification(
                user_id=shared_with_user_id,
                title=title,
                message=message,
                notification_type='document_shared',
                document_id=document_id,
                created_by_id=shared_by_user_id,
                priority=2,
                send_email=True
            )
            
            return notification_id is not None
            
        except Exception as e:
            logger.error(f"❌ Erreur notification partage: {str(e)}")
            return False
    
    @staticmethod
    def notify_document_commented(document_id: int, commenter_id: int, comment_text: str) -> bool:
        """Notifier un nouveau commentaire sur un document"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les infos
            cursor.execute("""
                SELECT d.titre, d.proprietaire_id,
                       u.nom as commenter_nom, u.prenom as commenter_prenom
                FROM document d
                JOIN utilisateur u ON u.id = %s
                WHERE d.id = %s
            """, (commenter_id, document_id))
            
            info = cursor.fetchone()
            if not info:
                return False
            
            # Récupérer les utilisateurs à notifier (propriétaire + abonnés)
            users_to_notify = NotificationService._get_document_subscribers(
                document_id, exclude_user_id=commenter_id
            )
            
            # Ajouter le propriétaire s'il n'est pas déjà dans la liste
            if info['proprietaire_id'] not in users_to_notify:
                users_to_notify.append(info['proprietaire_id'])
            
            cursor.close()
            conn.close()
            
            # Créer les notifications
            title = "Nouveau commentaire"
            message = f'{info["commenter_prenom"]} {info["commenter_nom"]} a commenté le document "{info["titre"]}"'
            
            created_count = NotificationService.create_bulk_notifications(
                user_ids=users_to_notify,
                title=title,
                message=message,
                notification_type='document_commented',
                document_id=document_id,
                created_by_id=commenter_id,
                priority=2,
                send_email=True,
                exclude_user_id=commenter_id
            )
            
            return created_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur notification commentaire: {str(e)}")
            return False
    
    @staticmethod
    def notify_workflow_assigned(workflow_id: int, assigned_user_id: int, assigner_id: int) -> bool:
        """Notifier l'assignation d'une tâche workflow"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les infos du workflow et des utilisateurs
            cursor.execute("""
                SELECT w.titre as workflow_title, w.description, w.date_echeance,
                       u1.nom as assigner_nom, u1.prenom as assigner_prenom,
                       u2.nom as assigned_nom, u2.prenom as assigned_prenom
                FROM workflow w,
                     utilisateur u1,
                     utilisateur u2
                WHERE w.id = %s 
                AND u1.id = %s 
                AND u2.id = %s
            """, (workflow_id, assigner_id, assigned_user_id))
            
            info = cursor.fetchone()
            if not info:
                return False
            
            cursor.close()
            conn.close()
            
            # Créer la notification
            title = "Nouvelle tâche assignée"
            message = f'{info["assigner_prenom"]} {info["assigner_nom"]} vous a assigné la tâche "{info["workflow_title"]}"'
            
            # Calculer la priorité selon l'échéance
            priority = 2  # Normal par défaut
            if info['date_echeance']:
                days_until_due = (info['date_echeance'] - datetime.now().date()).days
                if days_until_due <= 1:
                    priority = 4  # Urgent
                elif days_until_due <= 3:
                    priority = 3  # Haute
            
            notification_id = NotificationService.create_notification(
                user_id=assigned_user_id,
                title=title,
                message=message,
                notification_type='workflow_assigned',
                workflow_id=workflow_id,
                created_by_id=assigner_id,
                priority=priority,
                send_email=True,
                metadata={
                    'workflow_title': info['workflow_title'],
                    'due_date': info['date_echeance'].isoformat() if info['date_echeance'] else None,
                    'description': info['description']
                }
            )
            
            return notification_id is not None
            
        except Exception as e:
            logger.error(f"❌ Erreur notification workflow: {str(e)}")
            return False
    
    @staticmethod
    def notify_user_mentioned(mentioned_user_id: int, mentioner_id: int, 
                            context_type: str, context_id: int, context_title: str) -> bool:
        """Notifier qu'un utilisateur a été mentionné"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les infos du mentionneur
            cursor.execute("""
                SELECT nom, prenom FROM utilisateur WHERE id = %s
            """, (mentioner_id,))
            
            mentioner = cursor.fetchone()
            if not mentioner:
                return False
            
            # Enregistrer la mention
            cursor.execute("""
                INSERT INTO notification_mentions 
                (notification_id, mentioned_user_id, mentioned_by_user_id, 
                 context_type, context_id, created_at)
                VALUES (NULL, %s, %s, %s, %s, NOW())
            """, (mentioned_user_id, mentioner_id, context_type, context_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Créer la notification
            title = "Vous avez été mentionné"
            message = f'{mentioner["prenom"]} {mentioner["nom"]} vous a mentionné dans {context_type} "{context_title}"'
            
            notification_id = NotificationService.create_notification(
                user_id=mentioned_user_id,
                title=title,
                message=message,
                notification_type='user_mentioned',
                created_by_id=mentioner_id,
                priority=3,  # Haute priorité pour les mentions
                send_email=True,
                metadata={
                    'context_type': context_type,
                    'context_id': context_id,
                    'context_title': context_title
                }
            )
            
            return notification_id is not None
            
        except Exception as e:
            logger.error(f"❌ Erreur notification mention: {str(e)}")
            return False
    
    @staticmethod
    def notify_system_maintenance(start_time: datetime, end_time: datetime, 
                                description: str, affected_users: List[int] = None) -> bool:
        """Notifier une maintenance système"""
        try:
            if affected_users is None:
                # Notifier tous les utilisateurs actifs
                conn = db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute("""
                    SELECT id FROM utilisateur WHERE est_actif = true
                """)
                
                affected_users = [user['id'] for user in cursor.fetchall()]
                cursor.close()
                conn.close()
            
            # Créer les notifications
            title = "Maintenance système programmée"
            message = f"Maintenance prévue le {start_time.strftime('%d/%m/%Y')} de {start_time.strftime('%H:%M')} à {end_time.strftime('%H:%M')}"
            
            if description:
                message += f" - {description}"
            
            created_count = NotificationService.create_bulk_notifications(
                user_ids=affected_users,
                title=title,
                message=message,
                notification_type='system_maintenance',
                priority=3,  # Haute priorité
                send_email=True,
                expires_at=end_time,
                metadata={
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'description': description
                }
            )
            
            return created_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur notification maintenance: {str(e)}")
            return False
    
    @staticmethod
    def _get_document_subscribers(document_id: int, exclude_user_id: int = None) -> List[int]:
        """Récupérer les utilisateurs abonnés aux notifications d'un document"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            where_clause = "document_id = %s AND is_active = true"
            params = [document_id]
            
            if exclude_user_id:
                where_clause += " AND user_id != %s"
                params.append(exclude_user_id)
            
            cursor.execute(f"""
                SELECT user_id FROM document_subscriptions 
                WHERE {where_clause}
            """, params)
            
            subscribers = [sub['user_id'] for sub in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return subscribers
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération abonnés: {str(e)}")
            return []
    
    @staticmethod
    def _send_notification_email(user_id: int, title: str, message: str, 
                               notification_type: str, metadata: Dict[str, Any]) -> bool:
        """Envoyer une notification par email"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer l'email de l'utilisateur
            cursor.execute("""
                SELECT nom, prenom, email FROM utilisateur WHERE id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            if not user:
                return False
            
            cursor.close()
            conn.close()
            
            # Préparer les données pour l'email
            email_data = {
                'user_name': f"{user['prenom']} {user['nom']}",
                'notification_title': title,
                'notification_message': message,
                'notification_type': notification_type,
                'date': datetime.now().strftime('%d/%m/%Y à %H:%M'),
                'login_url': 'http://localhost:3000/notifications'
            }
            
            # Ajouter les métadonnées
            email_data.update(metadata)
            
            # Envoyer l'email
            return email_service.send_template_email(
                to=[user['email']],
                template_name='notification_general',
                subject=f"ESAG GED - {title}",
                template_data=email_data
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email notification: {str(e)}")
            return False
    
    @staticmethod
    def _log_notification_action(notification_id: int, user_id: int, action: str, 
                               channel: str, status: str, error_message: str = None):
        """Logger une action de notification"""
        try:
            conn = db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO notification_logs 
                (notification_id, user_id, action, channel, status, error_message, sent_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (notification_id, user_id, action, channel, status, error_message))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur log notification: {str(e)}")
    
    @staticmethod
    def cleanup_old_notifications(days: int = 90) -> int:
        """Nettoyer les anciennes notifications lues"""
        try:
            conn = db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT cleanup_old_notifications()")
            deleted_count = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ {deleted_count} anciennes notifications supprimées")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage notifications: {str(e)}")
            return 0
    
    @staticmethod
    def mark_expired_notifications() -> int:
        """Marquer comme lues les notifications expirées"""
        try:
            conn = db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT mark_expired_notifications()")
            updated_count = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if updated_count > 0:
                logger.info(f"✅ {updated_count} notifications expirées marquées comme lues")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"❌ Erreur marquage notifications expirées: {str(e)}")
            return 0

# Instance globale du service
notification_service = NotificationService() 