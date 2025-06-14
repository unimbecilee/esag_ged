#!/usr/bin/env python3
"""
Script de test pour le nouveau système de corbeille ESAG GED
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000/api"
TEST_USER_EMAIL = "one@example.com"
TEST_USER_PASSWORD = "password123"

class TrashSystemTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        
    def login(self):
        """Se connecter et obtenir un token"""
        print("🔐 Connexion...")
        
        response = self.session.post(f"{API_BASE_URL}/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print(f"✅ Connexion réussie - Token: {self.token[:20]}...")
            return True
        else:
            print(f"❌ Échec de la connexion: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
    
    def test_trash_stats(self):
        """Tester la récupération des statistiques"""
        print("\n📊 Test des statistiques de la corbeille...")
        
        response = self.session.get(f"{API_BASE_URL}/trash/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistiques récupérées:")
            print(f"   - Total éléments: {stats.get('total_items', 0)}")
            print(f"   - En attente: {stats.get('pending_deletion', 0)}")
            print(f"   - Restaurés: {stats.get('restored_items', 0)}")
            print(f"   - Supprimés définitivement: {stats.get('permanently_deleted', 0)}")
            print(f"   - Taille totale: {stats.get('total_size_formatted', '0 B')}")
            return True
        else:
            print(f"❌ Erreur récupération statistiques: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
    
    def test_trash_items(self):
        """Tester la récupération des éléments de la corbeille"""
        print("\n🗑️ Test de la récupération des éléments...")
        
        response = self.session.get(f"{API_BASE_URL}/trash?page=1&per_page=10")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            print(f"✅ {len(items)} éléments récupérés")
            
            for item in items[:3]:  # Afficher les 3 premiers
                print(f"   - {item.get('title', 'Sans titre')} ({item.get('item_type')})")
                print(f"     Supprimé il y a {item.get('days_in_trash', 0)} jours")
                print(f"     Expire dans {item.get('days_until_deletion', 0)} jours")
            
            return True, items
        else:
            print(f"❌ Erreur récupération éléments: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False, []
    
    def test_create_test_document(self):
        """Créer un document de test"""
        print("\n📄 Création d'un document de test...")
        
        # Créer un fichier temporaire
        test_content = f"Document de test créé le {datetime.now()}"
        
        files = {
            'file': ('test_document.txt', test_content, 'text/plain')
        }
        
        data = {
            'titre': 'Document de test pour corbeille',
            'description': 'Document créé pour tester le système de corbeille'
        }
        
        response = self.session.post(f"{API_BASE_URL}/documents/upload", 
                                   files=files, data=data)
        
        if response.status_code == 201:
            doc_data = response.json()
            doc_id = doc_data.get('id')
            print(f"✅ Document créé avec ID: {doc_id}")
            return doc_id
        else:
            print(f"❌ Erreur création document: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return None
    
    def test_move_to_trash(self, doc_id):
        """Tester le déplacement vers la corbeille"""
        print(f"\n🗑️ Test déplacement document {doc_id} vers la corbeille...")
        
        response = self.session.delete(f"{API_BASE_URL}/documents/{doc_id}", 
                                     json={"reason": "Test du système de corbeille"})
        
        if response.status_code == 200:
            print("✅ Document déplacé vers la corbeille")
            return True
        else:
            print(f"❌ Erreur déplacement: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
    
    def test_restore_from_trash(self, trash_id):
        """Tester la restauration depuis la corbeille"""
        print(f"\n♻️ Test restauration élément {trash_id}...")
        
        response = self.session.post(f"{API_BASE_URL}/trash/{trash_id}/restore")
        
        if response.status_code == 200:
            print("✅ Élément restauré avec succès")
            return True
        else:
            print(f"❌ Erreur restauration: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
    
    def test_permanent_delete(self, trash_id):
        """Tester la suppression définitive"""
        print(f"\n🔥 Test suppression définitive élément {trash_id}...")
        
        response = self.session.delete(f"{API_BASE_URL}/trash/{trash_id}")
        
        if response.status_code == 200:
            print("✅ Élément supprimé définitivement")
            return True
        else:
            print(f"❌ Erreur suppression définitive: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
    
    def test_bulk_operations(self, trash_ids):
        """Tester les opérations en masse"""
        if len(trash_ids) < 2:
            print("\n⚠️ Pas assez d'éléments pour tester les opérations en masse")
            return True
        
        print(f"\n📦 Test opérations en masse sur {len(trash_ids)} éléments...")
        
        # Test restauration en masse
        response = self.session.post(f"{API_BASE_URL}/trash/bulk-restore", 
                                   json={"trash_ids": trash_ids[:2]})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Restauration en masse: {result.get('message')}")
            return True
        else:
            print(f"❌ Erreur restauration en masse: {response.status_code}")
            return False
    
    def test_admin_features(self):
        """Tester les fonctionnalités admin"""
        print("\n👑 Test des fonctionnalités administrateur...")
        
        # Test récupération configuration
        response = self.session.get(f"{API_BASE_URL}/trash/config")
        
        if response.status_code == 200:
            config = response.json()
            print("✅ Configuration récupérée:")
            for key, value in config.items():
                print(f"   - {key}: {value.get('value')} ({value.get('description')})")
            
            # Test mise à jour configuration
            new_config = {
                "retention_days": 45,
                "auto_cleanup_enabled": True
            }
            
            response = self.session.put(f"{API_BASE_URL}/trash/config", 
                                      json=new_config)
            
            if response.status_code == 200:
                print("✅ Configuration mise à jour")
                return True
            else:
                print(f"❌ Erreur mise à jour config: {response.status_code}")
                return False
        else:
            print(f"❌ Erreur récupération config: {response.status_code}")
            if response.status_code == 403:
                print("   (Normal si l'utilisateur n'est pas admin)")
                return True
            return False
    
    def test_manual_cleanup(self):
        """Tester le nettoyage manuel"""
        print("\n🧹 Test nettoyage manuel...")
        
        response = self.session.post(f"{API_BASE_URL}/trash/cleanup")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Nettoyage terminé: {result.get('message')}")
            return True
        else:
            print(f"❌ Erreur nettoyage: {response.status_code}")
            if response.status_code == 403:
                print("   (Normal si l'utilisateur n'est pas admin)")
                return True
            return False
    
    def run_full_test(self):
        """Exécuter tous les tests"""
        print("🧪 TESTS DU SYSTÈME DE CORBEILLE ESAG GED")
        print("=" * 50)
        
        # Connexion
        if not self.login():
            return False
        
        # Tests de base
        success_count = 0
        total_tests = 0
        
        # Test 1: Statistiques
        total_tests += 1
        if self.test_trash_stats():
            success_count += 1
        
        # Test 2: Récupération des éléments
        total_tests += 1
        success, items = self.test_trash_items()
        if success:
            success_count += 1
        
        # Test 3: Création et suppression d'un document
        doc_id = self.test_create_test_document()
        if doc_id:
            total_tests += 1
            if self.test_move_to_trash(doc_id):
                success_count += 1
                
                # Récupérer l'ID dans la corbeille
                _, updated_items = self.test_trash_items()
                new_trash_item = None
                for item in updated_items:
                    if item.get('item_id') == doc_id:
                        new_trash_item = item
                        break
                
                if new_trash_item:
                    trash_id = new_trash_item['id']
                    
                    # Test 4: Restauration
                    total_tests += 1
                    if self.test_restore_from_trash(trash_id):
                        success_count += 1
                    
                    # Remettre en corbeille pour test suppression
                    self.test_move_to_trash(doc_id)
                    _, updated_items = self.test_trash_items()
                    for item in updated_items:
                        if item.get('item_id') == doc_id:
                            trash_id = item['id']
                            break
                    
                    # Test 5: Suppression définitive
                    total_tests += 1
                    if self.test_permanent_delete(trash_id):
                        success_count += 1
        
        # Test 6: Opérations en masse
        if items:
            total_tests += 1
            trash_ids = [item['id'] for item in items[:3]]
            if self.test_bulk_operations(trash_ids):
                success_count += 1
        
        # Test 7: Fonctionnalités admin
        total_tests += 1
        if self.test_admin_features():
            success_count += 1
        
        # Test 8: Nettoyage manuel
        total_tests += 1
        if self.test_manual_cleanup():
            success_count += 1
        
        # Résultats
        print(f"\n📊 RÉSULTATS DES TESTS")
        print("=" * 30)
        print(f"✅ Tests réussis: {success_count}/{total_tests}")
        print(f"📈 Taux de réussite: {(success_count/total_tests)*100:.1f}%")
        
        if success_count == total_tests:
            print("\n🎉 Tous les tests sont passés avec succès!")
            print("✅ Le système de corbeille fonctionne correctement")
        else:
            print(f"\n⚠️ {total_tests - success_count} test(s) ont échoué")
            print("🔧 Vérifiez les erreurs ci-dessus")
        
        return success_count == total_tests

def main():
    """Fonction principale"""
    tester = TrashSystemTester()
    success = tester.run_full_test()
    
    if success:
        print("\n🚀 Le système de corbeille est prêt à être utilisé!")
    else:
        print("\n🛠️ Des corrections sont nécessaires avant la mise en production")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 