from datetime import datetime
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
import json
from typing import List, Dict, Optional

class Workflow:
    def __init__(self, id=None, nom=None, description=None, date_creation=None, 
                 statut=None, createur_id=None, organisation_id=None):
        self.id = id
        self.nom = nom
        self.description = description
        self.date_creation = date_creation
        self.statut = statut
        self.createur_id = createur_id
        self.organisation_id = organisation_id

    @staticmethod
    def create(nom: str, description: str, createur_id: int, organisation_id: int = None) -> int:
        """Créer un nouveau workflow"""
        conn = db_connection()
        if not conn:
            raise Exception("Erreur de connexion à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO workflow (nom, description, date_creation, createur_id, organisation_id)
                VALUES (%s, %s, NOW(), %s, %s)
                RETURNING id
            """, (nom, description, createur_id, organisation_id))
            
            workflow_id = cursor.fetchone()['id']
            conn.commit()
            return workflow_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_id(workflow_id: int) -> Optional[Dict]:
        """Récupérer un workflow par ID"""
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT w.*, u.nom as createur_nom, u.prenom as createur_prenom
                FROM workflow w
                LEFT JOIN utilisateur u ON w.createur_id = u.id
                WHERE w.id = %s
            """, (workflow_id,))
            
            return cursor.fetchone()
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all(organisation_id: int = None) -> List[Dict]:
        """Récupérer tous les workflows"""
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            if organisation_id:
                cursor.execute("""
                    SELECT w.*, u.nom as createur_nom, u.prenom as createur_prenom,
                           COUNT(wi.id) as instances_count
                    FROM workflow w
                    LEFT JOIN utilisateur u ON w.createur_id = u.id
                    LEFT JOIN workflow_instance wi ON w.id = wi.workflow_id
                    WHERE w.organisation_id = %s OR w.organisation_id IS NULL
                    GROUP BY w.id, u.nom, u.prenom
                    ORDER BY w.date_creation DESC
                """, (organisation_id,))
            else:
                cursor.execute("""
                    SELECT w.*, u.nom as createur_nom, u.prenom as createur_prenom,
                           COUNT(wi.id) as instances_count
                    FROM workflow w
                    LEFT JOIN utilisateur u ON w.createur_id = u.id
                    LEFT JOIN workflow_instance wi ON w.id = wi.workflow_id
                    GROUP BY w.id, u.nom, u.prenom
                    ORDER BY w.date_creation DESC
                """)
            
            return cursor.fetchall()
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def update(workflow_id: int, nom: str = None, description: str = None) -> bool:
        """Mettre à jour un workflow"""
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if nom:
                updates.append("nom = %s")
                params.append(nom)
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            
            if not updates:
                return True
            
            params.append(workflow_id)
            query = f"UPDATE workflow SET {', '.join(updates)} WHERE id = %s"
            
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(workflow_id: int) -> bool:
        """Supprimer un workflow (seulement si aucune instance active)"""
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Vérifier s'il y a des instances actives
            cursor.execute("""
                SELECT COUNT(*) as count FROM workflow_instance 
                WHERE workflow_id = %s AND statut IN ('EN_COURS')
            """, (workflow_id,))
            
            count = cursor.fetchone()['count']
            if count > 0:
                raise Exception("Impossible de supprimer un workflow avec des instances actives")
            
            # Supprimer les étapes
            cursor.execute("DELETE FROM etapeworkflow WHERE workflow_id = %s", (workflow_id,))
            
            # Supprimer le workflow
            cursor.execute("DELETE FROM workflow WHERE id = %s", (workflow_id,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_etapes(workflow_id: int) -> List[Dict]:
        """Récupérer les étapes d'un workflow avec leurs approbateurs"""
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les étapes
            cursor.execute("""
                SELECT e.*, 
                       COUNT(wa.id) as approbateurs_count
                FROM etapeworkflow e
                LEFT JOIN workflow_approbateur wa ON e.id = wa.etape_id
                WHERE e.workflow_id = %s
                GROUP BY e.id
                ORDER BY e.ordre
            """, (workflow_id,))
            
            etapes = cursor.fetchall()
            
            # Pour chaque étape, récupérer ses approbateurs
            for etape in etapes:
                cursor.execute("""
                    SELECT wa.*,
                           u.nom as utilisateur_nom, u.prenom as utilisateur_prenom,
                           r.nom as role_nom,
                           o.nom as organisation_nom
                    FROM workflow_approbateur wa
                    LEFT JOIN utilisateur u ON wa.utilisateur_id = u.id
                    LEFT JOIN role r ON wa.role_id = r.id
                    LEFT JOIN organisation o ON wa.organisation_id = o.id
                    WHERE wa.etape_id = %s
                """, (etape['id'],))
                
                approbateurs_raw = cursor.fetchall()
                approbateurs = []
                
                for app in approbateurs_raw:
                    if app['utilisateur_id']:
                        approbateurs.append({
                            'type': 'utilisateur',
                            'id': app['utilisateur_id'],
                            'nom': app['utilisateur_nom'],
                            'prenom': app['utilisateur_prenom']
                        })
                    elif app['role_id']:
                        approbateurs.append({
                            'type': 'role',
                            'id': app['role_id'],
                            'nom': app['role_nom']
                        })
                    elif app['organisation_id']:
                        approbateurs.append({
                            'type': 'organisation',
                            'id': app['organisation_id'],
                            'nom': app['organisation_nom']
                        })
                
                etape['approbateurs'] = approbateurs
            
            return etapes
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_etape(workflow_id: int, nom: str, description: str = None, 
                  type_approbation: str = 'SIMPLE', delai_max: int = None) -> int:
        """Ajouter une étape au workflow"""
        conn = db_connection()
        if not conn:
            raise Exception("Erreur de connexion à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Obtenir le prochain ordre
            cursor.execute("""
                SELECT COALESCE(MAX(ordre), 0) + 1 as next_ordre 
                FROM etapeworkflow WHERE workflow_id = %s
            """, (workflow_id,))
            
            next_ordre = cursor.fetchone()['next_ordre']
            
            cursor.execute("""
                INSERT INTO etapeworkflow (workflow_id, nom, description, ordre, type_approbation, delai_max)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (workflow_id, nom, description, next_ordre, type_approbation, delai_max))
            
            etape_id = cursor.fetchone()['id']
            conn.commit()
            return etape_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_approbateur(etape_id: int, utilisateur_id: int = None, 
                       role_id: int = None, organisation_id: int = None) -> int:
        """Ajouter un approbateur à une étape"""
        if not any([utilisateur_id, role_id, organisation_id]):
            raise Exception("Au moins un type d'approbateur doit être spécifié")
        
        conn = db_connection()
        if not conn:
            raise Exception("Erreur de connexion à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO workflow_approbateur (etape_id, utilisateur_id, role_id, organisation_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (etape_id, utilisateur_id, role_id, organisation_id))
            
            approbateur_id = cursor.fetchone()['id']
            conn.commit()
            return approbateur_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def to_dict(workflow_row) -> Dict:
        """Convertir une ligne de base de données en dictionnaire"""
        if not workflow_row:
            return None
        
        return {
            'id': workflow_row['id'],
            'nom': workflow_row['nom'],
            'description': workflow_row['description'],
            'date_creation': workflow_row['date_creation'].isoformat() if workflow_row['date_creation'] else None,
            'statut': workflow_row['statut'],
            'createur_id': workflow_row['createur_id'],
            'organisation_id': workflow_row['organisation_id'],
            'createur_nom': workflow_row.get('createur_nom'),
            'createur_prenom': workflow_row.get('createur_prenom'),
            'instances_count': workflow_row.get('instances_count', 0)
        } 