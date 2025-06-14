#!/usr/bin/env python3
"""
API unifiée pour le système de corbeille ESAG GED
Gestion complète de la corbeille avec configuration automatique
"""

from flask import Blueprint, request, jsonify, current_app
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import logging
import json
import os

# Import du décorateur d'authentification
from AppFlask.api.auth import token_required, log_user_action

logger = logging.getLogger(__name__)

bp = Blueprint('trash_unified', __name__)

# ================================
# ROUTES PRINCIPALES DE LA CORBEILLE
# ================================

@bp.route('/trash', methods=['GET'])
@token_required
def get_trash_items(current_user):
    """Récupérer les éléments de la corbeille avec filtres et pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        item_type = request.args.get('type')  # document, folder, etc.
        user_filter = request.args.get('user_filter', 'own')  # own, all (admin only)
        search = request.args.get('search', '')
        
        offset = (page - 1) * per_page
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Construire la requête selon les filtres
        where_conditions = ["t.restored_at IS NULL", "t.permanent_delete_at IS NULL"]
        params = []
        
        # Filtrer par utilisateur
        if user_filter == 'own' or current_user['role'].lower() != 'admin':
            where_conditions.append("t.deleted_by = %s")
            params.append(current_user['id'])
        
        # Filtrer par type d'élément
        if item_type:
            where_conditions.append("t.item_type = %s")
            params.append(item_type)
        
        # Recherche dans les métadonnées
        if search:
            where_conditions.append("(t.item_data->>'titre' ILIKE %s OR t.item_data->>'nom' ILIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        where_clause = " AND ".join(where_conditions)
        
        # Compter le total
        cursor.execute(f"""
            SELECT COUNT(*) as total 
            FROM trash t
            WHERE {where_clause}
        """, params)
        
        total = cursor.fetchone()['total']
        
        # Récupérer les éléments avec informations utilisateur
        cursor.execute(f"""
            SELECT t.*, 
                   u1.prenom || ' ' || u1.nom as deleted_by_name,
                   u2.prenom || ' ' || u2.nom as restored_by_name,
                   EXTRACT(DAY FROM (CURRENT_TIMESTAMP - t.deleted_at)) as days_in_trash,
                   tc.setting_value::INTEGER - EXTRACT(DAY FROM (CURRENT_TIMESTAMP - t.deleted_at)) as days_until_deletion
            FROM trash t
            LEFT JOIN utilisateur u1 ON t.deleted_by = u1.id
            LEFT JOIN utilisateur u2 ON t.restored_by = u2.id
            CROSS JOIN trash_config tc
            WHERE {where_clause} AND tc.setting_name = 'retention_days'
            ORDER BY t.deleted_at DESC
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        
        items = cursor.fetchall()
        
        # Formater les données pour le frontend
        formatted_items = []
        for item in items:
            item_dict = dict(item)
            
            # Parser les métadonnées JSON
            if item_dict['item_data']:
                item_dict['metadata'] = item_dict['item_data']
                item_dict['title'] = item_dict['item_data'].get('titre') or item_dict['item_data'].get('nom', 'Sans titre')
                item_dict['description'] = item_dict['item_data'].get('description', '')
                item_dict['size'] = item_dict['item_data'].get('taille', 0)
                item_dict['file_type'] = item_dict['item_data'].get('mime_type', 'unknown')
            
            # Formater les dates
            if item_dict['deleted_at']:
                item_dict['deleted_at'] = item_dict['deleted_at'].isoformat()
            if item_dict['restored_at']:
                item_dict['restored_at'] = item_dict['restored_at'].isoformat()
            if item_dict['permanent_delete_at']:
                item_dict['permanent_delete_at'] = item_dict['permanent_delete_at'].isoformat()
            
            formatted_items.append(item_dict)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'items': formatted_items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'has_next': (page * per_page) < total,
            'has_prev': page > 1
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur récupération corbeille: {str(e)}")
        return jsonify({'message': 'Erreur lors de la récupération des éléments'}), 500

