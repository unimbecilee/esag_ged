"""
Script de test d'intégration pour le workflow de validation de documents
"""

import requests
import json
import time
from typing import Dict, Any

class ValidationWorkflowIntegrationTest:
    """Classe pour tester l'intégration complète du workflow de validation"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.token = None
        self.test_document_id = None
        self.test_instance_id = None
        
    def authenticate(self, email: str, password: str) -> bool:
        """Authentification pour obtenir un token"""
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                print(f"✅ Authentification réussie pour {email}")
                return True
            else:
                print(f"❌ Échec d'authentification: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur d'authentification: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Retourne les headers avec le token d'authentification"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def create_test_document(self) -> bool:
        """Crée un document de test"""
        try:
            # Utiliser l'endpoint documents_unified qui fonctionne
            import tempfile
            import os
            
            # Créer un fichier temporaire pour le test
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write("Contenu de test pour le workflow de validation")
                temp_file_path = temp_file.name
            
            try:
                # Préparer les données multipart/form-data
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('test_document.txt', f, 'text/plain')}
                    data = {
                        'titre': 'Document Test Workflow',
                        'description': 'Document créé pour tester le workflow de validation',
                        'type_document': 'Document',
                        'service': 'GED'
                    }
                    
                    headers = {"Authorization": f"Bearer {self.token}"}
                    
                    response = requests.post(
                        f"{self.base_url}/api/documents/upload", 
                        headers=headers,
                        files=files,
                        data=data
                    )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.test_document_id = data.get('document_id')
                    print(f"✅ Document de test créé avec l'ID: {self.test_document_id}")
                    return True
                else:
                    print(f"❌ Échec de création du document: {response.status_code}")
                    print(f"Réponse: {response.text}")
                    return False
                    
            finally:
                # Nettoyer le fichier temporaire
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
        except Exception as e:
            print(f"❌ Erreur lors de la création du document: {e}")
            return False
    
    def test_start_workflow(self) -> bool:
        """Test de démarrage du workflow"""
        try:
            print("\n🧪 Test: Démarrage du workflow de validation")
            
            response = requests.post(f"{self.base_url}/api/validation-workflow/start",
                headers=self.get_headers(),
                json={
                    "document_id": self.test_document_id,
                    "commentaire": "Test d'intégration du workflow de validation"
                }
            )
            
            print(f"Statut de la réponse: {response.status_code}")
            print(f"Réponse: {response.text}")
            
            if response.status_code == 201:
                data = response.json()
                if data.get('success'):
                    self.test_instance_id = data['data']['instance_id']
                    print(f"✅ Workflow démarré avec succès. Instance ID: {self.test_instance_id}")
                    return True
                else:
                    print(f"❌ Échec du démarrage: {data.get('message')}")
                    return False
            else:
                print(f"❌ Échec du démarrage du workflow: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du démarrage du workflow: {e}")
            return False
    
    def test_get_pending_approvals(self) -> bool:
        """Test de récupération des approbations en attente"""
        try:
            print("\n🧪 Test: Récupération des approbations en attente")
            
            response = requests.get(f"{self.base_url}/api/validation-workflow/pending",
                headers=self.get_headers()
            )
            
            print(f"Statut de la réponse: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    approvals = data.get('data', [])
                    print(f"✅ {len(approvals)} approbation(s) en attente récupérée(s)")
                    
                    # Afficher les détails des approbations
                    for approval in approvals:
                        print(f"  - Document: {approval.get('document_titre')}")
                        print(f"    Étape: {approval.get('etape_nom')}")
                        print(f"    Instance ID: {approval.get('instance_id')}")
                    
                    return True
                else:
                    print(f"❌ Échec de récupération: {data.get('message')}")
                    return False
            else:
                print(f"❌ Échec de récupération des approbations: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des approbations: {e}")
            return False
    
    def test_get_workflow_details(self) -> bool:
        """Test de récupération des détails du workflow"""
        try:
            print("\n🧪 Test: Récupération des détails du workflow")
            
            if not self.test_instance_id:
                print("❌ Aucune instance de workflow à tester")
                return False
            
            response = requests.get(f"{self.base_url}/api/validation-workflow/instance/{self.test_instance_id}",
                headers=self.get_headers()
            )
            
            print(f"Statut de la réponse: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    details = data.get('data', {})
                    instance = details.get('instance', {})
                    etapes = details.get('etapes', [])
                    
                    print(f"✅ Détails du workflow récupérés")
                    print(f"  - Statut: {instance.get('statut')}")
                    print(f"  - Document: {instance.get('document_titre')}")
                    print(f"  - Nombre d'étapes: {len(etapes)}")
                    
                    for etape in etapes:
                        print(f"    Étape {etape.get('ordre')}: {etape.get('nom')} - {etape.get('statut_etape', 'EN_ATTENTE')}")
                    
                    return True
                else:
                    print(f"❌ Échec de récupération: {data.get('message')}")
                    return False
            else:
                print(f"❌ Échec de récupération des détails: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des détails: {e}")
            return False
    
    def test_document_status(self) -> bool:
        """Test de récupération du statut du document"""
        try:
            print("\n🧪 Test: Statut du workflow pour le document")
            
            if not self.test_document_id:
                print("❌ Aucun document de test")
                return False
            
            response = requests.get(f"{self.base_url}/api/validation-workflow/document/{self.test_document_id}/status",
                headers=self.get_headers()
            )
            
            print(f"Statut de la réponse: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    status = data.get('data', {})
                    print(f"✅ Statut du document récupéré")
                    print(f"  - A un workflow: {status.get('has_workflow')}")
                    print(f"  - Statut workflow: {status.get('statut')}")
                    print(f"  - Étape courante: {status.get('etape_courante_nom')}")
                    
                    return True
                else:
                    print(f"❌ Échec de récupération: {data.get('message')}")
                    return False
            else:
                print(f"❌ Échec de récupération du statut: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du statut: {e}")
            return False
    
    def test_workflow_statistics(self) -> bool:
        """Test de récupération des statistiques (admin uniquement)"""
        try:
            print("\n🧪 Test: Statistiques des workflows")
            
            response = requests.get(f"{self.base_url}/api/validation-workflow/statistics",
                headers=self.get_headers()
            )
            
            print(f"Statut de la réponse: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stats = data.get('data', {})
                    general = stats.get('general', {})
                    
                    print(f"✅ Statistiques récupérées")
                    print(f"  - Total instances: {general.get('total_instances', 0)}")
                    print(f"  - En cours: {general.get('en_cours', 0)}")
                    print(f"  - Approuvés: {general.get('approuves', 0)}")
                    print(f"  - Rejetés: {general.get('rejetes', 0)}")
                    
                    return True
                else:
                    print(f"❌ Échec de récupération: {data.get('message')}")
                    return False
            else:
                print(f"❌ Échec de récupération des statistiques: {response.status_code}")
                print("Note: Les statistiques peuvent nécessiter des droits administrateur")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")
            return False
    
    def cleanup_test_data(self) -> bool:
        """Nettoie les données de test"""
        try:
            print("\n🧹 Nettoyage des données de test")
            
            # Note: Adapter selon votre API pour supprimer le document de test
            if self.test_document_id:
                # Exemple de suppression (à adapter)
                # response = requests.delete(f"{self.base_url}/api/documents/{self.test_document_id}",
                #     headers=self.get_headers()
                # )
                print(f"ℹ️ Document de test ID {self.test_document_id} à supprimer manuellement si nécessaire")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Exécute tous les tests d'intégration"""
        print("🚀 Démarrage des tests d'intégration du workflow de validation")
        print("=" * 60)
        
        tests = [
            ("Création du document de test", self.create_test_document),
            ("Démarrage du workflow", self.test_start_workflow),
            ("Récupération des approbations en attente", self.test_get_pending_approvals),
            ("Récupération des détails du workflow", self.test_get_workflow_details),
            ("Statut du workflow pour le document", self.test_document_status),
            ("Statistiques des workflows", self.test_workflow_statistics),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}...")
            try:
                success = test_func()
                results.append((test_name, success))
                if success:
                    print(f"✅ {test_name}: RÉUSSI")
                else:
                    print(f"❌ {test_name}: ÉCHEC")
            except Exception as e:
                print(f"❌ {test_name}: ERREUR - {e}")
                results.append((test_name, False))
        
        # Nettoyage
        self.cleanup_test_data()
        
        # Résumé des résultats
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅ RÉUSSI" if success else "❌ ÉCHEC"
            print(f"{status:<10} {test_name}")
        
        print(f"\n🎯 Résultat global: {passed}/{total} tests réussis")
        
        if passed == total:
            print("🎉 Tous les tests sont passés avec succès!")
            return True
        else:
            print("⚠️ Certains tests ont échoué. Vérifiez les logs ci-dessus.")
            return False


