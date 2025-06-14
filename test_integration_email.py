#!/usr/bin/env python3
"""
Test d'intégration du système email ESAG GED
Vérifie que toutes les modifications sont bien appliquées
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config_loading():
    """Test du chargement de la configuration"""
    print("🔧 TEST CHARGEMENT CONFIGURATION")
    print("=" * 40)
    
    try:
        import config
        print(f"✅ MAIL_SERVER: {config.MAIL_SERVER}")
        print(f"✅ MAIL_USERNAME: {config.MAIL_USERNAME}")
        print(f"✅ MAIL_PASSWORD: {config.MAIL_PASSWORD[:4]}***")
        print(f"✅ Variables d'environnement définies: {bool(os.getenv('MAIL_SERVER'))}")
        return True
    except Exception as e:
        print(f"❌ Erreur chargement config: {str(e)}")
        return False

def test_email_service():
    """Test du service email"""
    print("\n📧 TEST SERVICE EMAIL")
    print("=" * 40)
    
    try:
        from AppFlask.services.email_service import email_service
        from AppFlask import create_app
        
        app = create_app()
        with app.app_context():
            print(f"✅ Service configuré: {email_service.is_configured()}")
            
            # Test de connexion
            connection_test = email_service.test_connection()
            print(f"✅ Test connexion: {connection_test}")
            
            return connection_test.get('success', False)
            
    except Exception as e:
        print(f"❌ Erreur service email: {str(e)}")
        return False

def test_user_creation_integration():
    """Test de l'intégration avec la création d'utilisateur"""
    print("\n👤 TEST INTÉGRATION CRÉATION UTILISATEUR")
    print("=" * 40)
    
    try:
        # Vérifier que le code d'envoi d'email est présent dans auth.py
        with open('AppFlask/api/auth.py', 'r', encoding='utf-8') as f:
            auth_content = f.read()
            
        has_email_import = 'from AppFlask.services.email_service import email_service' in auth_content
        has_welcome_email = 'send_template_email' in auth_content and 'welcome' in auth_content
        has_password_reset = 'password_reset' in auth_content
        
        print(f"✅ Import service email: {has_email_import}")
        print(f"✅ Email de bienvenue: {has_welcome_email}")
        print(f"✅ Réinitialisation mot de passe: {has_password_reset}")
        
        return has_email_import and has_welcome_email and has_password_reset
        
    except Exception as e:
        print(f"❌ Erreur test intégration: {str(e)}")
        return False

def test_templates():
    """Test des templates email"""
    print("\n📝 TEST TEMPLATES EMAIL")
    print("=" * 40)
    
    try:
        from AppFlask.services.email_service import email_service
        from AppFlask import create_app
        
        app = create_app()
        with app.app_context():
            # Tester les templates par défaut
            templates = email_service._get_default_templates()
            
            required_templates = ['welcome', 'password_reset']
            for template_name in required_templates:
                has_template = template_name in templates
                print(f"✅ Template '{template_name}': {has_template}")
                
                if has_template:
                    template = templates[template_name]
                    has_html = 'html' in template and len(template['html']) > 100
                    has_text = 'text' in template and len(template['text']) > 50
                    print(f"   - HTML: {has_html}")
                    print(f"   - Text: {has_text}")
            
            return len(templates) >= 2
            
    except Exception as e:
        print(f"❌ Erreur test templates: {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TEST INTÉGRATION SYSTÈME EMAIL ESAG GED")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_config_loading),
        ("Service Email", test_email_service),
        ("Intégration Utilisateur", test_user_creation_integration),
        ("Templates", test_templates)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur dans {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Résumé
    print("\n🎯 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 RÉSULTAT: {passed}/{len(results)} tests passés")
    
    if passed == len(results):
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        print("✅ Votre système email est entièrement intégré et fonctionnel")
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("1. Démarrez le serveur: python main.py")
        print("2. Testez la création d'un utilisateur")
        print("3. Vérifiez l'email de bienvenue")
    else:
        print("\n⚠️ Certains tests ont échoué")
        print("Vérifiez les erreurs ci-dessus")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 