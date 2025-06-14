import logging
from flask import Blueprint, request, jsonify
from AppFlask.api.auth import token_required
from AppFlask.services.email_service import email_service
from AppFlask.config.email_config import EmailConfig
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Blueprint pour l'API email
bp = Blueprint('email', __name__)

@bp.route('/email/config', methods=['GET'])
@token_required
def get_email_config(current_user):
    """Récupère la configuration email actuelle"""
    try:
        # Vérifier les permissions admin
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403
        
        config = EmailConfig.get_config()
        
        # Masquer le mot de passe pour la sécurité
        safe_config = {k: v for k, v in config.items() if k != 'MAIL_PASSWORD'}
        safe_config['MAIL_PASSWORD'] = '***' if config['MAIL_PASSWORD'] else ''
        safe_config['is_configured'] = EmailConfig.is_configured()
        
        # Ajouter les presets de fournisseurs
        safe_config['providers'] = EmailConfig.get_provider_presets()
        
        return jsonify(safe_config)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la config email: {str(e)}")
        return jsonify({'message': 'Erreur serveur'}), 500

@bp.route('/email/config', methods=['PUT'])
@token_required
def update_email_config(current_user):
    """Met à jour la configuration email"""
    try:
        # Vérifier les permissions admin
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Aucune donnée reçue'}), 400
        
        # Sauvegarder la configuration en base de données
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si la table de configuration existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'email_config'
            );
        """)
        
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            # Créer la table si elle n'existe pas
            cursor.execute("""
                CREATE TABLE email_config (
                    id SERIAL PRIMARY KEY,
                    mail_server VARCHAR(255) NOT NULL,
                    mail_port INTEGER NOT NULL DEFAULT 587,
                    mail_use_tls BOOLEAN DEFAULT true,
                    mail_use_ssl BOOLEAN DEFAULT false,
                    mail_username VARCHAR(255) NOT NULL,
                    mail_password VARCHAR(255) NOT NULL,
                    mail_default_sender VARCHAR(255) NOT NULL,
                    mail_max_emails INTEGER DEFAULT 50,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        
        # Vérifier s'il existe déjà une configuration
        cursor.execute("SELECT id FROM email_config WHERE is_active = true LIMIT 1")
        existing_config = cursor.fetchone()
        
        if existing_config:
            # Mettre à jour la configuration existante
            cursor.execute("""
                UPDATE email_config SET 
                    mail_server = %s,
                    mail_port = %s,
                    mail_use_tls = %s,
                    mail_use_ssl = %s,
                    mail_username = %s,
                    mail_password = %s,
                    mail_default_sender = %s,
                    mail_max_emails = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                data.get('mail_server', ''),
                data.get('mail_port', 587),
                data.get('mail_use_tls', True),
                data.get('mail_use_ssl', False),
                data.get('mail_username', ''),
                data.get('mail_password', ''),
                data.get('mail_default_sender', ''),
                data.get('mail_max_emails', 50),
                existing_config['id']
            ))
        else:
            # Créer une nouvelle configuration
            cursor.execute("""
                INSERT INTO email_config (
                    mail_server, mail_port, mail_use_tls, mail_use_ssl,
                    mail_username, mail_password, mail_default_sender, mail_max_emails
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('mail_server', ''),
                data.get('mail_port', 587),
                data.get('mail_use_tls', True),
                data.get('mail_use_ssl', False),
                data.get('mail_username', ''),
                data.get('mail_password', ''),
                data.get('mail_default_sender', ''),
                data.get('mail_max_emails', 50)
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Mettre à jour les variables d'environnement (pour la session actuelle)
        import os
        os.environ['MAIL_SERVER'] = data.get('mail_server', '')
        os.environ['MAIL_PORT'] = str(data.get('mail_port', 587))
        os.environ['MAIL_USE_TLS'] = str(data.get('mail_use_tls', True))
        os.environ['MAIL_USE_SSL'] = str(data.get('mail_use_ssl', False))
        os.environ['MAIL_USERNAME'] = data.get('mail_username', '')
        os.environ['MAIL_PASSWORD'] = data.get('mail_password', '')
        os.environ['MAIL_DEFAULT_SENDER'] = data.get('mail_default_sender', '')
        
        logger.info("Configuration email mise à jour avec succès")
        return jsonify({'message': 'Configuration email mise à jour avec succès'})
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la config email: {str(e)}")
        return jsonify({'message': 'Erreur serveur'}), 500

@bp.route('/email/test', methods=['POST'])
@token_required
def test_email_connection(current_user):
    """Teste la connexion email"""
    try:
        # Vérifier les permissions admin
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403
        
        # Tester la connexion
        result = email_service.test_connection()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
        
    except Exception as e:
        logger.error(f"Erreur lors du test de connexion email: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors du test: {str(e)}'
        }), 500

@bp.route('/email/send-test', methods=['POST'])
@token_required
def send_test_email(current_user):
    """Envoie un email de test"""
    try:
        # Vérifier les permissions admin
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403
        
        data = request.get_json()
        if not data or not data.get('email'):
            return jsonify({'message': 'Email destinataire requis'}), 400
        
        test_email = data['email']
        
        # Envoyer l'email de test
        success = email_service.send_email(
            to=[test_email],
            subject='Test ESAG GED - Configuration Email',
            body='''
            Bonjour,
            
            Ceci est un email de test pour vérifier la configuration du système ESAG GED.
            
            Si vous recevez cet email, la configuration est correcte !
            
            Cordialement,
            L'équipe ESAG GED
            ''',
            html_body='''
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Test ESAG GED - Configuration Email</h2>
                    <p>Bonjour,</p>
                    <p>Ceci est un email de test pour vérifier la configuration du système ESAG GED.</p>
                    <div style="background: #d4edda; color: #155724; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                        <p style="margin: 0;"><strong>✅ Si vous recevez cet email, la configuration est correcte !</strong></p>
                    </div>
                    <p>Cordialement,<br>L'équipe ESAG GED</p>
                </div>
            </body>
            </html>
            '''
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Email de test envoyé avec succès à {test_email}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Échec de l\'envoi de l\'email de test'
            }), 400
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de test: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors de l\'envoi: {str(e)}'
        }), 500

