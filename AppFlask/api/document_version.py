from flask import Blueprint, request, jsonify, send_file
from ..models.document_version import DocumentVersion
from ..models.document_comment import DocumentComment
from .auth import token_required
import os
import tempfile
import shutil

bp = Blueprint('document_version', __name__, url_prefix='/api/documents')

@bp.route('/<int:document_id>/versions', methods=['GET'])
@token_required
def get_document_versions(current_user, document_id):
    """
    Récupère toutes les versions d'un document
    """
    try:
        # Version simplifiée sans dépendance à created_by
        from ..db import db_connection
        from psycopg2.extras import RealDictCursor
        
        conn = db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Erreur de connexion à la base de données'
            }), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Requête sans created_by pour éviter l'erreur
        cursor.execute("""
            SELECT v.id, v.document_id, v.version_number, v.fichier, 
                   v.taille, v.mime_type, v.commentaire, v.created_at,
                   'Utilisateur' as created_by_name
            FROM document_version v
            WHERE v.document_id = %s
            ORDER BY v.version_number DESC
        """, (document_id,))
        
        versions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        versions_data = []
        for version in versions:
            version_dict = dict(version)
            if version_dict.get('created_at'):
                version_dict['created_at'] = version_dict['created_at'].isoformat()
            versions_data.append(version_dict)
        
        return jsonify({
            'success': True,
            'versions': versions_data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération des versions: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/versions/<int:version_number>', methods=['GET'])
@token_required
def get_document_version(current_user, document_id, version_number):
    """
    Récupère une version spécifique d'un document
    """
    try:
        version = DocumentVersion.get_version_by_number(document_id, version_number)
        
        if not version:
            return jsonify({
                'success': False,
                'message': 'Version non trouvée'
            }), 404
        
        version_dict = DocumentVersion.to_dict(version)
        
        return jsonify({
            'success': True,
            'version': version_dict
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la récupération de la version: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/versions/<int:version_number>/download', methods=['GET'])
@token_required
def download_document_version(current_user, document_id, version_number):
    """
    Télécharge une version spécifique d'un document
    """
    try:
        version = DocumentVersion.get_version_by_number(document_id, version_number)
        
        if not version:
            return jsonify({
                'success': False,
                'message': 'Version non trouvée'
            }), 404
        
        # Vérifier si le fichier existe
        if not version['fichier'] or not os.path.exists(version['fichier']):
            return jsonify({
                'success': False,
                'message': 'Fichier de version non trouvé'
            }), 404
        
        return send_file(
            version['fichier'],
            as_attachment=True,
            download_name=f"document_v{version_number}_{os.path.basename(version['fichier'])}"
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors du téléchargement: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/versions/restore', methods=['POST'])
@token_required
def restore_document_version(current_user, document_id):
    """
    Restaure une version antérieure comme version actuelle
    """
    try:
        data = request.get_json()
        version_number = data.get('version_number')
        
        if not version_number:
            return jsonify({
                'success': False,
                'message': 'Numéro de version requis'
            }), 400
        
        success = DocumentVersion.restore_version(document_id, version_number, current_user['id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Version {version_number} restaurée avec succès'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de la restauration'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la restauration: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/versions/<int:version_id>/delete', methods=['DELETE'])
@token_required
def delete_document_version(current_user, document_id, version_id):
    """
    Supprime une version spécifique (sauf la version courante)
    """
    try:
        success = DocumentVersion.delete_version(version_id, current_user['id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Version supprimée avec succès'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Impossible de supprimer cette version'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la suppression: {str(e)}'
        }), 500

@bp.route('/<int:document_id>/versions/compare', methods=['POST'])
@token_required
def compare_document_versions(current_user, document_id):
    """
    Compare deux versions d'un document
    """
    try:
        data = request.get_json()
        version1 = data.get('version1')
        version2 = data.get('version2')
        
        if not version1 or not version2:
            return jsonify({
                'success': False,
                'message': 'Deux numéros de version requis'
            }), 400
        
        v1_data = DocumentVersion.get_version_by_number(document_id, version1)
        v2_data = DocumentVersion.get_version_by_number(document_id, version2)
        
        if not v1_data or not v2_data:
            return jsonify({
                'success': False,
                'message': 'Une ou plusieurs versions non trouvées'
            }), 404
        
        # Comparaison basique des métadonnées
        comparison = {
            'version1': DocumentVersion.to_dict(v1_data),
            'version2': DocumentVersion.to_dict(v2_data),
            'differences': {
                'size_diff': v2_data['taille'] - v1_data['taille'],
                'time_diff': (v2_data['created_at'] - v1_data['created_at']).total_seconds(),
                'mime_type_changed': v1_data['mime_type'] != v2_data['mime_type']
            }
        }
        
        return jsonify({
            'success': True,
            'comparison': comparison
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur lors de la comparaison: {str(e)}'
        }), 500 