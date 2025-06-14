#!/usr/bin/env python3
"""
Test de l'API de la corbeille ESAG GED
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000/api"
LOGIN_URL = "http://localhost:5000/api/auth/login"

class TrashAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        
    def login(self, email="admin@esag.com", password="admin123"):
        """Se connecter et récupérer le token"""
        print(f"🔐 Connexion avec {email}...")
        
        response = self.session.post(LOGIN_URL, json={
            'email': email,
            'password': password
        })
        
        print(f"Status de connexion: {response.status_code}")
        print(f"Réponse: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            if self.token:
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                print("✅ Connexion réussie")
                return True
            else:
                print("❌ Token non reçu")
                return False
        else:
            print(f"❌ Erreur de connexion: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
    
    def test_get_trash_items(self):
        """Tester la récupération des éléments de la corbeille"""
        print("\n📋 Test récupération des éléments de la corbeille...")
        
        response = self.session.get(f"{API_BASE_URL}/trash")
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Récupération réussie")
            print(f"📊 Structure de la réponse:")
            print(f"   - Type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"   - Clés: {list(data.keys())}")
                if 'items' in data:
                    items = data['items']
                    print(f"   - Nombre d'éléments: {len(items)}")
                    
                    if items:
                        print(f"📄 Premier élément:")
                        first_item = items[0]
                        for key, value in first_item.items():
                            if key == 'item_data' and isinstance(value, dict):
                                print(f"   - {key}: {json.dumps(value, indent=4, ensure_ascii=False)}")
                            else:
                                print(f"   - {key}: {value}")
                    else:
                        print("   - Aucun élément dans la corbeille")
                        
                if 'total' in data:
                    print(f"   - Total: {data['total']}")
                if 'page' in data:
                    print(f"   - Page: {data['page']}")
                    
            elif isinstance(data, list):
                print(f"   - Nombre d'éléments: {len(data)}")
                if data:
                    print(f"📄 Premier élément:")
                    first_item = data[0]
                    for key, value in first_item.items():
                        print(f"   - {key}: {value}")
            
            return data
        else:
            print(f"❌ Erreur: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return None
    
    def test_get_trash_stats(self):
        """Tester la récupération des statistiques de la corbeille"""
        print("\n📊 Test récupération des statistiques...")
        
        response = self.session.get(f"{API_BASE_URL}/trash/stats")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Statistiques récupérées")
            print(f"📈 Statistiques:")
            for key, value in data.items():
                print(f"   - {key}: {value}")
            return data
        else:
            print(f"❌ Erreur stats: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return None
    
    def test_database_direct(self):
        """Test direct de la base de données"""
        print("\n🗄️ Test direct de la base de données...")
        
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Connexion à la base de données (configuration corrigée)
            conn = psycopg2.connect(
                host="postgresql-thefau.alwaysdata.net",
                database="thefau_archive",
                user="thefau",
                password="Passecale2002@"
            )
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Compter les éléments dans la corbeille
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN item_type = 'document' THEN 1 END) as documents,
                       COUNT(CASE WHEN item_type = 'folder' THEN 1 END) as folders
                FROM trash 
                WHERE restored_at IS NULL AND permanent_delete_at IS NULL
            """)
            
            stats = cursor.fetchone()
            print(f"📊 Statistiques directes:")
            print(f"   - Total: {stats['total']}")
            print(f"   - Documents: {stats['documents']}")
            print(f"   - Dossiers: {stats['folders']}")
            
            # Récupérer quelques éléments
            cursor.execute("""
                SELECT id, item_id, item_type, item_data, deleted_at, deleted_by
                FROM trash 
                WHERE restored_at IS NULL AND permanent_delete_at IS NULL
                ORDER BY deleted_at DESC
                LIMIT 5
            """)
            
            items = cursor.fetchall()
            print(f"\n📄 Éléments récents ({len(items)}):")
            for item in items:
                item_dict = dict(item)
                print(f"   - ID: {item_dict['id']}")
                print(f"     Type: {item_dict['item_type']}")
                print(f"     Item ID: {item_dict['item_id']}")
                print(f"     Supprimé le: {item_dict['deleted_at']}")
                print(f"     Par: {item_dict['deleted_by']}")
                if item_dict['item_data']:
                    data = item_dict['item_data']
                    title = data.get('titre') or data.get('nom', 'Sans titre')
                    print(f"     Titre: {title}")
                print()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur base de données: {e}")
            return False
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🧪 === TEST DE L'API CORBEILLE ESAG GED ===")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test de connexion
        if not self.login():
            print("❌ Impossible de se connecter, arrêt des tests")
            return
        
        # Test direct de la base de données
        self.test_database_direct()
        
        # Test de l'API
        trash_data = self.test_get_trash_items()
        
        # Test des statistiques
        stats_data = self.test_get_trash_stats()
        
        print("\n✅ Tests terminés")

if __name__ == "__main__":
    tester = TrashAPITester()
    tester.run_all_tests() 