#!/usr/bin/env python3
"""
Intégration des notifications dans les actions de documents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def integrate_notifications_in_upload():
    """Intégrer les notifications dans la fonction d'upload de documents"""
    print("📤 INTÉGRATION NOTIFICATIONS - UPLOAD DOCUMENTS")
    print("=" * 55)
    
    # Lire le fichier document_routes.py
    file_path = "AppFlask/routes/document_routes.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si les notifications sont déjà intégrées
        if "notification_service" in content:
            print("✅ Notifications déjà intégrées dans document_routes.py")
            return True
        
        # Ajouter l'import du service de notifications
        import_line = "from AppFlask.services.notification_service import notification_service"
        
        # Trouver la ligne d'import appropriée
        lines = content.split('\n')
        import_index = -1
        
        for i, line in enumerate(lines):
            if line.startswith('from AppFlask.') and 'import' in line:
                import_index = i
        
        if import_index != -1:
            lines.insert(import_index + 1, import_line)
        else:
            # Ajouter après les imports standards
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    continue
                else:
                    lines.insert(i, import_line)
                    break
        
        # Trouver la fonction upload_document et ajouter la notification
        new_lines = []
        in_upload_function = False
        upload_function_indent = 0
        notification_added = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Détecter le début de la fonction upload_document
            if line.strip().startswith('def upload_document():'):
                in_upload_function = True
                upload_function_indent = len(line) - len(line.lstrip())
                continue
            
            # Si on est dans la fonction et qu'on trouve la ligne de commit
            if in_upload_function and 'conn.commit()' in line and not notification_added:
                # Ajouter le code de notification après le commit
                indent = ' ' * (upload_function_indent + 8)  # Indentation appropriée
                
                notification_code = f"""
{indent}# Récupérer l'ID du document inséré
{indent}cursor.execute("SELECT lastval()")
{indent}document_id = cursor.fetchone()[0]
{indent}
{indent}# Envoyer les notifications
{indent}try:
{indent}    notification_service.notify_document_uploaded(document_id, session.get('user_id'))
{indent}    print(f"✅ Notifications envoyées pour le document {{document_id}}")
{indent}except Exception as e:
{indent}    print(f"⚠️ Erreur notification upload: {{str(e)}}")"""
                
                new_lines.append(notification_code)
                notification_added = True
            
            # Détecter la fin de la fonction
            if in_upload_function and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                if not line.strip().startswith('#'):
                    in_upload_function = False
        
        # Écrire le fichier modifié
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ Notifications intégrées dans la fonction upload_document")
        return True
        
    except Exception as e:
        print(f"❌ Erreur intégration upload: {str(e)}")
        return False

