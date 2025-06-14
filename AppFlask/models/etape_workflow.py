from datetime import datetime
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional

class EtapeWorkflow:
    def __init__(self, id=None, workflow_id=None, nom=None, description=None, 
                 ordre=None, type_approbation=None, delai_max=None):
        self.id = id
        self.workflow_id = workflow_id
        self.nom = nom
        self.description = description
        self.ordre = ordre
        self.type_approbation = type_approbation
        self.delai_max = delai_max

    @staticmethod
    def get_by_id(etape_id: int) -> Optional[Dict]:
        """Récupérer une étape par ID"""
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM etapeworkflow WHERE id = %s
            """, (etape_id,))
            
            etape = cursor.fetchone()
            return etape
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_workflow(workflow_id: int) -> List[Dict]:
        """Récupérer toutes les étapes d'un workflow"""
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM etapeworkflow 
                WHERE workflow_id = %s 
                ORDER BY ordre
            """, (workflow_id,))
            
            etapes = cursor.fetchall()
            return etapes
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_next_etape(workflow_id: int, current_etape_id: int) -> Optional[Dict]:
        """Récupérer l'étape suivante d'un workflow"""
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM etapeworkflow 
                WHERE workflow_id = %s AND ordre > (
                    SELECT ordre FROM etapeworkflow WHERE id = %s
                )
                ORDER BY ordre 
                LIMIT 1
            """, (workflow_id, current_etape_id))
            
            next_etape = cursor.fetchone()
            return next_etape
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_approbateurs(etape_id: int) -> List[Dict]:
        """Récupérer les approbateurs d'une étape"""
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Récupérer les approbateurs directs (utilisateurs)
            cursor.execute("""
                SELECT u.id, u.nom, u.prenom, u.email, 'utilisateur' as type_approbateur
                FROM workflow_approbateur wa
                JOIN utilisateur u ON wa.utilisateur_id = u.id
                WHERE wa.etape_id = %s AND wa.utilisateur_id IS NOT NULL
            """, (etape_id,))
            
            direct_approvers = cursor.fetchall()
            
            # Récupérer les approbateurs par rôle
            cursor.execute("""
                SELECT u.id, u.nom, u.prenom, u.email, 'role' as type_approbateur, r.nom as role_nom
                FROM workflow_approbateur wa
                JOIN role r ON wa.role_id = r.id
                JOIN utilisateur u ON u.role = r.nom
                WHERE wa.etape_id = %s AND wa.role_id IS NOT NULL
            """, (etape_id,))
            
            role_approvers = cursor.fetchall()
            
            # Récupérer les approbateurs par organisation
            cursor.execute("""
                SELECT u.id, u.nom, u.prenom, u.email, 'organisation' as type_approbateur, o.nom as organisation_nom
                FROM workflow_approbateur wa
                JOIN organisation o ON wa.organisation_id = o.id
                JOIN membre m ON o.id = m.organisation_id
                JOIN utilisateur u ON m.utilisateur_id = u.id
                WHERE wa.etape_id = %s AND wa.organisation_id IS NOT NULL
            """, (etape_id,))
            
            org_approvers = cursor.fetchall()
            
            # Combiner tous les approbateurs
            return direct_approvers + role_approvers + org_approvers
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def create(workflow_id: int, nom: str, description: str, ordre: int, 
               type_approbation: str, delai_max: int) -> int:
        """Créer une nouvelle étape de workflow"""
        conn = db_connection()
        if not conn:
            raise Exception("Erreur de connexion à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                INSERT INTO etapeworkflow 
                (workflow_id, nom, description, ordre, type_approbation, delai_max)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (workflow_id, nom, description, ordre, type_approbation, delai_max))
            
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
    def update(etape_id: int, nom: str = None, description: str = None, 
               ordre: int = None, type_approbation: str = None, delai_max: int = None) -> bool:
        """Mettre à jour une étape de workflow"""
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Construire la requête de mise à jour dynamiquement
            update_fields = []
            params = []
            
            if nom is not None:
                update_fields.append("nom = %s")
                params.append(nom)
                
            if description is not None:
                update_fields.append("description = %s")
                params.append(description)
                
            if ordre is not None:
                update_fields.append("ordre = %s")
                params.append(ordre)
                
            if type_approbation is not None:
                update_fields.append("type_approbation = %s")
                params.append(type_approbation)
                
            if delai_max is not None:
                update_fields.append("delai_max = %s")
                params.append(delai_max)
                
            if not update_fields:
                return False
                
            # Ajouter l'ID de l'étape aux paramètres
            params.append(etape_id)
            
            query = f"""
                UPDATE etapeworkflow 
                SET {", ".join(update_fields)}
                WHERE id = %s
            """
            
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def delete(etape_id: int) -> bool:
        """Supprimer une étape de workflow"""
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Supprimer d'abord les approbateurs associés
            cursor.execute("""
                DELETE FROM workflow_approbateur WHERE etape_id = %s
            """, (etape_id,))
            
            # Puis supprimer l'étape
            cursor.execute("""
                DELETE FROM etapeworkflow WHERE id = %s
            """, (etape_id,))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def add_approbateur(etape_id: int, utilisateur_id: int = None, 
                       role_id: int = None, organisation_id: int = None) -> bool:
        """Ajouter un approbateur à une étape"""
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO workflow_approbateur 
                (etape_id, utilisateur_id, role_id, organisation_id)
                VALUES (%s, %s, %s, %s)
            """, (etape_id, utilisateur_id, role_id, organisation_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def remove_approbateur(etape_id: int, utilisateur_id: int = None, 
                          role_id: int = None, organisation_id: int = None) -> bool:
        """Supprimer un approbateur d'une étape"""
        conn = db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Construire la requête de suppression dynamiquement
            where_clauses = ["etape_id = %s"]
            params = [etape_id]
            
            if utilisateur_id is not None:
                where_clauses.append("utilisateur_id = %s")
                params.append(utilisateur_id)
                
            if role_id is not None:
                where_clauses.append("role_id = %s")
                params.append(role_id)
                
            if organisation_id is not None:
                where_clauses.append("organisation_id = %s")
                params.append(organisation_id)
                
            query = f"""
                DELETE FROM workflow_approbateur 
                WHERE {" AND ".join(where_clauses)}
            """
            
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def to_dict(etape_row) -> Dict:
        """Convertir une ligne d'étape en dictionnaire"""
        return {
            'id': etape_row['id'],
            'workflow_id': etape_row['workflow_id'],
            'nom': etape_row['nom'],
            'description': etape_row['description'],
            'ordre': etape_row['ordre'],
            'type_approbation': etape_row['type_approbation'],
            'delai_max': etape_row['delai_max']
        } 