#!/usr/bin/env python3
"""
Vérification des utilisateurs dans la base de données
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def check_users():
    """Vérifier les utilisateurs dans la base de données"""
    try:
        # Connexion à la base de données (configuration corrigée)
        conn = psycopg2.connect(
            host="postgresql-thefau.alwaysdata.net",
            database="thefau_archive",  # Nom correct de la base
            user="thefau",
            password="Passecale2002@"  # Mot de passe correct
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer tous les utilisateurs
        cursor.execute("""
            SELECT id, nom, prenom, email, role, date_creation
            FROM utilisateur
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        print(f"👥 Utilisateurs trouvés ({len(users)}):")
        print("-" * 80)
        
        for user in users:
            print(f"ID: {user['id']}")
            print(f"Nom: {user['nom']} {user['prenom']}")
            print(f"Email: {user['email']}")
            print(f"Rôle: {user['role']}")
            print(f"Créé le: {user['date_creation']}")
            print("-" * 40)
        
        # Vérifier la corbeille
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN item_type = 'document' THEN 1 END) as documents
            FROM trash 
            WHERE restored_at IS NULL AND permanent_delete_at IS NULL
        """)
        
        trash_stats = cursor.fetchone()
        print(f"\n🗑️ Statistiques de la corbeille:")
        print(f"Total éléments: {trash_stats['total']}")
        print(f"Documents: {trash_stats['documents']}")
        
        # Récupérer quelques éléments de la corbeille
        cursor.execute("""
            SELECT id, item_id, item_type, item_data, deleted_at, deleted_by
            FROM trash 
            WHERE restored_at IS NULL AND permanent_delete_at IS NULL
            ORDER BY deleted_at DESC
            LIMIT 3
        """)
        
        trash_items = cursor.fetchall()
        print(f"\n📄 Éléments récents dans la corbeille ({len(trash_items)}):")
        for item in trash_items:
            print(f"- ID: {item['id']}, Type: {item['item_type']}, Item ID: {item['item_id']}")
            if item['item_data']:
                data = item['item_data']
                title = data.get('titre') or data.get('nom', 'Sans titre')
                print(f"  Titre: {title}")
        
        cursor.close()
        conn.close()
        
        return users
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

if __name__ == "__main__":
    check_users() 