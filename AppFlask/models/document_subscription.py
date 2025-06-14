from datetime import datetime
from AppFlask.db import db_connection

class DocumentSubscription:
    def __init__(self, document_id, user_id, notify_new_version=True, notify_metadata_change=True, 
                 notify_comments=True, notify_workflow=True):
        self.document_id = document_id
        self.user_id = user_id
        self.notify_new_version = notify_new_version
        self.notify_metadata_change = notify_metadata_change
        self.notify_comments = notify_comments
        self.notify_workflow = notify_workflow
        self.created_at = datetime.utcnow()

    @staticmethod
    def create(document_id, user_id, notify_new_version=True, notify_metadata_change=True, 
               notify_comments=True, notify_workflow=True):
        """
        Crée un nouvel abonnement à un document
        """
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Vérifier si un abonnement existe déjà
            cursor.execute("""
                SELECT id FROM document_subscription
                WHERE document_id = %s AND user_id = %s
            """, (document_id, user_id))
            
            existing = cursor.fetchone()
            if existing:
                # Mettre à jour l'abonnement existant
                cursor.execute("""
                    UPDATE document_subscription
                    SET notify_new_version = %s, notify_metadata_change = %s,
                        notify_comments = %s, notify_workflow = %s, updated_at = %s
                    WHERE document_id = %s AND user_id = %s
                    RETURNING id
                """, (
                    notify_new_version, notify_metadata_change, notify_comments, 
                    notify_workflow, datetime.utcnow(), document_id, user_id
                ))
                
                subscription_id = cursor.fetchone()['id']
            else:
                # Créer un nouvel abonnement
                cursor.execute("""
                    INSERT INTO document_subscription (
                        document_id, user_id, notify_new_version, notify_metadata_change,
                        notify_comments, notify_workflow, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    document_id, user_id, notify_new_version, notify_metadata_change,
                    notify_comments, notify_workflow, datetime.utcnow()
                ))
                
                subscription_id = cursor.fetchone()['id']
            
            conn.commit()
            return subscription_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_subscription(document_id, user_id):
        """
        Récupère l'abonnement d'un utilisateur à un document
        """
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM document_subscription
                WHERE document_id = %s AND user_id = %s
            """, (document_id, user_id))
            
            subscription = cursor.fetchone()
            return subscription
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_document_subscribers(document_id, event_type=None):
        """
        Récupère tous les utilisateurs abonnés à un document, filtré par type d'événement si spécifié
        """
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT s.*, u.nom, u.prenom, u.email
                FROM document_subscription s
                JOIN utilisateur u ON s.user_id = u.id
                WHERE s.document_id = %s
            """
            
            params = [document_id]
            
            # Filtrer par type d'événement si spécifié
            if event_type == 'new_version':
                query += " AND s.notify_new_version = TRUE"
            elif event_type == 'metadata_change':
                query += " AND s.notify_metadata_change = TRUE"
            elif event_type == 'comments':
                query += " AND s.notify_comments = TRUE"
            elif event_type == 'workflow':
                query += " AND s.notify_workflow = TRUE"
            
            cursor.execute(query, params)
            subscribers = cursor.fetchall()
            return subscribers
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_subscriptions(user_id):
        """
        Récupère tous les abonnements d'un utilisateur
        """
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, d.titre as document_titre
                FROM document_subscription s
                JOIN document d ON s.document_id = d.id
                WHERE s.user_id = %s
                ORDER BY s.created_at DESC
            """, (user_id,))
            
            subscriptions = cursor.fetchall()
            return subscriptions
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(document_id, user_id):
        """
        Supprime un abonnement
        """
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM document_subscription
                WHERE document_id = %s AND user_id = %s
                RETURNING id
            """, (document_id, user_id))
            
            result = cursor.fetchone()
            conn.commit()
            return result is not None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def notify_subscribers(document_id, event_type, event_data):
        """
        Récupère les abonnés à notifier pour un événement spécifique
        """
        subscribers = DocumentSubscription.get_document_subscribers(document_id, event_type)
        
        # À ce stade, vous pourriez intégrer avec un service de notification
        # pour envoyer des e-mails, des notifications push, etc.
        # Pour l'instant, nous retournons simplement la liste des abonnés à notifier
        return subscribers

    @staticmethod
    def to_dict(subscription):
        """
        Convertit un objet abonnement en dictionnaire
        """
        if not subscription:
            return None
            
        return {
            'id': subscription['id'],
            'document_id': subscription['document_id'],
            'user_id': subscription['user_id'],
            'notify_new_version': subscription['notify_new_version'],
            'notify_metadata_change': subscription['notify_metadata_change'],
            'notify_comments': subscription['notify_comments'],
            'notify_workflow': subscription['notify_workflow'],
            'created_at': subscription['created_at'].isoformat() if subscription['created_at'] else None,
            'updated_at': subscription['updated_at'].isoformat() if subscription.get('updated_at') else None,
            'document_titre': subscription.get('document_titre'),
            'user_name': f"{subscription.get('prenom')} {subscription.get('nom')}" if subscription.get('nom') else None,
            'user_email': subscription.get('email')
        } 