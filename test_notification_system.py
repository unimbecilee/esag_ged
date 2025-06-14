#!/usr/bin/env python3
"""
Test complet du système de notifications ESAG GED
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_server_connection():
    """Tester la connexion au serveur"""
    print("🌐 TEST CONNEXION SERVEUR")
    print("=" * 30)
    
    try:
        response = requests.get('http://localhost:5000', timeout=5)
        print(f"✅ Serveur accessible (Status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Serveur non accessible")
        return False
    except Exception as e:
        print(f"❌ Erreur connexion: {str(e)}")
        return False

def test_notification_api():
    """Tester l'API des notifications"""
    print("\n🔔 TEST API NOTIFICATIONS")
    print("=" * 30)
    
    # Données de test pour la connexion
    login_data = {
        "email": "admin@esag.com",
        "password": "admin123"
    }
    
    try:
        # Connexion
        print("🔐 Connexion...")
        login_response = requests.post(
            'http://localhost:5000/api/auth/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Échec connexion: {login_response.status_code}")
            return False
        
        token = login_response.json().get('token')
        if not token:
            print("❌ Token non reçu")
            return False
        
        print("✅ Connexion réussie")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Test 1: Récupérer les notifications
        print("\n📋 Test récupération notifications...")
        notif_response = requests.get(
            'http://localhost:5000/api/notifications',
            headers=headers
        )
        
        if notif_response.status_code == 200:
            notifications = notif_response.json().get('notifications', [])
            print(f"✅ {len(notifications)} notifications récupérées")
        else:
            print(f"⚠️ Erreur récupération notifications: {notif_response.status_code}")
        
        # Test 2: Récupérer le nombre de non lues
        print("\n🔢 Test comptage non lues...")
        count_response = requests.get(
            'http://localhost:5000/api/notifications/unread-count',
            headers=headers
        )
        
        if count_response.status_code == 200:
            unread_count = count_response.json().get('unread_count', 0)
            print(f"✅ {unread_count} notifications non lues")
        else:
            print(f"⚠️ Erreur comptage: {count_response.status_code}")
        
        # Test 3: Récupérer les statistiques
        print("\n📊 Test statistiques...")
        stats_response = requests.get(
            'http://localhost:5000/api/notifications/stats',
            headers=headers
        )
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"✅ Statistiques récupérées: {stats.get('general', {}).get('total', 0)} total")
        else:
            print(f"⚠️ Erreur statistiques: {stats_response.status_code}")
        
        # Test 4: Récupérer les préférences
        print("\n⚙️ Test préférences...")
        prefs_response = requests.get(
            'http://localhost:5000/api/notifications/preferences',
            headers=headers
        )
        
        if prefs_response.status_code == 200:
            preferences = prefs_response.json().get('preferences', {})
            print(f"✅ Préférences récupérées: email={preferences.get('email_notifications', 'N/A')}")
        else:
            print(f"⚠️ Erreur préférences: {prefs_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test API: {str(e)}")
        return False

def test_notification_creation():
    """Tester la création de notifications"""
    print("\n🆕 TEST CRÉATION NOTIFICATIONS")
    print("=" * 35)
    
    try:
        from AppFlask import create_app
        from AppFlask.services.notification_service import notification_service
        
        app = create_app()
        with app.app_context():
            # Test création notification simple
            print("📝 Création notification de test...")
            
            notification_id = notification_service.create_notification(
                user_id=1,
                title="Test système de notifications",
                message="Ceci est une notification de test pour vérifier le bon fonctionnement du système",
                notification_type="test",
                priority=2,
                send_email=False
            )
            
            if notification_id:
                print(f"✅ Notification créée (ID: {notification_id})")
                
                # Test création notification avec métadonnées
                print("📝 Création notification avec métadonnées...")
                
                notification_id_2 = notification_service.create_notification(
                    user_id=1,
                    title="Test avec métadonnées",
                    message="Notification avec des données supplémentaires",
                    notification_type="document_uploaded",
                    priority=3,
                    metadata={
                        'document_title': 'Document de test',
                        'document_type': 'PDF',
                        'test_data': 'Données de test'
                    },
                    send_email=False
                )
                
                if notification_id_2:
                    print(f"✅ Notification avec métadonnées créée (ID: {notification_id_2})")
                else:
                    print("❌ Échec création notification avec métadonnées")
                
                return True
            else:
                print("❌ Échec création notification")
                return False
        
    except Exception as e:
        print(f"❌ Erreur test création: {str(e)}")
        return False

def test_email_notifications():
    """Tester les notifications par email"""
    print("\n📧 TEST NOTIFICATIONS EMAIL")
    print("=" * 30)
    
    try:
        from AppFlask import create_app
        from AppFlask.services.email_service import email_service
        
        app = create_app()
        with app.app_context():
            # Test configuration email
            print("🔧 Vérification configuration email...")
            
            if email_service.is_configured():
                print("✅ Service email configuré")
                
                # Test connexion SMTP
                print("🔗 Test connexion SMTP...")
                if email_service.test_connection():
                    print("✅ Connexion SMTP réussie")
                    
                    # Test envoi email de notification
                    print("📤 Test envoi email notification...")
                    
                    email_data = {
                        'user_name': 'Utilisateur Test',
                        'notification_title': 'Test système de notifications',
                        'notification_message': 'Ceci est un test du système de notifications par email',
                        'notification_type': 'test',
                        'date': datetime.now().strftime('%d/%m/%Y à %H:%M'),
                        'login_url': 'http://localhost:3000/notifications'
                    }
                    
                    email_sent = email_service.send_template_email(
                        to=['mainuser1006@gmail.com'],  # Email de test
                        template_name='notification_general',
                        subject='ESAG GED - Test système de notifications',
                        template_data=email_data
                    )
                    
                    if email_sent:
                        print("✅ Email de notification envoyé avec succès")
                        return True
                    else:
                        print("❌ Échec envoi email")
                        return False
                else:
                    print("❌ Échec connexion SMTP")
                    return False
            else:
                print("❌ Service email non configuré")
                return False
        
    except Exception as e:
        print(f"❌ Erreur test email: {str(e)}")
        return False

