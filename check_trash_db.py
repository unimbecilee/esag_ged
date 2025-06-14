#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
import json

def check_trash_db():
    try:
        conn = psycopg2.connect(
            host='postgresql-thefau.alwaysdata.net',
            database='thefau_archive',
            user='thefau',
            password='Thefau2024!'
        )

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier les éléments dans la corbeille
        cursor.execute("""
            SELECT * FROM trash 
            WHERE restored_at IS NULL AND permanent_delete_at IS NULL
            ORDER BY deleted_at DESC 
            LIMIT 10
        """)
        
        items = cursor.fetchall()
        
        print("=== ÉLÉMENTS DANS LA CORBEILLE ===")
        print(f"Nombre d'éléments: {len(items)}")
        print()
        
        for item in items:
            print(f"ID: {item['id']}")
            print(f"Type: {item['item_type']}")
            print(f"Item ID: {item['item_id']}")
            print(f"Supprimé le: {item['deleted_at']}")
            print(f"Supprimé par: {item['deleted_by']}")
            
            # Afficher les données JSON de manière lisible
            if item['item_data']:
                data = item['item_data']
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        pass
                print(f"Données: {data}")
            
            print("---")
        
        # Vérifier aussi les statistiques
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN restored_at IS NOT NULL THEN 1 END) as restored,
                COUNT(CASE WHEN permanent_delete_at IS NOT NULL THEN 1 END) as permanently_deleted,
                COUNT(CASE WHEN restored_at IS NULL AND permanent_delete_at IS NULL THEN 1 END) as active
            FROM trash
        """)
        
        stats = cursor.fetchone()
        print("\n=== STATISTIQUES CORBEILLE ===")
        print(f"Total éléments: {stats['total']}")
        print(f"Actifs (dans la corbeille): {stats['active']}")
        print(f"Restaurés: {stats['restored']}")
        print(f"Supprimés définitivement: {stats['permanently_deleted']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_trash_db() 