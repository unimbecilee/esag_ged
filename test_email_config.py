#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration email
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_email_configuration():
    """Tester la configuration email"""
    print("📧 Test de la configuration email ESAG GED")
    print("=" * 50)
    
    try:
        # Import du service email
        from AppFlask.services.email_service import email_service
        print("✅ Service email importé avec succès")
        
        # Test de connexion SMTP
        print("\n🔧 Test de connexion SMTP...")
        result = email_service.test_connection()
        
        if result.get('success'):
            print("✅ Connexion SMTP réussie !")
            print(f"📧 Serveur: {result.get('server', 'N/A')}")
            print(f"🔐 Port: {result.get('port', 'N/A')}")
            print(f"🛡️ TLS: Activé")
            
            # Test d'envoi d'email
            print("\n📨 Test d'envoi d'email...")
            
            # Email de test vers l'expéditeur
            test_email_result = email_service.send_email(
                to=["mainuser1006@gmail.com"],  # Votre propre email
                subject="🧪 Test ESAG GED - Configuration réussie",
                body="Félicitations ! Votre configuration email fonctionne parfaitement.",
                html_body="""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #28a745;">✅ Test de Configuration Réussi</h2>
                    <p>Félicitations ! Votre système d'email ESAG GED est maintenant opérationnel.</p>
                    <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <strong>🎉 Fonctionnalités disponibles :</strong>
                        <ul>
                            <li>Email de bienvenue pour nouveaux utilisateurs</li>
                            <li>Réinitialisation de mot de passe</li>
                            <li>Notifications de documents</li>
                            <li>Notifications de workflows</li>
                        </ul>
                    </div>
                    <p>Votre système est prêt à être utilisé !</p>
                </body>
                </html>
                """
            )
            
            if test_email_result:
                print("✅ Email de test envoyé avec succès !")
                print(f"📬 Vérifiez votre boîte mail : mainuser1006@gmail.com")
                print("\n🎉 CONFIGURATION COMPLÈTE ET FONCTIONNELLE ! 🎉")
            else:
                print("❌ Échec de l'envoi de l'email de test")
                
        else:
            print(f"❌ Erreur de connexion SMTP: {result.get('error', 'Inconnue')}")
            print("\n🔧 Vérifications suggérées :")
            print("1. Mot de passe d'application Gmail correct")
            print("2. Authentification à 2 facteurs activée sur Gmail")
            print("3. Connexion internet stable")
            
    except ImportError as e:
        print(f"❌ Erreur d'import: {str(e)}")
        print("Assurez-vous que le service email est bien configuré")
        
    except Exception as e:
        print(f"❌ Erreur inattendue: {str(e)}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_email_configuration() 