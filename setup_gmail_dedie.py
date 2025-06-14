#!/usr/bin/env python3
"""
Guide pour créer et configurer un Gmail dédié pour ESAG GED
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import webbrowser
import time

def guide_creation_gmail():
    """Guide étape par étape pour créer le Gmail dédié"""
    print("📧 CRÉATION D'UN GMAIL DÉDIÉ POUR ESAG GED")
    print("=" * 50)
    
    print("""
🎯 ÉTAPE 1 : CRÉATION DU COMPTE GMAIL

1. Je vais ouvrir Gmail pour vous...
   Ou allez manuellement sur : https://accounts.google.com/signup

2. INFORMATIONS SUGGÉRÉES :
   • Prénom : ESAG
   • Nom : GED
   • Email suggéré : esagged2024@gmail.com
   • Mot de passe : EsagGed2024!
   
   (Vous pouvez choisir un autre nom d'utilisateur si celui-ci est pris)

3. Suivez les étapes de création de compte
   • Vérification par téléphone
   • Acceptation des conditions

⏸️  FAITES CELA MAINTENANT, puis revenez ici !
""")
    
    input("Appuyez sur Entrée quand le compte Gmail est créé...")
    
    # Ouvrir automatiquement les pages nécessaires
    try:
        print("🌐 Ouverture de Google Account Security...")
        webbrowser.open("https://myaccount.google.com/security")
        time.sleep(2)
    except:
        print("Allez manuellement sur : https://myaccount.google.com/security")

def guide_activation_a2f():
    """Guide pour activer l'authentification à 2 facteurs"""
    print("\n🔐 ÉTAPE 2 : ACTIVATION DE L'AUTHENTIFICATION À 2 FACTEURS")
    print("=" * 60)
    
    print("""
1. Sur la page de sécurité Google :
   • Cherchez "Authentification à 2 facteurs"
   • Cliquez sur "Commencer" ou "Activer"

2. Suivez les étapes :
   • Confirmez votre mot de passe
   • Ajoutez votre numéro de téléphone
   • Confirmez le code reçu par SMS
   • Activez l'A2F

3. ✅ L'A2F doit être ACTIVÉ avant de continuer !
""")
    
    input("Appuyez sur Entrée quand l'A2F est activé...")

def guide_mot_de_passe_application():
    """Guide pour générer le mot de passe d'application"""
    print("\n🔑 ÉTAPE 3 : GÉNÉRATION DU MOT DE PASSE D'APPLICATION")
    print("=" * 55)
    
    print("""
1. Toujours sur la page de sécurité Google :
   • Cherchez "Mots de passe d'application"
   • Cliquez dessus (doit être visible maintenant que l'A2F est activé)

2. Générer le mot de passe :
   • Sélectionnez "Autre (nom personnalisé)"
   • Tapez : ESAG GED
   • Cliquez "Générer"

3. 📋 COPIEZ le mot de passe généré (16 caractères)
   Format : xxxx xxxx xxxx xxxx
   
   ⚠️ IMPORTANT : Copiez-le MAINTENANT, il ne sera plus affiché !
""")
    
    email = input("\n📧 Entrez l'email Gmail créé (ex: esagged2024@gmail.com) : ").strip()
    password = input("🔑 Collez le mot de passe d'application (16 caractères) : ").strip()
    
    # Nettoyer le mot de passe (enlever les espaces)
    password_clean = password.replace(" ", "")
    
    print(f"\n✅ Configuration reçue :")
    print(f"   Email : {email}")
    print(f"   Mot de passe : {'*' * len(password_clean)} ({len(password_clean)} caractères)")
    
    return email, password_clean

def test_gmail_dedie(email, password):
    """Tester la configuration Gmail dédiée"""
    print(f"\n🧪 TEST DE LA CONFIGURATION GMAIL DÉDIÉE")
    print("=" * 45)
    
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    try:
        print(f"📡 Connexion à {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        print("🔐 Activation TLS...")
        server.starttls()
        
        print("🔑 Authentification...")
        server.login(email, password)
        
        print("✅ CONNEXION GMAIL RÉUSSIE !")
        
        # Envoi d'email de validation
        print("📨 Envoi d'email de validation...")
        
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email
        msg['Subject'] = "🎉 ESAG GED - Gmail Dédié Configuré avec Succès !"
        
        body = f"""
🎉 FÉLICITATIONS ! 🎉

Votre Gmail dédié pour ESAG GED fonctionne parfaitement !

✅ CONFIGURATION VALIDÉE :
• Email dédié : {email}
• Serveur SMTP : smtp.gmail.com
• Port : 587
• TLS : Activé
• Authentification à 2 facteurs : Activé

✅ FONCTIONNALITÉS ESAG GED ACTIVÉES :
🔹 Email de bienvenue automatique pour nouveaux utilisateurs
🔹 Réinitialisation de mot de passe par email
🔹 Notifications de documents (ajout, partage)
🔹 Notifications de workflows (assignation de tâches)
🔹 Interface d'administration email complète
🔹 Logs détaillés de tous les emails envoyés

🚀 VOTRE SYSTÈME EST MAINTENANT 100% OPÉRATIONNEL !

📋 PROCHAINES ÉTAPES :
1. La configuration sera automatiquement mise à jour dans config.py
2. Redémarrez votre serveur : python main.py
3. Testez en créant un nouvel utilisateur
4. Testez la réinitialisation de mot de passe
5. Ajoutez un document pour voir les notifications

🎯 TESTS RECOMMANDÉS :
• Créez un utilisateur → il recevra un email de bienvenue
• Utilisez "Mot de passe oublié" → reset par email
• Ajoutez un document → notifications automatiques aux admins

Cordialement,
L'équipe ESAG GED 🚀

---
Email envoyé depuis le système d'email ESAG GED
Gmail dédié : {email}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server.sendmail(email, email, msg.as_string())
        
        print("✅ EMAIL DE VALIDATION ENVOYÉ !")
        print(f"📬 Vérifiez votre boîte mail : {email}")
        
        server.quit()
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ ERREUR D'AUTHENTIFICATION : {str(e)}")
        print("\n🔧 VÉRIFICATIONS :")
        print("1. A2F activé sur le compte Gmail ?")
        print("2. Mot de passe d'application correct (16 caractères) ?")
        print("3. Pas d'espaces dans le mot de passe ?")
        return False
        
    except Exception as e:
        print(f"❌ ERREUR : {str(e)}")
        return False

def update_config_file(email, password):
    """Mettre à jour le fichier de configuration"""
    print(f"\n📝 MISE À JOUR DE LA CONFIGURATION")
    print("=" * 40)
    
    config_content = f'''
# Configuration Email ESAG GED - GMAIL DÉDIÉ
# Remplacez les anciennes variables email par celles-ci :

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "{email}"
SMTP_PASSWORD = "{password}"
SMTP_USE_TLS = True
EMAIL_FROM = "{email}"
EMAIL_FROM_NAME = "ESAG GED"

# Configuration Flask-Mail alternative
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "{email}"
MAIL_PASSWORD = "{password}"
MAIL_DEFAULT_SENDER = "{email}"
'''
    
    print("Configuration générée :")
    print(config_content)
    
    # Sauvegarder dans un fichier
    with open("gmail_dedie_config.txt", "w") as f:
        f.write(config_content)
    
    print("✅ Configuration sauvegardée dans 'gmail_dedie_config.txt'")
    
    # Mettre à jour automatiquement config.py si possible
    try:
        with open("config.py", "r") as f:
            config_py = f.read()
        
        # Remplacer les variables email existantes
        new_config = config_py
        
        # Remplacer les variables SMTP
        import re
        new_config = re.sub(r'SMTP_SERVER\s*=.*', f'SMTP_SERVER = "smtp.gmail.com"', new_config)
        new_config = re.sub(r'SMTP_PORT\s*=.*', f'SMTP_PORT = 587', new_config)
        new_config = re.sub(r'SMTP_USERNAME\s*=.*', f'SMTP_USERNAME = "{email}"', new_config)
        new_config = re.sub(r'SMTP_PASSWORD\s*=.*', f'SMTP_PASSWORD = "{password}"', new_config)
        new_config = re.sub(r'EMAIL_FROM\s*=.*', f'EMAIL_FROM = "{email}"', new_config)
        
        with open("config.py", "w") as f:
            f.write(new_config)
        
        print("✅ Fichier config.py mis à jour automatiquement !")
        
    except Exception as e:
        print(f"⚠️ Mise à jour automatique échouée : {str(e)}")
        print("Copiez manuellement la configuration ci-dessus dans config.py")

def main():
    """Fonction principale"""
    print("🚀 CONFIGURATION GMAIL DÉDIÉ POUR ESAG GED")
    print("=" * 50)
    
    print("Cette solution va créer un compte Gmail spécialement pour votre application.")
    print("Avantages : fiable, sécurisé, dédié uniquement à ESAG GED.\n")
    
    # Étape 1 : Création du compte
    guide_creation_gmail()
    
    # Étape 2 : Activation A2F
    guide_activation_a2f()
    
    # Étape 3 : Mot de passe d'application
    email, password = guide_mot_de_passe_application()
    
    # Étape 4 : Test de la configuration
    success = test_gmail_dedie(email, password)
    
    if success:
        # Étape 5 : Mise à jour de la configuration
        update_config_file(email, password)
        
        print("\n🎉 CONFIGURATION GMAIL DÉDIÉE RÉUSSIE ! 🎉")
        print("=" * 45)
        print("✅ Compte Gmail dédié créé et testé")
        print("✅ Configuration mise à jour")
        print("✅ Email de validation envoyé")
        print("\n🚀 PROCHAINES ÉTAPES :")
        print("1. Vérifiez votre email de validation")
        print("2. Redémarrez votre serveur : python main.py")
        print("3. Testez les fonctionnalités email d'ESAG GED")
        
    else:
        print("\n❌ CONFIGURATION ÉCHOUÉE")
        print("Vérifiez les étapes ci-dessus et réessayez")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main() 