#!/usr/bin/env python3
"""
Configuration simple du système de corbeille ESAG GED
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

def setup_simple_trash():
    """Configuration simple de la corbeille"""
    print("🗑️ CONFIGURATION SIMPLE DE LA CORBEILLE")
    print("=" * 45)
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Modifier les colonnes pour permettre NULL
        print("🔄 Modification des colonnes pour permettre NULL...")
        try:
            cursor.execute("""
                ALTER TABLE trash 
                ALTER COLUMN deleted_by DROP NOT NULL,
                ALTER COLUMN restored_by DROP NOT NULL,
                ALTER COLUMN permanent_delete_by DROP NOT NULL
            """)
            print("   ✅ Colonnes modifiées")
        except Exception as e:
            print(f"   ⚠️ Colonnes déjà modifiées: {e}")
        
        # 2. Ajouter quelques documents de test simples
        print("📄 Ajout de documents de test...")
        
        # Récupérer un utilisateur existant
        cursor.execute("SELECT id, nom, prenom FROM utilisateur WHERE id > 0 LIMIT 1")
        user = cursor.fetchone()
        
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        print(f"👤 Utilisateur trouvé: {user['prenom']} {user['nom']} (ID: {user['id']})")
        
        # Documents de test
        test_documents = [
            {
                'item_id': 5001,
                'titre': 'Rapport mensuel Mars 2024',
                'description': 'Rapport d\'activité du mois de mars',
                'fichier': 'rapport_mars_2024.pdf',
                'taille': 1500000,
                'mime_type': 'application/pdf'
            },
            {
                'item_id': 5002,
                'titre': 'Présentation budget 2024',
                'description': 'Slides de présentation du budget annuel',
                'fichier': 'budget_2024.pptx',
                'taille': 3200000,
                'mime_type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            },
            {
                'item_id': 5003,
                'titre': 'Contrat partenaire ABC',
                'description': 'Contrat de partenariat avec ABC Corp',
                'fichier': 'contrat_abc.docx',
                'taille': 800000,
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            },
            {
                'item_id': 5004,
                'titre': 'Base données prospects',
                'description': 'Liste des prospects commerciaux',
                'fichier': 'prospects.xlsx',
                'taille': 2100000,
                'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        ]
        
        # Ajouter les documents
        for i, doc in enumerate(test_documents):
            # Dates variées
            days_ago = 5 + (i * 3)  # 5, 8, 11, 14 jours
            deleted_at = datetime.now() - timedelta(days=days_ago)
            
            # Calculer la date d'expiration (30 jours après suppression)
            expiry_date = deleted_at + timedelta(days=30)
            
            try:
                cursor.execute("""
                    INSERT INTO trash (
                        item_id, item_type, item_data, deleted_by, deleted_at,
                        expiry_date, size_bytes, deletion_reason
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    doc['item_id'],
                    'document',
                    json.dumps(doc),
                    user['id'],
                    deleted_at,
                    expiry_date,
                    doc['taille'],
                    f"Test de suppression {i+1}"
                ))
                
                print(f"   ✅ {doc['titre']} (supprimé il y a {days_ago} jours)")
                
            except Exception as e:
                if "duplicate key" in str(e):
                    print(f"   ⚠️ {doc['titre']} (déjà existant)")
                else:
                    print(f"   ❌ Erreur pour {doc['titre']}: {e}")
        
        # 3. Ajouter quelques dossiers
        print("📁 Ajout de dossiers de test...")
        
        test_folders = [
            {
                'item_id': 6001,
                'nom': 'Archives Q1 2024',
                'description': 'Dossier d\'archives du premier trimestre'
            },
            {
                'item_id': 6002,
                'nom': 'Projets en pause',
                'description': 'Dossier des projets temporairement suspendus'
            }
        ]
        
        for i, folder in enumerate(test_folders):
            days_ago = 10 + (i * 5)  # 10, 15 jours
            deleted_at = datetime.now() - timedelta(days=days_ago)
            expiry_date = deleted_at + timedelta(days=30)
            
            try:
                cursor.execute("""
                    INSERT INTO trash (
                        item_id, item_type, item_data, deleted_by, deleted_at,
                        expiry_date, size_bytes, deletion_reason
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    folder['item_id'],
                    'folder',
                    json.dumps(folder),
                    user['id'],
                    deleted_at,
                    expiry_date,
                    0,  # Les dossiers n'ont pas de taille
                    "Réorganisation des dossiers"
                ))
                
                print(f"   ✅ {folder['nom']} (supprimé il y a {days_ago} jours)")
                
            except Exception as e:
                if "duplicate key" in str(e):
                    print(f"   ⚠️ {folder['nom']} (déjà existant)")
                else:
                    print(f"   ❌ Erreur pour {folder['nom']}: {e}")
        
        # 4. Ajouter un élément restauré
        print("♻️ Ajout d'un élément restauré...")
        
        restored_doc = {
            'item_id': 7001,
            'titre': 'Document restauré',
            'description': 'Document qui a été restauré depuis la corbeille',
            'fichier': 'document_restaure.pdf',
            'taille': 1000000,
            'mime_type': 'application/pdf'
        }
        
        deleted_at = datetime.now() - timedelta(days=20)
        restored_at = datetime.now() - timedelta(days=15)
        
        try:
            cursor.execute("""
                INSERT INTO trash (
                    item_id, item_type, item_data, deleted_by, deleted_at,
                    restored_at, restored_by, size_bytes, deletion_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                restored_doc['item_id'],
                'document',
                json.dumps(restored_doc),
                user['id'],
                deleted_at,
                restored_at,
                user['id'],
                restored_doc['taille'],
                "Test de restauration"
            ))
            
            print(f"   ✅ {restored_doc['titre']} (restauré il y a 15 jours)")
            
        except Exception as e:
            if "duplicate key" in str(e):
                print(f"   ⚠️ Document restauré (déjà existant)")
            else:
                print(f"   ❌ Erreur: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Configuration simple terminée!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def check_trash_status():
    """Vérifier le statut de la corbeille"""
    print("\n📊 VÉRIFICATION DU STATUT DE LA CORBEILLE")
    print("=" * 45)
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Statistiques générales
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE restored_at IS NULL AND permanent_delete_at IS NULL) as pending,
                COUNT(*) FILTER (WHERE restored_at IS NOT NULL) as restored,
                COUNT(*) FILTER (WHERE permanent_delete_at IS NOT NULL) as deleted,
                COALESCE(SUM(size_bytes), 0) as total_size
            FROM trash
        """)
        
        stats = cursor.fetchone()
        
        print(f"📈 Statistiques:")
        print(f"   - Total éléments: {stats['total']}")
        print(f"   - En attente de suppression: {stats['pending']}")
        print(f"   - Restaurés: {stats['restored']}")
        print(f"   - Supprimés définitivement: {stats['deleted']}")
        print(f"   - Taille totale: {stats['total_size']} bytes ({stats['total_size']/1024/1024:.2f} MB)")
        
        # Par type
        cursor.execute("""
            SELECT item_type, COUNT(*) as count
            FROM trash
            WHERE restored_at IS NULL AND permanent_delete_at IS NULL
            GROUP BY item_type
        """)
        
        types = cursor.fetchall()
        if types:
            print(f"\n📋 Par type (en attente):")
            for type_info in types:
                print(f"   - {type_info['item_type']}: {type_info['count']}")
        
        # Éléments récents
        cursor.execute("""
            SELECT item_type, item_data, deleted_at
            FROM trash
            WHERE restored_at IS NULL AND permanent_delete_at IS NULL
            ORDER BY deleted_at DESC
            LIMIT 5
        """)
        
        recent = cursor.fetchall()
        if recent:
            print(f"\n🕒 Éléments récents:")
            for item in recent:
                data = item['item_data']
                title = data.get('titre') or data.get('nom', 'Sans titre')
                days_ago = (datetime.now() - item['deleted_at']).days
                print(f"   - {title} ({item['item_type']}) - il y a {days_ago} jours")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Fonction principale"""
    success = True
    
    if not setup_simple_trash():
        success = False
    
    if not check_trash_status():
        success = False
    
    if success:
        print(f"\n🎉 SYSTÈME DE CORBEILLE CONFIGURÉ!")
        print("=" * 40)
        print("✅ La corbeille contient maintenant des données de test")
        print("🚀 Vous pouvez tester:")
        print("   - L'API REST: http://localhost:5000/api/trash")
        print("   - L'interface web: http://localhost:3000/corbeille")
        print("   - Les statistiques: http://localhost:5000/api/trash/stats")
        print("\n💡 Fonctionnalités disponibles:")
        print("   - Visualisation des éléments supprimés")
        print("   - Restauration d'éléments")
        print("   - Suppression définitive")
        print("   - Statistiques détaillées")
        print("   - Filtrage et recherche")
    else:
        print(f"\n❌ Échec de la configuration")

if __name__ == "__main__":
    main() 