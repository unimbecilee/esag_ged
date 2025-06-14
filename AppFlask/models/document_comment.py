from datetime import datetime
from AppFlask.db import db_connection

class DocumentComment:
    def __init__(self, document_id, content, created_by, parent_id=None):
        self.document_id = document_id
        self.content = content
        self.created_by = created_by
        self.parent_id = parent_id
        self.created_at = datetime.utcnow()

    @staticmethod
    def create(document_id, content, created_by, parent_id=None):
        """
        Crée un nouveau commentaire sur un document
        """
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO document_comment (document_id, content, created_by, parent_id, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (document_id, content, created_by, parent_id, datetime.utcnow()))
            
            comment_id = cursor.fetchone()['id']
            conn.commit()
            return comment_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_comments(document_id):
        """
        Récupère tous les commentaires d'un document, organisés hiérarchiquement
        """
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Récupérer d'abord tous les commentaires racines (sans parent)
            cursor.execute("""
                SELECT c.*, u.nom as user_nom, u.prenom as user_prenom
                FROM document_comment c
                LEFT JOIN utilisateur u ON c.created_by = u.id
                WHERE c.document_id = %s AND c.parent_id IS NULL
                ORDER BY c.created_at ASC
            """, (document_id,))
            
            root_comments = cursor.fetchall()
            
            # Pour chaque commentaire racine, récupérer ses réponses
            result = []
            for comment in root_comments:
                comment_with_replies = {
                    'comment': comment,
                    'replies': DocumentComment._get_replies(comment['id'], cursor)
                }
                result.append(comment_with_replies)
            
            return result
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def _get_replies(parent_id, cursor):
        """
        Fonction récursive pour récupérer les réponses à un commentaire
        """
        cursor.execute("""
            SELECT c.*, u.nom as user_nom, u.prenom as user_prenom
            FROM document_comment c
            LEFT JOIN utilisateur u ON c.created_by = u.id
            WHERE c.parent_id = %s
            ORDER BY c.created_at ASC
        """, (parent_id,))
        
        replies = cursor.fetchall()
        result = []
        
        for reply in replies:
            reply_with_replies = {
                'comment': reply,
                'replies': DocumentComment._get_replies(reply['id'], cursor)
            }
            result.append(reply_with_replies)
        
        return result

    @staticmethod
    def get_comment(comment_id):
        """
        Récupère un commentaire spécifique
        """
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, u.nom as user_nom, u.prenom as user_prenom
                FROM document_comment c
                LEFT JOIN utilisateur u ON c.created_by = u.id
                WHERE c.id = %s
            """, (comment_id,))
            
            comment = cursor.fetchone()
            return comment
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(comment_id, content, updated_by):
        """
        Met à jour un commentaire existant
        """
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Vérifier que l'utilisateur est bien l'auteur du commentaire
            cursor.execute("""
                SELECT created_by FROM document_comment
                WHERE id = %s
            """, (comment_id,))
            
            comment = cursor.fetchone()
            if not comment or comment['created_by'] != updated_by:
                return False
            
            cursor.execute("""
                UPDATE document_comment
                SET content = %s, updated_at = %s
                WHERE id = %s
                RETURNING id
            """, (content, datetime.utcnow(), comment_id))
            
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
    def delete(comment_id, deleted_by):
        """
        Supprime un commentaire
        """
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Vérifier que l'utilisateur est bien l'auteur du commentaire
            cursor.execute("""
                SELECT created_by FROM document_comment
                WHERE id = %s
            """, (comment_id,))
            
            comment = cursor.fetchone()
            if not comment or comment['created_by'] != deleted_by:
                return False
            
            # Supprimer le commentaire et toutes ses réponses
            cursor.execute("""
                WITH RECURSIVE comment_tree AS (
                    SELECT id FROM document_comment WHERE id = %s
                    UNION ALL
                    SELECT c.id FROM document_comment c
                    JOIN comment_tree ct ON c.parent_id = ct.id
                )
                DELETE FROM document_comment
                WHERE id IN (SELECT id FROM comment_tree)
                RETURNING id
            """, (comment_id,))
            
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
    def to_dict(comment):
        """
        Convertit un objet commentaire en dictionnaire
        """
        if not comment:
            return None
            
        return {
            'id': comment['id'],
            'document_id': comment['document_id'],
            'content': comment['content'],
            'parent_id': comment['parent_id'],
            'created_by': comment['created_by'],
            'created_at': comment['created_at'].isoformat() if comment['created_at'] else None,
            'updated_at': comment['updated_at'].isoformat() if comment.get('updated_at') else None,
            'created_by_name': f"{comment['user_prenom']} {comment['user_nom']}" if comment.get('user_nom') else None
        } 