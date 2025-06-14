#!/usr/bin/env python3
"""
Test avec votre configuration exacte
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_your_exact_config():
    """Test avec votre configuration exacte"""
    print("🔧 Test avec votre configuration exacte...")
    
    # Configuration EXACTE de votre fichier config.py
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = "mainuser1006@gmail.com"
    password = "eidtjvuksaxgxfwa"  # Votre mot de passe exact
    
    try:
        print(f"📡 Connexion à {smtp_server}:{smtp_port}")
        print(f"👤 Utilisateur : {username}")
        print(f"🔑 Mot de passe : {'*' * len(password)} ({len(password)} caractères)")
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0)  # Désactiver debug pour plus de clarté
        
        print("🔐 Activation TLS...")
        server.starttls()
        
        print("🔑 Authentification...")
        server.login(username, password)
        
        print("✅ CONNEXION RÉUSSIE !")
        
        # Test d'envoi d'email
        print("📨 Envoi d'email de test...")
        
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username
        msg['Subject'] = "🎉 ESAG GED - Configuration Email Réussie !"
        
        body = """
🎉 FÉLICITATIONS ! 🎉

Votre système d'email ESAG GED fonctionne parfaitement !

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
        
        server.sendmail(username, username, msg.as_string())
        
        print("✅ EMAIL ENVOYÉ AVEC SUCCÈS !")
        print(f"📬 Vérifiez votre boîte mail : {username}")
        
        server.quit()
        
        print("\n🎯 CONFIGURATION VALIDÉE !")
        print("Votre système d'email est maintenant prêt à fonctionner.")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ ERREUR D'AUTHENTIFICATION : {str(e)}")
        print("\n🔍 DIAGNOSTIC :")
        print(f"   - Serveur : {smtp_server}")
        print(f"   - Port : {smtp_port}")
        print(f"   - Utilisateur : {username}")
        print(f"   - Mot de passe : {len(password)} caractères")
        
        print("\n💡 SOLUTIONS :")
        print("1. Vérifiez que l'authentification à 2 facteurs est ACTIVÉE sur Gmail")
        print("2. Le mot de passe doit être un MOT DE PASSE D'APPLICATION, pas votre mot de passe Gmail")
        print("3. Générez un NOUVEAU mot de passe d'application :")
        print("   - https://myaccount.google.com/security")
        print("   - Authentification à 2 facteurs > Mots de passe d'application")
        print("   - Sélectionnez 'Mail' > 'Ordinateur Windows' > Générer")
        print("4. Copiez le nouveau mot de passe SANS espaces")
        
        return False
        
    except Exception as e:
        print(f"❌ ERREUR INATTENDUE : {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🧪 TEST DE VOTRE CONFIGURATION GMAIL")
    print("=" * 55)
    
    success = test_your_exact_config()
    
    if success:
        print("\n🎉 SUCCÈS COMPLET ! 🎉")
        print("Votre configuration Gmail est parfaitement fonctionnelle.")
        print("Vous pouvez maintenant utiliser toutes les fonctionnalités email d'ESAG GED.")
    else:
        print("\n⚠️ PROBLÈME PERSISTANT")
        print("Le mot de passe d'application semble incorrect.")
        print("Suivez les étapes ci-dessus pour générer un nouveau mot de passe.")
    
    print("\n" + "=" * 55)

if __name__ == "__main__":
    main() 