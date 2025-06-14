#!/usr/bin/env python3
"""
Script pour créer des notifications de test
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

# Configuration de la base de données
DB_CONFIG = {
    'host': 'postgresql-thefau.alwaysdata.net',
    'database': 'thefau_archive',
    'user': 'thefau',
    'password': 'Thefau2019'
}

def create_test_notifications():
    """Créer des notifications de test"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les utilisateurs
        cursor.execute("SELECT id, nom, prenom FROM utilisateur LIMIT 4")
        users = cursor.fetchall()
        
        if not users:
            print("❌ Aucun utilisateur trouvé")
            return
        
        print(f"📋 Création de notifications pour {len(users)} utilisateurs...")
        
        # Types de notifications de test
        test_notifications = [
            {
                'title': 'Nouveau document partagé',
                'message': 'Un nouveau document "Rapport mensuel" a été partagé avec vous',
                'type': 'partage',
                'priority': 2
            },
            {
                'title': 'Document modifié',
                'message': 'Le document "Contrat client" a été modifié',
                'type': 'modification',
                'priority': 1
            },
            {
                'title': 'Nouveau commentaire',
                'message': 'Un nouveau commentaire a été ajouté sur "Présentation projet"',
                'type': 'commentaire',
                'priority': 2
            },
            {
                'title': 'Maintenance système',
                'message': 'Maintenance programmée ce soir de 22h à 23h',
                'type': 'system',
                'priority': 3
            },
            {
                'title': 'Workflow assigné',
                'message': 'Une nouvelle tâche vous a été assignée dans le workflow "Validation documents"',
                'type': 'workflow',
                'priority': 3
            }
        ]
        
        notifications_created = 0
        
        for user in users:
            for i, notif in enumerate(test_notifications):
                # Créer quelques notifications lues et non lues
                is_read = i < 2  # Les 2 premières sont lues
                read_at = datetime.now() if is_read else None
                
                cursor.execute("""
                    INSERT INTO notifications 
                    (user_id, title, message, type, priority, is_read, read_at, 
                     metadata, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user['id'],
                    notif['title'],
                    notif['message'],
                    notif['type'],
                    notif['priority'],
                    is_read,
                    read_at,
                    json.dumps({'test': True}),
                    datetime.now() - timedelta(hours=i),  # Échelonner dans le temps
                    datetime.now() + timedelta(days=30)   # Expire dans 30 jours
                ))
                
                notifications_created += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ {notifications_created} notifications de test créées avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des notifications: {e}")

def create_test_preferences():
    """Créer des préférences de test pour tous les utilisateurs"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les utilisateurs
        cursor.execute("SELECT id FROM utilisateur")
        users = cursor.fetchall()
        
        print(f"📋 Création de préférences pour {len(users)} utilisateurs...")
        
        for user in users:
            cursor.execute("""
                INSERT INTO user_notification_preferences 
                (user_id, email_notifications, app_notifications, document_notifications,
                 workflow_notifications, mention_notifications, system_notifications,
                 weekend_notifications, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (user_id) DO NOTHING
            """, (
                user['id'],
                True,   # email_notifications
                True,   # app_notifications
                True,   # document_notifications
                True,   # workflow_notifications
                True,   # mention_notifications
                True,   # system_notifications
                True    # weekend_notifications
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Préférences créées pour tous les utilisateurs")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des préférences: {e}")

def main():
    """Fonction principale"""
    print("🧪 Création de données de test pour les notifications")
    print("=" * 50)
    
    create_test_preferences()
    create_test_notifications()
    
    print("\n" + "=" * 50)
    print("✅ Données de test créées avec succès")

if __name__ == "__main__":
    main() 