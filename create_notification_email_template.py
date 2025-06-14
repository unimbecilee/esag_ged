#!/usr/bin/env python3
"""
Création du template email pour les notifications générales
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def create_notification_email_template():
    """Créer le template email pour les notifications générales"""
    print("📧 CRÉATION DU TEMPLATE EMAIL NOTIFICATIONS")
    print("=" * 50)
    
    # Template HTML pour notifications générales
    html_template = '''
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 30px; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">🔔 ESAG GED - Notification</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{{notification_title}}</p>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px;">
                <p style="font-size: 16px; margin-bottom: 20px;">Bonjour <strong>{{user_name}}</strong>,</p>
                
                <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #495057; margin-top: 0;">📋 Notification</h3>
                    <p style="margin: 0; font-size: 16px;">{{notification_message}}</p>
                    
                    {% if document_title %}
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #dee2e6;">
                        <p style="margin: 0;"><strong>📄 Document :</strong> {{document_title}}</p>
                    </div>
                    {% endif %}
                    
                    {% if workflow_title %}
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #dee2e6;">
                        <p style="margin: 0;"><strong>⚡ Workflow :</strong> {{workflow_title}}</p>
                        {% if due_date %}
                        <p style="margin: 5px 0 0 0; color: #dc3545;"><strong>📅 Échéance :</strong> {{due_date}}</p>
                        {% endif %}
                    </div>
                    {% endif %}
                </div>
                
                <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #1565c0;"><strong>💡 Astuce :</strong> Connectez-vous à ESAG GED pour voir tous les détails et gérer vos notifications.</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{login_url}}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 12px 30px; border-radius: 6px; font-weight: bold;">Voir dans ESAG GED</a>
                </div>
                
                <div style="border-top: 1px solid #dee2e6; padding-top: 20px; margin-top: 30px;">
                    <p style="margin: 0; font-size: 14px; color: #6c757d;">
                        <strong>Type :</strong> {{notification_type}} | 
                        <strong>Date :</strong> {{date}}
                    </p>
                </div>
                
                <p style="margin-top: 20px;">Cordialement,<br><strong>L'équipe ESAG GED</strong></p>
            </div>
            
            <!-- Footer -->
            <div style="background: #f8f9fa; text-align: center; padding: 20px; border-radius: 0 0 10px 10px; border-top: 1px solid #dee2e6;">
                <p style="margin: 0; color: #6c757d; font-size: 14px;">© 2025 ESAG GED - Système de Gestion Électronique de Documents</p>
                <p style="margin: 5px 0 0 0; color: #6c757d; font-size: 12px;">
                    Vous recevez cet email car vous êtes abonné aux notifications ESAG GED.
                    <br>Vous pouvez modifier vos préférences dans les paramètres de votre compte.
                </p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    # Template texte pour notifications générales
    text_template = '''ESAG GED - Notification

{{notification_title}}

Bonjour {{user_name}},

{{notification_message}}

{% if document_title %}
Document : {{document_title}}
{% endif %}

{% if workflow_title %}
Workflow : {{workflow_title}}
{% if due_date %}Échéance : {{due_date}}{% endif %}
{% endif %}

Type : {{notification_type}}
Date : {{date}}

Connectez-vous à ESAG GED pour voir tous les détails :
{{login_url}}

Cordialement,
L'équipe ESAG GED

---
© 2025 ESAG GED - Système de Gestion Électronique de Documents
Vous pouvez modifier vos préférences de notification dans les paramètres de votre compte.'''
    
    try:
        conn = db_connection()
        if not conn:
            print("❌ Erreur de connexion à la base de données")
            return False
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si le template existe déjà
        cursor.execute("SELECT id FROM email_templates WHERE name = %s", ('notification_general',))
        existing = cursor.fetchone()
        
        if existing:
            print("📝 Template 'notification_general' trouvé, mise à jour...")
            
            # Mettre à jour le template existant
            cursor.execute("""
                UPDATE email_templates 
                SET html_content = %s, 
                    text_content = %s,
                    subject = %s,
                    description = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE name = %s
            """, (
                html_template,
                text_template,
                'ESAG GED - {{notification_title}}',
                'Template général pour toutes les notifications système',
                'notification_general'
            ))
            
            print("✅ Template mis à jour avec succès!")
            
        else:
            print("📝 Création du template 'notification_general'...")
            
            # Créer le nouveau template
            cursor.execute("""
                INSERT INTO email_templates 
                (name, subject, html_content, text_content, description, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                'notification_general',
                'ESAG GED - {{notification_title}}',
                html_template,
                text_template,
                'Template général pour toutes les notifications système',
                True
            ))
            
            print("✅ Template créé avec succès!")
        
        conn.commit()
        
        # Vérification
        cursor.execute("SELECT name, subject FROM email_templates WHERE name = %s", ('notification_general',))
        template = cursor.fetchone()
        
        if template:
            print(f"✅ Vérification : Template '{template['name']}' disponible")
            print(f"   Sujet : {template['subject']}")
        else:
            print("❌ Erreur : Template non trouvé après création")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du template: {str(e)}")
        return False

