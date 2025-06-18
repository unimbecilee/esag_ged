#!/usr/bin/env python3
"""
Test complet du système de workflow de validation avec notifications
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import tempfile
from datetime import datetime

class WorkflowNotificationTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.admin_token = None
        self.chef_token = None
        self.user_token = None
        self.test_document_id = None
        self.workflow_instance_id = None
        
    def authenticate_users(self):
        """Authentifier les différents utilisateurs"""
        print("🔐 AUTHENTIFICATION DES UTILISATEURS")
        print("=" * 40)
        
        # Admin
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json={
                'email': 'admin@esag.com',
                'password': 'admin123'
            })
            if response.status_code == 200:
                self.admin_token = response.json().get('access_token')
                print("✅ Admin authentifié")
            else:
                print(f"❌ Échec authentification admin: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur authentification admin: {e}")
        
        # Chef de service
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json={
                'email': 'chef@esag.com',
                'password': 'password123'
            })
            if response.status_code == 200:
                self.chef_token = response.json().get('access_token')
                print("✅ Chef de service authentifié")
            else:
                print(f"❌ Échec authentification chef: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur authentification chef: {e}")
        
        # Utilisateur normal
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json={
                'email': 'user@esag.com',
                'password': 'password123'
            })
            if response.status_code == 200:
                self.user_token = response.json().get('access_token')
                print("✅ Utilisateur authentifié")
            else:
                print(f"❌ Échec authentification utilisateur: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur authentification utilisateur: {e}")
    
    def create_test_document(self):
        """Créer un document de test"""
        print("\n📄 CRÉATION DOCUMENT DE TEST")
        print("=" * 30)
        
        if not self.user_token:
            print("❌ Token utilisateur requis")
            return False
        
        try:
            # Créer un fichier temporaire
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write("Document de test pour workflow de validation avec notifications")
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('test_workflow_notifications.txt', f, 'text/plain')}
                    data = {
                        'titre': 'Document Test Workflow Notifications',
                        'description': 'Document créé pour tester le système complet de workflow avec notifications'
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/api/documents_unified",
                        headers={'Authorization': f'Bearer {self.user_token}'},
                        files=files,
                        data=data
                    )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    self.test_document_id = result.get('id') or result.get('data', {}).get('id')
                    print(f"✅ Document créé avec ID: {self.test_document_id}")
                    return True
                else:
                    print(f"❌ Erreur création document: {response.status_code} - {response.text}")
                    return False
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            print(f"❌ Exception création document: {e}")
            return False
    
    def start_validation_workflow(self):
        """Démarrer le workflow de validation"""
        print("\n⚡ DÉMARRAGE WORKFLOW DE VALIDATION")
        print("=" * 35)
        
        if not self.user_token or not self.test_document_id:
            print("❌ Token utilisateur et document requis")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/validation-workflow/start",
                headers={
                    'Authorization': f'Bearer {self.user_token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'document_id': self.test_document_id,
                    'commentaire': 'Test du workflow avec notifications automatiques'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                self.workflow_instance_id = result.get('data', {}).get('instance_id')
                print(f"✅ Workflow démarré - Instance ID: {self.workflow_instance_id}")
                print(f"   Statut: {result.get('data', {}).get('status')}")
                print(f"   Étape courante: {result.get('data', {}).get('etape_courante_id')}")
                return True
            else:
                print(f"❌ Erreur démarrage workflow: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception démarrage workflow: {e}")
            return False
    
    def check_pending_approvals(self, token, user_type):
        """Vérifier les approbations en attente"""
        print(f"\n📋 APPROBATIONS EN ATTENTE ({user_type})")
        print("=" * 30)
        
        if not token:
            print(f"❌ Token {user_type} requis")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/validation-workflow/pending",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if response.status_code == 200:
                result = response.json()
                approvals = result.get('data', [])
                print(f"✅ {len(approvals)} approbation(s) en attente pour {user_type}")
                
                for approval in approvals:
                    print(f"   📄 Document: {approval.get('document_titre')}")
                    print(f"   🔄 Étape: {approval.get('etape_nom')}")
                    print(f"   👤 Demandeur: {approval.get('initiateur_prenom')} {approval.get('initiateur_nom')}")
                    print(f"   📅 Date: {approval.get('date_creation')}")
                    print()
                
                return len(approvals) > 0
            else:
                print(f"❌ Erreur récupération approbations: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception récupération approbations: {e}")
            return False
    
    def check_notifications(self, token, user_type):
        """Vérifier les notifications"""
        print(f"\n🔔 NOTIFICATIONS ({user_type})")
        print("=" * 20)
        
        if not token:
            print(f"❌ Token {user_type} requis")
            return False
        
        try:
            # Essayer plusieurs endpoints de notifications
            endpoints = [
                "/api/notifications",
                "/api/notifications/unread",
                "/api/user/notifications"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers={'Authorization': f'Bearer {token}'}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        notifications = result if isinstance(result, list) else result.get('data', [])
                        print(f"✅ {len(notifications)} notification(s) trouvée(s) via {endpoint}")
                        
                        for notif in notifications[:3]:  # Afficher les 3 premières
                            print(f"   🔔 {notif.get('title', notif.get('titre', 'Sans titre'))}")
                            print(f"      Message: {notif.get('message', 'Sans message')}")
                            print(f"      Type: {notif.get('type', 'Inconnu')}")
                            print()
                        
                        return True
                except Exception as e:
                    continue
            
            print(f"❌ Aucun endpoint de notifications fonctionnel pour {user_type}")
            return False
            
        except Exception as e:
            print(f"❌ Exception vérification notifications: {e}")
            return False
    
    def test_chef_approval(self):
        """Tester l'approbation par le chef de service"""
        print("\n✅ TEST APPROBATION CHEF DE SERVICE")
        print("=" * 35)
        
        if not self.chef_token or not self.workflow_instance_id:
            print("❌ Token chef et instance workflow requis")
            return False
        
        try:
            # Récupérer les détails de l'instance pour obtenir l'étape courante
            response = requests.get(
                f"{self.base_url}/api/validation-workflow/instance/{self.workflow_instance_id}",
                headers={'Authorization': f'Bearer {self.chef_token}'}
            )
            
            if response.status_code != 200:
                print(f"❌ Erreur récupération instance: {response.status_code}")
                return False
            
            instance = response.json().get('data', {})
            etape_courante_id = instance.get('etape_courante_id')
            
            if not etape_courante_id:
                print("❌ Étape courante non trouvée")
                return False
            
            # Approuver
            response = requests.post(
                f"{self.base_url}/api/validation-workflow/approve",
                headers={
                    'Authorization': f'Bearer {self.chef_token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'instance_id': self.workflow_instance_id,
                    'etape_id': etape_courante_id,
                    'decision': 'APPROUVE',
                    'commentaire': 'Document approuvé par le chef de service - test notifications'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Approbation chef de service réussie")
                print(f"   Message: {result.get('message')}")
                print(f"   Prochaine étape: {result.get('data', {}).get('next_step')}")
                return True
            else:
                print(f"❌ Erreur approbation chef: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception approbation chef: {e}")
            return False
    
    def test_admin_approval(self):
        """Tester l'approbation finale par l'admin (directeur)"""
        print("\n✅ TEST APPROBATION FINALE (DIRECTEUR)")
        print("=" * 35)
        
        if not self.admin_token or not self.workflow_instance_id:
            print("❌ Token admin et instance workflow requis")
            return False
        
        try:
            # Récupérer les détails de l'instance pour obtenir l'étape courante
            response = requests.get(
                f"{self.base_url}/api/validation-workflow/instance/{self.workflow_instance_id}",
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if response.status_code != 200:
                print(f"❌ Erreur récupération instance: {response.status_code}")
                return False
            
            instance = response.json().get('data', {})
            etape_courante_id = instance.get('etape_courante_id')
            
            if not etape_courante_id:
                print("❌ Étape courante non trouvée")
                return False
            
            # Approuver
            response = requests.post(
                f"{self.base_url}/api/validation-workflow/approve",
                headers={
                    'Authorization': f'Bearer {self.admin_token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'instance_id': self.workflow_instance_id,
                    'etape_id': etape_courante_id,
                    'decision': 'APPROUVE',
                    'commentaire': 'Document approuvé par le directeur - validation finale complète'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Approbation finale réussie")
                print(f"   Message: {result.get('message')}")
                print(f"   Statut final: {result.get('data', {}).get('status')}")
                return True
            else:
                print(f"❌ Erreur approbation finale: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception approbation finale: {e}")
            return False
    
    def check_final_status(self):
        """Vérifier le statut final du document et workflow"""
        print("\n🎯 VÉRIFICATION STATUT FINAL")
        print("=" * 30)
        
        if not self.user_token or not self.test_document_id:
            print("❌ Token utilisateur et document requis")
            return False
        
        try:
            # Vérifier le statut du workflow pour le document
            response = requests.get(
                f"{self.base_url}/api/validation-workflow/document/{self.test_document_id}/status",
                headers={'Authorization': f'Bearer {self.user_token}'}
            )
            
            if response.status_code == 200:
                result = response.json()
                status_data = result.get('data', {})
                print("✅ Statut final du workflow:")
                print(f"   📄 Document ID: {self.test_document_id}")
                print(f"   🔄 Statut workflow: {status_data.get('workflow_status')}")
                print(f"   📊 Statut document: {status_data.get('document_status')}")
                print(f"   ⏱️  Durée totale: {status_data.get('duration', 'N/A')}")
                print(f"   📈 Étapes complétées: {status_data.get('completed_steps', 0)}/{status_data.get('total_steps', 0)}")
                return True
            else:
                print(f"❌ Erreur vérification statut: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception vérification statut: {e}")
            return False
    
    def run_complete_test(self):
        """Exécuter le test complet"""
        print("🚀 TEST COMPLET WORKFLOW + NOTIFICATIONS")
        print("=" * 50)
        print(f"⏰ Début du test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {
            'authentication': False,
            'document_creation': False,
            'workflow_start': False,
            'chef_pending': False,
            'chef_notifications': False,
            'chef_approval': False,
            'admin_pending': False,
            'admin_notifications': False,
            'admin_approval': False,
            'final_status': False
        }
        
        # 1. Authentification
        self.authenticate_users()
        results['authentication'] = all([self.admin_token, self.chef_token, self.user_token])
        
        # 2. Création document
        if results['authentication']:
            results['document_creation'] = self.create_test_document()
        
        # 3. Démarrage workflow
        if results['document_creation']:
            results['workflow_start'] = self.start_validation_workflow()
        
        # 4. Vérifications chef de service
        if results['workflow_start']:
            results['chef_pending'] = self.check_pending_approvals(self.chef_token, "Chef de service")
            results['chef_notifications'] = self.check_notifications(self.chef_token, "Chef de service")
            
            # 5. Approbation chef
            if results['chef_pending']:
                results['chef_approval'] = self.test_chef_approval()
        
        # 6. Vérifications admin (directeur)
        if results['chef_approval']:
            results['admin_pending'] = self.check_pending_approvals(self.admin_token, "Admin/Directeur")
            results['admin_notifications'] = self.check_notifications(self.admin_token, "Admin/Directeur")
            
            # 7. Approbation finale
            if results['admin_pending']:
                results['admin_approval'] = self.test_admin_approval()
        
        # 8. Statut final
        if results['admin_approval']:
            results['final_status'] = self.check_final_status()
        
        # Résumé
        print("\n📊 RÉSUMÉ DU TEST")
        print("=" * 25)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_name, passed in results.items():
            status = "✅ RÉUSSI" if passed else "❌ ÉCHOUÉ"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n🎯 SCORE: {passed_tests}/{total_tests} tests réussis ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("\n🎉 TOUS LES TESTS RÉUSSIS!")
            print("✅ Le système de workflow avec notifications fonctionne parfaitement")
        elif passed_tests >= total_tests * 0.8:
            print("\n✅ SYSTÈME FONCTIONNEL")
            print("⚠️ Quelques améliorations mineures nécessaires")
        else:
            print("\n⚠️ SYSTÈME PARTIELLEMENT FONCTIONNEL")
            print("🔧 Des corrections sont nécessaires")
        
        return passed_tests == total_tests

def main():
    """Fonction principale"""
    tester = WorkflowNotificationTester()
    success = tester.run_complete_test()
    return success

if __name__ == "__main__":
    main() 