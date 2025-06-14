#!/usr/bin/env python3
"""
Correction du template email en base de données
Ajouter le mot de passe généré dans le template de bienvenue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def fix_welcome_template():
    """Corriger le template de bienvenue pour inclure le mot de passe"""
    print("🔧 CORRECTION TEMPLATE EMAIL")
    print("=" * 40)
    
    # Template HTML corrigé avec mot de passe
    correct_html_template = '''
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 30px; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">🎉 Bienvenue sur ESAG GED</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Votre compte a été créé avec succès</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px;">
                <p style="font-size: 16px; margin-bottom: 20px;">Bonjour <strong>{{user_name}}</strong>,</p>
                
                <p>Votre compte ESAG GED a été créé par un administrateur. Voici vos informations de connexion :</p>
                
                <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #495057; margin-top: 0;">🔐 Vos informations de connexion</h3>
                    <p><strong>Email :</strong> {{user_email}}</p>
                    <p><strong>Mot de passe temporaire :</strong> <code style="background: #e9ecef; padding: 4px 8px; border-radius: 4px; font-family: monospace; font-size: 16px; color: #d63384;">{{generated_password}}</code></p>
                    <p><strong>Rôle :</strong> {{user_role}}</p>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404;"><strong>⚠️ Important :</strong> Nous vous recommandons fortement de changer votre mot de passe lors de votre première connexion.</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{login_url}}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 12px 30px; border-radius: 6px; font-weight: bold;">Se connecter maintenant</a>
                </div>
                
                <p>Si vous avez des questions, n'hésitez pas à contacter l'équipe d'administration.</p>
                
                <p>Cordialement,<br><strong>L'équipe ESAG GED</strong></p>
            </div>
            
            <!-- Footer -->
            <div style="background: #f8f9fa; text-align: center; padding: 20px; border-radius: 0 0 10px 10px; border-top: 1px solid #dee2e6;">
                <p style="margin: 0; color: #6c757d; font-size: 14px;">© 2025 ESAG GED - Système de Gestion Électronique de Documents</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    # Template texte corrigé
    correct_text_template = '''Bienvenue sur ESAG GED !

Bonjour {{user_name}},

Votre compte ESAG GED a été créé par un administrateur.

Vos informations de connexion :
- Email : {{user_email}}
- Mot de passe temporaire : {{generated_password}}
- Rôle : {{user_role}}

IMPORTANT : Nous vous recommandons de changer votre mot de passe lors de votre première connexion.

Connectez-vous ici : {{login_url}}

Cordialement,
L'équipe ESAG GED'''
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si le template existe
        cursor.execute("SELECT id, name FROM email_templates WHERE name = %s", ('welcome',))
        existing_template = cursor.fetchone()
        
        if existing_template:
            print(f"📝 Template 'welcome' trouvé (ID: {existing_template['id']})")
            
            # Mettre à jour le template
            cursor.execute("""
                UPDATE email_templates 
                SET html_content = %s, 
                    text_content = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE name = %s
            """, (correct_html_template, correct_text_template, 'welcome'))
            
            print("✅ Template mis à jour avec succès!")
            
        else:
            print("📝 Template 'welcome' non trouvé, création...")
            
            # Créer le template
            cursor.execute("""
                INSERT INTO email_templates (name, subject, html_content, text_content, description, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                'welcome',
                'Bienvenue sur ESAG GED - Votre compte a été créé',
                correct_html_template,
                correct_text_template,
                'Template de bienvenue pour les nouveaux utilisateurs avec mot de passe',
                True
            ))
            
            print("✅ Template créé avec succès!")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Vérification
        print("\n🔍 VÉRIFICATION:")
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT html_content FROM email_templates WHERE name = %s", ('welcome',))
        template = cursor.fetchone()
        
        if template and '{{generated_password}}' in template['html_content']:
            print("✅ Le template contient maintenant {{generated_password}}!")
        else:
            print("❌ Problème : le template ne contient toujours pas {{generated_password}}")
            
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {str(e)}")
        return False

def test_template_after_fix():
    """Tester le template après correction"""
    print("\n🧪 TEST APRÈS CORRECTION")
    print("=" * 40)
    
    try:
        from AppFlask.services.email_service import email_service
        from AppFlask import create_app
        from jinja2 import Template
        
        app = create_app()
        with app.app_context():
            # Récupérer le template corrigé
            template_content = email_service._get_email_template('welcome')
            
            if template_content:
                html_content = template_content.get('html', '')
                
                # Données de test
                test_data = {
                    'user_name': 'Test Utilisateur',
                    'user_email': 'test@exemple.com',
                    'user_role': 'Utilisateur',
                    'generated_password': 'MotDePasseTest123',
                    'login_url': 'http://localhost:3000/login'
                }
                
                # Rendu du template
                template = Template(html_content)
                rendered = template.render(**test_data)
                
                if 'MotDePasseTest123' in rendered:
                    print("✅ Le template fonctionne maintenant correctement!")
                    print("✅ Le mot de passe apparaît bien dans l'email rendu")
                else:
                    print("❌ Le mot de passe n'apparaît toujours pas")
                    
                return True
            else:
                print("❌ Template non trouvé après correction")
                return False
                
    except Exception as e:
        print(f"❌ Erreur test: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🔧 CORRECTION TEMPLATE EMAIL - MOT DE PASSE MANQUANT")
    print("=" * 55)
    
    # Correction du template
    fix_success = fix_welcome_template()
    
    if fix_success:
        # Test après correction
        test_template_after_fix()
        
        print("\n🎉 CORRECTION TERMINÉE!")
        print("=" * 30)
        print("✅ Le template email contient maintenant le mot de passe généré")
        print("✅ Les prochains utilisateurs créés recevront leur mot de passe par email")
        print("\n🚀 PROCHAINES ÉTAPES:")
        print("1. Redémarrez le serveur si nécessaire")
        print("2. Créez un nouvel utilisateur pour tester")
        print("3. Vérifiez que l'email contient bien le mot de passe")
    else:
        print("\n❌ ÉCHEC DE LA CORRECTION")
        print("Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main() 