@bp.route('/email/templates', methods=['GET'])
@token_required
def get_email_templates(current_user):
    """Récupère la liste des templates d'email"""
    try:
        # Vérifier les permissions admin
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si la table des templates existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'email_templates'
            );
        """)
        
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            # Créer la table et insérer les templates par défaut
            cursor.execute("""
                CREATE TABLE email_templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    html_content TEXT NOT NULL,
                    text_content TEXT,
                    description TEXT,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Insérer les templates par défaut
            default_templates = [
                {
                    'name': 'document_notification',
                    'subject': 'Notification de document - ESAG GED',
                    'description': 'Template pour les notifications de documents',
                    'html_content': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #2c3e50;">ESAG GED - Notification</h2>
                            <p>Bonjour,</p>
                            <p>Un document a été {{ action }} dans le système ESAG GED :</p>
                            <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                                <h3 style="margin: 0 0 10px 0;">{{ document_title }}</h3>
                                <p style="margin: 0;"><strong>Type :</strong> {{ document_type }}</p>
                                <p style="margin: 0;"><strong>Date :</strong> {{ date }}</p>
                            </div>
                            <p>Cordialement,<br>L'équipe ESAG GED</p>
                        </div>
                    </body>
                    </html>
                    ''',
                    'text_content': '''
                    ESAG GED - Notification
                    
                    Bonjour,
                    
                    Un document a été {{ action }} dans le système ESAG GED :
                    
                    Titre : {{ document_title }}
                    Type : {{ document_type }}
                    Date : {{ date }}
                    
                    Cordialement,
                    L'équipe ESAG GED
                    '''
                },
                {
                    'name': 'welcome',
                    'subject': 'Bienvenue sur ESAG GED',
                    'description': 'Template de bienvenue pour les nouveaux utilisateurs',
                    'html_content': '''
                    <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                            <h2 style="color: #2c3e50;">Bienvenue sur ESAG GED</h2>
                            <p>Bonjour {{ user_name }},</p>
                            <p>Votre compte a été créé avec succès sur ESAG GED.</p>
                            <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
                                <p style="margin: 0;"><strong>Email :</strong> {{ user_email }}</p>
                                <p style="margin: 0;"><strong>Rôle :</strong> {{ user_role }}</p>
                            </div>
                            <p>Cordialement,<br>L'équipe ESAG GED</p>
                        </div>
                    </body>
                    </html>
                    ''',
                    'text_content': '''
                    Bienvenue sur ESAG GED
                    
                    Bonjour {{ user_name }},
                    
                    Votre compte a été créé avec succès sur ESAG GED.
                    
                    Email : {{ user_email }}
                    Rôle : {{ user_role }}
                    
                    Cordialement,
                    L'équipe ESAG GED
                    '''
                }
            ]
            
            for template in default_templates:
                cursor.execute("""
                    INSERT INTO email_templates (name, subject, html_content, text_content, description)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    template['name'],
                    template['subject'],
                    template['html_content'],
                    template['text_content'],
                    template['description']
                ))
            
            conn.commit()
        
        # Récupérer tous les templates
        cursor.execute("""
            SELECT id, name, subject, description, is_active, created_at, updated_at
            FROM email_templates
            ORDER BY name
        """)
        
        templates = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify([dict(template) for template in templates])
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des templates: {str(e)}")
        return jsonify({'message': 'Erreur serveur'}), 500

@bp.route('/email/logs', methods=['GET'])
@token_required
def get_email_logs(current_user):
    """Récupère les logs d'envoi d'emails"""
    try:
        # Vérifier les permissions admin
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si la table des logs existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'email_logs'
            );
        """)
        
        table_exists = cursor.fetchone()['exists']
        
        if not table_exists:
            return jsonify({
                'logs': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0
            })
        
        # Compter le total
        cursor.execute("SELECT COUNT(*) as count FROM email_logs")
        total = cursor.fetchone()['count']
        
        # Récupérer les logs avec pagination
        cursor.execute("""
            SELECT id, recipients, subject, sender, sent_at, status
            FROM email_logs
            ORDER BY sent_at DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))
        
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'logs': [dict(log) for log in logs],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des logs email: {str(e)}")
        return jsonify({'message': 'Erreur serveur'}), 500 