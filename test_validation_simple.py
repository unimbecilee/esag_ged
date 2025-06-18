"""
Test simple pour vérifier le système de validation workflow
"""

import requests
import json

def test_validation_workflow():
    """Test simple du workflow de validation"""
    base_url = "http://localhost:5000"
    
    print("🧪 Test simple du workflow de validation")
    print("=" * 50)
    
    # Étape 1: Authentification
    print("1. Authentification...")
    auth_response = requests.post(f"{base_url}/api/auth/login", json={
        "email": "admin@esag.com",
        "password": "admin123"
    })
    
    if auth_response.status_code != 200:
        print(f"❌ Échec d'authentification: {auth_response.status_code}")
        print(f"Réponse: {auth_response.text}")
        return False
    
    token = auth_response.json().get('token')
    if not token:
        print("❌ Token non reçu")
        return False
    
    print("✅ Authentification réussie")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Étape 2: Test des approbations en attente
    print("\n2. Test des approbations en attente...")
    pending_response = requests.get(f"{base_url}/api/validation-workflow/pending", headers=headers)
    
    print(f"Statut: {pending_response.status_code}")
    print(f"Réponse: {pending_response.text}")
    
    if pending_response.status_code == 200:
        data = pending_response.json()
        if data.get('success'):
            approvals = data.get('data', [])
            print(f"✅ {len(approvals)} approbation(s) en attente")
        else:
            print(f"❌ Erreur: {data.get('message')}")
    else:
        print(f"❌ Erreur HTTP: {pending_response.status_code}")
    
    # Étape 3: Test des statistiques
    print("\n3. Test des statistiques...")
    stats_response = requests.get(f"{base_url}/api/validation-workflow/statistics", headers=headers)
    
    print(f"Statut: {stats_response.status_code}")
    print(f"Réponse: {stats_response.text}")
    
    if stats_response.status_code == 200:
        data = stats_response.json()
        if data.get('success'):
            stats = data.get('data', {})
            general = stats.get('general', {})
            print(f"✅ Statistiques récupérées:")
            print(f"   - Total: {general.get('total_instances', 0)}")
            print(f"   - En cours: {general.get('en_cours', 0)}")
            print(f"   - Approuvés: {general.get('approuves', 0)}")
        else:
            print(f"❌ Erreur: {data.get('message')}")
    else:
        print(f"❌ Erreur HTTP: {stats_response.status_code}")
    
    # Étape 4: Test avec un document existant (si disponible)
    print("\n4. Test de statut de document...")
    
    # Essayons avec l'ID 1
    doc_status_response = requests.get(f"{base_url}/api/validation-workflow/document/1/status", headers=headers)
    
    print(f"Statut: {doc_status_response.status_code}")
    print(f"Réponse: {doc_status_response.text}")
    
    if doc_status_response.status_code == 200:
        data = doc_status_response.json()
        if data.get('success'):
            status = data.get('data', {})
            print(f"✅ Statut du document 1:")
            print(f"   - A un workflow: {status.get('has_workflow')}")
            print(f"   - Statut: {status.get('statut', 'N/A')}")
        else:
            print(f"❌ Erreur: {data.get('message')}")
    else:
        print(f"❌ Erreur HTTP: {doc_status_response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎯 Test terminé")
    
    return True

if __name__ == "__main__":
    test_validation_workflow() 