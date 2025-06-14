from AppFlask.db import db_connection
import logging
import json
from datetime import datetime
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class Folder:
    @staticmethod
    def create(title, description=None, parent_id=None, owner_id=None):
        """
        Crée un nouveau dossier
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                INSERT INTO dossier (titre, description, parent_id, proprietaire_id, date_creation, derniere_modification)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id
            """
            cursor.execute(query, (title, description, parent_id, owner_id))
            result = cursor.fetchone()
            
            # Mettre à jour le chemin une fois que l'ID est connu
            folder_id = result['id']
            
            # Construire le chemin
            path = f"/{folder_id}"
            if parent_id:
                # Récupérer le chemin du parent
                cursor.execute("SELECT chemin FROM dossier WHERE id = %s", (parent_id,))
                parent = cursor.fetchone()
                if parent and parent['chemin']:
                    path = f"{parent['chemin']}/{folder_id}"
            
            # Mettre à jour le chemin
            cursor.execute("UPDATE dossier SET chemin = %s WHERE id = %s", (path, folder_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return folder_id
        except Exception as e:
            logger.error(f"Erreur lors de la création du dossier: {str(e)}")
            raise

    @staticmethod
    def get_folder(folder_id):
        """
        Récupère un dossier par son ID
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT d.*, u.nom as proprietaire_nom, u.prenom as proprietaire_prenom
                FROM dossier d
                LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
                WHERE d.id = %s
            """
            cursor.execute(query, (folder_id,))
            folder = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return folder
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du dossier: {str(e)}")
            raise

    @staticmethod
    def get_subfolders(parent_id=None):
        """
        Récupère tous les sous-dossiers d'un dossier parent
        Si parent_id est None, récupère les dossiers racine
        """
        try:
            logger.info(f"Récupération des sous-dossiers pour parent_id={parent_id}")
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if parent_id is None or parent_id == '':
                # Récupérer les dossiers racine (parent_id IS NULL)
                query = """
                    SELECT d.*, u.nom as proprietaire_nom, u.prenom as proprietaire_prenom,
                           (SELECT COUNT(*) FROM dossier WHERE parent_id = d.id) as sous_dossiers_count,
                           (SELECT COUNT(*) FROM document WHERE dossier_id = d.id) as documents_count
                    FROM dossier d
                    LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
                    WHERE d.parent_id IS NULL
                    ORDER BY d.titre
                """
                logger.info("Exécution de la requête pour les dossiers racine")
                cursor.execute(query)
            else:
                # Récupérer les sous-dossiers d'un parent spécifique
                query = """
                    SELECT d.*, u.nom as proprietaire_nom, u.prenom as proprietaire_prenom,
                           (SELECT COUNT(*) FROM dossier WHERE parent_id = d.id) as sous_dossiers_count,
                           (SELECT COUNT(*) FROM document WHERE dossier_id = d.id) as documents_count
                    FROM dossier d
                    LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
                    WHERE d.parent_id = %s
                    ORDER BY d.titre
                """
                logger.info(f"Exécution de la requête pour les sous-dossiers de {parent_id}")
                cursor.execute(query, (parent_id,))
            
            folders = cursor.fetchall()
            logger.info(f"Nombre de dossiers trouvés: {len(folders)}")
            
            # Log des détails des dossiers trouvés
            for folder in folders:
                logger.info(f"Dossier trouvé: ID={folder['id']}, Titre={folder['titre']}, Parent={folder['parent_id']}")
            
            # Vérification supplémentaire pour le parent_id=2
            if parent_id == 2 and len(folders) == 0:
                logger.info("Aucun dossier trouvé pour parent_id=2, renvoi d'une liste vide")
                
            cursor.close()
            conn.close()
            
            return folders
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des sous-dossiers: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    @staticmethod
    def update(folder_id, title=None, description=None, parent_id=None):
        """
        Met à jour un dossier
        """
        try:
            conn = db_connection()
            cursor = conn.cursor()
            
            # Construire la requête dynamiquement en fonction des champs fournis
            update_fields = []
            params = []
            
            if title is not None:
                update_fields.append("titre = %s")
                params.append(title)
                
            if description is not None:
                update_fields.append("description = %s")
                params.append(description)
                
            if parent_id is not None:
                update_fields.append("parent_id = %s")
                params.append(parent_id)
                
            if not update_fields:
                return False
                
            update_fields.append("derniere_modification = CURRENT_TIMESTAMP")
            
            query = f"""
                UPDATE dossier
                SET {", ".join(update_fields)}
                WHERE id = %s
            """
            params.append(folder_id)
            
            cursor.execute(query, tuple(params))
            
            # Si le parent a changé, mettre à jour le chemin
            if parent_id is not None:
                # Récupérer le chemin du parent
                cursor.execute("SELECT chemin FROM dossier WHERE id = %s", (parent_id,))
                parent = cursor.fetchone()
                
                path = f"/{folder_id}"
                if parent and parent[0]:  # parent[0] est le chemin du parent
                    path = f"{parent[0]}/{folder_id}"
                    
                # Mettre à jour le chemin de ce dossier
                cursor.execute("UPDATE dossier SET chemin = %s WHERE id = %s", (path, folder_id))
                
                # Mettre à jour récursivement les chemins des sous-dossiers
                Folder._update_subfolders_paths(cursor, folder_id, path)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du dossier: {str(e)}")
            raise

    @staticmethod
    def delete(folder_id):
        """
        Supprime un dossier (le déplace dans la corbeille)
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les informations du dossier
            cursor.execute("SELECT * FROM dossier WHERE id = %s", (folder_id,))
            folder = cursor.fetchone()
            
            if not folder:
                return False
                
            # Déplacer le dossier dans la corbeille
            cursor.execute("""
                INSERT INTO trash (item_id, item_type, item_data, deleted_by, deleted_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """, (
                folder_id,
                'folder',
                json.dumps(dict(folder)),
                folder['proprietaire_id']
            ))
            
            # Supprimer le dossier
            cursor.execute("DELETE FROM dossier WHERE id = %s", (folder_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du dossier: {str(e)}")
            raise

    @staticmethod
    def _update_subfolders_paths(cursor, parent_id, parent_path):
        """
        Met à jour récursivement les chemins des sous-dossiers
        """
        # Récupérer tous les sous-dossiers
        cursor.execute("SELECT id FROM dossier WHERE parent_id = %s", (parent_id,))
        subfolders = cursor.fetchall()
        
        for subfolder in subfolders:
            subfolder_id = subfolder[0]
            new_path = f"{parent_path}/{subfolder_id}"
            
            # Mettre à jour le chemin
            cursor.execute("UPDATE dossier SET chemin = %s WHERE id = %s", (new_path, subfolder_id))
            
            # Récursion pour les sous-dossiers
            Folder._update_subfolders_paths(cursor, subfolder_id, new_path)

    @staticmethod
    def get_breadcrumb(folder_id):
        """
        Récupère le fil d'Ariane pour un dossier
        """
        try:
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer le chemin du dossier
            cursor.execute("SELECT chemin FROM dossier WHERE id = %s", (folder_id,))
            result = cursor.fetchone()
            
            if not result or not result['chemin']:
                return []
                
            path = result['chemin']
            folder_ids = [int(id) for id in path.strip('/').split('/')]
            
            # Récupérer les informations de tous les dossiers dans le chemin
            placeholders = ', '.join(['%s'] * len(folder_ids))
            query = f"""
                SELECT id, titre
                FROM dossier
                WHERE id IN ({placeholders})
                ORDER BY POSITION(id::text IN %s)
            """
            
            # Construire la chaîne de position
            position_str = '/' + '/'.join(str(id) for id in folder_ids) + '/'
            
            cursor.execute(query, folder_ids + [position_str])
            breadcrumb = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return breadcrumb
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du fil d'Ariane: {str(e)}")
            raise

    @staticmethod
    def to_dict(folder):
        """
        Convertit un objet dossier en dictionnaire
        """
        if not folder:
            return None
            
        return {
            'id': folder['id'],
            'titre': folder['titre'],
            'description': folder['description'],
            'parent_id': folder['parent_id'],
            'proprietaire_id': folder['proprietaire_id'],
            'proprietaire_nom': folder.get('proprietaire_nom'),
            'proprietaire_prenom': folder.get('proprietaire_prenom'),
            'date_creation': folder['date_creation'].isoformat() if folder['date_creation'] else None,
            'derniere_modification': folder['derniere_modification'].isoformat() if folder['derniere_modification'] else None,
            'chemin': folder['chemin'],
            'sous_dossiers_count': folder.get('sous_dossiers_count', 0),
            'documents_count': folder.get('documents_count', 0)
        }