def main():
    """Fonction principale pour exécuter les tests"""
    print("🧪 Tests d'intégration du workflow de validation")
    print("=" * 60)
    
    # Configuration
    BASE_URL = "http://localhost:5000"
    
    # Informations d'authentification (à adapter selon vos données de test)
    ADMIN_EMAIL = "admin@esag.com"  # Utilisateur avec rôle Admin
    ADMIN_PASSWORD = "admin123"
    
    CHEF_EMAIL = "chef@esag.com"    # Utilisateur avec rôle chef_de_service
    CHEF_PASSWORD = "chef123"
    
    # Test avec un administrateur
    print("\n👨‍💼 Tests avec un compte administrateur")
    admin_test = ValidationWorkflowIntegrationTest(BASE_URL)
    
    if admin_test.authenticate(ADMIN_EMAIL, ADMIN_PASSWORD):
        admin_success = admin_test.run_all_tests()
    else:
        print("❌ Impossible de s'authentifier en tant qu'administrateur")
        admin_success = False
    
    # Test avec un chef de service (si disponible)
    print("\n" + "=" * 60)
    print("👨‍💼 Tests avec un compte chef de service")
    chef_test = ValidationWorkflowIntegrationTest(BASE_URL)
    
    if chef_test.authenticate(CHEF_EMAIL, CHEF_PASSWORD):
        chef_success = chef_test.test_get_pending_approvals()
    else:
        print("❌ Impossible de s'authentifier en tant que chef de service")
        chef_success = False
    
    # Résultat final
    print("\n" + "=" * 60)
    print("🏁 RÉSULTAT FINAL DES TESTS D'INTÉGRATION")
    print("=" * 60)
    
    if admin_success and chef_success:
        print("🎉 Tous les tests d'intégration sont passés avec succès!")
        print("✅ Le workflow de validation fonctionne correctement")
        return True
    else:
        print("⚠️ Certains tests d'intégration ont échoué")
        print("❌ Vérifiez la configuration et les logs ci-dessus")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 