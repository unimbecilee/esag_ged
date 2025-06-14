#!/usr/bin/env python3
"""
Middleware pour les notifications automatiques ESAG GED
"""

from functools import wraps
from AppFlask.services.notification_service import notification_service
import logging

logger = logging.getLogger(__name__)

def with_notifications(notification_type: str, **notification_kwargs):
    """
    Décorateur pour ajouter automatiquement des notifications aux actions
    
    Args:
        notification_type: Type de notification ('document_uploaded', 'document_shared', etc.)
        **notification_kwargs: Arguments supplémentaires pour la notification
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Exécuter la fonction originale
                result = func(*args, **kwargs)
                
                # Si la fonction a réussi, envoyer la notification
                if hasattr(result, 'status_code') and result.status_code < 400:
                    # Extraire les informations nécessaires selon le type
                    if notification_type == 'document_uploaded':
                        document_id = kwargs.get('document_id') or notification_kwargs.get('document_id')
                        uploader_id = kwargs.get('user_id') or notification_kwargs.get('user_id')
                        
                        if document_id and uploader_id:
                            notification_service.notify_document_uploaded(document_id, uploader_id)
                    
                    elif notification_type == 'document_shared':
                        document_id = kwargs.get('document_id') or notification_kwargs.get('document_id')
                        shared_with_id = kwargs.get('shared_with_id') or notification_kwargs.get('shared_with_id')
                        shared_by_id = kwargs.get('shared_by_id') or notification_kwargs.get('shared_by_id')
                        
                        if document_id and shared_with_id and shared_by_id:
                            notification_service.notify_document_shared(document_id, shared_with_id, shared_by_id)
                    
                    elif notification_type == 'document_commented':
                        document_id = kwargs.get('document_id') or notification_kwargs.get('document_id')
                        commenter_id = kwargs.get('commenter_id') or notification_kwargs.get('commenter_id')
                        comment_text = kwargs.get('comment_text') or notification_kwargs.get('comment_text', '')
                        
                        if document_id and commenter_id:
                            notification_service.notify_document_commented(document_id, commenter_id, comment_text)
                
                return result
                
            except Exception as e:
                logger.error(f"Erreur dans le middleware de notifications: {str(e)}")
                # Retourner le résultat original même en cas d'erreur de notification
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def notify_on_success(notification_func, *notification_args, **notification_kwargs):
    """
    Décorateur générique pour envoyer une notification en cas de succès
    
    Args:
        notification_func: Fonction de notification à appeler
        *notification_args: Arguments pour la fonction de notification
        **notification_kwargs: Arguments nommés pour la fonction de notification
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Vérifier si l'opération a réussi
                success = False
                if hasattr(result, 'status_code'):
                    success = result.status_code < 400
                elif isinstance(result, tuple) and len(result) == 2:
                    # Format (data, status_code)
                    success = result[1] < 400
                elif isinstance(result, dict) and 'error' not in result:
                    success = True
                
                if success:
                    try:
                        notification_func(*notification_args, **notification_kwargs)
                        logger.info(f"Notification envoyée: {notification_func.__name__}")
                    except Exception as e:
                        logger.error(f"Erreur notification: {str(e)}")
                
                return result
                
            except Exception as e:
                logger.error(f"Erreur dans notify_on_success: {str(e)}")
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Décorateurs spécialisés pour chaque type d'action
def notify_document_upload(document_id_key='document_id', user_id_key='user_id'):
    """Décorateur pour notifier l'upload d'un document"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            try:
                # Extraire les IDs depuis les kwargs ou le résultat
                document_id = kwargs.get(document_id_key)
                user_id = kwargs.get(user_id_key)
                
                if document_id and user_id:
                    notification_service.notify_document_uploaded(document_id, user_id)
            except Exception as e:
                logger.error(f"Erreur notification upload: {str(e)}")
            
            return result
        return wrapper
    return decorator

def notify_document_share(doc_id_key='doc_id', shared_with_key='shared_with_id', shared_by_key='shared_by_id'):
    """Décorateur pour notifier le partage d'un document"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            try:
                document_id = kwargs.get(doc_id_key)
                shared_with_id = kwargs.get(shared_with_key)
                shared_by_id = kwargs.get(shared_by_key)
                
                if document_id and shared_with_id and shared_by_id:
                    notification_service.notify_document_shared(document_id, shared_with_id, shared_by_id)
            except Exception as e:
                logger.error(f"Erreur notification partage: {str(e)}")
            
            return result
        return wrapper
    return decorator
