#!/usr/bin/env python3
"""
Debug du template email - Vérifier pourquoi le mot de passe n'apparaît pas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jinja2 import Template

def test_template_rendering():
    """Tester le rendu du template avec les données"""
    print("🧪 TEST RENDU TEMPLATE EMAIL")
    print("=" * 40)
    
    # Template de bienvenue (version simplifiée pour test)
    template_html = '''
    <html>
    <body>
        <h1>Bienvenue {{user_name}}</h1>
        <p>Email: {{user_email}}</p>
        <p>Mot de passe: {{generated_password}}</p>
        <p>Rôle: {{user_role}}</p>
    </body>
    </html>
    '''
    
    # Données de test (comme celles envoyées par auth.py)
    test_data = {
        'user_name': 'landry Dansou',
        'user_email': 'landrydns@gmail.com',
        'user_role': 'Admin',
        'generated_password': 'TestPassword123',
        'login_url': 'http://localhost:3000/login'
    }
    
    print("📋 DONNÉES DE TEST:")
    for key, value in test_data.items():
        print(f"  {key}: {value}")
    
    print("\n🔧 RENDU DU TEMPLATE:")
    try:
        template = Template(template_html)
        rendered = template.render(**test_data)
        print(rendered)
        
        # Vérifier si le mot de passe est présent
        if test_data['generated_password'] in rendered:
            print("\n✅ Le mot de passe est bien présent dans le rendu!")
        else:
            print("\n❌ Le mot de passe est ABSENT du rendu!")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur de rendu: {str(e)}")
        return False

def test_service_email_template():
    """Tester le service email directement"""
    print("\n📧 TEST SERVICE EMAIL")
    print("=" * 40)
    
    try:
        from AppFlask.services.email_service import email_service
        from AppFlask import create_app
        
        app = create_app()
        with app.app_context():
            # Récupérer le template welcome
            template_content = email_service._get_email_template('welcome')
            
            if template_content:
                print("✅ Template 'welcome' trouvé")
                
                # Vérifier si le template contient la variable generated_password
                html_content = template_content.get('html', '')
                text_content = template_content.get('text', '')
                
                has_password_html = '{{generated_password}}' in html_content
                has_password_text = '{{generated_password}}' in text_content
                
                print(f"📝 Template HTML contient {{{{generated_password}}}}: {has_password_html}")
                print(f"📝 Template TEXT contient {{{{generated_password}}}}: {has_password_text}")
                
                if has_password_html or has_password_text:
                    print("✅ Le template contient bien la variable du mot de passe")
                    
                    # Test de rendu avec données réelles
                    test_data = {
                        'user_name': 'landry Dansou',
                        'user_email': 'landrydns@gmail.com',
                        'user_role': 'Admin',
                        'generated_password': 'TestPassword123',
                        'login_url': 'http://localhost:3000/login'
                    }
                    
                    template = Template(html_content)
                    rendered = template.render(**test_data)
                    
                    if 'TestPassword123' in rendered:
                        print("✅ Le rendu contient bien le mot de passe!")
                    else:
                        print("❌ Le rendu ne contient PAS le mot de passe!")
                        print("🔍 Extrait du rendu:")
                        # Chercher la section du mot de passe
                        lines = rendered.split('\n')
                        for i, line in enumerate(lines):
                            if 'mot de passe' in line.lower() or 'password' in line.lower():
                                print(f"  Ligne {i}: {line.strip()}")
                else:
                    print("❌ Le template ne contient PAS la variable generated_password!")
                    
            else:
                print("❌ Template 'welcome' non trouvé")
                
        return True
        
    except Exception as e:
        print(f"❌ Erreur test service: {str(e)}")
        return False

def test_auth_data_preparation():
    """Tester la préparation des données dans auth.py"""
    print("\n👤 TEST PRÉPARATION DONNÉES AUTH")
    print("=" * 40)
    
    try:
        # Simuler les données comme dans auth.py
        data = {
            'prenom': 'landry',
            'nom': 'Dansou', 
            'email': 'landrydns@gmail.com',
            'role': 'Admin'
        }
        
        generated_password = 'TestPassword123'
        
        # Préparer les données comme dans auth.py
        email_data = {
            'user_name': f"{data['prenom']} {data['nom']}",
            'user_email': data['email'],
            'user_role': data['role'],
            'generated_password': generated_password,
            'login_url': 'http://localhost:3000/login'
        }
        
        print("📋 DONNÉES PRÉPARÉES:")
        for key, value in email_data.items():
            print(f"  {key}: {value}")
            
        # Vérifier que generated_password est bien présent
        if 'generated_password' in email_data and email_data['generated_password']:
            print("✅ generated_password est bien présent dans les données!")
        else:
            print("❌ generated_password est ABSENT des données!")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur test données: {str(e)}")
        return False

def main():
    """Fonction principale de debug"""
    print("🔍 DEBUG TEMPLATE EMAIL - PROBLÈME MOT DE PASSE")
    print("=" * 50)
    
    tests = [
        ("Rendu Template", test_template_rendering),
        ("Service Email", test_service_email_template),
        ("Données Auth", test_auth_data_preparation)
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
    print("\n🎯 RÉSUMÉ DEBUG")
    print("=" * 30)
    
    for test_name, result in results:
        status = "✅ OK" if result else "❌ KO"
        print(f"{test_name}: {status}")
    
    print("\n💡 SOLUTION RECOMMANDÉE:")
    print("Si le template contient bien {{generated_password}} mais que")
    print("l'email reçu ne l'affiche pas, le problème vient probablement")
    print("du fait que le service email utilise le mauvais template ou")
    print("que les données ne sont pas correctement transmises.")

if __name__ == "__main__":
    main() 