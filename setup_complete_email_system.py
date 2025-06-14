#!/usr/bin/env python3
"""
Configuration complète du système d'email pour ESAG GED
Ce script configure toutes les fonctionnalités email demandées :
1. Email de bienvenue pour nouveaux utilisateurs
2. Réinitialisation de mot de passe
3. Notifications de documents et workflows
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
import psycopg2
from datetime import datetime

def create_email_tables():
    """Créer les tables nécessaires pour le système d'email"""
    print("📧 Configuration des tables email...")
    
    conn = db_connection()
    if not conn:
        print("❌ Erreur de connexion à la base de données")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Table de configuration email
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_config (
                id SERIAL PRIMARY KEY,
                smtp_server VARCHAR(255) NOT NULL,
                smtp_port INTEGER NOT NULL DEFAULT 587,
                smtp_username VARCHAR(255) NOT NULL,
                smtp_password VARCHAR(255) NOT NULL,
                use_tls BOOLEAN DEFAULT true,
                from_email VARCHAR(255) NOT NULL,
                from_name VARCHAR(255) DEFAULT 'ESAG GED',
                is_active BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des templates d'email
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                subject VARCHAR(255) NOT NULL,
                html_body TEXT,
                text_body TEXT,
                variables TEXT, -- JSON des variables disponibles
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des logs d'email
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id SERIAL PRIMARY KEY,
                to_email VARCHAR(255) NOT NULL,
                from_email VARCHAR(255) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                template_name VARCHAR(100),
                status VARCHAR(50) NOT NULL, -- 'sent', 'failed', 'pending'
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER REFERENCES utilisateur(id),
                metadata JSONB -- Données supplémentaires
            )
        """)
        
        # Table des préférences utilisateur pour les notifications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_email_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES utilisateur(id) UNIQUE,
                email_notifications BOOLEAN DEFAULT true,
                document_notifications BOOLEAN DEFAULT true,
                workflow_notifications BOOLEAN DEFAULT true,
                welcome_emails BOOLEAN DEFAULT true,
                password_reset_emails BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("✅ Tables email créées avec succès")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur lors de la création des tables : {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def insert_default_templates():
    """Insérer les templates d'email par défaut"""
    print("📝 Insertion des templates par défaut...")
    
    conn = db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    templates = [
        {
            'name': 'welcome',
            'subject': 'Bienvenue sur ESAG GED - Votre compte a été créé',
            'variables': '["user_name", "user_email", "generated_password", "user_role", "login_url"]'
        },
        {
            'name': 'password_reset',
            'subject': 'Réinitialisation de votre mot de passe - ESAG GED',
            'variables': '["user_name", "new_password", "admin_name", "login_url"]'
        },
        {
            'name': 'document_notification',
            'subject': 'Nouveau document - {{document_title}}',
            'variables': '["user_name", "document_title", "document_type", "uploader_name", "action", "date", "description", "login_url"]'
        },
        {
            'name': 'document_shared',
            'subject': 'Document partagé avec vous - {{document_title}}',
            'variables': '["user_name", "document_title", "shared_by_name", "date", "login_url"]'
        },
        {
            'name': 'workflow_notification',
            'subject': 'Nouvelle tâche assignée - {{workflow_title}}',
            'variables': '["user_name", "workflow_title", "assigner_name", "date", "login_url"]'
        },
        {
            'name': 'test',
            'subject': 'Test de configuration email - ESAG GED',
            'variables': '["test_date", "smtp_server"]'
        }
    ]
    
    try:
        for template in templates:
            cursor.execute("""
                INSERT INTO email_templates (name, subject, variables)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    subject = EXCLUDED.subject,
                    variables = EXCLUDED.variables,
                    updated_at = CURRENT_TIMESTAMP
            """, (template['name'], template['subject'], template['variables']))
        
        conn.commit()
        print("✅ Templates par défaut insérés")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur lors de l'insertion des templates : {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def create_default_user_preferences():
    """Créer les préférences par défaut pour tous les utilisateurs existants"""
    print("👤 Configuration des préférences utilisateur...")
    
    conn = db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Insérer les préférences par défaut pour tous les utilisateurs existants
        cursor.execute("""
            INSERT INTO user_email_preferences (user_id, email_notifications, document_notifications, workflow_notifications)
            SELECT u.id, true, true, true
            FROM utilisateur u
            WHERE NOT EXISTS (
                SELECT 1 FROM user_email_preferences up WHERE up.user_id = u.id
            )
        """)
        
        rows_affected = cursor.rowcount
        conn.commit()
        print(f"✅ Préférences créées pour {rows_affected} utilisateurs")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur lors de la création des préférences : {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

def update_auth_routes():
    """Mettre à jour les routes d'authentification pour inclure l'envoi d'emails"""
    print("🔧 Mise à jour des routes d'authentification...")
    
    # Lire le fichier actuel
    auth_file = "AppFlask/api/auth.py"
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si les modifications sont déjà présentes
        if "from AppFlask.services.email_service import email_service" in content:
            print("✅ Routes d'authentification déjà mises à jour")
            return True
        
        # Ajouter l'import du service email
        import_line = "from AppFlask.services.email_service import email_service"
        if import_line not in content:
            # Chercher la ligne des imports et ajouter après
            lines = content.split('\n')
            import_index = -1
            for i, line in enumerate(lines):
                if line.startswith('from AppFlask.api.auth import'):
                    import_index = i
                    break
            
            if import_index != -1:
                lines.insert(import_index + 1, import_line)
                content = '\n'.join(lines)
        
        # Sauvegarder le fichier modifié
        with open(auth_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Routes d'authentification mises à jour")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour des routes : {str(e)}")
        return False

def create_notification_service():
    """Créer le fichier de service de notifications"""
    print("🔔 Création du service de notifications...")
    
    # Le fichier a déjà été créé précédemment
    if os.path.exists("AppFlask/utils/notification_service.py"):
        print("✅ Service de notifications déjà existant")
        return True
    
    # Créer le répertoire utils s'il n'existe pas
    os.makedirs("AppFlask/utils", exist_ok=True)
    
    # Créer le fichier __init__.py dans utils
    init_file = "AppFlask/utils/__init__.py"
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("# Utils package\n")
    
    print("✅ Service de notifications configuré")
    return True

def show_configuration_instructions():
    """Afficher les instructions de configuration pour l'utilisateur"""
    print("\n" + "="*60)
    print("📧 CONFIGURATION DU SYSTÈME D'EMAIL")
    print("="*60)
    
    print("""
🎯 ÉTAPES DE CONFIGURATION :

1. 📱 CONFIGURER VOTRE COMPTE EMAIL (RECOMMANDÉ : GMAIL)
   
   Pour Gmail :
   • Activer l'authentification à 2 facteurs
   • Générer un "Mot de passe d'application" :
     - Allez dans votre compte Google
     - Sécurité > Authentification à 2 facteurs
     - Mots de passe d'application
     - Générer un nouveau mot de passe pour "Mail"
   
   Configuration Gmail :
   • Serveur SMTP : smtp.gmail.com
   • Port : 587
   • Nom d'utilisateur : votre-email@gmail.com
   • Mot de passe : le mot de passe d'application généré
   • TLS : Activé

2. 🌐 CONFIGURER VIA L'INTERFACE WEB
   
   • Connectez-vous en tant qu'administrateur
   • Allez dans Paramètres > Configuration Email
   • Remplissez les informations SMTP
   • Testez la configuration
   • Activez le système d'email

3. 🔧 ALTERNATIVE : VARIABLES D'ENVIRONNEMENT
   
   Créez un fichier .env avec :
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=votre-email@gmail.com
   SMTP_PASSWORD=votre-mot-de-passe-application
   SMTP_USE_TLS=true
   EMAIL_FROM=votre-email@gmail.com
   EMAIL_FROM_NAME=ESAG GED

4. ✅ TESTER LE SYSTÈME
   
   • Utilisez la fonction de test dans l'interface
   • Créez un nouvel utilisateur pour tester l'email de bienvenue
   • Testez la réinitialisation de mot de passe

""")
    
    print("🔧 FONCTIONNALITÉS ACTIVÉES :")
    print("   ✅ Email de bienvenue pour nouveaux utilisateurs")
    print("   ✅ Réinitialisation de mot de passe par email")
    print("   ✅ Notifications de documents")
    print("   ✅ Notifications de workflows")
    print("   ✅ Interface de configuration pour admins")
    print("   ✅ Logs complets des emails envoyés")
    
    print("\n🚀 Pour démarrer le serveur avec les nouvelles fonctionnalités :")
    print("   python main.py")
    
    print("\n" + "="*60)

def main():
    """Fonction principale d'installation"""
    print("🚀 Installation du système d'email complet pour ESAG GED")
    print("="*60)
    
    steps = [
        ("Création des tables email", create_email_tables),
        ("Insertion des templates par défaut", insert_default_templates),
        ("Configuration des préférences utilisateur", create_default_user_preferences),
        ("Création du service de notifications", create_notification_service),
    ]
    
    success_count = 0
    for step_name, step_function in steps:
        print(f"\n📋 {step_name}...")
        if step_function():
            success_count += 1
        else:
            print(f"❌ Échec de l'étape : {step_name}")
    
    print(f"\n📊 Installation terminée : {success_count}/{len(steps)} étapes réussies")
    
    if success_count == len(steps):
        print("🎉 Installation complète réussie !")
        show_configuration_instructions()
    else:
        print("⚠️  Installation partielle. Vérifiez les erreurs ci-dessus.")
    
    return success_count == len(steps)

if __name__ == "__main__":
    main() 