@bp.route('/trash/<int:trash_id>/restore', methods=['POST'])
@token_required
def restore_item(current_user, trash_id):
    """Restaurer un élément depuis la corbeille"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer l'élément
        cursor.execute("""
            SELECT * FROM trash 
            WHERE id = %s AND restored_at IS NULL AND permanent_delete_at IS NULL
        """, (trash_id,))
        
        trash_item = cursor.fetchone()
        if not trash_item:
            return jsonify({'message': 'Élément non trouvé dans la corbeille'}), 404
        
        # Vérifier les permissions
        if current_user['role'].lower() != 'admin' and trash_item['deleted_by'] != current_user['id']:
            return jsonify({'message': 'Permission insuffisante'}), 403
        
        # Restaurer selon le type d'élément
        if trash_item['item_type'] == 'document':
            success = restore_document(cursor, trash_item, current_user['id'])
        elif trash_item['item_type'] == 'folder':
            success = restore_folder(cursor, trash_item, current_user['id'])
        else:
            return jsonify({'message': f'Type d\'élément non supporté: {trash_item["item_type"]}'}), 400
        
        if not success:
            return jsonify({'message': 'Erreur lors de la restauration'}), 500
        
        # Marquer comme restauré
        cursor.execute("""
            UPDATE trash 
            SET restored_at = CURRENT_TIMESTAMP, restored_by = %s
            WHERE id = %s
        """, (current_user['id'], trash_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log de l'action
        log_user_action(
            current_user['id'],
            'RESTORE_FROM_TRASH',
            f"Restauration de {trash_item['item_type']}: {trash_item['item_data'].get('titre', 'Sans titre')}",
            request
        )
        
        return jsonify({'message': 'Élément restauré avec succès'}), 200
        
    except Exception as e:
        logger.error(f"Erreur restauration: {str(e)}")
        return jsonify({'message': 'Erreur lors de la restauration'}), 500

@bp.route('/trash/<int:trash_id>', methods=['DELETE'])
@token_required
def delete_permanently(current_user, trash_id):
    """Supprimer définitivement un élément de la corbeille"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer l'élément
        cursor.execute("""
            SELECT * FROM trash 
            WHERE id = %s AND restored_at IS NULL AND permanent_delete_at IS NULL
        """, (trash_id,))
        
        trash_item = cursor.fetchone()
        if not trash_item:
            return jsonify({'message': 'Élément non trouvé dans la corbeille'}), 404
        
        # Vérifier les permissions
        if current_user['role'].lower() != 'admin' and trash_item['deleted_by'] != current_user['id']:
            return jsonify({'message': 'Permission insuffisante'}), 403
        
        # Supprimer le fichier physique si c'est un document
        if trash_item['item_type'] == 'document' and trash_item['item_data'].get('fichier'):
            file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 
                                   trash_item['item_data']['fichier'])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Impossible de supprimer le fichier {file_path}: {e}")
        
        # Marquer comme supprimé définitivement
        cursor.execute("""
            UPDATE trash 
            SET permanent_delete_at = CURRENT_TIMESTAMP, permanent_delete_by = %s
            WHERE id = %s
        """, (current_user['id'], trash_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log de l'action
        log_user_action(
            current_user['id'],
            'PERMANENT_DELETE',
            f"Suppression définitive de {trash_item['item_type']}: {trash_item['item_data'].get('titre', 'Sans titre')}",
            request
        )
        
        return jsonify({'message': 'Élément supprimé définitivement'}), 200
        
    except Exception as e:
        logger.error(f"Erreur suppression définitive: {str(e)}")
        return jsonify({'message': 'Erreur lors de la suppression définitive'}), 500

@bp.route('/trash/bulk-restore', methods=['POST'])
@token_required
def bulk_restore(current_user):
    """Restaurer plusieurs éléments en une fois"""
    try:
        data = request.get_json()
        trash_ids = data.get('trash_ids', [])
        
        if not trash_ids:
            return jsonify({'message': 'Aucun élément sélectionné'}), 400
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        restored_count = 0
        errors = []
        
        for trash_id in trash_ids:
            try:
                # Récupérer l'élément
                cursor.execute("""
                    SELECT * FROM trash 
                    WHERE id = %s AND restored_at IS NULL AND permanent_delete_at IS NULL
                """, (trash_id,))
                
                trash_item = cursor.fetchone()
                if not trash_item:
                    errors.append(f"Élément {trash_id} non trouvé")
                    continue
                
                # Vérifier les permissions
                if current_user['role'].lower() != 'admin' and trash_item['deleted_by'] != current_user['id']:
                    errors.append(f"Permission insuffisante pour l'élément {trash_id}")
                    continue
                
                # Restaurer selon le type
                if trash_item['item_type'] == 'document':
                    success = restore_document(cursor, trash_item, current_user['id'])
                elif trash_item['item_type'] == 'folder':
                    success = restore_folder(cursor, trash_item, current_user['id'])
                else:
                    errors.append(f"Type non supporté pour l'élément {trash_id}")
                    continue
                
                if success:
                    # Marquer comme restauré
                    cursor.execute("""
                        UPDATE trash 
                        SET restored_at = CURRENT_TIMESTAMP, restored_by = %s
                        WHERE id = %s
                    """, (current_user['id'], trash_id))
                    restored_count += 1
                else:
                    errors.append(f"Erreur lors de la restauration de l'élément {trash_id}")
                    
            except Exception as e:
                errors.append(f"Erreur pour l'élément {trash_id}: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log de l'action
        log_user_action(
            current_user['id'],
            'BULK_RESTORE',
            f"Restauration en masse: {restored_count} éléments restaurés",
            request
        )
        
        return jsonify({
            'message': f'{restored_count} éléments restaurés avec succès',
            'restored_count': restored_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur restauration en masse: {str(e)}")
        return jsonify({'message': 'Erreur lors de la restauration en masse'}), 500

@bp.route('/trash/bulk-delete', methods=['DELETE'])
@token_required
def bulk_delete(current_user):
    """Supprimer définitivement plusieurs éléments en une fois"""
    try:
        data = request.get_json()
        trash_ids = data.get('trash_ids', [])
        
        if not trash_ids:
            return jsonify({'message': 'Aucun élément sélectionné'}), 400
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        deleted_count = 0
        errors = []
        
        for trash_id in trash_ids:
            try:
                # Récupérer l'élément
                cursor.execute("""
                    SELECT * FROM trash 
                    WHERE id = %s AND restored_at IS NULL AND permanent_delete_at IS NULL
                """, (trash_id,))
                
                trash_item = cursor.fetchone()
                if not trash_item:
                    errors.append(f"Élément {trash_id} non trouvé")
                    continue
                
                # Vérifier les permissions
                if current_user['role'].lower() != 'admin' and trash_item['deleted_by'] != current_user['id']:
                    errors.append(f"Permission insuffisante pour l'élément {trash_id}")
                    continue
                
                # Supprimer le fichier physique si nécessaire
                if trash_item['item_type'] == 'document' and trash_item['item_data'].get('fichier'):
                    file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 
                                           trash_item['item_data']['fichier'])
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logger.warning(f"Impossible de supprimer le fichier {file_path}: {e}")
                
                # Marquer comme supprimé définitivement
                cursor.execute("""
                    UPDATE trash 
                    SET permanent_delete_at = CURRENT_TIMESTAMP, permanent_delete_by = %s
                    WHERE id = %s
                """, (current_user['id'], trash_id))
                
                deleted_count += 1
                
            except Exception as e:
                errors.append(f"Erreur pour l'élément {trash_id}: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log de l'action
        log_user_action(
            current_user['id'],
            'BULK_DELETE',
            f"Suppression définitive en masse: {deleted_count} éléments supprimés",
            request
        )
        
        return jsonify({
            'message': f'{deleted_count} éléments supprimés définitivement',
            'deleted_count': deleted_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur suppression en masse: {str(e)}")
        return jsonify({'message': 'Erreur lors de la suppression en masse'}), 500

# ================================
# ROUTES DE CONFIGURATION
# ================================

@bp.route('/trash/config', methods=['GET'])
@token_required
def get_trash_config(current_user):
    """Récupérer la configuration de la corbeille"""
    try:
        # Seuls les admins peuvent voir la configuration complète
        if current_user['role'].lower() != 'admin':
            return jsonify({'message': 'Accès administrateur requis'}), 403
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT setting_name, setting_value, setting_type, description
            FROM trash_config
            ORDER BY setting_name
        """)
        
        configs = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Formater la configuration
        config_dict = {}
        for config in configs:
            value = config['setting_value']
            if config['setting_type'] == 'boolean':
                value = value.lower() == 'true'
            elif config['setting_type'] == 'integer':
                value = int(value)
            
            config_dict[config['setting_name']] = {
                'value': value,
                'type': config['setting_type'],
                'description': config['description']
            }
        
        return jsonify(config_dict), 200
        
    except Exception as e:
        logger.error(f"Erreur récupération config: {str(e)}")
        return jsonify({'message': 'Erreur lors de la récupération de la configuration'}), 500

@bp.route('/trash/config', methods=['PUT'])
@token_required
def update_trash_config(current_user):
    """Mettre à jour la configuration de la corbeille"""
    try:
        # Seuls les admins peuvent modifier la configuration
        if current_user['role'].lower() != 'admin':
            return jsonify({'message': 'Accès administrateur requis'}), 403
        
        data = request.get_json()
        
        conn = db_connection()
        cursor = conn.cursor()
        
        updated_count = 0
        for setting_name, setting_value in data.items():
            # Convertir la valeur en string pour le stockage
            if isinstance(setting_value, bool):
                value_str = 'true' if setting_value else 'false'
            else:
                value_str = str(setting_value)
            
            cursor.execute("""
                UPDATE trash_config 
                SET setting_value = %s, updated_at = CURRENT_TIMESTAMP
                WHERE setting_name = %s
            """, (value_str, setting_name))
            
            if cursor.rowcount > 0:
                updated_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log de l'action
        log_user_action(
            current_user['id'],
            'UPDATE_TRASH_CONFIG',
            f"Mise à jour de la configuration de la corbeille: {updated_count} paramètres modifiés",
            request
        )
        
        return jsonify({
            'message': f'{updated_count} paramètres mis à jour avec succès',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur mise à jour config: {str(e)}")
        return jsonify({'message': 'Erreur lors de la mise à jour de la configuration'}), 500

# ================================
# ROUTES DE STATISTIQUES
# ================================

@bp.route('/trash/stats', methods=['GET'])
@token_required
def get_trash_stats(current_user):
    """Récupérer les statistiques de la corbeille"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Statistiques selon le rôle
        if current_user['role'].lower() == 'admin':
            # Admin voit toutes les statistiques
            cursor.execute("SELECT get_trash_stats() as stats")
            stats = cursor.fetchone()['stats']
            
            cursor.execute("SELECT get_trash_size() as total_size")
            total_size = cursor.fetchone()['total_size']
        else:
            # Utilisateur normal voit seulement ses statistiques
            cursor.execute("SELECT get_trash_stats(%s) as stats", (current_user['id'],))
            stats = cursor.fetchone()['stats']
            
            cursor.execute("SELECT get_trash_size(%s) as total_size", (current_user['id'],))
            total_size = cursor.fetchone()['total_size']
        
        # Ajouter la taille totale aux statistiques
        stats['total_size_bytes'] = total_size
        stats['total_size_formatted'] = format_file_size(total_size)
        
        cursor.close()
        conn.close()
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Erreur statistiques: {str(e)}")
        return jsonify({'message': 'Erreur lors de la récupération des statistiques'}), 500

@bp.route('/trash/cleanup', methods=['POST'])
@token_required
def manual_cleanup(current_user):
    """Déclencher un nettoyage manuel de la corbeille"""
    try:
        # Seuls les admins peuvent déclencher un nettoyage manuel
        if current_user['role'].lower() != 'admin':
            return jsonify({'message': 'Accès administrateur requis'}), 403
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT cleanup_trash() as deleted_count")
        deleted_count = cursor.fetchone()['deleted_count']
        
        cursor.close()
        conn.close()
        
        # Log de l'action
        log_user_action(
            current_user['id'],
            'MANUAL_CLEANUP',
            f"Nettoyage manuel de la corbeille: {deleted_count} éléments supprimés",
            request
        )
        
        return jsonify({
            'message': f'Nettoyage terminé: {deleted_count} éléments supprimés définitivement',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur nettoyage manuel: {str(e)}")
        return jsonify({'message': 'Erreur lors du nettoyage manuel'}), 500

# ================================
# FONCTIONS UTILITAIRES
# ================================

def restore_document(cursor, trash_item, restored_by_id):
    """Restaurer un document depuis la corbeille"""
    try:
        item_data = trash_item['item_data']
        
        cursor.execute("""
            INSERT INTO document (
                titre, description, fichier, taille, mime_type,
                cloudinary_url, cloudinary_public_id, proprietaire_id,
                date_ajout, derniere_modification, modifie_par, dossier_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                titre = EXCLUDED.titre,
                description = EXCLUDED.description,
                derniere_modification = CURRENT_TIMESTAMP,
                modifie_par = %s
        """, (
            item_data.get('titre', 'Document restauré'),
            item_data.get('description', ''),
            item_data.get('fichier', ''),
            item_data.get('taille', 0),
            item_data.get('mime_type', ''),
            item_data.get('cloudinary_url', ''),
            item_data.get('cloudinary_public_id', ''),
            trash_item['deleted_by'],
            trash_item['deleted_at'],
            datetime.now(),
            restored_by_id,
            item_data.get('dossier_id'),
            restored_by_id
        ))
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur restauration document: {str(e)}")
        return False

def restore_folder(cursor, trash_item, restored_by_id):
    """Restaurer un dossier depuis la corbeille"""
    try:
        item_data = trash_item['item_data']
        
        cursor.execute("""
            INSERT INTO dossier (
                nom, description, proprietaire_id, parent_id,
                date_creation, derniere_modification
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                nom = EXCLUDED.nom,
                description = EXCLUDED.description,
                derniere_modification = CURRENT_TIMESTAMP
        """, (
            item_data.get('nom', 'Dossier restauré'),
            item_data.get('description', ''),
            trash_item['deleted_by'],
            item_data.get('parent_id'),
            trash_item['deleted_at'],
            datetime.now()
        ))
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur restauration dossier: {str(e)}")
        return False

def format_file_size(size_bytes):
    """Formater la taille d'un fichier en unités lisibles"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

# ================================
# ROUTES OPTIONS POUR CORS
# ================================

@bp.route('/trash', methods=['OPTIONS'])
def handle_trash_options():
    return '', 200

@bp.route('/trash/<int:trash_id>/restore', methods=['OPTIONS'])
def handle_restore_options(trash_id):
    return '', 200

@bp.route('/trash/<int:trash_id>', methods=['OPTIONS'])
def handle_delete_options(trash_id):
    return '', 200

@bp.route('/trash/bulk-restore', methods=['OPTIONS'])
def handle_bulk_restore_options():
    return '', 200

@bp.route('/trash/bulk-delete', methods=['OPTIONS'])
def handle_bulk_delete_options():
    return '', 200

@bp.route('/trash/config', methods=['OPTIONS'])
def handle_config_options():
    return '', 200

@bp.route('/trash/stats', methods=['OPTIONS'])
def handle_stats_options():
    return '', 200

@bp.route('/trash/cleanup', methods=['OPTIONS'])
def handle_cleanup_options():
    return '', 200 