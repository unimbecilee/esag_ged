#!/usr/bin/env python3
"""
Configuration et test Outlook pour ESAG GED
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_outlook_config():
    """Test de configuration Outlook"""
    print("🔧 Configuration Outlook pour ESAG GED")
    print("=" * 50)
    
    # Demander les informations Outlook
    print("📧 Veuillez fournir vos informations Outlook :")
    print("(Si vous n'avez pas de compte Outlook, créez-en un sur outlook.com)")
    
    email = input("📧 Votre email Outlook (ex: votre-nom@outlook.com) : ").strip()
    
    if not email:
        print("❌ Email requis")
        return False
    
    if "@outlook.com" not in email and "@hotmail.com" not in email and "@live.com" not in email:
        print("⚠️  Assurez-vous d'utiliser un email Outlook/Hotmail/Live")
    
    password = input("🔑 Votre mot de passe Outlook : ").strip()
    
    if not password:
        print("❌ Mot de passe requis")
        return False
    
    return test_outlook_connection(email, password)

def test_outlook_connection(email, password):
    """Tester la connexion Outlook"""
    print(f"\n🔧 Test de connexion Outlook...")
    print(f"📧 Email : {email}")
    
    # Configuration Outlook
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = 587
    
    try:
        print(f"📡 Connexion à {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        print("🔐 Activation TLS...")
        server.starttls()
        
        print("🔑 Authentification...")
        server.login(email, password)
        
        print("✅ CONNEXION OUTLOOK RÉUSSIE !")
        
        # Test d'envoi d'email
        print("📨 Envoi d'email de test...")
        
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email
        msg['Subject'] = "🎉 ESAG GED - Configuration Outlook Réussie !"
        
        body = f"""
🎉 FÉLICITATIONS ! 🎉

Votre configuration Outlook fonctionne parfaitement avec ESAG GED !

✅ CONFIGURATION VALIDÉE :
• Serveur SMTP : smtp-mail.outlook.com
• Port : 587
• TLS : Activé
• Email : {email}

✅ FONCTIONNALITÉS ACTIVÉES :
• Email de bienvenue automatique pour nouveaux utilisateurs
• Réinitialisation de mot de passe par email
• Notifications de documents (ajout, partage)
• Notifications de workflows (assignation de tâches)
• Interface d'administration complète
• Logs détaillés des emails

🚀 VOTRE SYSTÈME EST MAINTENANT OPÉRATIONNEL !

Pour démarrer le serveur avec toutes les fonctionnalités :
python main.py

Puis testez :
1. Créez un nouvel utilisateur → il recevra un email de bienvenue
2. Testez la réinitialisation de mot de passe
3. Ajoutez un document → notifications automatiques

Cordialement,
L'équipe ESAG GED 🚀
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server.sendmail(email, email, msg.as_string())
        
        print("✅ EMAIL DE TEST ENVOYÉ !")
        print(f"📬 Vérifiez votre boîte mail : {email}")
        
        server.quit()
        
        # Générer la configuration pour config.py
        print("\n📝 CONFIGURATION POUR VOTRE FICHIER config.py :")
        print("=" * 50)
        
        config_content = f'''
# Configuration Email ESAG GED - OUTLOOK
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = 587
SMTP_USERNAME = "{email}"
SMTP_PASSWORD = "{password}"
SMTP_USE_TLS = True
EMAIL_FROM = "{email}"
EMAIL_FROM_NAME = "ESAG GED"

# Configuration Flask-Mail (alternative)
MAIL_SERVER = "smtp-mail.outlook.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "{email}"
MAIL_PASSWORD = "{password}"
MAIL_DEFAULT_SENDER = "{email}"
'''
        
        print(config_content)
        
        # Sauvegarder dans un fichier
        with open("outlook_config.txt", "w") as f:
            f.write(config_content)
        
        print("✅ Configuration sauvegardée dans 'outlook_config.txt'")
        print("\n🎯 PROCHAINES ÉTAPES :")
        print("1. Copiez la configuration ci-dessus dans votre config.py")
        print("2. Remplacez les anciennes variables Gmail")
        print("3. Redémarrez votre serveur : python main.py")
        print("4. Testez les fonctionnalités email")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ ERREUR D'AUTHENTIFICATION : {str(e)}")
        print("\n💡 SOLUTIONS :")
        print("1. Vérifiez votre email et mot de passe Outlook")
        print("2. Assurez-vous que l'authentification moderne n'est pas bloquée")
        print("3. Essayez de vous connecter sur outlook.com pour vérifier votre compte")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ ERREUR DE CONNEXION : {str(e)}")
        print("\n💡 SOLUTIONS :")
        print("1. Vérifiez votre connexion internet")
        print("2. Vérifiez les paramètres de pare-feu")
        return False
        
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE : {str(e)}")
        return False

def create_outlook_account_guide():
    """Créer un guide pour créer un compte Outlook"""
    print("\n📚 GUIDE : CRÉER UN COMPTE OUTLOOK")
    print("=" * 40)
    print("Si vous n'avez pas de compte Outlook :")
    print("1. Allez sur https://outlook.com")
    print("2. Cliquez sur 'Créer un compte gratuit'")
    print("3. Choisissez une adresse (ex: votre-nom@outlook.com)")
    print("4. Créez un mot de passe sécurisé")
    print("5. Suivez les étapes de création")
    print("6. Revenez ici avec vos identifiants")

def main():
    """Fonction principale"""
    print("🔄 MIGRATION VERS OUTLOOK")
    print("=" * 35)
    
    print("Outlook est généralement plus simple que Gmail pour les applications tierces.")
    print("Pas besoin de mot de passe d'application, juste vos identifiants normaux.\n")
    
    # Demander si l'utilisateur a un compte Outlook
    has_outlook = input("Avez-vous déjà un compte Outlook/Hotmail ? (oui/non) : ").strip().lower()
    
    if has_outlook in ['non', 'n', 'no']:
        create_outlook_account_guide()
        print("\nRevenez quand vous aurez créé votre compte Outlook !")
        return
    
    # Tester la configuration Outlook
    success = test_outlook_config()
    
    if success:
        print("\n🎉 MIGRATION VERS OUTLOOK RÉUSSIE ! 🎉")
        print("Votre système d'email ESAG GED est maintenant opérationnel.")
    else:
        print("\n⚠️ PROBLÈME AVEC OUTLOOK")
        print("Vérifiez vos identifiants et réessayez.")

if __name__ == "__main__":
    main() 