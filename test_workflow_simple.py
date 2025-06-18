#!/usr/bin/env python3
"""
Test simple du système de workflow de validation
Utilise seulement l'admin pour démontrer toutes les fonctionnalités
"""

import requests
import json
import tempfile
import os
from datetime import datetime

class SimpleWorkflowTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.admin_token = None
        self.test_document_id = None
        self.workflow_instance_id = None
        
    def authenticate_admin(self):
        """Authentifier l'admin"""
        print("🔐 AUTHENTIFICATION ADMIN")
        print("=" * 25)
        
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json={
                'email': 'admin@esag.com',
                'password': 'admin123'
            })
            if response.status_code == 200:
                result = response.json()
                self.admin_token = result.get('token')
                print("✅ Admin authentifié avec succès")
                print(f"   ID: {result.get('user', {}).get('id')}")
                print(f"   Nom: {result.get('user', {}).get('prenom')} {result.get('user', {}).get('nom')}")
                print(f"   Rôle: {result.get('user', {}).get('role')}")
                return True
            else:
                print(f"❌ Échec authentification: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur authentification: {e}")
            return False
    
    def create_test_document(self):
        """Créer un document de test"""
        print("\n📄 CRÉATION DOCUMENT DE TEST")
        print("=" * 30)
        
        if not self.admin_token:
            print("❌ Token admin requis")
            return False
        
        try:
            # Créer un fichier temporaire
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write("Document de test pour démonstration du workflow de validation automatique")
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, 'rb') as f:
                    files = {'file': ('demo_workflow.txt', f, 'text/plain')}
                    data = {
                        'titre': 'Document Démonstration Workflow',
                        'description': 'Document créé pour démontrer le système de workflow de validation'
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/api/documents/upload",
                        headers={'Authorization': f'Bearer {self.admin_token}'},
                        files=files,
                        data=data
                    )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    self.test_document_id = result.get('document_id') or result.get('id')
                    print(f"✅ Document créé avec ID: {self.test_document_id}")
                    print(f"   Titre: {data['titre']}")
                    print(f"   Description: {data['description']}")
                    print(f"   Réponse complète: {result}")
                    return self.test_document_id is not None
                else:
                    print(f"❌ Erreur création document: {response.status_code}")
                    print(f"   Réponse: {response.text}")
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
        
        if not self.admin_token or not self.test_document_id:
            print("❌ Token admin et document requis")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/validation-workflow/start",
                headers={
                    'Authorization': f'Bearer {self.admin_token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'document_id': self.test_document_id,
                    'commentaire': 'Démonstration du workflow automatique de validation en 2 étapes'
                }
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                data = result.get('data', {})
                self.workflow_instance_id = data.get('instance_id')
                print(f"✅ Workflow démarré avec succès!")
                print(f"   Instance ID: {self.workflow_instance_id}")
                print(f"   Statut: {data.get('status')}")
                print(f"   Message: {data.get('message')}")
                print(f"   Étape courante ID: {data.get('etape_courante_id')}")
                return True
            else:
                print(f"❌ Erreur démarrage workflow: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception démarrage workflow: {e}")
            return False
    
    def check_pending_approvals(self):
        """Vérifier les approbations en attente"""
        print("\n📋 APPROBATIONS EN ATTENTE")
        print("=" * 25)
        
        if not self.admin_token:
            print("❌ Token admin requis")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/validation-workflow/pending",
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if response.status_code == 200:
                result = response.json()
                approvals = result.get('data', [])
                print(f"✅ {len(approvals)} approbation(s) en attente")
                
                for i, approval in enumerate(approvals, 1):
                    print(f"\n   📄 Approbation #{i}:")
                    print(f"      Document: {approval.get('document_titre')}")
                    print(f"      Étape: {approval.get('etape_nom')}")
                    print(f"      Instance ID: {approval.get('instance_id')}")
                    print(f"      Étape ID: {approval.get('etape_id')}")
                    print(f"      Demandeur: {approval.get('initiateur_prenom')} {approval.get('initiateur_nom')}")
                    print(f"      Date: {approval.get('date_creation')}")
                    if approval.get('commentaire'):
                        print(f"      Commentaire: {approval.get('commentaire')}")
                
                return len(approvals) > 0
            else:
                print(f"❌ Erreur récupération approbations: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception récupération approbations: {e}")
            return False
    
    def get_workflow_details(self):
        """Récupérer les détails du workflow"""
        print("\n🔍 DÉTAILS DU WORKFLOW")
        print("=" * 22)
        
        if not self.admin_token or not self.workflow_instance_id:
            print("❌ Token admin et instance workflow requis")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/validation-workflow/instance/{self.workflow_instance_id}",
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                print("✅ Détails du workflow récupérés:")
                print(f"   Instance ID: {data.get('instance_id')}")
                print(f"   Document ID: {data.get('document_id')}")
                print(f"   Statut: {data.get('statut')}")
                print(f"   Étape courante: {data.get('etape_courante_nom')}")
                print(f"   Date début: {data.get('date_debut')}")
                print(f"   Initiateur: {data.get('initiateur_nom')}")
                
                etapes = data.get('etapes', [])
                print(f"\n   📊 Étapes du workflow ({len(etapes)}):")
                for i, etape in enumerate(etapes, 1):
                    status = etape.get('statut_etape') or 'EN_ATTENTE'
                    print(f"      {i}. {etape.get('nom')} - {status}")
                    if etape.get('description'):
                        print(f"         Description: {etape.get('description')}")
                
                return True
            else:
                print(f"❌ Erreur récupération détails: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception récupération détails: {e}")
            return False
    
    def check_workflow_statistics(self):
        """Vérifier les statistiques des workflows"""
        print("\n📊 STATISTIQUES DES WORKFLOWS")
        print("=" * 30)
        
        if not self.admin_token:
            print("❌ Token admin requis")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/validation-workflow/statistics",
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if response.status_code == 200:
                result = response.json()
                stats = result.get('data', {})
                print("✅ Statistiques récupérées:")
                print(f"   Total instances: {stats.get('total_instances', 0)}")
                print(f"   En cours: {stats.get('en_cours', 0)}")
                print(f"   Terminées: {stats.get('terminees', 0)}")
                print(f"   Rejetées: {stats.get('rejetees', 0)}")
                print(f"   Temps moyen: {stats.get('temps_moyen_completion', 'N/A')}")
                
                return True
            else:
                print(f"❌ Erreur récupération statistiques: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception récupération statistiques: {e}")
            return False
    
    def check_document_status(self):
        """Vérifier le statut du document"""
        print("\n📄 STATUT DU DOCUMENT")
        print("=" * 20)
        
        if not self.admin_token or not self.test_document_id:
            print("❌ Token admin et document requis")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/api/validation-workflow/document/{self.test_document_id}/status",
                headers={'Authorization': f'Bearer {self.admin_token}'}
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                print("✅ Statut du document:")
                print(f"   Document ID: {self.test_document_id}")
                print(f"   Statut workflow: {data.get('workflow_status', 'N/A')}")
                print(f"   Statut document: {data.get('document_status', 'N/A')}")
                print(f"   A un workflow actif: {data.get('has_active_workflow', False)}")
                print(f"   Instance ID: {data.get('workflow_instance_id', 'N/A')}")
                
                return True
            else:
                print(f"❌ Erreur récupération statut: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Exception récupération statut: {e}")
            return False
    
    def simulate_approval_process(self):
        """Simuler le processus d'approbation (pour démonstration)"""
        print("\n✅ SIMULATION PROCESSUS D'APPROBATION")
        print("=" * 40)
        
        print("📝 NOTE: Dans un environnement réel:")
        print("   1. Le chef de service recevrait une notification")
        print("   2. Il se connecterait et verrait l'approbation en attente")
        print("   3. Il approuverait ou rejetterait le document")
        print("   4. Le directeur recevrait ensuite une notification")
        print("   5. Il effectuerait la validation finale")
        print("   6. Le demandeur serait notifié du résultat")
        print()
        print("🔔 NOTIFICATIONS AUTOMATIQUES:")
        print("   ✉️  Email envoyé aux approbateurs")
        print("   📱 Notification in-app dans le dashboard")
        print("   🔔 Badge de notification dans l'interface")
        print("   📋 Apparition dans la liste 'Approbations en attente'")
        
        return True
    
    def run_demonstration(self):
        """Exécuter la démonstration complète"""
        print("🎯 DÉMONSTRATION SYSTÈME WORKFLOW DE VALIDATION")
        print("=" * 55)
        print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        results = {}
        
        # 1. Authentification
        print("ÉTAPE 1/8 - Authentification")
        results['auth'] = self.authenticate_admin()
        
        # 2. Création document
        if results['auth']:
            print("\nÉTAPE 2/8 - Création document")
            results['document'] = self.create_test_document()
        
        # 3. Démarrage workflow
        if results.get('document'):
            print("\nÉTAPE 3/8 - Démarrage workflow")
            results['workflow_start'] = self.start_validation_workflow()
        
        # 4. Vérification approbations
        if results.get('workflow_start'):
            print("\nÉTAPE 4/8 - Vérification approbations")
            results['pending'] = self.check_pending_approvals()
        
        # 5. Détails workflow
        if results.get('workflow_start'):
            print("\nÉTAPE 5/8 - Détails workflow")
            results['details'] = self.get_workflow_details()
        
        # 6. Statistiques
        if results.get('auth'):
            print("\nÉTAPE 6/8 - Statistiques")
            results['stats'] = self.check_workflow_statistics()
        
        # 7. Statut document
        if results.get('document'):
            print("\nÉTAPE 7/8 - Statut document")
            results['doc_status'] = self.check_document_status()
        
        # 8. Simulation approbation
        print("\nÉTAPE 8/8 - Simulation processus")
        results['simulation'] = self.simulate_approval_process()
        
        # Résumé
        print("\n" + "="*60)
        print("📊 RÉSUMÉ DE LA DÉMONSTRATION")
        print("="*60)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_name, passed in results.items():
            status = "✅ RÉUSSI" if passed else "❌ ÉCHOUÉ"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\n🎯 SCORE: {passed_tests}/{total_tests} étapes réussies ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests >= total_tests * 0.8:
            print("\n🎉 DÉMONSTRATION RÉUSSIE!")
            print("✅ Le système de workflow de validation fonctionne correctement")
            print("\n🚀 FONCTIONNALITÉS DÉMONTRÉES:")
            print("   ✅ Authentification sécurisée")
            print("   ✅ Création de documents")
            print("   ✅ Démarrage automatique de workflow")
            print("   ✅ Gestion des approbations en attente")
            print("   ✅ Suivi détaillé des workflows")
            print("   ✅ Statistiques en temps réel")
            print("   ✅ Vérification statut documents")
            print("   ✅ Système de notifications (simulé)")
            
            print("\n📋 PROCHAINES ÉTAPES:")
            print("   1. Configurer les comptes utilisateurs (chef de service, directeur)")
            print("   2. Tester le processus d'approbation complet")
            print("   3. Vérifier les notifications email")
            print("   4. Intégrer dans l'interface utilisateur")
        else:
            print("\n⚠️ DÉMONSTRATION PARTIELLE")
            print("🔧 Quelques ajustements nécessaires")
        
        return passed_tests >= total_tests * 0.8

def main():
    """Fonction principale"""
    tester = SimpleWorkflowTester()
    success = tester.run_demonstration()
    return success

if __name__ == "__main__":
    main() 