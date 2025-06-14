from datetime import datetime
from AppFlask.db import db_connection
import json

class DocumentVersion:
    def __init__(self, document_id, version_number, fichier, taille, mime_type, commentaire, created_by):
        self.document_id = document_id
        self.version_number = version_number
        self.fichier = fichier
        self.taille = taille
        self.mime_type = mime_type
        self.commentaire = commentaire
        self.created_by = created_by
        self.created_at = datetime.utcnow()

    @staticmethod
    def create(document_id, fichier, taille, mime_type, commentaire, created_by):
        """
        Crée une nouvelle version d'un document
        """
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Déterminer le numéro de version (dernière version + 1)
            cursor.execute("""
                SELECT MAX(version_number) as last_version
                FROM document_version
                WHERE document_id = %s
            """, (document_id,))
            
            result = cursor.fetchone()
            last_version = result['last_version'] if result and result['last_version'] else 0
            new_version_number = last_version + 1
            
            # Insérer la nouvelle version
            cursor.execute("""
                INSERT INTO document_version (document_id, version_number, fichier, taille, mime_type, commentaire, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                document_id, 
                new_version_number, 
                fichier, 
                taille, 
                mime_type, 
                commentaire, 
                created_by, 
                datetime.utcnow()
            ))
            
            version_id = cursor.fetchone()['id']
            
            # Mettre à jour le document avec la nouvelle version
            cursor.execute("""
                UPDATE document
                SET fichier = %s, taille = %s, mime_type = %s, derniere_modification = %s, modifie_par = %s
                WHERE id = %s
            """, (fichier, taille, mime_type, datetime.utcnow(), created_by, document_id))
            
            conn.commit()
            return version_id, new_version_number
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_versions(document_id):
        """
        Récupère toutes les versions d'un document
        """
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, u.nom as user_nom, u.prenom as user_prenom
                FROM document_version v
                LEFT JOIN utilisateur u ON v.created_by = u.id
                WHERE v.document_id = %s
                ORDER BY v.version_number DESC
            """, (document_id,))
            
            versions = cursor.fetchall()
            return versions
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_version(version_id):
        """
        Récupère une version spécifique
        """
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, u.nom as user_nom, u.prenom as user_prenom
                FROM document_version v
                LEFT JOIN utilisateur u ON v.created_by = u.id
                WHERE v.id = %s
            """, (version_id,))
            
            version = cursor.fetchone()
            return version
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_version_by_number(document_id, version_number):
        """
        Récupère une version spécifique par son numéro
        """
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, u.nom as user_nom, u.prenom as user_prenom
                FROM document_version v
                LEFT JOIN utilisateur u ON v.created_by = u.id
                WHERE v.document_id = %s AND v.version_number = %s
            """, (document_id, version_number))
            
            version = cursor.fetchone()
            return version
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def restore_version(document_id, version_number, restored_by):
        """
        Restaure une version antérieure comme version actuelle
        """
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Récupérer les informations de la version à restaurer
            cursor.execute("""
                SELECT * FROM document_version
                WHERE document_id = %s AND version_number = %s
            """, (document_id, version_number))
            
            version_to_restore = cursor.fetchone()
            if not version_to_restore:
                return False
            
            # Créer une nouvelle version basée sur l'ancienne
            cursor.execute("""
                SELECT MAX(version_number) as last_version
                FROM document_version
                WHERE document_id = %s
            """, (document_id,))
            
            result = cursor.fetchone()
            last_version = result['last_version'] if result and result['last_version'] else 0
            new_version_number = last_version + 1
            
            # Insérer la nouvelle version (restauration)
            cursor.execute("""
                INSERT INTO document_version (
                    document_id, version_number, fichier, taille, mime_type, 
                    commentaire, created_by, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                document_id,
                new_version_number,
                version_to_restore['fichier'],
                version_to_restore['taille'],
                version_to_restore['mime_type'],
                f"Restauration de la version {version_number}",
                restored_by,
                datetime.utcnow()
            ))
            
            # Mettre à jour le document avec la version restaurée
            cursor.execute("""
                UPDATE document
                SET fichier = %s, taille = %s, mime_type = %s, 
                    derniere_modification = %s, modifie_par = %s
                WHERE id = %s
            """, (
                version_to_restore['fichier'],
                version_to_restore['taille'],
                version_to_restore['mime_type'],
                datetime.utcnow(),
                restored_by,
                document_id
            ))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def to_dict(version):
        """
        Convertit un objet version en dictionnaire
        """
        if not version:
            return None
            
        return {
            'id': version['id'],
            'document_id': version['document_id'],
            'version_number': version['version_number'],
            'fichier': version['fichier'],
            'taille': version['taille'],
            'mime_type': version['mime_type'],
            'commentaire': version['commentaire'],
            'created_by': version['created_by'],
            'created_at': version['created_at'].isoformat() if version['created_at'] else None,
            'created_by_name': f"{version['user_prenom']} {version['user_nom']}" if version.get('user_nom') else None
        } 