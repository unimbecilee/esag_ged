#!/usr/bin/env python3
"""
Solution pour l'authentification Outlook moderne
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enable_outlook_basic_auth():
    """Guide pour activer l'authentification basique Outlook"""
    print("🔧 SOLUTION : Activer l'authentification basique Outlook")
    print("=" * 60)
    
    print("""
📧 ÉTAPES POUR ACTIVER L'AUTHENTIFICATION SMTP DANS OUTLOOK :

1. 🌐 CONNECTEZ-VOUS SUR OUTLOOK.COM
   - Allez sur https://outlook.com
   - Connectez-vous avec : esagged@outlook.fr

2. ⚙️ PARAMÈTRES DE COMPTE
   - Cliquez sur l'icône ⚙️ (paramètres) en haut à droite
   - Sélectionnez "Afficher tous les paramètres Outlook"
   - Allez dans "Courrier" > "Synchronisation du courrier"

3. 🔐 ACTIVER L'AUTHENTIFICATION SMTP
   - Cherchez "Authentification SMTP"
   - OU allez dans "Paramètres" > "Sécurité"
   - Activez "Authentification moderne" ou "SMTP authentifié"

4. 🔑 ALTERNATIVE : MOT DE PASSE D'APPLICATION
   - Si disponible, créez un "mot de passe d'application"
   - Utilisez ce mot de passe au lieu de votre mot de passe principal

5. 🛡️ SÉCURITÉ (si l'option existe)
   - Désactivez "Sécurité par défaut" temporairement
   - Ou activez "Applications moins sécurisées"
""")

def test_outlook_alternatives():
    """Tester différentes configurations Outlook"""
    print("\n🧪 TEST DES ALTERNATIVES OUTLOOK")
    print("=" * 40)
    
    email = "esagged@outlook.fr"
    password = "Passecale2002@"
    
    # Configuration 1: Port 25
    print("1️⃣ Test avec port 25...")
    if test_smtp_config(email, password, "smtp-mail.outlook.com", 25, use_tls=False):
        return True
    
    # Configuration 2: Port 465 (SSL)
    print("2️⃣ Test avec port 465 (SSL)...")
    if test_smtp_config(email, password, "smtp-mail.outlook.com", 465, use_ssl=True):
        return True
    
    # Configuration 3: Serveur alternatif
    print("3️⃣ Test avec serveur alternatif...")
    if test_smtp_config(email, password, "smtp.office365.com", 587, use_tls=True):
        return True
    
    return False

def test_smtp_config(email, password, server, port, use_tls=False, use_ssl=False):
    """Tester une configuration SMTP spécifique"""
    try:
        print(f"   📡 {server}:{port} (TLS={use_tls}, SSL={use_ssl})")
        
        if use_ssl:
            server_conn = smtplib.SMTP_SSL(server, port)
        else:
            server_conn = smtplib.SMTP(server, port)
            
        if use_tls and not use_ssl:
            server_conn.starttls()
            
        server_conn.login(email, password)
        
        print("   ✅ SUCCÈS !")
        
        # Test d'envoi
        msg = MIMEText("Test ESAG GED - Configuration réussie !")
        msg['Subject'] = "✅ ESAG GED - Test Outlook réussi"
        msg['From'] = email
        msg['To'] = email
        
        server_conn.send_message(msg)
        server_conn.quit()
        
        print(f"   📧 Email de test envoyé !")
        
        # Afficher la configuration gagnante
        print(f"\n🎯 CONFIGURATION GAGNANTE :")
        print(f"SMTP_SERVER = \"{server}\"")
        print(f"SMTP_PORT = {port}")
        print(f"SMTP_USE_TLS = {use_tls}")
        print(f"SMTP_USE_SSL = {use_ssl}")
        print(f"SMTP_USERNAME = \"{email}\"")
        print(f"SMTP_PASSWORD = \"{password}\"")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Échec : {str(e)}")
        return False

def create_gmail_fallback():
    """Proposition de solution de secours avec un nouveau Gmail"""
    print("\n🔄 SOLUTION DE SECOURS : NOUVEAU COMPTE GMAIL")
    print("=" * 50)
    
    print("""
Si Outlook continue de poser problème, voici une solution rapide :

1. 📧 CRÉER UN NOUVEAU COMPTE GMAIL DÉDIÉ
   - Allez sur https://accounts.google.com/signup
   - Créez : esagged.system@gmail.com (ou similaire)
   - Mot de passe simple : EsagGed2024!

2. 🔐 CONFIGURER L'AUTHENTIFICATION À 2 FACTEURS
   - Activez immédiatement l'A2F
   - Générez un mot de passe d'application

3. ✅ AVANTAGES
   - Compte dédié uniquement pour ESAG GED
   - Pas de risque avec votre compte personnel
   - Configuration Gmail plus stable pour les applications

Voulez-vous essayer cette approche ?
""")

def main():
    """Fonction principale"""
    print("🔧 RÉSOLUTION DU PROBLÈME OUTLOOK")
    print("=" * 45)
    
    print("Outlook a bloqué l'authentification basique.")
    print("Voici les solutions disponibles :\n")
    
    # Guide pour activer l'auth Outlook
    enable_outlook_basic_auth()
    
    # Tester des alternatives
    print("\n" + "="*60)
    success = test_outlook_alternatives()
    
    if not success:
        print("\n❌ TOUTES LES CONFIGURATIONS OUTLOOK ONT ÉCHOUÉ")
        create_gmail_fallback()
        
        choice = input("\nQue voulez-vous faire ? (outlook/gmail/stop) : ").strip().lower()
        
        if choice == "gmail":
            print("\n🎯 Créez un nouveau compte Gmail dédié et revenez ici !")
        elif choice == "outlook":
            print("\n🎯 Suivez le guide ci-dessus pour activer l'auth Outlook !")
        else:
            print("\n⏸️ Configuration en pause. Revenez quand vous aurez choisi une solution !")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main() 