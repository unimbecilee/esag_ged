from datetime import datetime
from AppFlask.db import db_connection

class DocumentCheckout:
    def __init__(self, document_id, checked_out_by, expiration=None):
        self.document_id = document_id
        self.checked_out_by = checked_out_by
        self.checked_out_at = datetime.utcnow()
        self.expiration = expiration if expiration else self.checked_out_at + datetime.timedelta(days=1)
        self.checked_in_at = None

    @staticmethod
    def check_out(document_id, user_id, expiration=None):
        """
        Réserve (check-out) un document pour modification exclusive
        """
        conn = db_connection()
        if not conn:
            return None, "Erreur de connexion à la base de données"
        
        try:
            cursor = conn.cursor()
            
            # Vérifier si le document est déjà réservé
            cursor.execute("""
                SELECT * FROM document_checkout
                WHERE document_id = %s AND checked_in_at IS NULL
            """, (document_id,))
            
            existing = cursor.fetchone()
            if existing:
                # Le document est déjà réservé
                cursor.close()
                conn.close()
                return None, "Le document est déjà réservé par un autre utilisateur"
            
            # Calculer la date d'expiration par défaut (1 jour)
            if not expiration:
                expiration = datetime.utcnow() + datetime.timedelta(days=1)
            
            # Réserver le document
            cursor.execute("""
                INSERT INTO document_checkout (document_id, checked_out_by, checked_out_at, expiration)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (document_id, user_id, datetime.utcnow(), expiration))
            
            checkout_id = cursor.fetchone()['id']
            
            # Mettre à jour le statut du document
            cursor.execute("""
                UPDATE document
                SET is_checked_out = TRUE, checked_out_by = %s
                WHERE id = %s
            """, (user_id, document_id))
            
            conn.commit()
            return checkout_id, None
        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def check_in(document_id, user_id):
        """
        Libère (check-in) un document précédemment réservé
        """
        conn = db_connection()
        if not conn:
            return False, "Erreur de connexion à la base de données"
        
        try:
            cursor = conn.cursor()
            
            # Vérifier si le document est réservé par cet utilisateur
            cursor.execute("""
                SELECT * FROM document_checkout
                WHERE document_id = %s AND checked_out_by = %s AND checked_in_at IS NULL
            """, (document_id, user_id))
            
            checkout = cursor.fetchone()
            if not checkout:
                cursor.close()
                conn.close()
                return False, "Le document n'est pas réservé par vous"
            
            # Libérer le document
            cursor.execute("""
                UPDATE document_checkout
                SET checked_in_at = %s
                WHERE id = %s
                RETURNING id
            """, (datetime.utcnow(), checkout['id']))
            
            result = cursor.fetchone()
            
            # Mettre à jour le statut du document
            cursor.execute("""
                UPDATE document
                SET is_checked_out = FALSE, checked_out_by = NULL
                WHERE id = %s
            """, (document_id,))
            
            conn.commit()
            return result is not None, None
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def force_check_in(document_id, admin_id):
        """
        Force la libération d'un document (pour les administrateurs)
        """
        conn = db_connection()
        if not conn:
            return False, "Erreur de connexion à la base de données"
        
        try:
            cursor = conn.cursor()
            
            # Vérifier si le document est réservé
            cursor.execute("""
                SELECT * FROM document_checkout
                WHERE document_id = %s AND checked_in_at IS NULL
            """, (document_id,))
            
            checkout = cursor.fetchone()
            if not checkout:
                cursor.close()
                conn.close()
                return False, "Le document n'est pas réservé"
            
            # Libérer le document de force
            cursor.execute("""
                UPDATE document_checkout
                SET checked_in_at = %s, force_checked_in_by = %s
                WHERE id = %s
                RETURNING id
            """, (datetime.utcnow(), admin_id, checkout['id']))
            
            result = cursor.fetchone()
            
            # Mettre à jour le statut du document
            cursor.execute("""
                UPDATE document
                SET is_checked_out = FALSE, checked_out_by = NULL
                WHERE id = %s
            """, (document_id,))
            
            conn.commit()
            return result is not None, None
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_checkout_status(document_id):
        """
        Récupère le statut de réservation d'un document
        """
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, u.nom as user_nom, u.prenom as user_prenom
                FROM document_checkout c
                LEFT JOIN utilisateur u ON c.checked_out_by = u.id
                WHERE c.document_id = %s AND c.checked_in_at IS NULL
            """, (document_id,))
            
            checkout = cursor.fetchone()
            return checkout
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_checkouts(user_id):
        """
        Récupère tous les documents réservés par un utilisateur
        """
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, d.titre as document_titre
                FROM document_checkout c
                JOIN document d ON c.document_id = d.id
                WHERE c.checked_out_by = %s AND c.checked_in_at IS NULL
                ORDER BY c.checked_out_at DESC
            """, (user_id,))
            
            checkouts = cursor.fetchall()
            return checkouts
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_checkout_history(document_id):
        """
        Récupère l'historique complet des réservations d'un document
        """
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, 
                       u1.nom as checked_out_by_nom, u1.prenom as checked_out_by_prenom,
                       u2.nom as force_checked_in_by_nom, u2.prenom as force_checked_in_by_prenom
                FROM document_checkout c
                LEFT JOIN utilisateur u1 ON c.checked_out_by = u1.id
                LEFT JOIN utilisateur u2 ON c.force_checked_in_by = u2.id
                WHERE c.document_id = %s
                ORDER BY c.checked_out_at DESC
            """, (document_id,))
            
            history = cursor.fetchall()
            return history
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def cleanup_expired_checkouts():
        """
        Nettoie les réservations expirées
        """
        conn = db_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE document_checkout
                SET checked_in_at = %s, is_expired = TRUE
                WHERE checked_in_at IS NULL AND expiration < %s
                RETURNING document_id
            """, (datetime.utcnow(), datetime.utcnow()))
            
            expired_docs = cursor.fetchall()
            
            # Mettre à jour les documents correspondants
            for doc in expired_docs:
                cursor.execute("""
                    UPDATE document
                    SET is_checked_out = FALSE, checked_out_by = NULL
                    WHERE id = %s
                """, (doc['document_id'],))
            
            conn.commit()
            return len(expired_docs)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def to_dict(checkout):
        """
        Convertit un objet checkout en dictionnaire
        """
        if not checkout:
            return None
            
        result = {
            'id': checkout['id'],
            'document_id': checkout['document_id'],
            'checked_out_by': checkout['checked_out_by'],
            'checked_out_at': checkout['checked_out_at'].isoformat() if checkout['checked_out_at'] else None,
            'expiration': checkout['expiration'].isoformat() if checkout['expiration'] else None,
            'checked_in_at': checkout['checked_in_at'].isoformat() if checkout.get('checked_in_at') else None,
            'is_expired': checkout.get('is_expired', False),
            'force_checked_in_by': checkout.get('force_checked_in_by'),
            'document_titre': checkout.get('document_titre')
        }
        
        # Ajouter les noms des utilisateurs s'ils sont disponibles
        if checkout.get('user_nom'):
            result['checked_out_by_name'] = f"{checkout['user_prenom']} {checkout['user_nom']}"
            
        if checkout.get('force_checked_in_by_nom'):
            result['force_checked_in_by_name'] = f"{checkout['force_checked_in_by_prenom']} {checkout['force_checked_in_by_nom']}"
            
        return result