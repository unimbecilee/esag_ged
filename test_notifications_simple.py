#!/usr/bin/env python3
"""
Test simple du système de notifications
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def test_notification_creation():
    """Test de création de notification simple"""
    print("🧪 TEST DE CRÉATION DE NOTIFICATION")
    print("=" * 40)
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer un utilisateur pour le test
        cursor.execute("SELECT id, nom, prenom FROM utilisateur LIMIT 1")
        user = cursor.fetchone()
        
        if not user:
            print("❌ Aucun utilisateur trouvé pour le test")
            return False
        
        print(f"👤 Test avec l'utilisateur: {user['prenom']} {user['nom']}")
        
        # Créer une notification de test simple
        cursor.execute("""
            INSERT INTO notifications (
                user_id, title, message, type, priority, 
                metadata, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            user['id'],
            'Test système de notifications',
            'Ceci est une notification de test pour vérifier le fonctionnement du système.',
            'system_test',
            2,
            '{"test": true, "created_by": "test_script"}'
        ))
        
        notification_id = cursor.fetchone()['id']
        conn.commit()
        
        print(f"✅ Notification créée avec l'ID: {notification_id}")
        
        # Vérifier le nombre de notifications non lues
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM notifications 
            WHERE user_id = %s AND is_read = false
        """, (user['id'],))
        
        unread_count = cursor.fetchone()['count']
        print(f"📊 Nombre de notifications non lues: {unread_count}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False

def test_notification_preferences():
    """Test des préférences de notification"""
    print("\n⚙️ TEST DES PRÉFÉRENCES")
    print("=" * 30)
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier les préférences existantes
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM user_notification_preferences
        """)
        
        prefs_count = cursor.fetchone()['count']
        print(f"👥 Préférences configurées pour {prefs_count} utilisateurs")
        
        # Créer des préférences pour les utilisateurs sans préférences
        cursor.execute("""
            INSERT INTO user_notification_preferences (user_id)
            SELECT u.id 
            FROM utilisateur u
            WHERE NOT EXISTS (
                SELECT 1 FROM user_notification_preferences p 
                WHERE p.user_id = u.id
            )
        """)
        
        new_prefs = cursor.rowcount
        if new_prefs > 0:
            print(f"✅ {new_prefs} nouvelles préférences créées")
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test préférences: {str(e)}")
        return False

def test_notification_api():
    """Test simple de l'API de notifications"""
    print("\n🌐 TEST API NOTIFICATIONS")
    print("=" * 30)
    
    try:
        # Importer le service de notifications
        from AppFlask.services.notification_service import NotificationService
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer un utilisateur
        cursor.execute("SELECT id FROM utilisateur LIMIT 1")
        user = cursor.fetchone()
        
        if user:
            # Tester la création de notification via le service
            notification_id = NotificationService.create_notification(
                user_id=user['id'],
                title='Test API Service',
                message='Test de création de notification via le service API',
                notification_type='test',
                priority=1,
                send_email=False  # Pas d'email pour le test
            )
            
            if notification_id:
                print(f"✅ Notification créée via API: {notification_id}")
            else:
                print("❌ Échec création via API")
        
        cursor.close()
        conn.close()
        
        return notification_id is not None
        
    except Exception as e:
        print(f"❌ Erreur test API: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    print("🔔 TEST SYSTÈME DE NOTIFICATIONS - VERSION SIMPLE")
    print("=" * 55)
    
    # Test de création basique
    creation_test = test_notification_creation()
    
    # Test des préférences
    preferences_test = test_notification_preferences()
    
    # Test de l'API
    api_test = test_notification_api()
    
    print("\n🎯 RÉSULTATS DES TESTS")
    print("=" * 25)
    print(f"Création notification: {'✅ RÉUSSI' if creation_test else '❌ ÉCHOUÉ'}")
    print(f"Préférences utilisateur: {'✅ RÉUSSI' if preferences_test else '❌ ÉCHOUÉ'}")
    print(f"API Service: {'✅ RÉUSSI' if api_test else '❌ ÉCHOUÉ'}")
    
    if creation_test and preferences_test and api_test:
        print("\n🎉 SYSTÈME DE NOTIFICATIONS FONCTIONNEL!")
        print("\n📋 VÉRIFICATIONS À FAIRE:")
        print("1. Vérifier l'affichage des notifications dans l'interface")
        print("2. Tester le badge de notification dans la sidebar")
        print("3. Tester les clics sur les notifications")
        print("4. Vérifier les notifications de workflow")
        print("5. Tester les demandes d'archivage")
        
        return True
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        return False

if __name__ == "__main__":
    main() 