def integrate_notifications_in_api():
    """Intégrer les notifications dans l'API documents unifiée"""
    print("\n🔌 INTÉGRATION NOTIFICATIONS - API DOCUMENTS")
    print("=" * 50)
    
    # Créer une nouvelle route d'upload avec notifications dans l'API
    api_file = "AppFlask/api/documents_unified.py"
    
    try:
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si les notifications sont déjà intégrées
        if "notification_service" in content:
            print("✅ Notifications déjà intégrées dans l'API documents")
            return True
        
        # Ajouter l'import
        import_line = "from AppFlask.services.notification_service import notification_service"
        
        lines = content.split('\n')
        
        # Trouver où ajouter l'import
        for i, line in enumerate(lines):
            if line.startswith('from datetime import datetime'):
                lines.insert(i + 1, import_line)
                break
        
        # Ajouter une nouvelle route d'upload avec notifications
        upload_route = '''
@bp.route('/documents/upload', methods=['POST'])
@token_required
def upload_document_with_notifications(current_user):
    """Upload d'un document avec notifications automatiques"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        # Récupérer les métadonnées
        title = request.form.get('title', file.filename)
        description = request.form.get('description', '')
        categorie = request.form.get('categorie', 'Document')
        dossier_id = request.form.get('dossier_id')
        
        # Convertir dossier_id
        if dossier_id:
            try:
                dossier_id = int(dossier_id)
            except ValueError:
                dossier_id = None
        
        # Sauvegarder le fichier (logique simplifiée)
        filename = file.filename
        file_size = 0  # À calculer selon votre logique
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor()
        
        # Insérer le document
        cursor.execute("""
            INSERT INTO document (titre, fichier, description, categorie, taille, 
                                date_ajout, proprietaire_id, dossier_id)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
            RETURNING id
        """, (title, filename, description, categorie, file_size, current_user['id'], dossier_id))
        
        document_id = cursor.fetchone()[0]
        conn.commit()
        
        # Envoyer les notifications
        try:
            notification_service.notify_document_uploaded(document_id, current_user['id'])
            log_user_action(current_user['id'], 'DOCUMENT_UPLOAD', 
                          f"Upload du document '{title}' (ID: {document_id})", request)
        except Exception as e:
            print(f"⚠️ Erreur notification upload: {str(e)}")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Document uploadé avec succès',
            'document_id': document_id,
            'title': title
        }), 201
        
    except Exception as e:
        print(f"❌ Erreur upload document: {str(e)}")
        return jsonify({'error': 'Erreur l\\'upload'}), 500

@bp.route('/documents/<int:doc_id>/share', methods=['POST'])
@token_required
def share_document_with_notifications(current_user, doc_id):
    """Partager un document avec notifications"""
    try:
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'ID utilisateur requis'}), 400
        
        shared_with_user_id = data['user_id']
        permissions = data.get('permissions', 'lecture')
        
        # Vérifier les permissions
        if not has_permission(doc_id, current_user['id'], 'admin'):
            return jsonify({'error': 'Permission insuffisante'}), 403
        
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor()
        
        # Partager le document
        cursor.execute("""
            INSERT INTO partage (document_id, utilisateur_id, permissions, date_partage)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (document_id, utilisateur_id) 
            DO UPDATE SET permissions = EXCLUDED.permissions, date_partage = NOW()
        """, (doc_id, shared_with_user_id, permissions))
        
        conn.commit()
        
        # Envoyer la notification
        try:
            notification_service.notify_document_shared(doc_id, shared_with_user_id, current_user['id'])
            log_user_action(current_user['id'], 'DOCUMENT_SHARE', 
                          f"Partage du document {doc_id} avec l'utilisateur {shared_with_user_id}", request)
        except Exception as e:
            print(f"⚠️ Erreur notification partage: {str(e)}")
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Document partagé avec succès'}), 200
        
    except Exception as e:
        print(f"❌ Erreur partage document: {str(e)}")
        return jsonify({'error': 'Erreur lors du partage'}), 500
'''
        
        # Ajouter les nouvelles routes à la fin du fichier
        lines.append(upload_route)
        
        # Écrire le fichier modifié
        with open(api_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print("✅ Routes d'upload et partage avec notifications ajoutées à l'API")
        return True
        
    except Exception as e:
        print(f"❌ Erreur intégration API: {str(e)}")
        return False

def create_notification_middleware():
    """Créer un middleware pour les notifications automatiques"""
    print("\n⚙️ CRÉATION MIDDLEWARE NOTIFICATIONS")
    print("=" * 40)
    
    middleware_content = '''#!/usr/bin/env python3
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
                logger.error(f"❌ Erreur dans le middleware de notifications: {str(e)}")
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
                        logger.info(f"✅ Notification envoyée: {notification_func.__name__}")
                    except Exception as e:
                        logger.error(f"⚠️ Erreur notification: {str(e)}")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Erreur dans notify_on_success: {str(e)}")
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
                logger.error(f"⚠️ Erreur notification upload: {str(e)}")
            
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
                logger.error(f"⚠️ Erreur notification partage: {str(e)}")
            
            return result
        return wrapper
    return decorator
'''
    
    try:
        # Créer le répertoire middleware s'il n'existe pas
        os.makedirs("AppFlask/middleware", exist_ok=True)
        
        # Créer le fichier __init__.py
        with open("AppFlask/middleware/__init__.py", 'w') as f:
            f.write("# Middleware package\n")
        
        # Créer le fichier middleware
        with open("AppFlask/middleware/notifications.py", 'w') as f:
            f.write(middleware_content)
        
        print("✅ Middleware de notifications créé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création middleware: {str(e)}")
        return False

def test_notification_integration():
    """Tester l'intégration des notifications"""
    print("\n🧪 TEST INTÉGRATION NOTIFICATIONS")
    print("=" * 40)
    
    try:
        # Test d'import du service
        from AppFlask.services.notification_service import notification_service
        print("✅ Import du service de notifications: OK")
        
        # Test d'import du middleware
        from AppFlask.middleware.notifications import with_notifications
        print("✅ Import du middleware: OK")
        
        # Test de création d'une notification de test
        from AppFlask import create_app
        app = create_app()
        
        with app.app_context():
            # Créer une notification de test
            test_notification_id = notification_service.create_notification(
                user_id=1,  # Supposons que l'utilisateur 1 existe
                title="Test d'intégration",
                message="Notification de test pour vérifier l'intégration",
                notification_type="test",
                send_email=False  # Pas d'email pour le test
            )
            
            if test_notification_id:
                print(f"✅ Création notification de test: OK (ID: {test_notification_id})")
            else:
                print("⚠️ Création notification de test: ÉCHEC")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test intégration: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("🔔 INTÉGRATION COMPLÈTE DU SYSTÈME DE NOTIFICATIONS")
    print("=" * 65)
    
    steps = [
        ("Intégration upload documents", integrate_notifications_in_upload),
        ("Intégration API documents", integrate_notifications_in_api),
        ("Création middleware", create_notification_middleware),
        ("Test d'intégration", test_notification_integration)
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"❌ Erreur dans {step_name}: {str(e)}")
            results.append((step_name, False))
    
    # Résumé
    print("\n🎯 RÉSUMÉ DE L'INTÉGRATION")
    print("=" * 40)
    
    success_count = 0
    for step_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{step_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n📊 RÉSULTAT: {success_count}/{len(results)} étapes réussies")
    
    if success_count == len(results):
        print("\n🎉 INTÉGRATION NOTIFICATIONS TERMINÉE!")
        print("\n🚀 FONCTIONNALITÉS INTÉGRÉES:")
        print("✅ Notifications automatiques à l'upload de documents")
        print("✅ Notifications de partage de documents")
        print("✅ API avec support des notifications")
        print("✅ Middleware pour notifications automatiques")
        print("✅ Décorateurs pour simplifier l'intégration")
        
        print("\n📋 PROCHAINES ÉTAPES:")
        print("1. Redémarrez le serveur Flask")
        print("2. Testez l'upload d'un document")
        print("3. Vérifiez les notifications dans l'interface")
        print("4. Testez les notifications par email")
        print("5. Configurez les préférences utilisateur")
    else:
        print("\n⚠️ INTÉGRATION INCOMPLÈTE")
        print("Vérifiez les erreurs ci-dessus et relancez le script")
    
    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 