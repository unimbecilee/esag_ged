from datetime import datetime
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional

class WorkflowApprobation:
    def __init__(self, id=None, instance_id=None, etape_id=None, approbateur_id=None, 
                 decision=None, commentaire=None, date_decision=None):
        self.id = id
        self.instance_id = instance_id
        self.etape_id = etape_id
        self.approbateur_id = approbateur_id
        self.decision = decision  # 'APPROUVE', 'REJETE'
        self.commentaire = commentaire
        self.date_decision = date_decision or datetime.now()

    @staticmethod
    def get_by_id(approbation_id: int) -> Optional[Dict]:
        """Récupérer une approbation par ID"""
        conn = db_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM workflow_approbation WHERE id = %s
            """, (approbation_id,))
            
            approbation = cursor.fetchone()
            return approbation
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_instance(instance_id: int) -> List[Dict]:
        """Récupérer toutes les approbations d'une instance de workflow"""
        conn = db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT wa.*, 
                       u.nom as approbateur_nom, u.prenom as approbateur_prenom,
                       e.nom as etape_nom, e.ordre as etape_ordre
                FROM workflow_approbation wa
                JOIN utilisateur u ON wa.approbateur_id = u.id
                JOIN etapeworkflow e ON wa.etape_id = e.id
                WHERE wa.instance_id = %s
                ORDER BY e.ordre, wa.date_decision
            """, (instance_id,))
            
            approbations = cursor.fetchall()
            return approbations
            
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def create(instance_id: int, etape_id: int, approbateur_id: int, 
               decision: str, commentaire: str = None) -> int:
        """Créer une nouvelle approbation de workflow"""
        conn = db_connection()
        if not conn:
            raise Exception("Erreur de connexion à la base de données")
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                INSERT INTO workflow_approbation 
                (instance_id, etape_id, approbateur_id, decision, commentaire, date_decision)
                VALUES (%s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (instance_id, etape_id, approbateur_id, decision, commentaire))
            
            approbation_id = cursor.fetchone()['id']
            conn.commit()
            return approbation_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def to_dict(approbation_row) -> Dict:
        """Convertir une ligne d'approbation en dictionnaire"""
        return {
            'id': approbation_row['id'],
            'instance_id': approbation_row['instance_id'],
            'etape_id': approbation_row['etape_id'],
            'approbateur_id': approbation_row['approbateur_id'],
            'decision': approbation_row['decision'],
            'commentaire': approbation_row['commentaire'],
            'date_decision': approbation_row['date_decision'].strftime('%Y-%m-%d %H:%M:%S') if approbation_row['date_decision'] else None
        }