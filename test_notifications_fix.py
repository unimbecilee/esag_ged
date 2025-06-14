#!/usr/bin/env python3
"""
Script de test pour vérifier les routes de notifications
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"
TEST_EMAIL = "admin@esag.com"
TEST_PASSWORD = "admin123"

def test_login():
    """Tester la connexion et récupérer le token"""
    print("🔐 Test de connexion...")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ Connexion réussie, token obtenu: {token[:20]}...")
            return token
        else:
            print(f"❌ Échec de connexion: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

def test_notifications_api(token):
    """Tester les routes de notifications"""
    print("\n📢 Test des routes de notifications...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Récupérer les notifications
    print("\n1. Test GET /api/notifications")
    try:
        response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Notifications récupérées: {len(data.get('notifications', []))} notifications")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Compteur non lues
    print("\n2. Test GET /api/notifications/unread-count")
    try:
        response = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Compteur non lues: {data.get('unread_count', 0)}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Préférences
    print("\n3. Test GET /api/notifications/preferences")
    try:
        response = requests.get(f"{BASE_URL}/api/notifications/preferences", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Préférences récupérées: {data}")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_documents_subscriptions(token):
    """Tester les routes d'abonnements aux documents"""
    print("\n📄 Test des routes d'abonnements aux documents...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test: Mes abonnements
    print("\n1. Test GET /api/documents/my-subscriptions")
    try:
        response = requests.get(f"{BASE_URL}/api/documents/my-subscriptions", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Abonnements récupérés: {len(data.get('subscriptions', []))} abonnements")
        else:
            print(f"❌ Erreur: {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("🧪 Test des routes de notifications ESAG GED")
    print("=" * 50)
    
    # Test de connexion
    token = test_login()
    if not token:
        print("❌ Impossible de continuer sans token")
        sys.exit(1)
    
    # Test des APIs
    test_notifications_api(token)
    test_documents_subscriptions(token)
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés")

if __name__ == "__main__":
    main() 