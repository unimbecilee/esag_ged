#!/usr/bin/env python3
"""
Correction des contraintes de clé étrangère dans la table trash
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def fix_trash_constraints():
    """Corriger les contraintes de clé étrangère"""
    print("🔧 CORRECTION DES CONTRAINTES DE LA CORBEILLE")
    print("=" * 45)
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor()
        
        # Supprimer les contraintes existantes si elles existent
        print("🗑️ Suppression des contraintes existantes...")
        
        constraints_to_drop = [
            'trash_deleted_by_fkey',
            'trash_restored_by_fkey', 
            'trash_permanent_delete_by_fkey'
        ]
        
        for constraint in constraints_to_drop:
            try:
                cursor.execute(f"""
                    ALTER TABLE trash DROP CONSTRAINT IF EXISTS {constraint}
                """)
                print(f"   ✅ Contrainte {constraint} supprimée")
            except Exception as e:
                print(f"   ⚠️ Contrainte {constraint} non trouvée: {e}")
        
        # Modifier les colonnes pour permettre NULL et 0
        print("🔄 Modification des colonnes...")
        
        cursor.execute("""
            ALTER TABLE trash 
            ALTER COLUMN deleted_by DROP NOT NULL,
            ALTER COLUMN restored_by DROP NOT NULL,
            ALTER COLUMN permanent_delete_by DROP NOT NULL
        """)
        
        # Ajouter les nouvelles contraintes avec gestion du 0 (système)
        print("➕ Ajout des nouvelles contraintes...")
        
        cursor.execute("""
            ALTER TABLE trash 
            ADD CONSTRAINT trash_deleted_by_fkey 
            FOREIGN KEY (deleted_by) 
            REFERENCES utilisateur(id) 
            ON DELETE SET NULL
            DEFERRABLE INITIALLY DEFERRED
        """)
        
        cursor.execute("""
            ALTER TABLE trash 
            ADD CONSTRAINT trash_restored_by_fkey 
            FOREIGN KEY (restored_by) 
            REFERENCES utilisateur(id) 
            ON DELETE SET NULL
            DEFERRABLE INITIALLY DEFERRED
        """)
        
        cursor.execute("""
            ALTER TABLE trash 
            ADD CONSTRAINT trash_permanent_delete_by_fkey 
            FOREIGN KEY (permanent_delete_by) 
            REFERENCES utilisateur(id) 
            ON DELETE SET NULL
            DEFERRABLE INITIALLY DEFERRED
        """)
        
        # Ajouter des contraintes CHECK pour gérer le cas 0 = système
        print("✅ Ajout des contraintes CHECK...")
        
        cursor.execute("""
            ALTER TABLE trash 
            ADD CONSTRAINT check_deleted_by 
            CHECK (deleted_by IS NULL OR deleted_by > 0)
        """)
        
        cursor.execute("""
            ALTER TABLE trash 
            ADD CONSTRAINT check_restored_by 
            CHECK (restored_by IS NULL OR restored_by > 0)
        """)
        
        cursor.execute("""
            ALTER TABLE trash 
            ADD CONSTRAINT check_permanent_delete_by 
            CHECK (permanent_delete_by IS NULL OR permanent_delete_by >= 0)
        """)
        
        # Créer un utilisateur système virtuel pour les opérations automatiques
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

def test_constraints():
    """Tester les nouvelles contraintes"""
    print("\n🧪 TEST DES NOUVELLES CONTRAINTES")
    print("=" * 35)
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
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

def main():
    """Fonction principale"""
    success = True
    
    if not fix_trash_constraints():
        success = False
    
    if not test_constraints():
        success = False
    
    if success:
        print("\n🎉 Contraintes de la corbeille corrigées et testées!")
        print("✅ Le système peut maintenant gérer:")
        print("   - Les suppressions par utilisateurs")
        print("   - Les suppressions automatiques (système)")
        print("   - Les valeurs NULL pour les champs optionnels")
    else:
        print("\n❌ Échec de la correction des contraintes")

if __name__ == "__main__":
    main() 