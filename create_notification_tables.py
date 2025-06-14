#!/usr/bin/env python3
"""
Création des tables pour le système de notifications ESAG GED
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def create_notification_tables():
    """Créer toutes les tables nécessaires pour le système de notifications"""
    print("🔔 CRÉATION DES TABLES DE NOTIFICATIONS")
    print("=" * 50)
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor()
        
        # 1. Table des notifications principales
        print("📋 Création de la table 'notifications'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(50) NOT NULL DEFAULT 'info',
                document_id INTEGER REFERENCES document(id) ON DELETE SET NULL,
                workflow_id INTEGER DEFAULT NULL,
                created_by_id INTEGER REFERENCES utilisateur(id) ON DELETE SET NULL,
                is_read BOOLEAN DEFAULT FALSE,
                read_at TIMESTAMP DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                priority INTEGER DEFAULT 1,
                expires_at TIMESTAMP DEFAULT NULL
            );
        """)
        
        # Index pour optimiser les requêtes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
            CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
            CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
            CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
            CREATE INDEX IF NOT EXISTS idx_notifications_document_id ON notifications(document_id);
        """)
        
        # 2. Table des préférences de notification par utilisateur
        print("⚙️ Création de la table 'user_notification_preferences'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_notification_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES utilisateur(id) ON DELETE CASCADE,
                email_notifications BOOLEAN DEFAULT TRUE,
                app_notifications BOOLEAN DEFAULT TRUE,
                document_notifications BOOLEAN DEFAULT TRUE,
                workflow_notifications BOOLEAN DEFAULT TRUE,
                comment_notifications BOOLEAN DEFAULT TRUE,
                share_notifications BOOLEAN DEFAULT TRUE,
                mention_notifications BOOLEAN DEFAULT TRUE,
                digest_frequency VARCHAR(20) DEFAULT 'daily',
                quiet_hours_start TIME DEFAULT '22:00',
                quiet_hours_end TIME DEFAULT '08:00',
                weekend_notifications BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 3. Table des abonnements aux documents
        print("📄 Création de la table 'document_subscriptions'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
                document_id INTEGER NOT NULL REFERENCES document(id) ON DELETE CASCADE,
                notification_types TEXT[] DEFAULT ARRAY['all'],
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, document_id)
            );
        """)
        
        # 4. Table des abonnements aux dossiers
        print("📁 Création de la table 'folder_subscriptions'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folder_subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
                folder_id INTEGER NOT NULL,
                notification_types TEXT[] DEFAULT ARRAY['all'],
                is_active BOOLEAN DEFAULT TRUE,
                include_subdirectories BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, folder_id)
            );
        """)
        
        # 5. Table des logs de notifications (pour audit)
        print("📊 Création de la table 'notification_logs'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id SERIAL PRIMARY KEY,
                notification_id INTEGER REFERENCES notifications(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
                action VARCHAR(50) NOT NULL,
                channel VARCHAR(20) NOT NULL,
                status VARCHAR(20) NOT NULL,
                error_message TEXT DEFAULT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'
            );
        """)
        
        # 6. Table des templates de notifications
        print("📝 Création de la table 'notification_templates'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                title_template VARCHAR(255) NOT NULL,
                message_template TEXT NOT NULL,
                email_template TEXT DEFAULT NULL,
                type VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                variables TEXT[] DEFAULT ARRAY[]::TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 7. Table des mentions (@utilisateur)
        print("👤 Création de la table 'notification_mentions'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_mentions (
                id SERIAL PRIMARY KEY,
                notification_id INTEGER NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
                mentioned_user_id INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
                mentioned_by_user_id INTEGER NOT NULL REFERENCES utilisateur(id) ON DELETE CASCADE,
                context_type VARCHAR(50) NOT NULL,
                context_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        print("✅ Toutes les tables de notifications créées avec succès!")
        
        # Insérer les préférences par défaut pour les utilisateurs existants
        print("\n👥 Création des préférences par défaut...")
        cursor.execute("""
            INSERT INTO user_notification_preferences (user_id)
            SELECT u.id 
            FROM utilisateur u
            WHERE NOT EXISTS (
                SELECT 1 FROM user_notification_preferences p 
                WHERE p.user_id = u.id
            )
        """)
        
        preferences_created = cursor.rowcount
        print(f"✅ {preferences_created} préférences par défaut créées")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return False

def insert_default_templates():
    """Insérer les templates de notifications par défaut"""
    print("\n📝 INSERTION DES TEMPLATES PAR DÉFAUT")
    print("=" * 40)
    
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        templates = [
            {
                'name': 'document_uploaded',
                'title': 'Nouveau document ajouté',
                'message': 'Le document "{{document_title}}" a été ajouté par {{uploader_name}}',
                'type': 'document',
                'variables': ['document_title', 'uploader_name', 'document_type', 'upload_date']
            },
            {
                'name': 'document_updated',
                'title': 'Document modifié',
                'message': 'Le document "{{document_title}}" a été modifié par {{modifier_name}}',
                'type': 'document',
                'variables': ['document_title', 'modifier_name', 'modification_date']
            },
            {
                'name': 'document_shared',
                'title': 'Document partagé avec vous',
                'message': '{{sharer_name}} a partagé le document "{{document_title}}" avec vous',
                'type': 'share',
                'variables': ['document_title', 'sharer_name', 'share_date']
            },
            {
                'name': 'document_commented',
                'title': 'Nouveau commentaire',
                'message': '{{commenter_name}} a commenté le document "{{document_title}}"',
                'type': 'comment',
                'variables': ['document_title', 'commenter_name', 'comment_text', 'comment_date']
            },
            {
                'name': 'workflow_assigned',
                'title': 'Nouvelle tâche assignée',
                'message': 'Une nouvelle tâche "{{workflow_title}}" vous a été assignée par {{assigner_name}}',
                'type': 'workflow',
                'variables': ['workflow_title', 'assigner_name', 'due_date', 'priority']
            },
            {
                'name': 'user_mentioned',
                'title': 'Vous avez été mentionné',
                'message': '{{mentioner_name}} vous a mentionné dans {{context_type}} "{{context_title}}"',
                'type': 'mention',
                'variables': ['mentioner_name', 'context_type', 'context_title', 'mention_date']
            },
            {
                'name': 'system_maintenance',
                'title': 'Maintenance système',
                'message': 'Maintenance programmée le {{maintenance_date}} de {{start_time}} à {{end_time}}',
                'type': 'system',
                'variables': ['maintenance_date', 'start_time', 'end_time', 'description']
            }
        ]
        
        for template in templates:
            cursor.execute("""
                INSERT INTO notification_templates 
                (name, title_template, message_template, type, variables)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    title_template = EXCLUDED.title_template,
                    message_template = EXCLUDED.message_template,
                    type = EXCLUDED.type,
                    variables = EXCLUDED.variables,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                template['name'],
                template['title'],
                template['message'],
                template['type'],
                template['variables']
            ))
        
        conn.commit()
        print(f"✅ {len(templates)} templates de notifications insérés")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur insertion templates: {str(e)}")
        return False

def create_notification_functions():
    """Créer les fonctions PostgreSQL pour les notifications"""
    print("\n⚙️ CRÉATION DES FONCTIONS POSTGRESQL")
    print("=" * 40)
    
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        # Fonction pour nettoyer les anciennes notifications
        cursor.execute("""
            CREATE OR REPLACE FUNCTION cleanup_old_notifications()
            RETURNS INTEGER AS $$
            DECLARE
                deleted_count INTEGER;
            BEGIN
                DELETE FROM notifications 
                WHERE created_at < NOW() - INTERVAL '90 days'
                AND is_read = TRUE;
                
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                RETURN deleted_count;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Fonction pour marquer automatiquement comme lues les notifications expirées
        cursor.execute("""
            CREATE OR REPLACE FUNCTION mark_expired_notifications()
            RETURNS INTEGER AS $$
            DECLARE
                updated_count INTEGER;
            BEGIN
                UPDATE notifications 
                SET is_read = TRUE, read_at = NOW()
                WHERE expires_at IS NOT NULL 
                AND expires_at < NOW() 
                AND is_read = FALSE;
                
                GET DIAGNOSTICS updated_count = ROW_COUNT;
                RETURN updated_count;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Trigger pour mettre à jour updated_at
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_notification_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Appliquer le trigger
        cursor.execute("""
            DROP TRIGGER IF EXISTS trigger_update_notification_timestamp ON notifications;
            CREATE TRIGGER trigger_update_notification_timestamp
                BEFORE UPDATE ON notifications
                FOR EACH ROW
                EXECUTE FUNCTION update_notification_timestamp();
        """)
        
        conn.commit()
        print("✅ Fonctions PostgreSQL créées")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création fonctions: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🔔 CONFIGURATION COMPLÈTE DU SYSTÈME DE NOTIFICATIONS")
    print("=" * 60)
    
    steps = [
        ("Création des tables", create_notification_tables),
        ("Templates par défaut", insert_default_templates),
        ("Fonctions PostgreSQL", create_notification_functions)
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"❌ Erreur dans {step_name}: {str(e)}")
            results.append((step_name, False))
    
    # Résumé
    print("\n🎯 RÉSUMÉ DE LA CONFIGURATION")
    print("=" * 40)
    
    success_count = 0
    for step_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{step_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n📊 RÉSULTAT: {success_count}/{len(results)} étapes réussies")
    
    if success_count == len(results):
        print("\n🎉 SYSTÈME DE NOTIFICATIONS CONFIGURÉ AVEC SUCCÈS!")
        print("\n🚀 FONCTIONNALITÉS DISPONIBLES:")
        print("✅ Notifications en temps réel dans l'application")
        print("✅ Notifications par email automatiques")
        print("✅ Abonnements aux documents et dossiers")
        print("✅ Préférences utilisateur personnalisables")
        print("✅ Mentions d'utilisateurs (@utilisateur)")
        print("✅ Templates de notifications personnalisés")
        print("✅ Logs et audit des notifications")
        print("✅ Nettoyage automatique des anciennes notifications")
        
        print("\n📋 PROCHAINES ÉTAPES:")
        print("1. Redémarrez le serveur Flask")
        print("2. Testez les notifications dans l'interface")
        print("3. Configurez les préférences utilisateur")
        print("4. Testez les notifications par email")
    else:
        print("\n⚠️ CONFIGURATION INCOMPLÈTE")
        print("Vérifiez les erreurs ci-dessus et relancez le script")
    
    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 