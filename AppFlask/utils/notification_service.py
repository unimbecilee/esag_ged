import logging
from typing import List, Dict, Any, Optional
from AppFlask.services.email_service import email_service
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Service pour envoyer des notifications par email"""
    
    @staticmethod
    def notify_document_uploaded(document_id: int, uploader_id: int, document_title: str, document_type: str = 'Document'):
        """Notifier les utilisateurs concernés qu'un nouveau document a été ajouté"""
        try:
            # Récupérer les utilisateurs à notifier (admins et utilisateurs ayant accès au dossier parent)
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les informations du document et de l'uploader
            cursor.execute("""
                SELECT d.*, u.nom as uploader_nom, u.prenom as uploader_prenom, u.email as uploader_email
                FROM document d
                JOIN utilisateur u ON d.proprietaire_id = u.id
                WHERE d.id = %s
            """, (document_id,))
            document = cursor.fetchone()
            
            if not document:
                logger.warning(f"Document {document_id} non trouvé pour notification")
                return False
            
            # Récupérer les utilisateurs à notifier
            users_to_notify = []
            
            # 1. Tous les admins
            cursor.execute("""
                SELECT id, nom, prenom, email 
                FROM utilisateur 
                WHERE role = 'admin' AND id != %s
                AND EXISTS (
                    SELECT 1 FROM parametres 
                    WHERE user_id = utilisateur.id 
                    AND email_notifications = true
                )
            """, (uploader_id,))
            
            admins = cursor.fetchall()
            users_to_notify.extend(admins)
            
            # 2. Utilisateurs avec accès au dossier parent (si applicable)
            if document.get('dossier_id'):
                cursor.execute("""
                    SELECT DISTINCT u.id, u.nom, u.prenom, u.email
                    FROM utilisateur u
                    JOIN partage p ON u.id = p.utilisateur_id
                    WHERE p.dossier_id = %s AND u.id != %s
                    AND EXISTS (
                        SELECT 1 FROM parametres 
                        WHERE user_id = u.id 
                        AND email_notifications = true
                    )
                """, (document['dossier_id'], uploader_id))
                
                folder_users = cursor.fetchall()
                users_to_notify.extend(folder_users)
            
            cursor.close()
            conn.close()
            
            # Supprimer les doublons
            unique_users = {user['email']: user for user in users_to_notify}.values()
            
            # Envoyer les notifications
            for user in unique_users:
                try:
                    email_data = {
                        'user_name': f"{user['prenom']} {user['nom']}",
                        'document_title': document_title,
                        'document_type': document_type,
                        'uploader_name': f"{document['uploader_prenom']} {document['uploader_nom']}",
                        'action': 'ajouté',
                        'date': datetime.now().strftime('%d/%m/%Y à %H:%M'),
                        'description': document.get('description', ''),
                        'login_url': 'http://localhost:3000/my-documents'
                    }
                    
                    email_service.send_template_email(
                        to=[user['email']],
                        template_name='document_notification',
                        subject=f'Nouveau document ajouté - {document_title}',
                        template_data=email_data
                    )
                    
                    logger.info(f"✅ Notification envoyée à {user['email']} pour le document {document_title}")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur notification email à {user['email']}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi des notifications de document: {str(e)}")
            return False
    
    @staticmethod
    def notify_document_shared(document_id: int, shared_with_user_id: int, shared_by_user_id: int, document_title: str):
        """Notifier un utilisateur qu'un document a été partagé avec lui"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les informations des utilisateurs
            cursor.execute("""
                SELECT u1.nom as shared_with_nom, u1.prenom as shared_with_prenom, u1.email as shared_with_email,
                       u2.nom as shared_by_nom, u2.prenom as shared_by_prenom
                FROM utilisateur u1, utilisateur u2
                WHERE u1.id = %s AND u2.id = %s
            """, (shared_with_user_id, shared_by_user_id))
            
            users_info = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not users_info:
                return False
            
            # Vérifier si l'utilisateur a activé les notifications email
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT email_notifications 
                FROM parametres 
                WHERE user_id = %s
            """, (shared_with_user_id,))
            
            settings = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not settings or not settings.get('email_notifications', True):
                logger.info(f"Notifications désactivées pour l'utilisateur {shared_with_user_id}")
                return True
            
            # Préparer les données pour l'email
            email_data = {
                'user_name': f"{users_info['shared_with_prenom']} {users_info['shared_with_nom']}",
                'document_title': document_title,
                'shared_by_name': f"{users_info['shared_by_prenom']} {users_info['shared_by_nom']}",
                'date': datetime.now().strftime('%d/%m/%Y à %H:%M'),
                'login_url': 'http://localhost:3000/shared-documents'
            }
            
            # Envoyer l'email
            email_sent = email_service.send_template_email(
                to=[users_info['shared_with_email']],
                template_name='document_shared',
                subject=f'Document partagé avec vous - {document_title}',
                template_data=email_data
            )
            
            if email_sent:
                logger.info(f"✅ Notification de partage envoyée à {users_info['shared_with_email']}")
            else:
                logger.warning(f"⚠️ Échec notification de partage à {users_info['shared_with_email']}")
            
            return email_sent
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la notification de partage: {str(e)}")
            return False
    
    @staticmethod
    def notify_workflow_assigned(workflow_id: int, assigned_user_id: int, assigner_id: int, workflow_title: str):
        """Notifier un utilisateur qu'un workflow lui a été assigné"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les informations des utilisateurs
            cursor.execute("""
                SELECT u1.nom as assigned_nom, u1.prenom as assigned_prenom, u1.email as assigned_email,
                       u2.nom as assigner_nom, u2.prenom as assigner_prenom
                FROM utilisateur u1, utilisateur u2
                WHERE u1.id = %s AND u2.id = %s
            """, (assigned_user_id, assigner_id))
            
            users_info = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not users_info:
                return False
            
            # Vérifier si l'utilisateur a activé les notifications email
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT email_notifications 
                FROM parametres 
                WHERE user_id = %s
            """, (assigned_user_id,))
            
            settings = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not settings or not settings.get('email_notifications', True):
                logger.info(f"Notifications désactivées pour l'utilisateur {assigned_user_id}")
                return True
            
            # Préparer les données pour l'email
            email_data = {
                'user_name': f"{users_info['assigned_prenom']} {users_info['assigned_nom']}",
                'workflow_title': workflow_title,
                'assigner_name': f"{users_info['assigner_prenom']} {users_info['assigner_nom']}",
                'date': datetime.now().strftime('%d/%m/%Y à %H:%M'),
                'login_url': 'http://localhost:3000/workflow'
            }
            
            # Envoyer l'email
            email_sent = email_service.send_template_email(
                to=[users_info['assigned_email']],
                template_name='workflow_notification',
                subject=f'Nouvelle tâche assignée - {workflow_title}',
                template_data=email_data
            )
            
            if email_sent:
                logger.info(f"✅ Notification de workflow envoyée à {users_info['assigned_email']}")
            else:
                logger.warning(f"⚠️ Échec notification de workflow à {users_info['assigned_email']}")
            
            return email_sent
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la notification de workflow: {str(e)}")
            return False
    
    @staticmethod
    def send_custom_notification(user_ids: List[int], subject: str, message: str, template_data: Dict[str, Any] = None):
        """Envoyer une notification personnalisée à une liste d'utilisateurs"""
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les emails des utilisateurs
            placeholders = ','.join(['%s'] * len(user_ids))
            cursor.execute(f"""
                SELECT u.id, u.nom, u.prenom, u.email
                FROM utilisateur u
                WHERE u.id IN ({placeholders})
                AND EXISTS (
                    SELECT 1 FROM parametres 
                    WHERE user_id = u.id 
                    AND email_notifications = true
                )
            """, user_ids)
            
            users = cursor.fetchall()
            cursor.close()
            conn.close()
            
            sent_count = 0
            for user in users:
                try:
                    # Préparer les données de base
                    email_data = {
                        'user_name': f"{user['prenom']} {user['nom']}",
                        'message': message,
                        'date': datetime.now().strftime('%d/%m/%Y à %H:%M'),
                        'login_url': 'http://localhost:3000/dashboard'
                    }
                    
                    # Ajouter les données personnalisées si fournies
                    if template_data:
                        email_data.update(template_data)
                    
                    # Envoyer l'email
                    email_sent = email_service.send_email(
                        to=[user['email']],
                        subject=subject,
                        body=message,
                        html_body=f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                                <h2 style="color: #2c3e50;">ESAG GED - Notification</h2>
                                <p>Bonjour {email_data['user_name']},</p>
                                <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                                    <p style="margin: 0;">{message}</p>
                                </div>
                                <p>Cordialement,<br>L'équipe ESAG GED</p>
                            </div>
                        </body>
                        </html>
                        """
                    )
                    
                    if email_sent:
                        sent_count += 1
                        logger.info(f"✅ Notification personnalisée envoyée à {user['email']}")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur notification personnalisée à {user['email']}: {str(e)}")
            
            logger.info(f"📧 {sent_count}/{len(users)} notifications personnalisées envoyées")
            return sent_count > 0
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi des notifications personnalisées: {str(e)}")
            return False

# Instance globale du service
notification_service = NotificationService() 