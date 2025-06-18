from datetime import datetime
from AppFlask.db import db_connection

class History:
    def __init__(self, action_type, entity_type, entity_id, entity_name, description, metadata, user_id):
        self.action_type = action_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.entity_name = entity_name
        self.description = description
        self.metadata = metadata
        self.user_id = user_id
        self.created_at = datetime.utcnow()

    @staticmethod
    def create(action_type, entity_type, entity_id, entity_name, description, metadata, user_id):
        conn = db_connection()
        if not conn:
            return None
        
        try:
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO history (action_type, entity_type, entity_id, entity_name, description, metadata, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (action_type, entity_type, entity_id, entity_name, description, metadata, user_id))
            
            result = cursor.fetchone()
            history_id = result['id'] if isinstance(result, dict) else result[0]
            conn.commit()
            return history_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_all(page=1, per_page=50, **filters):
        conn = db_connection()
        if not conn:
            return [], 0
        
        try:
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Construction de la requête de base
            query = """
                SELECT h.*, u.nom as user_nom, u.prenom as user_prenom
                FROM history h
                LEFT JOIN utilisateur u ON h.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            # Ajout des filtres
            if filters.get('action_type'):
                query += " AND h.action_type = %s"
                params.append(filters['action_type'])
            if filters.get('entity_type'):
                query += " AND h.entity_type = %s"
                params.append(filters['entity_type'])
            if filters.get('user_id'):
                query += " AND h.user_id = %s"
                params.append(filters['user_id'])
            if filters.get('start_date'):
                query += " AND h.created_at >= %s"
                params.append(filters['start_date'])
            if filters.get('end_date'):
                query += " AND h.created_at <= %s"
                params.append(filters['end_date'])
            
            # Compte total pour la pagination
            count_query = f"SELECT COUNT(*) as count FROM ({query}) as count_query"
            cursor.execute(count_query, params)
            count_result = cursor.fetchone()
            total = count_result['count'] if isinstance(count_result, dict) else count_result[0]
            
            # Ajout de la pagination
            query += " ORDER BY h.created_at DESC LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])
            
            cursor.execute(query, params)
            items = cursor.fetchall()
            
            return items, total
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def to_dict(history_item):
        return {
            'id': history_item['id'],
            'action_type': history_item['action_type'],
            'entity_type': history_item['entity_type'],
            'entity_id': history_item['entity_id'],
            'entity_name': history_item['entity_name'],
            'description': history_item['description'],
            'metadata': history_item['metadata'],
            'created_at': history_item['created_at'].isoformat() if history_item['created_at'] else None,
            'user_id': history_item['user_id'],
            'user_name': f"{history_item['user_prenom']} {history_item['user_nom']}" if history_item['user_nom'] else None
        } 