"""
Test complet du workflow de validation avec un document existant
"""

import requests
import json
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def test_workflow_complete():
    """Test complet du workflow de validation"""
    base_url = "http://localhost:5000"
    
    print("🧪 Test complet du workflow de validation")
    print("=" * 60)
    
    # Étape 1: Récupérer un document existant
    print("1. Recherche d'un document existant...")
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, titre FROM document LIMIT 1")
        document = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not document:
            print("❌ Aucun document trouvé dans la base")
            return False
        
        document_id = document['id']
        document_titre = document['titre']
        print(f"✅ Document trouvé: ID={document_id}, Titre='{document_titre}'")
        
    except Exception as e:
        print(f"❌ Erreur lors de la recherche de document: {e}")
        return False
    
    # Étape 2: Authentification
    print("\n2. Authentification...")
    auth_response = requests.post(f"{base_url}/api/auth/login", json={
        "email": "admin@esag.com",
        "password": "admin123"
    })
    
    if auth_response.status_code != 200:
        print(f"❌ Échec d'authentification: {auth_response.status_code}")
        return False
    
    token = auth_response.json().get('token')
    print("✅ Authentification réussie")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Étape 3: Démarrer un workflow
    print("\n3. Démarrage du workflow de validation...")
    workflow_response = requests.post(f"{base_url}/api/validation-workflow/start",
        headers=headers,
        json={
            "document_id": document_id,
            "commentaire": "Test automatique du workflow de validation"
        }
    )
    
    print(f"Statut: {workflow_response.status_code}")
    print(f"Réponse: {workflow_response.text}")
    
    if workflow_response.status_code == 201:
        data = workflow_response.json()
        if data.get('success'):
            instance_id = data['data']['instance_id']
            print(f"✅ Workflow démarré avec succès! Instance ID: {instance_id}")
            
            # Étape 4: Vérifier le statut du document
            print("\n4. Vérification du statut du document...")
            status_response = requests.get(f"{base_url}/api/validation-workflow/document/{document_id}/status",
                headers=headers
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('success'):
                    status_info = status_data['data']
                    print(f"✅ Statut mis à jour:")
                    print(f"   - A un workflow: {status_info.get('has_workflow')}")
                    print(f"   - Statut: {status_info.get('statut')}")
                    print(f"   - Étape courante: {status_info.get('etape_courante_nom')}")
            
            # Étape 5: Vérifier les détails de l'instance
            print("\n5. Détails de l'instance de workflow...")
            details_response = requests.get(f"{base_url}/api/validation-workflow/instance/{instance_id}",
                headers=headers
            )
            
            if details_response.status_code == 200:
                details_data = details_response.json()
                if details_data.get('success'):
                    details = details_data['data']
                    instance = details['instance']
                    etapes = details['etapes']
                    
                    print(f"✅ Détails récupérés:")
                    print(f"   - Document: {instance.get('document_titre')}")
                    print(f"   - Statut: {instance.get('statut')}")
                    print(f"   - Initiateur: {instance.get('initiateur_prenom')} {instance.get('initiateur_nom')}")
                    print(f"   - Nombre d'étapes: {len(etapes)}")
                    
                    for etape in etapes:
                        print(f"     Étape {etape.get('ordre')}: {etape.get('nom')} - {etape.get('statut_etape', 'EN_ATTENTE')}")
            
            # Étape 6: Vérifier les approbations en attente
            print("\n6. Approbations en attente...")
            pending_response = requests.get(f"{base_url}/api/validation-workflow/pending",
                headers=headers
            )
            
            if pending_response.status_code == 200:
                pending_data = pending_response.json()
                if pending_data.get('success'):
                    approvals = pending_data.get('data', [])
                    print(f"✅ {len(approvals)} approbation(s) en attente")
                    
                    for approval in approvals:
                        print(f"   - Document: {approval.get('document_titre')}")
                        print(f"     Étape: {approval.get('etape_nom')}")
                        print(f"     Initiateur: {approval.get('initiateur_prenom')} {approval.get('initiateur_nom')}")
            
            print(f"\n🎉 Test complet réussi! Workflow créé avec l'instance ID: {instance_id}")
            return True
            
        else:
            print(f"❌ Échec du démarrage: {data.get('message')}")
            return False
    else:
        print(f"❌ Erreur HTTP: {workflow_response.status_code}")
        return False

if __name__ == "__main__":
    success = test_workflow_complete()
    if success:
        print("\n✅ Tous les tests sont passés!")
    else:
        print("\n❌ Certains tests ont échoué")
    exit(0 if success else 1) 