#!/usr/bin/env python3
"""
Test simple de l'API trash
"""

import requests
import json

def test_trash_api():
    """Test simple de l'API trash"""
    
    # 1. Test de connexion
    print("🔐 Test de connexion...")
    login_response = requests.post("http://localhost:5000/api/auth/login", json={
        'email': 'admin@esag.com',
        'password': 'admin123'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Erreur de connexion: {login_response.status_code}")
        print(f"Réponse: {login_response.text}")
        return
    
    token = login_response.json().get('token')
    print(f"✅ Connexion réussie, token: {token[:20]}...")
    
    # 2. Test de l'API trash
    print("\n📋 Test de l'API trash...")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    trash_response = requests.get("http://localhost:5000/api/trash", headers=headers)
    
    print(f"Status: {trash_response.status_code}")
    print(f"Headers: {dict(trash_response.headers)}")
    print(f"Content-Type: {trash_response.headers.get('Content-Type', 'Non défini')}")
    
    if trash_response.status_code == 200:
        try:
            data = trash_response.json()
            print("✅ Réponse JSON valide")
            print(f"📊 Données reçues:")
            print(f"   - Type: {type(data)}")
            if isinstance(data, dict):
                print(f"   - Clés: {list(data.keys())}")
                if 'items' in data:
                    print(f"   - Nombre d'éléments: {len(data['items'])}")
                    if data['items']:
                        print(f"   - Premier élément: {data['items'][0].get('title', 'Sans titre')}")
            elif isinstance(data, list):
                print(f"   - Nombre d'éléments: {len(data)}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON: {e}")
            print(f"Contenu brut: {trash_response.text[:200]}...")
    else:
        print(f"❌ Erreur API: {trash_response.status_code}")
        print(f"Contenu: {trash_response.text[:200]}...")
    
    # 3. Test des statistiques
    print("\n📊 Test des statistiques...")
    stats_response = requests.get("http://localhost:5000/api/trash/stats", headers=headers)
    
    print(f"Status stats: {stats_response.status_code}")
    if stats_response.status_code == 200:
        try:
            stats_data = stats_response.json()
            print("✅ Statistiques reçues")
            print(f"📈 Stats: {stats_data}")
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON stats: {e}")
    else:
        print(f"❌ Erreur stats: {stats_response.status_code}")
        print(f"Contenu stats: {stats_response.text[:200]}...")

if __name__ == "__main__":
    test_trash_api() 