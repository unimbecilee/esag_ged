import os
from typing import Dict, Any

class EmailConfig:
    """Configuration pour l'envoi d'emails"""
    
    # Configuration par défaut
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@esag.com')
    
    # Configuration avancée
    MAIL_MAX_EMAILS = int(os.getenv('MAIL_MAX_EMAILS', 50))
    MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'False').lower() in ('true', '1', 't')
    MAIL_ASCII_ATTACHMENTS = os.getenv('MAIL_ASCII_ATTACHMENTS', 'False').lower() in ('true', '1', 't')
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Retourne la configuration complète pour Flask-Mail"""
        return {
            'MAIL_SERVER': cls.MAIL_SERVER,
            'MAIL_PORT': cls.MAIL_PORT,
            'MAIL_USE_TLS': cls.MAIL_USE_TLS,
            'MAIL_USE_SSL': cls.MAIL_USE_SSL,
            'MAIL_USERNAME': cls.MAIL_USERNAME,
            'MAIL_PASSWORD': cls.MAIL_PASSWORD,
            'MAIL_DEFAULT_SENDER': cls.MAIL_DEFAULT_SENDER,
            'MAIL_MAX_EMAILS': cls.MAIL_MAX_EMAILS,
            'MAIL_SUPPRESS_SEND': cls.MAIL_SUPPRESS_SEND,
            'MAIL_ASCII_ATTACHMENTS': cls.MAIL_ASCII_ATTACHMENTS,
        }
    
    @classmethod
    def is_configured(cls) -> bool:
        """Vérifie si la configuration email est complète"""
        return bool(cls.MAIL_SERVER and cls.MAIL_USERNAME and cls.MAIL_PASSWORD)
    
    @classmethod
    def get_provider_presets(cls) -> Dict[str, Dict[str, Any]]:
        """Retourne les configurations prédéfinies pour différents fournisseurs"""
        return {
            'gmail': {
                'MAIL_SERVER': 'smtp.gmail.com',
                'MAIL_PORT': 587,
                'MAIL_USE_TLS': True,
                'MAIL_USE_SSL': False,
                'description': 'Gmail (nécessite un mot de passe d\'application)'
            },
            'outlook': {
                'MAIL_SERVER': 'smtp-mail.outlook.com',
                'MAIL_PORT': 587,
                'MAIL_USE_TLS': True,
                'MAIL_USE_SSL': False,
                'description': 'Outlook/Hotmail'
            },
            'yahoo': {
                'MAIL_SERVER': 'smtp.mail.yahoo.com',
                'MAIL_PORT': 587,
                'MAIL_USE_TLS': True,
                'MAIL_USE_SSL': False,
                'description': 'Yahoo Mail'
            },
            'custom': {
                'MAIL_SERVER': '',
                'MAIL_PORT': 587,
                'MAIL_USE_TLS': True,
                'MAIL_USE_SSL': False,
                'description': 'Configuration personnalisée'
            }
        } 