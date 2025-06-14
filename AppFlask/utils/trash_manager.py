#!/usr/bin/env python3
"""
Gestionnaire utilitaire pour les opérations de corbeille ESAG GED
Fonctions centralisées pour déplacer, restaurer et gérer les éléments de la corbeille
"""

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import logging
import json
import os

logger = logging.getLogger(__name__)

class TrashManager:
    """Gestionnaire centralisé pour les opérations de corbeille"""
    
    @staticmethod
    def move_to_trash(item_id, item_type, user_id, deletion_reason=None, original_path=None):
        """
        Déplacer un élément vers la corbeille
        
        Args:
            item_id (int): ID de l'élément à supprimer
            item_type (str): Type d'élément ('document', 'folder', 'user', etc.)
            user_id (int): ID de l'utilisateur qui effectue la suppression
            deletion_reason (str, optional): Raison de la suppression
            original_path (str, optional): Chemin original de l'élément
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les données de l'élément selon son type
            item_data = TrashManager._get_item_data(cursor, item_id, item_type)
            if not item_data:
                logger.error(f"Élément {item_type} avec ID {item_id} non trouvé")
                return False
            
            # Calculer la date d'expiration
            cursor.execute("""
                SELECT setting_value::INTEGER as retention_days 
                FROM trash_config 
                WHERE setting_name = 'retention_days'
            """)
            retention_config = cursor.fetchone()
            retention_days = retention_config['retention_days'] if retention_config else 30
            
            expiry_date = datetime.now() + timedelta(days=retention_days)
            
            # Calculer la taille de l'élément
            size_bytes = TrashManager._calculate_item_size(item_data, item_type)
            
            # Insérer dans la corbeille
            cursor.execute("""
                INSERT INTO trash (
                    item_id, item_type, item_data, deleted_by, deleted_at,
                    expiry_date, size_bytes, original_path, deletion_reason
                ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
                RETURNING id
            """, (
                item_id, item_type, json.dumps(item_data), user_id,
                expiry_date, size_bytes, original_path, deletion_reason
            ))
            
            trash_id = cursor.fetchone()['id']
            
            # Supprimer l'élément de sa table d'origine
            success = TrashManager._delete_from_original_table(cursor, item_id, item_type)
            if not success:
                # Rollback si la suppression échoue
                conn.rollback()
                return False
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Élément {item_type} (ID: {item_id}) déplacé vers la corbeille (Trash ID: {trash_id})")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du déplacement vers la corbeille: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
                cursor.close()
                conn.close()
            return False
    
    @staticmethod
    def restore_from_trash(trash_id, user_id):
        """
        Restaurer un élément depuis la corbeille
        
        Args:
            trash_id (int): ID de l'élément dans la corbeille
            user_id (int): ID de l'utilisateur qui effectue la restauration
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer l'élément de la corbeille
            cursor.execute("""
                SELECT * FROM trash 
                WHERE id = %s AND restored_at IS NULL AND permanent_delete_at IS NULL
            """, (trash_id,))
            
            trash_item = cursor.fetchone()
            if not trash_item:
                logger.error(f"Élément de corbeille avec ID {trash_id} non trouvé")
                return False
            
            # Restaurer selon le type d'élément
            success = TrashManager._restore_to_original_table(cursor, trash_item)
            if not success:
                conn.rollback()
                return False
            
            # Marquer comme restauré dans la corbeille
            cursor.execute("""
                UPDATE trash 
                SET restored_at = CURRENT_TIMESTAMP, restored_by = %s
                WHERE id = %s
            """, (user_id, trash_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Élément {trash_item['item_type']} (Trash ID: {trash_id}) restauré avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
                cursor.close()
                conn.close()
            return False
    
    @staticmethod
    def delete_permanently(trash_id, user_id):
        """
        Supprimer définitivement un élément de la corbeille
        
        Args:
            trash_id (int): ID de l'élément dans la corbeille
            user_id (int): ID de l'utilisateur qui effectue la suppression
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer l'élément de la corbeille
            cursor.execute("""
                SELECT * FROM trash 
                WHERE id = %s AND restored_at IS NULL AND permanent_delete_at IS NULL
            """, (trash_id,))
            
            trash_item = cursor.fetchone()
            if not trash_item:
                logger.error(f"Élément de corbeille avec ID {trash_id} non trouvé")
                return False
            
            # Supprimer les fichiers physiques si nécessaire
            TrashManager._delete_physical_files(trash_item)
            
            # Marquer comme supprimé définitivement
            cursor.execute("""
                UPDATE trash 
                SET permanent_delete_at = CURRENT_TIMESTAMP, permanent_delete_by = %s
                WHERE id = %s
            """, (user_id, trash_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Élément {trash_item['item_type']} (Trash ID: {trash_id}) supprimé définitivement")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression définitive: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
                cursor.close()
                conn.close()
            return False
    
    @staticmethod
    def cleanup_expired_items():
        """
        Nettoyer automatiquement les éléments expirés de la corbeille
        
        Returns:
            int: Nombre d'éléments supprimés
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Vérifier si le nettoyage automatique est activé
            cursor.execute("""
                SELECT setting_value::BOOLEAN as enabled 
                FROM trash_config 
                WHERE setting_name = 'auto_cleanup_enabled'
            """)
            config = cursor.fetchone()
            if not config or not config['enabled']:
                return 0
            
            # Récupérer les éléments expirés
            cursor.execute("""
                SELECT id, item_type, item_data FROM trash 
                WHERE expiry_date < CURRENT_TIMESTAMP 
                AND restored_at IS NULL 
                AND permanent_delete_at IS NULL
            """)
            
            expired_items = cursor.fetchall()
            deleted_count = 0
            
            for item in expired_items:
                # Supprimer les fichiers physiques
                TrashManager._delete_physical_files(item)
                
                # Marquer comme supprimé définitivement
                cursor.execute("""
                    UPDATE trash 
                    SET permanent_delete_at = CURRENT_TIMESTAMP, permanent_delete_by = 0
                    WHERE id = %s
                """, (item['id'],))
                
                deleted_count += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"Nettoyage automatique: {deleted_count} éléments supprimés définitivement")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage automatique: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
                cursor.close()
                conn.close()
            return 0
    
    @staticmethod
    def get_user_trash_stats(user_id):
        """
        Obtenir les statistiques de corbeille pour un utilisateur
        
        Args:
            user_id (int): ID de l'utilisateur
            
        Returns:
            dict: Statistiques de la corbeille
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(*) FILTER (WHERE restored_at IS NULL AND permanent_delete_at IS NULL) as pending_deletion,
                    COUNT(*) FILTER (WHERE restored_at IS NOT NULL) as restored_items,
                    COUNT(*) FILTER (WHERE permanent_delete_at IS NOT NULL) as permanently_deleted,
                    COALESCE(SUM(size_bytes), 0) as total_size,
                    MIN(deleted_at) as oldest_item,
                    MAX(deleted_at) as newest_item
                FROM trash 
                WHERE deleted_by = %s
            """, (user_id,))
            
            stats = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return dict(stats) if stats else {}
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            return {}
    
    @staticmethod
    def _get_item_data(cursor, item_id, item_type):
        """Récupérer les données d'un élément selon son type"""
        try:
            if item_type == 'document':
                cursor.execute("""
                    SELECT titre, description, fichier, taille, mime_type,
                           cloudinary_url, cloudinary_public_id, proprietaire_id, dossier_id
                    FROM document WHERE id = %s
                """, (item_id,))
            elif item_type == 'folder':
                cursor.execute("""
                    SELECT nom, description, proprietaire_id, parent_id
                    FROM dossier WHERE id = %s
                """, (item_id,))
            elif item_type == 'user':
                cursor.execute("""
                    SELECT nom, prenom, email, role, categorie, numero_tel
                    FROM utilisateur WHERE id = %s
                """, (item_id,))
            else:
                logger.error(f"Type d'élément non supporté: {item_type}")
                return None
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données: {str(e)}")
            return None
    
    @staticmethod
    def _calculate_item_size(item_data, item_type):
        """Calculer la taille d'un élément"""
        if item_type == 'document' and 'taille' in item_data:
            return item_data['taille'] or 0
        return 0
    
    @staticmethod
    def _delete_from_original_table(cursor, item_id, item_type):
        """Supprimer un élément de sa table d'origine"""
        try:
            if item_type == 'document':
                cursor.execute("DELETE FROM document WHERE id = %s", (item_id,))
            elif item_type == 'folder':
                cursor.execute("DELETE FROM dossier WHERE id = %s", (item_id,))
            elif item_type == 'user':
                cursor.execute("DELETE FROM utilisateur WHERE id = %s", (item_id,))
            else:
                logger.error(f"Type d'élément non supporté pour suppression: {item_type}")
                return False
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la table d'origine: {str(e)}")
            return False
    
    @staticmethod
    def _restore_to_original_table(cursor, trash_item):
        """Restaurer un élément dans sa table d'origine"""
        try:
            item_data = trash_item['item_data']
            item_type = trash_item['item_type']
            
            if item_type == 'document':
                cursor.execute("""
                    INSERT INTO document (
                        titre, description, fichier, taille, mime_type,
                        cloudinary_url, cloudinary_public_id, proprietaire_id,
                        date_ajout, derniere_modification, dossier_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                """, (
                    item_data.get('titre', ''),
                    item_data.get('description', ''),
                    item_data.get('fichier', ''),
                    item_data.get('taille', 0),
                    item_data.get('mime_type', ''),
                    item_data.get('cloudinary_url', ''),
                    item_data.get('cloudinary_public_id', ''),
                    item_data.get('proprietaire_id'),
                    trash_item['deleted_at'],
                    item_data.get('dossier_id')
                ))
            elif item_type == 'folder':
                cursor.execute("""
                    INSERT INTO dossier (
                        nom, description, proprietaire_id, parent_id,
                        date_creation, derniere_modification
                    ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    item_data.get('nom', ''),
                    item_data.get('description', ''),
                    item_data.get('proprietaire_id'),
                    item_data.get('parent_id'),
                    trash_item['deleted_at']
                ))
            elif item_type == 'user':
                cursor.execute("""
                    INSERT INTO utilisateur (
                        nom, prenom, email, role, categorie, numero_tel,
                        date_creation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    item_data.get('nom', ''),
                    item_data.get('prenom', ''),
                    item_data.get('email', ''),
                    item_data.get('role', 'user'),
                    item_data.get('categorie', ''),
                    item_data.get('numero_tel', ''),
                    trash_item['deleted_at']
                ))
            else:
                logger.error(f"Type d'élément non supporté pour restauration: {item_type}")
                return False
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration: {str(e)}")
            return False
    
    @staticmethod
    def _delete_physical_files(trash_item):
        """Supprimer les fichiers physiques associés à un élément"""
        try:
            if trash_item['item_type'] == 'document':
                item_data = trash_item['item_data']
                if 'fichier' in item_data and item_data['fichier']:
                    # Supprimer le fichier local
                    file_path = os.path.join('uploads', item_data['fichier'])
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Fichier physique supprimé: {file_path}")
                    
                    # TODO: Supprimer de Cloudinary si nécessaire
                    if 'cloudinary_public_id' in item_data and item_data['cloudinary_public_id']:
                        # Implémenter la suppression Cloudinary ici
                        pass
                        
        except Exception as e:
            logger.warning(f"Erreur lors de la suppression des fichiers physiques: {str(e)}")

# Fonctions utilitaires pour l'intégration facile
def move_document_to_trash(document_id, user_id, reason=None):
    """Déplacer un document vers la corbeille"""
    return TrashManager.move_to_trash(document_id, 'document', user_id, reason)

def move_folder_to_trash(folder_id, user_id, reason=None):
    """Déplacer un dossier vers la corbeille"""
    return TrashManager.move_to_trash(folder_id, 'folder', user_id, reason)

def move_user_to_trash(user_id, admin_id, reason=None):
    """Déplacer un utilisateur vers la corbeille"""
    return TrashManager.move_to_trash(user_id, 'user', admin_id, reason) 