#!/usr/bin/env python3
"""
Correction des fonctions de la corbeille
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def fix_trash_functions():
    """Corriger les fonctions de la corbeille"""
    print("🔧 CORRECTION DES FONCTIONS DE LA CORBEILLE")
    print("=" * 45)
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor()
        
        # Fonction corrigée pour nettoyer automatiquement la corbeille
        print("🧹 Correction de la fonction cleanup_trash()...")
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
                
                -- Log de l'opération (vérifier si la table system_logs existe)
                IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'system_logs') THEN
                    INSERT INTO system_logs (timestamp, level, event_type, message, additional_data)
                    VALUES (
                        CURRENT_TIMESTAMP, 
                        'INFO', 
                        'TRASH_CLEANUP', 
                        'Nettoyage automatique de la corbeille',
                        json_build_object('deleted_count', deleted_count, 'retention_days', retention_days)
                    );
                END IF;
                
                RETURN deleted_count;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Fonction corrigée pour obtenir les statistiques de la corbeille
        print("📊 Correction de la fonction get_trash_stats()...")
        cursor.execute("""
            CREATE OR REPLACE FUNCTION get_trash_stats(user_id_param INTEGER DEFAULT NULL)
            RETURNS JSON AS $$
            DECLARE
                result JSON;
                total_count INTEGER;
                pending_count INTEGER;
                restored_count INTEGER;
                deleted_count INTEGER;
                oldest_date TIMESTAMP;
                newest_date TIMESTAMP;
            BEGIN
                -- Compter les éléments selon les critères
                SELECT 
                    COUNT(*),
                    COUNT(*) FILTER (WHERE restored_at IS NULL AND permanent_delete_at IS NULL),
                    COUNT(*) FILTER (WHERE restored_at IS NOT NULL),
                    COUNT(*) FILTER (WHERE permanent_delete_at IS NOT NULL),
                    MIN(deleted_at),
                    MAX(deleted_at)
                INTO total_count, pending_count, restored_count, deleted_count, oldest_date, newest_date
                FROM trash 
                WHERE (user_id_param IS NULL OR deleted_by = user_id_param);
                
                -- Construire le résultat JSON
                SELECT json_build_object(
                    'total_items', total_count,
                    'pending_deletion', pending_count,
                    'restored_items', restored_count,
                    'permanently_deleted', deleted_count,
                    'oldest_item', oldest_date,
                    'newest_item', newest_date
                ) INTO result;
                
                RETURN result;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Fonction pour obtenir les éléments expirant bientôt
        print("⏰ Création de la fonction get_expiring_items()...")
        cursor.execute("""
            CREATE OR REPLACE FUNCTION get_expiring_items(days_before INTEGER DEFAULT 7)
            RETURNS TABLE(
                item_id INTEGER,
                item_type VARCHAR,
                item_data JSONB,
                deleted_by INTEGER,
                deleted_at TIMESTAMP,
                expires_in_days INTEGER
            ) AS $$
            DECLARE
                retention_days INTEGER;
            BEGIN
                -- Récupérer la configuration de rétention
                SELECT setting_value::INTEGER INTO retention_days 
                FROM trash_config WHERE setting_name = 'retention_days';
                
                RETURN QUERY
                SELECT 
                    t.item_id,
                    t.item_type,
                    t.item_data,
                    t.deleted_by,
                    t.deleted_at,
                    (retention_days - EXTRACT(DAY FROM (CURRENT_TIMESTAMP - t.deleted_at)))::INTEGER as expires_in_days
                FROM trash t
                WHERE t.restored_at IS NULL 
                AND t.permanent_delete_at IS NULL
                AND t.deleted_at < (CURRENT_TIMESTAMP - INTERVAL '1 day' * (retention_days - days_before))
                AND t.deleted_at >= (CURRENT_TIMESTAMP - INTERVAL '1 day' * retention_days)
                ORDER BY t.deleted_at ASC;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Fonction pour calculer la taille totale de la corbeille
        print("📏 Création de la fonction get_trash_size()...")
        cursor.execute("""
            CREATE OR REPLACE FUNCTION get_trash_size(user_id_param INTEGER DEFAULT NULL)
            RETURNS BIGINT AS $$
            DECLARE
                total_size BIGINT := 0;
            BEGIN
                SELECT COALESCE(SUM(size_bytes), 0) INTO total_size
                FROM trash 
                WHERE (user_id_param IS NULL OR deleted_by = user_id_param)
                AND restored_at IS NULL 
                AND permanent_delete_at IS NULL;
                
                RETURN total_size;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Fonctions de la corbeille corrigées avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def test_corrected_functions():
    """Tester les fonctions corrigées"""
    print("\n🧪 TEST DES FONCTIONS CORRIGÉES")
    print("=" * 35)
    
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test de la fonction de statistiques
        print("📊 Test de get_trash_stats()...")
        cursor.execute("SELECT get_trash_stats() as stats")
        stats = cursor.fetchone()['stats']
        print(f"   ✅ Statistiques: {stats}")
        
        # Test de la fonction de nettoyage
        print("🧹 Test de cleanup_trash()...")
        cursor.execute("SELECT cleanup_trash() as deleted_count")
        deleted_count = cursor.fetchone()['deleted_count']
        print(f"   ✅ Éléments supprimés: {deleted_count}")
        
        # Test de la fonction des éléments expirant
        print("⏰ Test de get_expiring_items()...")
        cursor.execute("SELECT * FROM get_expiring_items(7)")
        expiring = cursor.fetchall()
        print(f"   ✅ Éléments expirant dans 7 jours: {len(expiring)}")
        
        # Test de la fonction de taille
        print("📏 Test de get_trash_size()...")
        cursor.execute("SELECT get_trash_size() as total_size")
        total_size = cursor.fetchone()['total_size']
        print(f"   ✅ Taille totale de la corbeille: {total_size} bytes")
        
        cursor.close()
        conn.close()
        
        print("✅ Tous les tests réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        if 'conn' in locals():
            cursor.close()
            conn.close()
        return False

def main():
    """Fonction principale"""
    success = True
    
    if not fix_trash_functions():
        success = False
    
    if not test_corrected_functions():
        success = False
    
    if success:
        print("\n🎉 Fonctions de la corbeille corrigées et testées avec succès!")
    else:
        print("\n❌ Échec de la correction des fonctions")

if __name__ == "__main__":
    main() 