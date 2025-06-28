from flask import Blueprint, request, jsonify, g, current_app
from AppFlask.models.folder import Folder
from AppFlask.api.auth import token_required, log_user_action
from AppFlask.models.history import History
import json
from sqlalchemy.exc import SQLAlchemyError
from AppFlask.db import db_connection

folder_bp = Blueprint('folder', __name__)

@folder_bp.route('/', methods=['OPTIONS'])
def handle_options():
    """
    Gère les requêtes OPTIONS pour la route racine
    """
    response = current_app.make_default_options_response()
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@folder_bp.route('/<int:folder_id>', methods=['OPTIONS'])
def handle_folder_options(folder_id):
    """
    Gère les requêtes OPTIONS pour les routes avec ID
    """
    response = current_app.make_default_options_response()
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@folder_bp.route('/', methods=['POST'])
@token_required
def create_folder(current_user):
    """
    Crée un nouveau dossier
    """
    try:
        # Log des informations de débogage
        print("Tentative de création de dossier")
        print(f"User ID: {current_user['id']}")
        
        # Récupérer et valider les données
        data = request.json
        print(f"Données reçues: {data}")
        
        if not data:
            print("Erreur: Aucune donnée reçue")
            return jsonify({
                'status': 'error',
                'message': 'Aucune donnée fournie'
            }), 400
        
        if 'titre' not in data or not data['titre']:
            print("Erreur: Titre manquant")
            return jsonify({
                'status': 'error',
                'message': 'Le titre du dossier est requis'
            }), 400
        
        title = data['titre']
        description = data.get('description', '')
        parent_id = data.get('parent_id')
        
        print(f"Création du dossier: titre={title}, description={description}, parent_id={parent_id}")
        
        # Créer le dossier
        folder_id = Folder.create(
            title=title,
            description=description,
            parent_id=parent_id,
            owner_id=current_user['id']
        )
        
        print(f"Dossier créé avec l'ID: {folder_id}")
        
        # Enregistrer dans l'historique
        History.create(
            action_type='CREATE_FOLDER',
            entity_type='FOLDER',
            entity_id=folder_id,
            entity_name=title,
            description=f"Création du dossier {title}",
            metadata=json.dumps({
                'folder_id': folder_id,
                'parent_id': parent_id,
                'description': description
            }),
            user_id=current_user['id']
        )
        
        print("Historique enregistré")
        
        # Enregistrer aussi dans system_logs
        log_user_action(
            current_user['id'], 
            'FOLDER_CREATE', 
            f"Création du dossier '{title}' (ID: {folder_id})",
            request
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Dossier créé avec succès',
            'data': {'folder_id': folder_id}
        }), 201
    except Exception as e:
        print(f"Erreur lors de la création du dossier: {str(e)}")
        import traceback
        print(traceback.format_exc())
        current_app.logger.error(f"Erreur lors de la création du dossier: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@folder_bp.route('/<int:folder_id>', methods=['GET'])
@token_required
def get_folder(folder_id):
    """
    Récupère les informations d'un dossier
    """
    try:
        folder = Folder.get_folder(folder_id)
        
        if not folder:
            return jsonify({
                'status': 'error',
                'message': 'Dossier non trouvé'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': Folder.to_dict(folder)
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération du dossier: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@folder_bp.route('/', methods=['GET'])
@token_required
def get_root_folders(current_user):
    """
    Récupère tous les dossiers racine
    """
    try:
        parent_id = request.args.get('parent_id')
        
        # Convertir parent_id vide ou None en None
        if parent_id == '' or parent_id is None:
            parent_id = None
        else:
            try:
                parent_id = int(parent_id)
            except ValueError:
                parent_id = None
        
        print(f"DEBUG: Récupération des dossiers avec parent_id={parent_id}")
        folders = Folder.get_subfolders(parent_id)
        print(f"DEBUG: Nombre de dossiers trouvés: {len(folders)}")
        
        return jsonify([Folder.to_dict(folder) for folder in folders])
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des dossiers: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@folder_bp.route('/<int:folder_id>', methods=['PUT'])
@token_required
def update_folder(folder_id):
    """
    Met à jour un dossier
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Aucune donnée fournie'
            }), 400
        
        title = data.get('titre')
        description = data.get('description')
        parent_id = data.get('parent_id')
        
        success = Folder.update(
            folder_id=folder_id,
            title=title,
            description=description,
            parent_id=parent_id
        )
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Impossible de mettre à jour le dossier'
            }), 400
        
        # Enregistrer dans l'historique
        History.create(
            action_type='UPDATE_FOLDER',
            entity_type='FOLDER',
            entity_id=folder_id,
            entity_name=title if title else "Dossier",
            description=f"Mise à jour du dossier {folder_id}",
            metadata=json.dumps({
                'folder_id': folder_id,
                'title': title,
                'description': description,
                'parent_id': parent_id
            }),
            user_id=g.current_user['id']
        )
        
        # Enregistrer aussi dans system_logs
        log_user_action(
            g.current_user['id'], 
            'FOLDER_EDIT', 
            f"Modification du dossier '{title}' (ID: {folder_id})",
            request
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Dossier mis à jour avec succès'
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la mise à jour du dossier: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@folder_bp.route('/<int:folder_id>', methods=['DELETE'])
@token_required
def delete_folder(folder_id):
    """
    Supprime un dossier (le déplace dans la corbeille)
    """
    try:
        success = Folder.delete(folder_id)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Dossier non trouvé'
            }), 404
        
        # Enregistrer dans l'historique
        History.create(
            action_type='DELETE_FOLDER',
            entity_type='FOLDER',
            entity_id=folder_id,
            entity_name=f"Dossier {folder_id}",
            description=f"Suppression du dossier {folder_id}",
            metadata=json.dumps({
                'folder_id': folder_id
            }),
            user_id=g.current_user['id']
        )
        
        # Enregistrer aussi dans system_logs
        log_user_action(
            g.current_user['id'], 
            'FOLDER_DELETE', 
            f"Suppression du dossier (ID: {folder_id})",
            request
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Dossier supprimé avec succès'
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la suppression du dossier: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@folder_bp.route('/<int:folder_id>/breadcrumb', methods=['GET'])
@token_required
def get_breadcrumb(folder_id, current_user):
    """
    Récupère le fil d'Ariane pour un dossier
    """
    try:
        breadcrumb = Folder.get_breadcrumb(folder_id)
        
        return jsonify(breadcrumb)
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération du fil d'Ariane: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@folder_bp.route('/<int:folder_id>/children', methods=['GET'])
@token_required
def get_folder_children(folder_id, current_user):
    """
    Récupère les sous-dossiers d'un dossier spécifique
    """
    try:
        print(f"DEBUG: Récupération des enfants du dossier {folder_id}")
        folders = Folder.get_subfolders(folder_id)
        print(f"DEBUG: Nombre de sous-dossiers trouvés: {len(folders)}")
        
        return jsonify({
            'status': 'success',
            'data': [Folder.to_dict(folder) for folder in folders]
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des sous-dossiers: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500











 