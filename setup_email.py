#!/usr/bin/env python3
"""
Script de configuration et test du système d'email ESAG GED
"""

import os
import sys
import logging
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_email_tables():
    """Crée les tables nécessaires pour le système d'email"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Table de configuration email
        logger.info("Création de la table email_config...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_config (
                id SERIAL PRIMARY KEY,
                mail_server VARCHAR(255) NOT NULL,
                mail_port INTEGER NOT NULL DEFAULT 587,
                mail_use_tls BOOLEAN DEFAULT true,
                mail_use_ssl BOOLEAN DEFAULT false,
                mail_username VARCHAR(255) NOT NULL,
                mail_password VARCHAR(255) NOT NULL,
                mail_default_sender VARCHAR(255) NOT NULL,
                mail_max_emails INTEGER DEFAULT 50,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Table des templates d'email
        logger.info("Création de la table email_templates...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                subject VARCHAR(255) NOT NULL,
                html_content TEXT NOT NULL,
                text_content TEXT,
                description TEXT,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Table des logs d'email
        logger.info("Création de la table email_logs...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id SERIAL PRIMARY KEY,
                recipients TEXT NOT NULL,
                subject VARCHAR(255) NOT NULL,
                sender VARCHAR(255),
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'sent'
            );
        """)
        
        # Insérer les templates par défaut
        logger.info("Insertion des templates par défaut...")
        
        # Template de notification de document
        cursor.execute("""
            INSERT INTO email_templates (name, subject, html_content, text_content, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (
            'document_notification',
            'Notification de document - ESAG GED',
            '''
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">ESAG GED - Notification</h2>
                    <p>Bonjour,</p>
                    <p>Un document a été {{ action }} dans le système ESAG GED :</p>
                    <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0;">{{ document_title }}</h3>
                        <p style="margin: 0;"><strong>Type :</strong> {{ document_type }}</p>
                        <p style="margin: 0;"><strong>Date :</strong> {{ date }}</p>
                        {% if description %}
                        <p style="margin: 10px 0 0 0;"><strong>Description :</strong> {{ description }}</p>
                        {% endif %}
                    </div>
                    <p>Vous pouvez consulter ce document en vous connectant à ESAG GED.</p>
                    <p>Cordialement,<br>L'équipe ESAG GED</p>
                </div>
            </body>
            </html>
            ''',
            '''
            ESAG GED - Notification
            
            Bonjour,
            
            Un document a été {{ action }} dans le système ESAG GED :
            
            Titre : {{ document_title }}
            Type : {{ document_type }}
            Date : {{ date }}
            {% if description %}Description : {{ description }}{% endif %}
            
            Vous pouvez consulter ce document en vous connectant à ESAG GED.
            
            Cordialement,
            L'équipe ESAG GED
            ''',
            'Template pour les notifications de documents'
        ))
        
        # Template de bienvenue
        cursor.execute("""
            INSERT INTO email_templates (name, subject, html_content, text_content, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (
            'welcome',
            'Bienvenue sur ESAG GED',
            '''
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Bienvenue sur ESAG GED</h2>
                    <p>Bonjour {{ user_name }},</p>
                    <p>Votre compte a été créé avec succès sur ESAG GED.</p>
                    <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                        <p style="margin: 0;"><strong>Email :</strong> {{ user_email }}</p>
                        <p style="margin: 0;"><strong>Rôle :</strong> {{ user_role }}</p>
                    </div>
                    <p>Vous pouvez maintenant vous connecter et commencer à utiliser le système de gestion électronique de documents.</p>
                    <p>Cordialement,<br>L'équipe ESAG GED</p>
                </div>
            </body>
            </html>
            ''',
            '''
            Bienvenue sur ESAG GED
            
            Bonjour {{ user_name }},
            
            Votre compte a été créé avec succès sur ESAG GED.
            
            Email : {{ user_email }}
            Rôle : {{ user_role }}
            
            Vous pouvez maintenant vous connecter et commencer à utiliser le système de gestion électronique de documents.
            
            Cordialement,
            L'équipe ESAG GED
            ''',
            'Template de bienvenue pour les nouveaux utilisateurs'
        ))
        
        # Template de réinitialisation de mot de passe
        cursor.execute("""
            INSERT INTO email_templates (name, subject, html_content, text_content, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (
            'password_reset',
            'Réinitialisation de votre mot de passe - ESAG GED',
            '''
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Réinitialisation de mot de passe</h2>
                    <p>Bonjour {{ user_name }},</p>
                    <p>Vous avez demandé la réinitialisation de votre mot de passe pour ESAG GED.</p>
                    <div style="background: #fff3cd; color: #856404; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⚠️ Si vous n'avez pas fait cette demande, ignorez cet email.</strong></p>
                    </div>
                    <p>Votre nouveau mot de passe temporaire est :</p>
                    <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0; text-align: center;">
                        <h3 style="margin: 0; font-family: monospace; color: #007bff;">{{ new_password }}</h3>
                    </div>
                    <p><strong>Important :</strong> Veuillez changer ce mot de passe lors de votre prochaine connexion.</p>
                    <p>Cordialement,<br>L'équipe ESAG GED</p>
                </div>
            </body>
            </html>
            ''',
            '''
            Réinitialisation de mot de passe - ESAG GED
            
            Bonjour {{ user_name }},
            
            Vous avez demandé la réinitialisation de votre mot de passe pour ESAG GED.
            
            ⚠️ Si vous n'avez pas fait cette demande, ignorez cet email.
            
            Votre nouveau mot de passe temporaire est : {{ new_password }}
            
            Important : Veuillez changer ce mot de passe lors de votre prochaine connexion.
            
            Cordialement,
            L'équipe ESAG GED
            ''',
            'Template pour la réinitialisation de mot de passe'
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Tables d'email créées avec succès !")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création des tables d'email: {str(e)}")
        return False

def check_email_config():
    """Vérifie la configuration email actuelle"""
    logger.info("Vérification de la configuration email...")
    
    # Variables d'environnement
    env_vars = [
        'MAIL_SERVER',
        'MAIL_PORT', 
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER'
    ]
    
    missing_vars = []
    for var in env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️ Variables d'environnement manquantes: {', '.join(missing_vars)}")
        logger.info("Vous pouvez configurer ces variables dans un fichier .env ou via l'interface web")
    else:
        logger.info("✅ Configuration email trouvée dans les variables d'environnement")
    
    # Configuration en base de données
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT COUNT(*) as count FROM email_config WHERE is_active = true")
        result = cursor.fetchone()
        
        if result and result['count'] > 0:
            logger.info("✅ Configuration email trouvée en base de données")
        else:
            logger.info("ℹ️ Aucune configuration email en base de données")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification de la config en BDD: {str(e)}")

def show_email_setup_guide():
    """Affiche le guide de configuration email"""
    print("\n" + "="*60)
    print("📧 GUIDE DE CONFIGURATION EMAIL ESAG GED")
    print("="*60)
    print()
    print("1. CONFIGURATION VIA VARIABLES D'ENVIRONNEMENT:")
    print("   Créez un fichier .env avec les variables suivantes:")
    print()
    print("   # Gmail")
    print("   MAIL_SERVER=smtp.gmail.com")
    print("   MAIL_PORT=587")
    print("   MAIL_USE_TLS=True")
    print("   MAIL_USERNAME=votre.email@gmail.com")
    print("   MAIL_PASSWORD=votre_mot_de_passe_application")
    print("   MAIL_DEFAULT_SENDER=noreply@esag.com")
    print()
    print("   # Outlook")
    print("   MAIL_SERVER=smtp-mail.outlook.com")
    print("   MAIL_PORT=587")
    print("   MAIL_USE_TLS=True")
    print("   MAIL_USERNAME=votre.email@outlook.com")
    print("   MAIL_PASSWORD=votre_mot_de_passe")
    print("   MAIL_DEFAULT_SENDER=noreply@esag.com")
    print()
    print("2. CONFIGURATION VIA INTERFACE WEB:")
    print("   - Connectez-vous en tant qu'administrateur")
    print("   - Allez dans Paramètres > Configuration Email")
    print("   - Remplissez les champs de configuration SMTP")
    print("   - Testez la connexion")
    print("   - Envoyez un email de test")
    print()
    print("3. NOTES IMPORTANTES:")
    print("   - Pour Gmail, utilisez un mot de passe d'application")
    print("   - Activez l'authentification à 2 facteurs")
    print("   - Vérifiez les paramètres de sécurité de votre compte")
    print()
    print("="*60)

def main():
    """Fonction principale"""
    print("🚀 Configuration du système d'email ESAG GED")
    print()
    
    # Créer les tables
    if create_email_tables():
        print("✅ Tables d'email configurées")
    else:
        print("❌ Erreur lors de la configuration des tables")
        sys.exit(1)
    
    # Vérifier la configuration
    check_email_config()
    
    # Afficher le guide
    show_email_setup_guide()
    
    print("\n🎉 Configuration terminée !")
    print("Vous pouvez maintenant configurer les emails via l'interface web ou les variables d'environnement.")

if __name__ == "__main__":
    main() 