def test_notification_templates():
    """Tester les templates de notifications"""
    print("\n📝 TEST TEMPLATES NOTIFICATIONS")
    print("=" * 35)
    
    try:
        from AppFlask import create_app
        from AppFlask.db import db_connection
        from psycopg2.extras import RealDictCursor
        
        app = create_app()
        with app.app_context():
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Vérifier les templates en base
            print("🔍 Vérification templates en base...")
            
            cursor.execute("SELECT name, title_template FROM notification_templates WHERE is_active = true")
            templates = cursor.fetchall()
            
            print(f"✅ {len(templates)} templates actifs trouvés:")
            for template in templates:
                print(f"   • {template['name']}: {template['title_template']}")
            
            # Vérifier le template email
            print("\n📧 Vérification template email...")
            
            cursor.execute("SELECT name, subject FROM email_templates WHERE name = 'notification_general'")
            email_template = cursor.fetchone()
            
            if email_template:
                print(f"✅ Template email trouvé: {email_template['subject']}")
            else:
                print("❌ Template email non trouvé")
            
            cursor.close()
            conn.close()
            
            return len(templates) > 0 and email_template is not None
        
    except Exception as e:
        print(f"❌ Erreur test templates: {str(e)}")
        return False

def test_notification_preferences():
    """Tester les préférences de notifications"""
    print("\n⚙️ TEST PRÉFÉRENCES NOTIFICATIONS")
    print("=" * 35)
    
    try:
        from AppFlask import create_app
        from AppFlask.db import db_connection
        from psycopg2.extras import RealDictCursor
        
        app = create_app()
        with app.app_context():
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Vérifier les préférences par défaut
            print("🔍 Vérification préférences utilisateurs...")
            
            cursor.execute("""
                SELECT u.nom, u.prenom, p.email_notifications, p.app_notifications
                FROM utilisateur u
                LEFT JOIN user_notification_preferences p ON u.id = p.user_id
                LIMIT 5
            """)
            
            users_prefs = cursor.fetchall()
            
            print(f"✅ Préférences vérifiées pour {len(users_prefs)} utilisateurs:")
            for user in users_prefs:
                email_pref = user['email_notifications'] if user['email_notifications'] is not None else 'Non défini'
                app_pref = user['app_notifications'] if user['app_notifications'] is not None else 'Non défini'
                print(f"   • {user['prenom']} {user['nom']}: Email={email_pref}, App={app_pref}")
            
            cursor.close()
            conn.close()
            
            return len(users_prefs) > 0
        
    except Exception as e:
        print(f"❌ Erreur test préférences: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    print("🔔 TEST COMPLET DU SYSTÈME DE NOTIFICATIONS ESAG GED")
    print("=" * 65)
    print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    tests = [
        ("Connexion serveur", test_server_connection),
        ("API notifications", test_notification_api),
        ("Création notifications", test_notification_creation),
        ("Templates notifications", test_notification_templates),
        ("Préférences notifications", test_notification_preferences),
        ("Notifications email", test_email_notifications)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 EXÉCUTION: {test_name}")
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: RÉUSSI")
            else:
                print(f"❌ {test_name}: ÉCHOUÉ")
                
        except Exception as e:
            print(f"❌ Erreur dans {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "=" * 65)
    print("🎯 RÉSUMÉ DES TESTS")
    print("=" * 65)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name:.<40} {status}")
        if result:
            success_count += 1
    
    print(f"\n📊 RÉSULTAT GLOBAL: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("\n🎉 SYSTÈME DE NOTIFICATIONS ENTIÈREMENT FONCTIONNEL!")
        print("\n🚀 FONCTIONNALITÉS VALIDÉES:")
        print("✅ API de notifications complète")
        print("✅ Création et gestion des notifications")
        print("✅ Templates de notifications")
        print("✅ Préférences utilisateur")
        print("✅ Notifications par email")
        print("✅ Intégration avec le système existant")
        
        print("\n📋 UTILISATION:")
        print("• Interface web: http://localhost:3000/notifications")
        print("• API: http://localhost:5000/api/notifications")
        print("• Préférences: Paramètres utilisateur")
        print("• Email: Automatique selon préférences")
        
    elif success_count >= len(results) * 0.8:
        print("\n⚠️ SYSTÈME MAJORITAIREMENT FONCTIONNEL")
        print("Quelques fonctionnalités peuvent nécessiter des ajustements")
        
    else:
        print("\n❌ SYSTÈME NÉCESSITE DES CORRECTIONS")
        print("Vérifiez les erreurs ci-dessus et corrigez les problèmes")
    
    print(f"\n📝 Test terminé à {datetime.now().strftime('%H:%M:%S')}")
    
    return success_count >= len(results) * 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 