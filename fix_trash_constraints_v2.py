#!/usr/bin/env python3
"""
Correction des contraintes de clé étrangère dans la table trash - Version 2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def fix_trash_constraints_v2():
    """Corriger les contraintes de clé étrangère - Version 2"""
    print("🔧 CORRECTION DES CONTRAINTES DE LA CORBEILLE V2")
    print("=" * 50)
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor()
        
        # Vérifier d'abord les contraintes de rôle existantes
        print("🔍 Vérification des contraintes de rôle...")
        cursor.execute("""
            SELECT constraint_name, check_clause 
            FROM information_schema.check_constraints 
            WHERE table_name = 'utilisateur' AND constraint_name LIKE '%role%'
        """)
        
        role_constraints = cursor.fetchall()
        for constraint in role_constraints:
            print(f"   - {constraint[0]}: {constraint[1]}")
        
        # Modifier temporairement la contrainte de rôle pour permettre 'system'
        print("🔄 Modification de la contrainte de rôle...")
        
        # Supprimer l'ancienne contrainte
        cursor.execute("""
            ALTER TABLE utilisateur DROP CONSTRAINT IF EXISTS utilisateur_role_check
        """)
        
        # Ajouter la nouvelle contrainte avec 'system'
        cursor.execute("""
            ALTER TABLE utilisateur 
            ADD CONSTRAINT utilisateur_role_check 
            CHECK (role IN ('admin', 'user', 'system'))
        """)
        
        # Créer l'utilisateur système
        print("🤖 Création de l'utilisateur système...")
        
        cursor.execute("""
            INSERT INTO utilisateur (
                id, nom, prenom, email, mot_de_passe, role, 
                date_creation
            ) VALUES (
                0, 'Système', 'Automatique', 'system@esag-ged.local', 
                'no_password', 'system', CURRENT_TIMESTAMP
            ) ON CONFLICT (id) DO UPDATE SET
                nom = EXCLUDED.nom,
                prenom = EXCLUDED.prenom,
                role = EXCLUDED.role
        """)
        
        # Maintenant, supprimer et recréer les contraintes de la corbeille
        print("🗑️ Suppression des contraintes de corbeille...")
        
        constraints_to_drop = [
            'trash_deleted_by_fkey',
            'trash_restored_by_fkey', 
            'trash_permanent_delete_by_fkey',
            'check_deleted_by',
            'check_restored_by',
            'check_permanent_delete_by'
        ]
        
        for constraint in constraints_to_drop:
            try:
                cursor.execute(f"""
                    ALTER TABLE trash DROP CONSTRAINT IF EXISTS {constraint}
                """)
                print(f"   ✅ Contrainte {constraint} supprimée")
            except Exception as e:
                print(f"   ⚠️ Contrainte {constraint}: {e}")
        
        # Modifier les colonnes pour permettre NULL
        print("🔄 Modification des colonnes...")
        
        cursor.execute("""
            ALTER TABLE trash 
            ALTER COLUMN deleted_by DROP NOT NULL,
            ALTER COLUMN restored_by DROP NOT NULL,
            ALTER COLUMN permanent_delete_by DROP NOT NULL
        """)
        
        # Ajouter les nouvelles contraintes avec gestion du 0 (système)
        print("➕ Ajout des nouvelles contraintes...")
        
        # Pour deleted_by: doit référencer un utilisateur existant ou être NULL
        cursor.execute("""
            ALTER TABLE trash 
            ADD CONSTRAINT trash_deleted_by_fkey 
            FOREIGN KEY (deleted_by) 
            REFERENCES utilisateur(id) 
            ON DELETE SET NULL
        """)
        
        # Pour restored_by: doit référencer un utilisateur existant ou être NULL
        cursor.execute("""
            ALTER TABLE trash 
            ADD CONSTRAINT trash_restored_by_fkey 
            FOREIGN KEY (restored_by) 
            REFERENCES utilisateur(id) 
            ON DELETE SET NULL
        """)
        
        # Pour permanent_delete_by: peut être 0 (système), référencer un utilisateur, ou être NULL
        cursor.execute("""
            ALTER TABLE trash 
            ADD CONSTRAINT trash_permanent_delete_by_fkey 
            FOREIGN KEY (permanent_delete_by) 
            REFERENCES utilisateur(id) 
            ON DELETE SET NULL
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Contraintes corrigées avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def test_constraints_v2():
    """Tester les nouvelles contraintes - Version 2"""
    print("\n🧪 TEST DES NOUVELLES CONTRAINTES V2")
    print("=" * 40)
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier que l'utilisateur système existe
        cursor.execute("SELECT * FROM utilisateur WHERE id = 0")
        system_user = cursor.fetchone()
        
        if system_user:
            print(f"✅ Utilisateur système trouvé: {system_user['nom']} {system_user['prenom']}")
        else:
            print("❌ Utilisateur système non trouvé")
            return False
        
        # Test 1: Insertion avec utilisateur valide
        print("1️⃣ Test insertion avec utilisateur valide...")
        cursor.execute("SELECT id FROM utilisateur WHERE id > 0 LIMIT 1")
        user = cursor.fetchone()
        
        if user:
            cursor.execute("""
                INSERT INTO trash (
                    item_id, item_type, item_data, deleted_by, deleted_at
                ) VALUES (
                    99999, 'test', '{"test": true}', %s, CURRENT_TIMESTAMP
                ) RETURNING id
            """, (user['id'],))
            
            test_id = cursor.fetchone()['id']
            print(f"   ✅ Insertion réussie avec ID: {test_id}")
            
            # Nettoyer
            cursor.execute("DELETE FROM trash WHERE id = %s", (test_id,))
        
        # Test 2: Insertion avec système (0)
        print("2️⃣ Test insertion avec utilisateur système (0)...")
        cursor.execute("""
            INSERT INTO trash (
                item_id, item_type, item_data, permanent_delete_by, 
                deleted_at, permanent_delete_at
            ) VALUES (
                99998, 'test', '{"test": true}', 0, 
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            ) RETURNING id
        """)
        
        test_id = cursor.fetchone()['id']
        print(f"   ✅ Insertion système réussie avec ID: {test_id}")
        
        # Nettoyer
        cursor.execute("DELETE FROM trash WHERE id = %s", (test_id,))
        
        # Test 3: Insertion avec NULL
        print("3️⃣ Test insertion avec valeurs NULL...")
        cursor.execute("""
            INSERT INTO trash (
                item_id, item_type, item_data, deleted_by, deleted_at
            ) VALUES (
                99997, 'test', '{"test": true}', NULL, CURRENT_TIMESTAMP
            ) RETURNING id
        """)
        
        test_id = cursor.fetchone()['id']
        print(f"   ✅ Insertion NULL réussie avec ID: {test_id}")
        
        # Nettoyer
        cursor.execute("DELETE FROM trash WHERE id = %s", (test_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Tous les tests de contraintes réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def add_sample_trash_data():
    """Ajouter quelques données d'exemple dans la corbeille"""
    print("\n📝 AJOUT DE DONNÉES D'EXEMPLE")
    print("=" * 30)
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer un utilisateur existant
        cursor.execute("SELECT id FROM utilisateur WHERE id > 0 LIMIT 1")
        user = cursor.fetchone()
        
        if not user:
            print("❌ Aucun utilisateur trouvé")
            return False
        
        # Ajouter quelques documents de test
        test_items = [
            {
                'item_id': 1001,
                'item_type': 'document',
                'item_data': {
                    'titre': 'Document de test 1',
                    'description': 'Premier document de test',
                    'fichier': 'test1.pdf',
                    'taille': 1024000,
                    'mime_type': 'application/pdf'
                },
                'deleted_by': user['id'],
                'deletion_reason': 'Test du système'
            },
            {
                'item_id': 1002,
                'item_type': 'document',
                'item_data': {
                    'titre': 'Document de test 2',
                    'description': 'Deuxième document de test',
                    'fichier': 'test2.docx',
                    'taille': 512000,
                    'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                },
                'deleted_by': user['id'],
                'deletion_reason': 'Test de suppression'
            },
            {
                'item_id': 2001,
                'item_type': 'folder',
                'item_data': {
                    'nom': 'Dossier de test',
                    'description': 'Dossier pour tester la corbeille'
                },
                'deleted_by': user['id'],
                'deletion_reason': 'Réorganisation'
            }
        ]
        
        for item in test_items:
            cursor.execute("""
                INSERT INTO trash (
                    item_id, item_type, item_data, deleted_by, deleted_at,
                    size_bytes, deletion_reason
                ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
            """, (
                item['item_id'],
                item['item_type'],
                json.dumps(item['item_data']),
                item['deleted_by'],
                item['item_data'].get('taille', 0),
                item['deletion_reason']
            ))
            
            print(f"   ✅ {item['item_data'].get('titre') or item['item_data'].get('nom')} ajouté")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Données d'exemple ajoutées!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout: {e}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def main():
    """Fonction principale"""
    success = True
    
    if not fix_trash_constraints_v2():
        success = False
    
    if not test_constraints_v2():
        success = False
    
    if success:
        # Ajouter quelques données d'exemple
        add_sample_trash_data()
        
        print("\n🎉 Système de corbeille configuré et testé!")
        print("✅ Le système peut maintenant gérer:")
        print("   - Les suppressions par utilisateurs")
        print("   - Les suppressions automatiques (système)")
        print("   - Les valeurs NULL pour les champs optionnels")
        print("   - Les contraintes de clé étrangère correctes")
        print("\n🚀 Vous pouvez maintenant tester l'API de la corbeille!")
    else:
        print("\n❌ Échec de la configuration du système")

if __name__ == "__main__":
    import json
    main() 