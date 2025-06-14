#!/usr/bin/env python3
"""
Script pour ajouter des données de test dans la corbeille ESAG GED
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json
import random

def add_test_trash_data():
    """Ajouter des données de test dans la corbeille"""
    print("🗑️ AJOUT DE DONNÉES DE TEST DANS LA CORBEILLE")
    print("=" * 50)
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les utilisateurs existants
        cursor.execute("SELECT id, nom, prenom FROM utilisateur LIMIT 5")
        users = cursor.fetchall()
        
        if not users:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        print(f"👥 {len(users)} utilisateurs trouvés")
        
        # Données de test pour différents types d'éléments
        test_documents = [
            {
                'titre': 'Rapport financier Q4 2024',
                'description': 'Rapport trimestriel des finances',
                'fichier': 'rapport_q4_2024.pdf',
                'taille': 2048576,  # 2MB
                'mime_type': 'application/pdf'
            },
            {
                'titre': 'Présentation projet Alpha',
                'description': 'Slides de présentation du nouveau projet',
                'fichier': 'presentation_alpha.pptx',
                'taille': 5242880,  # 5MB
                'mime_type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            },
            {
                'titre': 'Contrat client XYZ',
                'description': 'Contrat signé avec le client XYZ Corp',
                'fichier': 'contrat_xyz.docx',
                'taille': 1048576,  # 1MB
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            },
            {
                'titre': 'Base de données clients',
                'description': 'Export de la base de données clients',
                'fichier': 'clients_export.xlsx',
                'taille': 3145728,  # 3MB
                'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            },
            {
                'titre': 'Photos événement corporate',
                'description': 'Photos de l\'événement d\'entreprise',
                'fichier': 'photos_event.zip',
                'taille': 52428800,  # 50MB
                'mime_type': 'application/zip'
            },
            {
                'titre': 'Manuel utilisateur v2.1',
                'description': 'Documentation utilisateur mise à jour',
                'fichier': 'manuel_v2.1.pdf',
                'taille': 4194304,  # 4MB
                'mime_type': 'application/pdf'
            },
            {
                'titre': 'Facture fournisseur ABC',
                'description': 'Facture du fournisseur ABC pour matériel',
                'fichier': 'facture_abc_001.pdf',
                'taille': 512000,  # 500KB
                'mime_type': 'application/pdf'
            },
            {
                'titre': 'Backup configuration serveur',
                'description': 'Sauvegarde des configurations serveur',
                'fichier': 'server_config_backup.json',
                'taille': 102400,  # 100KB
                'mime_type': 'application/json'
            }
        ]
        
        test_folders = [
            {
                'nom': 'Archives 2023',
                'description': 'Dossier d\'archives pour l\'année 2023'
            },
            {
                'nom': 'Projets abandonnés',
                'description': 'Dossier contenant les projets non aboutis'
            },
            {
                'nom': 'Temp - à trier',
                'description': 'Dossier temporaire pour documents à classer'
            },
            {
                'nom': 'Brouillons marketing',
                'description': 'Brouillons de campagnes marketing'
            }
        ]
        
        # Récupérer la configuration de rétention
        cursor.execute("""
            SELECT setting_value::INTEGER as retention_days 
            FROM trash_config 
            WHERE setting_name = 'retention_days'
        """)
        retention_config = cursor.fetchone()
        retention_days = retention_config['retention_days'] if retention_config else 30
        
        print(f"⏰ Durée de rétention configurée: {retention_days} jours")
        
        # Ajouter des documents dans la corbeille
        print("\n📄 Ajout de documents de test...")
        doc_count = 0
        
        for i, doc_data in enumerate(test_documents):
            user = random.choice(users)
            
            # Dates variées (certains récents, d'autres plus anciens)
            days_ago = random.randint(1, retention_days - 5)
            deleted_at = datetime.now() - timedelta(days=days_ago)
            expiry_date = deleted_at + timedelta(days=retention_days)
            
            # Raisons de suppression variées
            deletion_reasons = [
                "Document obsolète",
                "Suppression par l'utilisateur",
                "Nettoyage de dossier",
                "Version remplacée",
                "Erreur de création",
                "Projet annulé"
            ]
            
            cursor.execute("""
                INSERT INTO trash (
                    item_id, item_type, item_data, deleted_by, deleted_at,
                    expiry_date, size_bytes, deletion_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                1000 + i,  # ID fictif
                'document',
                json.dumps(doc_data),
                user['id'],
                deleted_at,
                expiry_date,
                doc_data['taille'],
                random.choice(deletion_reasons)
            ))
            
            doc_count += 1
            print(f"   ✅ {doc_data['titre']} (supprimé il y a {days_ago} jours)")
        
        # Ajouter des dossiers dans la corbeille
        print(f"\n📁 Ajout de dossiers de test...")
        folder_count = 0
        
        for i, folder_data in enumerate(test_folders):
            user = random.choice(users)
            
            days_ago = random.randint(5, retention_days - 2)
            deleted_at = datetime.now() - timedelta(days=days_ago)
            expiry_date = deleted_at + timedelta(days=retention_days)
            
            cursor.execute("""
                INSERT INTO trash (
                    item_id, item_type, item_data, deleted_by, deleted_at,
                    expiry_date, size_bytes, deletion_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                2000 + i,  # ID fictif
                'folder',
                json.dumps(folder_data),
                user['id'],
                deleted_at,
                expiry_date,
                0,  # Les dossiers n'ont pas de taille directe
                "Réorganisation des dossiers"
            ))
            
            folder_count += 1
            print(f"   ✅ {folder_data['nom']} (supprimé il y a {days_ago} jours)")
        
        # Ajouter quelques éléments restaurés pour les statistiques
        print(f"\n♻️ Ajout d'éléments restaurés...")
        restored_count = 0
        
        for i in range(3):
            user = random.choice(users)
            
            doc_data = {
                'titre': f'Document restauré {i+1}',
                'description': 'Document qui a été restauré depuis la corbeille',
                'fichier': f'restored_doc_{i+1}.pdf',
                'taille': random.randint(500000, 2000000),
                'mime_type': 'application/pdf'
            }
            
            deleted_at = datetime.now() - timedelta(days=random.randint(10, 20))
            restored_at = deleted_at + timedelta(days=random.randint(1, 5))
            
            cursor.execute("""
                INSERT INTO trash (
                    item_id, item_type, item_data, deleted_by, deleted_at,
                    restored_at, restored_by, size_bytes, deletion_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                3000 + i,  # ID fictif
                'document',
                json.dumps(doc_data),
                user['id'],
                deleted_at,
                restored_at,
                user['id'],
                doc_data['taille'],
                "Test de restauration"
            ))
            
            restored_count += 1
            print(f"   ✅ {doc_data['titre']} (restauré)")
        
        # Ajouter quelques éléments supprimés définitivement
        print(f"\n🔥 Ajout d'éléments supprimés définitivement...")
        deleted_count = 0
        
        for i in range(2):
            user = random.choice(users)
            
            doc_data = {
                'titre': f'Document supprimé définitivement {i+1}',
                'description': 'Document supprimé de façon permanente',
                'fichier': f'deleted_doc_{i+1}.pdf',
                'taille': random.randint(100000, 1000000),
                'mime_type': 'application/pdf'
            }
            
            deleted_at = datetime.now() - timedelta(days=random.randint(25, 35))
            permanent_delete_at = deleted_at + timedelta(days=retention_days + 1)
            
            cursor.execute("""
                INSERT INTO trash (
                    item_id, item_type, item_data, deleted_by, deleted_at,
                    permanent_delete_at, permanent_delete_by, size_bytes, deletion_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                4000 + i,  # ID fictif
                'document',
                json.dumps(doc_data),
                user['id'],
                deleted_at,
                permanent_delete_at,
                0,  # 0 = suppression automatique
                doc_data['taille'],
                "Nettoyage automatique"
            ))
            
            deleted_count += 1
            print(f"   ✅ {doc_data['titre']} (supprimé définitivement)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Résumé
        total_items = doc_count + folder_count + restored_count + deleted_count
        print(f"\n📊 RÉSUMÉ DES DONNÉES AJOUTÉES")
        print("=" * 35)
        print(f"📄 Documents en corbeille: {doc_count}")
        print(f"📁 Dossiers en corbeille: {folder_count}")
        print(f"♻️ Éléments restaurés: {restored_count}")
        print(f"🔥 Éléments supprimés définitivement: {deleted_count}")
        print(f"📊 Total: {total_items} éléments")
        
        print(f"\n✅ Données de test ajoutées avec succès!")
        print(f"🎯 Vous pouvez maintenant tester l'interface de la corbeille")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout des données: {e}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def check_existing_data():
    """Vérifier les données existantes dans la corbeille"""
    print("🔍 VÉRIFICATION DES DONNÉES EXISTANTES")
    print("=" * 40)
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Compter les éléments par statut
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
        
        print(f"📊 Statistiques actuelles:")
        print(f"   - Total éléments: {stats['total']}")
        print(f"   - En attente: {stats['pending']}")
        print(f"   - Restaurés: {stats['restored']}")
        print(f"   - Supprimés définitivement: {stats['deleted']}")
        print(f"   - Taille totale: {stats['total_size']} bytes")
        
        # Compter par type
        cursor.execute("""
            SELECT item_type, COUNT(*) as count
            FROM trash
            WHERE restored_at IS NULL AND permanent_delete_at IS NULL
            GROUP BY item_type
        """)
        
        types = cursor.fetchall()
        if types:
            print(f"\n📋 Par type d'élément:")
            for type_info in types:
                print(f"   - {type_info['item_type']}: {type_info['count']}")
        
        cursor.close()
        conn.close()
        
        return stats['total'] > 0
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Fonction principale"""
    print("🗑️ GESTIONNAIRE DE DONNÉES DE TEST - CORBEILLE ESAG GED")
    print("=" * 60)
    
    # Vérifier les données existantes
    has_data = check_existing_data()
    
    if has_data:
        print(f"\n⚠️ Des données existent déjà dans la corbeille.")
        response = input("Voulez-vous ajouter plus de données de test ? (o/N): ")
        if response.lower() not in ['o', 'oui', 'y', 'yes']:
            print("🚫 Opération annulée")
            return
    
    # Ajouter les données de test
    success = add_test_trash_data()
    
    if success:
        print(f"\n🎉 Configuration terminée!")
        print(f"🚀 Le système de corbeille est prêt avec des données de test")
        print(f"💡 Vous pouvez maintenant:")
        print(f"   - Tester l'interface web à http://localhost:3000/corbeille")
        print(f"   - Utiliser l'API REST pour les opérations")
        print(f"   - Configurer les paramètres de rétention")
    else:
        print(f"\n❌ Échec de la configuration")

if __name__ == "__main__":
    main() 