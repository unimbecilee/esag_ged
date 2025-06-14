from flask import Blueprint, request, jsonify, g, current_app, send_from_directory
from AppFlask.models.document_version import DocumentVersion
from AppFlask.api.auth import token_required
from AppFlask.models.history import History
from werkzeug.utils import secure_filename
import os
import json
import mimetypes
from datetime import datetime

version_bp = Blueprint('version', __name__, url_prefix='/versions')

@version_bp.route('/document/<int:document_id>', methods=['GET'])
@token_required
def get_document_versions(document_id):
    """
    Récupère toutes les versions d'un document
    """
    try:
        versions = DocumentVersion.get_versions(document_id)
        return jsonify({
            'status': 'success',
            'data': [DocumentVersion.to_dict(version) for version in versions]
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des versions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@version_bp.route('/document/<int:document_id>', methods=['POST'])
@token_required
def add_document_version(document_id):
    """
    Ajoute une nouvelle version à un document
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'Aucun fichier fourni'
            }), 400
            
        file = request.files['file']
        commentaire = request.form.get('commentaire', '')
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'Nom de fichier vide'
            }), 400
        
        # Sauvegarder le fichier
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(filepath)
        
        # Récupérer les informations du fichier
        file_size = os.path.getsize(filepath)
        mime_type = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
        
        # Créer la nouvelle version
        version_id, version_number = DocumentVersion.create(
            document_id=document_id,
            fichier=unique_filename,
            taille=file_size,
            mime_type=mime_type,
            commentaire=commentaire,
            created_by=g.current_user['id']
        )
        
        # Enregistrer dans l'historique
        History.create(
            action_type='CREATE_VERSION',
            entity_type='DOCUMENT',
            entity_id=document_id,
            entity_name=f"Version {version_number}",
            description=f"Nouvelle version {version_number} ajoutée au document {document_id}",
            metadata=json.dumps({
                'document_id': document_id,
                'version_number': version_number,
                'commentaire': commentaire,
                'taille': file_size,
                'mime_type': mime_type
            }),
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Nouvelle version ajoutée avec succès',
            'data': {
                'version_id': version_id,
                'version_number': version_number
            }
        }), 201
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'ajout d'une version: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@version_bp.route('/<int:version_id>', methods=['GET'])
@token_required
def get_version(version_id):
    """
    Récupère une version spécifique
    """
    try:
        version = DocumentVersion.get_version(version_id)
        
        if not version:
            return jsonify({
                'status': 'error',
                'message': 'Version non trouvée'
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': DocumentVersion.to_dict(version)
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération de la version: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@version_bp.route('/document/<int:document_id>/number/<int:version_number>', methods=['GET'])
@token_required
def get_version_by_number(document_id, version_number):
    """
    Récupère une version spécifique par son numéro
    """
    try:
        version = DocumentVersion.get_version_by_number(document_id, version_number)
        
        if not version:
            return jsonify({
                'status': 'error',
                'message': 'Version non trouvée'
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': DocumentVersion.to_dict(version)
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération de la version: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@version_bp.route('/document/<int:document_id>/restore/<int:version_number>', methods=['POST'])
@token_required
def restore_version(document_id, version_number):
    """
    Restaure une version antérieure comme version actuelle
    """
    try:
        success = DocumentVersion.restore_version(
            document_id=document_id,
            version_number=version_number,
            restored_by=g.current_user['id']
        )
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Impossible de restaurer la version'
            }), 400
            
        # Enregistrer dans l'historique
        History.create(
            action_type='RESTORE_VERSION',
            entity_type='DOCUMENT',
            entity_id=document_id,
            entity_name=f"Version {version_number}",
            description=f"Restauration de la version {version_number} du document {document_id}",
            metadata=json.dumps({
                'document_id': document_id,
                'version_number': version_number
            }),
            user_id=g.current_user['id']
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Version {version_number} restaurée avec succès'
        })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la restauration de la version: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@version_bp.route('/download/<int:version_id>', methods=['GET'])
@token_required
def download_version(version_id):
    """
    Télécharge une version spécifique d'un document
    """
    try:
        version = DocumentVersion.get_version(version_id)
        
        if not version:
            return jsonify({
                'status': 'error',
                'message': 'Version non trouvée'
            }), 404
            
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], version['fichier'])
        
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': 'Fichier non trouvé sur le serveur'
            }), 404
            
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            version['fichier'],
            as_attachment=True
        )
    except Exception as e:
        current_app.logger.error(f"Erreur lors du téléchargement de la version: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500