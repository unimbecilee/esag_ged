#!/usr/bin/env python3
"""
Script de diagnostic détaillé pour le système d'email
"""

import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_smtp():
    """Test direct de connexion SMTP sans le service"""
    print("🔍 Test direct SMTP Gmail...")
    
    # Configuration directe depuis votre config.py
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = "mainuser1006@gmail.com"
    password = "eidt jvuk saxg xfwa"  # Mot de passe d'application (avec espaces)
    
    try:
        print(f"📡 Connexion à {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Debug mode
        
        print("🔐 Activation TLS...")
        server.starttls()
        
        print("🔑 Authentification...")
        server.login(username, password)
        
        print("✅ Connexion SMTP réussie !")
        
        # Test d'envoi d'email simple
        print("📨 Test d'envoi d'email...")
        
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = username  # À vous-même
        msg['Subject'] = "🧪 Test ESAG GED - Configuration Gmail"
        
        body = """
        Félicitations ! 🎉
        
        Votre configuration Gmail fonctionne parfaitement avec ESAG GED.
        
        Les fonctionnalités suivantes sont maintenant disponibles :
        ✅ Email de bienvenue pour nouveaux utilisateurs
        ✅ Réinitialisation de mot de passe
        ✅ Notifications de documents
        ✅ Notifications de workflows
        
        Votre système est prêt à être utilisé !
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        text = msg.as_string()
        server.sendmail(username, username, text)
        
        print("✅ Email de test envoyé avec succès !")
        print(f"📬 Vérifiez votre boîte mail : {username}")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Erreur d'authentification : {str(e)}")
        print("\n🔧 Solutions possibles :")
        print("1. Vérifiez votre mot de passe d'application Gmail")
        print("2. Assurez-vous que l'authentification à 2 facteurs est activée")
        print("3. Générez un nouveau mot de passe d'application")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Erreur de connexion : {str(e)}")
        print("\n🔧 Solutions possibles :")
        print("1. Vérifiez votre connexion internet")
        print("2. Vérifiez les paramètres de pare-feu")
        return False
        
    except Exception as e:
        print(f"❌ Erreur inattendue : {str(e)}")
        return False

def check_config_file():
    """Vérifier le fichier de configuration"""
    print("📋 Vérification du fichier de configuration...")
    
    try:
        import config
        
        print("✅ Fichier config.py trouvé")
        
        # Vérifier les variables SMTP
        smtp_vars = [
            'SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 
            'SMTP_PASSWORD', 'SMTP_USE_TLS', 'EMAIL_FROM'
        ]
        
        for var in smtp_vars:
            if hasattr(config, var):
                value = getattr(config, var)
                if var == 'SMTP_PASSWORD':
                    print(f"✅ {var} = ****** (masqué)")
                else:
                    print(f"✅ {var} = {value}")
            else:
                print(f"❌ {var} manquant")
                
    except ImportError:
        print("❌ Fichier config.py non trouvé")
        return False
    
    return True

def main():
    """Fonction principale de diagnostic"""
    print("🔍 DIAGNOSTIC COMPLET DU SYSTÈME EMAIL")
    print("=" * 60)
    
    # 1. Vérifier le fichier de configuration
    print("\n1️⃣ VÉRIFICATION DE LA CONFIGURATION")
    config_ok = check_config_file()
    
    # 2. Test direct SMTP
    print("\n2️⃣ TEST DIRECT SMTP")
    if config_ok:
        smtp_ok = test_direct_smtp()
        
        if smtp_ok:
            print("\n🎉 DIAGNOSTIC COMPLET : SUCCÈS ! 🎉")
            print("Votre configuration Gmail est parfaitement fonctionnelle.")
            print("Vous pouvez maintenant démarrer votre serveur ESAG GED.")
        else:
            print("\n⚠️ DIAGNOSTIC : PROBLÈME IDENTIFIÉ")
            print("Suivez les solutions suggérées ci-dessus.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 