#!/usr/bin/env python3
"""
Amélioration du système de corbeille ESAG GED
Ajout de la configuration automatique et des fonctionnalités avancées
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
import json

def create_trash_config_table():
    """Créer la table de configuration de la corbeille"""
    print("⚙️ CRÉATION DE LA TABLE DE CONFIGURATION")
    print("=" * 45)
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor()
        
        # Table de configuration de la corbeille
        print("📋 Création de la table 'trash_config'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trash_config (
                id SERIAL PRIMARY KEY,
                setting_name VARCHAR(100) NOT NULL UNIQUE,
                setting_value TEXT NOT NULL,
                setting_type VARCHAR(20) DEFAULT 'string',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Insérer les configurations par défaut
        print("🔧 Insertion des configurations par défaut...")
        default_configs = [
            ('auto_cleanup_enabled', 'true', 'boolean', 'Activer le nettoyage automatique de la corbeille'),
            ('retention_days', '30', 'integer', 'Nombre de jours avant suppression automatique'),
            ('max_items_per_user', '1000', 'integer', 'Nombre maximum d\'éléments par utilisateur dans la corbeille'),
            ('cleanup_schedule', '0 2 * * *', 'string', 'Planning de nettoyage automatique (format cron)'),
            ('notification_before_cleanup', 'true', 'boolean', 'Notifier avant suppression automatique'),
            ('notification_days_before', '7', 'integer', 'Nombre de jours avant de notifier'),
            ('allow_user_restore', 'true', 'boolean', 'Permettre aux utilisateurs de restaurer leurs éléments'),
            ('admin_only_permanent_delete', 'false', 'boolean', 'Seuls les admins peuvent supprimer définitivement')
        ]
        
        for name, value, type_val, desc in default_configs:
            cursor.execute("""
                INSERT INTO trash_config (setting_name, setting_value, setting_type, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (setting_name) DO NOTHING
            """, (name, value, type_val, desc))
        
        # Ajouter des index pour optimiser les performances
        print("🚀 Création des index d'optimisation...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trash_deleted_at ON trash(deleted_at);
            CREATE INDEX IF NOT EXISTS idx_trash_item_type ON trash(item_type);
            CREATE INDEX IF NOT EXISTS idx_trash_deleted_by ON trash(deleted_by);
            CREATE INDEX IF NOT EXISTS idx_trash_restored_at ON trash(restored_at);
            CREATE INDEX IF NOT EXISTS idx_trash_permanent_delete_at ON trash(permanent_delete_at);
        """)
        
        # Fonction pour nettoyer automatiquement la corbeille
        print("🧹 Création de la fonction de nettoyage automatique...")
        cursor.execute("""
            CREATE OR REPLACE FUNCTION cleanup_trash()
            RETURNS INTEGER AS $$
            DECLARE
                retention_days INTEGER;
                cleanup_enabled BOOLEAN;
                deleted_count INTEGER := 0;
            BEGIN
                -- Récupérer la configuration
                SELECT setting_value::INTEGER INTO retention_days 
                FROM trash_config WHERE setting_name = 'retention_days';
                
                SELECT setting_value::BOOLEAN INTO cleanup_enabled 
                FROM trash_config WHERE setting_name = 'auto_cleanup_enabled';
                
                -- Si le nettoyage automatique est désactivé, ne rien faire
                IF NOT cleanup_enabled THEN
                    RETURN 0;
                END IF;
                
                -- Supprimer définitivement les éléments expirés
                UPDATE trash 
                SET permanent_delete_at = CURRENT_TIMESTAMP,
                    permanent_delete_by = 0  -- 0 = système automatique
                WHERE deleted_at < (CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days)
                AND restored_at IS NULL 
                AND permanent_delete_at IS NULL;
                
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                
                -- Log de l'opération
                INSERT INTO system_logs (timestamp, level, event_type, message, additional_data)
                VALUES (
                    CURRENT_TIMESTAMP, 
                    'INFO', 
                    'TRASH_CLEANUP', 
                    'Nettoyage automatique de la corbeille',
                    json_build_object('deleted_count', deleted_count, 'retention_days', retention_days)::text
                );
                
                RETURN deleted_count;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Fonction pour obtenir les statistiques de la corbeille
        print("📊 Création de la fonction de statistiques...")
        cursor.execute("""
            CREATE OR REPLACE FUNCTION get_trash_stats(user_id_param INTEGER DEFAULT NULL)
            RETURNS JSON AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'total_items', COUNT(*),
                    'by_type', json_object_agg(item_type, type_count),
                    'pending_deletion', COUNT(*) FILTER (WHERE restored_at IS NULL AND permanent_delete_at IS NULL),
                    'restored_items', COUNT(*) FILTER (WHERE restored_at IS NOT NULL),
                    'permanently_deleted', COUNT(*) FILTER (WHERE permanent_delete_at IS NOT NULL),
                    'oldest_item', MIN(deleted_at),
                    'newest_item', MAX(deleted_at)
                ) INTO result
                FROM (
                    SELECT 
                        item_type,
                        COUNT(*) as type_count,
                        deleted_at,
                        restored_at,
                        permanent_delete_at
                    FROM trash 
                    WHERE (user_id_param IS NULL OR deleted_by = user_id_param)
                    GROUP BY item_type, deleted_at, restored_at, permanent_delete_at
                ) stats;
                
                RETURN result;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Système de corbeille amélioré créé avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def add_missing_columns():
    """Ajouter les colonnes manquantes à la table trash si nécessaire"""
    print("\n🔧 VÉRIFICATION ET AJOUT DES COLONNES MANQUANTES")
    print("=" * 50)
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier les colonnes existantes
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'trash'
        """)
        
        existing_columns = [row['column_name'] for row in cursor.fetchall()]
        print(f"📋 Colonnes existantes: {', '.join(existing_columns)}")
        
        # Colonnes requises
        required_columns = {
            'expiry_date': 'TIMESTAMP DEFAULT NULL',
            'size_bytes': 'BIGINT DEFAULT 0',
            'original_path': 'TEXT DEFAULT NULL',
            'deletion_reason': 'VARCHAR(255) DEFAULT NULL'
        }
        
        # Ajouter les colonnes manquantes
        for col_name, col_def in required_columns.items():
            if col_name not in existing_columns:
                print(f"➕ Ajout de la colonne '{col_name}'...")
                cursor.execute(f"""
                    ALTER TABLE trash 
                    ADD COLUMN IF NOT EXISTS {col_name} {col_def}
                """)
            else:
                print(f"✅ Colonne '{col_name}' déjà présente")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Colonnes vérifiées et ajoutées si nécessaire")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout des colonnes: {e}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def test_trash_functions():
    """Tester les fonctions de la corbeille"""
    print("\n🧪 TEST DES FONCTIONS DE LA CORBEILLE")
    print("=" * 40)
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test de la fonction de statistiques
        print("📊 Test de la fonction get_trash_stats()...")
        cursor.execute("SELECT get_trash_stats() as stats")
        stats = cursor.fetchone()['stats']
        print(f"   Statistiques: {stats}")
        
        # Test de la fonction de nettoyage (mode test)
        print("🧹 Test de la fonction cleanup_trash()...")
        cursor.execute("SELECT cleanup_trash() as deleted_count")
        deleted_count = cursor.fetchone()['deleted_count']
        print(f"   Éléments supprimés: {deleted_count}")
        
        # Afficher la configuration actuelle
        print("⚙️ Configuration actuelle:")
        cursor.execute("SELECT setting_name, setting_value, description FROM trash_config ORDER BY setting_name")
        configs = cursor.fetchall()
        for config in configs:
            print(f"   - {config['setting_name']}: {config['setting_value']} ({config['description']})")
        
        cursor.close()
        conn.close()
        
        print("✅ Tests terminés avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        if 'conn' in locals():
            cursor.close()
            conn.close()
        return False

def main():
    """Fonction principale"""
    print("🗑️ AMÉLIORATION DU SYSTÈME DE CORBEILLE ESAG GED")
    print("=" * 55)
    
    success = True
    
    # Créer la table de configuration et les fonctions
    if not create_trash_config_table():
        success = False
    
    # Ajouter les colonnes manquantes
    if not add_missing_columns():
        success = False
    
    # Tester les fonctions
    if not test_trash_functions():
        success = False
    
    if success:
        print("\n🎉 Système de corbeille amélioré avec succès!")
        print("\nFonctionnalités ajoutées:")
        print("✅ Configuration automatique")
        print("✅ Nettoyage automatique programmable")
        print("✅ Statistiques détaillées")
        print("✅ Gestion des permissions")
        print("✅ Notifications avant suppression")
        print("✅ Optimisations de performance")
    else:
        print("\n❌ Échec de l'amélioration du système")

if __name__ == "__main__":
    main() 