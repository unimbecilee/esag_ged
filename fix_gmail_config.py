#!/usr/bin/env python3
"""
Script pour corriger et tester la configuration Gmail
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_fixed():
    """Test Gmail avec mot de passe d'application corrigé"""
    print("🔧 Test Gmail avec mot de passe d'application corrigé...")
    
    # Configuration corrigée
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = "mainuser1006@gmail.com"
    # Mot de passe d'application SANS espaces
    password = "eidtjvuksaxgxfwa"  # Retiré les espaces
    
    try:
        print(f"📡 Connexion à {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        print("🔐 Activation TLS...")
        server.starttls()
        
        print("🔑 Authentification...")
        server.login(username, password)
        
        print("✅ Connexion SMTP réussie !")
        
        # Test d'envoi d'email
        print("📨 Envoi d'email de test...")
        
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username
        msg['Subject'] = "✅ ESAG GED - Configuration Gmail Réussie"
        
        body = """
🎉 FÉLICITATIONS ! 🎉

Votre configuration Gmail fonctionne parfaitement avec ESAG GED !

✅ Fonctionnalités activées :
• Email de bienvenue pour nouveaux utilisateurs
• Réinitialisation de mot de passe par email
• Notifications de documents (ajout, partage)
• Notifications de workflows (assignation de tâches)

🚀 Votre système est maintenant prêt à être utilisé !

Pour démarrer le serveur :
python main.py

Cordialement,
L'équipe ESAG GED
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server.sendmail(username, username, msg.as_string())
        
        print("✅ Email de test envoyé avec succès !")
        print(f"📬 Vérifiez votre boîte mail : {username}")
        
        server.quit()
        
        print("\n🎯 MISE À JOUR NÉCESSAIRE :")
        print("Dans votre fichier config.py, corrigez :")
        print("SMTP_PASSWORD='eidtjvuksaxgxfwa'  # SANS espaces")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Erreur d'authentification : {str(e)}")
        print("\n🔧 Actions à effectuer :")
        print("1. Vérifiez que l'authentification à 2 facteurs est activée sur Gmail")
        print("2. Générez un nouveau mot de passe d'application :")
        print("   - Allez sur https://myaccount.google.com/security")
        print("   - Authentification à 2 facteurs > Mots de passe d'application")
        print("   - Créez un nouveau mot de passe pour 'Mail'")
        print("3. Utilisez le nouveau mot de passe SANS espaces")
        return False
        
    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
        return False

def create_corrected_config():
    """Créer un fichier de configuration email corrigé"""
    print("📝 Création du fichier de configuration email corrigé...")
    
    config_content = '''
# Configuration Email ESAG GED - CORRIGÉE
# Ajoutez ces lignes à votre config.py

# Configuration SMTP Gmail
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "mainuser1006@gmail.com"
SMTP_PASSWORD = "eidtjvuksaxgxfwa"  # SANS espaces !
SMTP_USE_TLS = True
EMAIL_FROM = "mainuser1006@gmail.com"
EMAIL_FROM_NAME = "ESAG GED"

# Configuration Flask-Mail (alternative)
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "mainuser1006@gmail.com"
MAIL_PASSWORD = "eidtjvuksaxgxfwa"  # SANS espaces !
MAIL_DEFAULT_SENDER = "mainuser1006@gmail.com"
'''
    
    with open("email_config_corrected.txt", "w") as f:
        f.write(config_content)
    
    print("✅ Configuration corrigée sauvegardée dans 'email_config_corrected.txt'")
    print("Copiez le contenu dans votre config.py")

def main():
    """Fonction principale"""
    print("🔧 CORRECTION DE LA CONFIGURATION GMAIL")
    print("=" * 50)
    
    # Test avec mot de passe corrigé
    success = test_gmail_fixed()
    
    if success:
        print("\n✅ CONFIGURATION GMAIL VALIDÉE !")
        create_corrected_config()
        print("\n🎯 PROCHAINES ÉTAPES :")
        print("1. Copiez la configuration corrigée dans votre config.py")
        print("2. Redémarrez votre serveur : python main.py")
        print("3. Testez les fonctionnalités email")
    else:
        print("\n❌ PROBLÈME PERSISTANT")
        print("Suivez les instructions ci-dessus pour résoudre le problème")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main() 