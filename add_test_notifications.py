#!/usr/bin/env python3
"""
Script pour ajouter des notifications de test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

def add_test_notifications():
    """Ajouter des notifications de test"""
    print("🔔 AJOUT DE NOTIFICATIONS DE TEST")
    print("=" * 40)
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les utilisateurs
        cursor.execute("SELECT id, nom, prenom FROM utilisateur LIMIT 4")
        users = cursor.fetchall()
        
        if not users:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        print(f"👥 Utilisateurs trouvés: {len(users)}")
        for user in users:
            print(f"   - {user['prenom']} {user['nom']} (ID: {user['id']})")
        
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
                'message': 'Une nouvelle tâche vous a été assignée',
                'type': 'workflow',
                'priority': 3
            }
        ]
        
        notifications_created = 0
        
        print(f"\n📋 Création de {len(test_notifications)} notifications par utilisateur...")
        
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
                    json.dumps({'test': True, 'user': user['prenom']}),
                    datetime.now() - timedelta(hours=i),  # Échelonner dans le temps
                    datetime.now() + timedelta(days=30)   # Expire dans 30 jours
                ))
                
                notifications_created += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ {notifications_created} notifications de test créées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des notifications: {e}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def main():
    """Fonction principale"""
    success = add_test_notifications()
    
    if success:
        print("\n🎉 Notifications de test ajoutées avec succès!")
        print("Vous pouvez maintenant tester l'interface de notifications.")
    else:
        print("\n❌ Échec de l'ajout des notifications de test")

if __name__ == "__main__":
    main() 