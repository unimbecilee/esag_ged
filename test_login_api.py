#!/usr/bin/env python3
"""
Script de test pour l'API de connexion
"""

import requests
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def check_recent_logs():
    """Vérifier les logs récents dans la base de données"""
    try:
        conn = psycopg2.connect(
            host='postgresql-thefau.alwaysdata.net',
            database='thefau_archive',
            user='thefau',
            password='Passecale2002@',
            port=5432
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n=== Dernières entrées dans system_logs ===")
        cursor.execute("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 3")
        logs_rows = cursor.fetchall()
        for row in logs_rows:
            print(f"ID: {row['id']}, User: {row['user_id']}, Action: {row['event_type']}, Message: {row['message']}, Date: {row['timestamp']}")
        
        print("\n=== Dernières entrées dans history ===")
        cursor.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT 3")
        history_rows = cursor.fetchall()
        for row in history_rows:
            print(f"ID: {row['id']}, User: {row['user_id']}, Action: {row['action_type']}, Description: {row['description']}, Date: {row['created_at']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des logs: {e}")

def test_login_api():
    """Tester l'API de connexion"""
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 Test de l'API de connexion")
    print("=" * 50)
    
    # Vérifier les logs avant
    print("📋 Logs AVANT la connexion:")
    check_recent_logs()
    
    # Test de connexion réussie
    print("\n🧪 Test de connexion réussie:")
    login_data = {
        "email": "admin@esag.com",
        "password": "admin123"  # Remplacez par le bon mot de passe
    }
    
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ Connexion réussie, token reçu")
            
            # Test de déconnexion
            print("\n🧪 Test de déconnexion:")
            headers = {"Authorization": f"Bearer {token}"}
            logout_response = requests.post(f"{base_url}/auth/logout", headers=headers)
            print(f"Logout Status: {logout_response.status_code}")
            print(f"Logout Response: {logout_response.text}")
            
        else:
            print(f"❌ Échec de connexion")
            
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur Flask. Assurez-vous qu'il est démarré sur http://127.0.0.1:5000")
        return
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return
    
    # Vérifier les logs après
    print("\n📋 Logs APRÈS les tests:")
    check_recent_logs()

if __name__ == "__main__":
    test_login_api() 