def test_template_rendering():
    """Tester le rendu du template avec des données d'exemple"""
    print("\n🧪 TEST DU TEMPLATE")
    print("=" * 30)
    
    try:
        from jinja2 import Template
        from AppFlask.services.email_service import email_service
        from AppFlask import create_app
        
        app = create_app()
        with app.app_context():
            # Récupérer le template
            template_content = email_service._get_email_template('notification_general')
            
            if not template_content:
                print("❌ Template non trouvé")
                return False
            
            # Données de test
            test_data = {
                'user_name': 'Jean Dupont',
                'notification_title': 'Nouveau document ajouté',
                'notification_message': 'Le document "Rapport mensuel" a été ajouté par Marie Martin',
                'notification_type': 'document_uploaded',
                'date': '15/01/2025 à 14:30',
                'login_url': 'http://localhost:3000/notifications',
                'document_title': 'Rapport mensuel',
                'workflow_title': None,
                'due_date': None
            }
            
            # Rendu du template
            template = Template(template_content['html'])
            rendered = template.render(**test_data)
            
            # Vérifications
            checks = [
                ('user_name', test_data['user_name']),
                ('notification_title', test_data['notification_title']),
                ('notification_message', test_data['notification_message']),
                ('document_title', test_data['document_title'])
            ]
            
            all_good = True
            for check_name, check_value in checks:
                if check_value in rendered:
                    print(f"✅ {check_name}: présent")
                else:
                    print(f"❌ {check_name}: ABSENT")
                    all_good = False
            
            if all_good:
                print("✅ Template fonctionne correctement!")
            else:
                print("❌ Problèmes détectés dans le template")
            
            return all_good
            
    except Exception as e:
        print(f"❌ Erreur test template: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("📧 CONFIGURATION TEMPLATE EMAIL NOTIFICATIONS")
    print("=" * 55)
    
    # Création du template
    template_created = create_notification_email_template()
    
    if template_created:
        # Test du template
        template_works = test_template_rendering()
        
        print("\n🎯 RÉSUMÉ")
        print("=" * 20)
        print(f"Création template: {'✅ RÉUSSI' if template_created else '❌ ÉCHOUÉ'}")
        print(f"Test template: {'✅ RÉUSSI' if template_works else '❌ ÉCHOUÉ'}")
        
        if template_created and template_works:
            print("\n🎉 TEMPLATE EMAIL NOTIFICATIONS CONFIGURÉ!")
            print("\n🚀 FONCTIONNALITÉS:")
            print("✅ Template HTML responsive et moderne")
            print("✅ Template texte pour compatibilité")
            print("✅ Support des variables dynamiques")
            print("✅ Design cohérent avec ESAG GED")
            print("✅ Informations contextuelles (document, workflow)")
            print("✅ Lien direct vers l'application")
            
            print("\n📋 VARIABLES DISPONIBLES:")
            print("• user_name - Nom de l'utilisateur")
            print("• notification_title - Titre de la notification")
            print("• notification_message - Message principal")
            print("• notification_type - Type de notification")
            print("• date - Date et heure")
            print("• login_url - Lien vers l'application")
            print("• document_title - Titre du document (optionnel)")
            print("• workflow_title - Titre du workflow (optionnel)")
            print("• due_date - Date d'échéance (optionnel)")
        else:
            print("\n⚠️ CONFIGURATION INCOMPLÈTE")
    else:
        print("\n❌ ÉCHEC DE LA CONFIGURATION")
    
    return template_created

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 