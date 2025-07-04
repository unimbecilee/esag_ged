#!/usr/bin/env python3
"""Script pour tester l'API des workflows"""

import requests
import json
import sys

def test_workflow_api():
    """Teste l'API des workflows"""
    base_url = "http://localhost:5000"
    
    print("=== TEST DE L'API WORKFLOW ===")
    
    # 1. Test de connexion
    print("\n1. Test de connexion au serveur...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   ✅ Serveur accessible - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Serveur inaccessible: {e}")
        print("   💡 Démarrez le serveur avec: python main.py")
        return
    
    # 2. Test de l'authentification
    print("\n2. Test de l'authentification...")
    login_data = {
        "email": "admin@example.com",  # Remplacez par un email valide
        "password": "password"         # Remplacez par un mot de passe valide
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"   ✅ Authentification réussie")
            print(f"   Token: {token[:50]}..." if token else "   ❌ Pas de token")
            
            # 3. Test de l'API des validations en attente
            if token:
                print("\n3. Test de l'API des validations en attente...")
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                try:
                    response = requests.get(f"{base_url}/api/validation-workflow/pending", 
                                          headers=headers, timeout=10)
                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ API accessible")
                        print(f"   Données: {json.dumps(data, indent=2)}")
                    else:
                        print(f"   ❌ Erreur API: {response.text}")
                        
                except Exception as e:
                    print(f"   ❌ Erreur lors de l'appel API: {e}")
        else:
            print(f"   ❌ Authentification échouée: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors de l'authentification: {e}")
    
    # 4. Instructions pour les tests manuels
    print("\n=== INSTRUCTIONS POUR LES TESTS MANUELS ===")
    print("1. Démarrez le serveur Flask:")
    print("   python main.py")
    print("\n2. Ouvrez votre navigateur et allez sur:")
    print("   http://localhost:5000")
    print("\n3. Connectez-vous avec un compte chef de service")
    print("\n4. Allez sur la page Workflows")
    print("\n5. Ouvrez la console du navigateur (F12)")
    print("\n6. Vérifiez l'onglet Network pour voir les requêtes")
    print("\n7. Vérifiez l'onglet Console pour voir les erreurs")
    
    print("\n=== VÉRIFICATIONS À FAIRE ===")
    print("□ Le serveur Flask démarre sans erreur")
    print("□ L'authentification fonctionne")
    print("□ L'API /api/validation-workflow/pending répond")
    print("□ L'utilisateur connecté a le bon rôle")
    print("□ Il y a des instances de workflow en cours")
    print("□ Les approbateurs sont correctement configurés")

if __name__ == '__main__':
    test_workflow_api() 