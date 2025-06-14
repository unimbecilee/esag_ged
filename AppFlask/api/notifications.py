#!/usr/bin/env python3
"""
API pour le système de notifications ESAG GED
Gestion des notifications en temps réel et par email
"""

from flask import Blueprint, request, jsonify, current_app
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import logging
import json

# Import du décorateur d'authentification depuis auth.py
from AppFlask.api.auth import token_required

logger = logging.getLogger(__name__)

bp = Blueprint('notifications', __name__)

@bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    """Récupérer les notifications de l'utilisateur"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        notification_type = request.args.get('type')
        
        offset = (page - 1) * per_page
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Construire la requête
        where_conditions = ["user_id = %s"]
        params = [current_user['id']]
        
        if unread_only:
            where_conditions.append("is_read = false")
        
        if notification_type:
            where_conditions.append("type = %s")
            params.append(notification_type)
        
        where_clause = " AND ".join(where_conditions)
        
        # Compter le total
        cursor.execute(f"""
            SELECT COUNT(*) as total 
            FROM notifications 
            WHERE {where_clause}
        """, params)
        
        total = cursor.fetchone()['total']
        
        # Récupérer les notifications
        cursor.execute(f"""
            SELECT n.*, d.titre as document_title
            FROM notifications n
            LEFT JOIN document d ON n.document_id = d.id
            WHERE {where_clause}
            ORDER BY n.created_at DESC
            LIMIT %s OFFSET %s
        """, params + [per_page, offset])
        
        notifications = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'notifications': [dict(n) for n in notifications],
            'total': total,
            'page': page,
            'per_page': per_page,
            'has_next': (page * per_page) < total,
            'has_prev': page > 1
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur récupération notifications: {str(e)}")
        return jsonify({'message': 'Erreur lors de la récupération des notifications'}), 500

@bp.route('/notifications/unread-count', methods=['GET'])
@token_required
def get_unread_count(current_user):
    """Récupérer le nombre de notifications non lues"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT COUNT(*) as unread_count 
            FROM notifications 
            WHERE user_id = %s AND is_read = false
        """, (current_user['id'],))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return jsonify({'unread_count': result['unread_count']}), 200
        
    except Exception as e:
        logger.error(f"Erreur comptage notifications: {str(e)}")
        return jsonify({'message': 'Erreur lors du comptage'}), 500

@bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@token_required
def mark_as_read(current_user, notification_id):
    """Marquer une notification comme lue"""
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE notifications 
            SET is_read = true, read_at = NOW() 
            WHERE id = %s AND user_id = %s
        """, (notification_id, current_user['id']))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'message': 'Notification non trouvée'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Notification marquée comme lue'}), 200
        
    except Exception as e:
        logger.error(f"Erreur marquage notification: {str(e)}")
        return jsonify({'message': 'Erreur lors du marquage'}), 500

@bp.route('/notifications/mark-all-read', methods=['PUT'])
@token_required
def mark_all_as_read(current_user):
    """Marquer toutes les notifications comme lues"""
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE notifications 
            SET is_read = true, read_at = NOW() 
            WHERE user_id = %s AND is_read = false
        """, (current_user['id'],))
        
        updated_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': f'{updated_count} notifications marquées comme lues',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur marquage notifications: {str(e)}")
        return jsonify({'message': 'Erreur lors du marquage'}), 500

@bp.route('/notifications/preferences', methods=['GET'])
@token_required
def get_notification_preferences(current_user):
    """Récupérer les préférences de notification de l'utilisateur"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Essayer de récupérer les préférences existantes
        try:
            cursor.execute("""
                SELECT * FROM user_notification_preferences 
                WHERE user_id = %s
            """, (current_user['id'],))
            
            preferences = cursor.fetchone()
            
            if preferences:
                cursor.close()
                conn.close()
                return jsonify(dict(preferences)), 200
        except Exception as e:
            logger.warning(f"Erreur récupération préférences DB: {str(e)}")
        
        cursor.close()
        conn.close()
        
        # Retourner des préférences par défaut si la table n'existe pas ou est vide
        default_preferences = {
            'user_id': current_user['id'],
            'email_notifications': True,
            'app_notifications': True,
            'document_notifications': True,
            'workflow_notifications': True,
            'comment_notifications': True,
            'share_notifications': True,
            'mention_notifications': True,
            'system_notifications': True,
            'digest_frequency': 'daily',
            'quiet_hours_start': '22:00:00',
            'quiet_hours_end': '08:00:00',
            'weekend_notifications': False
        }
        
        return jsonify(default_preferences), 200
        
    except Exception as e:
        logger.error(f"Erreur récupération préférences: {str(e)}")
        # En cas d'erreur, retourner quand même des préférences par défaut
        default_preferences = {
            'user_id': current_user['id'],
            'email_notifications': True,
            'app_notifications': True,
            'document_notifications': True,
            'workflow_notifications': True,
            'comment_notifications': True,
            'share_notifications': True,
            'mention_notifications': True,
            'system_notifications': True,
            'digest_frequency': 'daily',
            'quiet_hours_start': '22:00:00',
            'quiet_hours_end': '08:00:00',
            'weekend_notifications': False
        }
        
        return jsonify(default_preferences), 200

@bp.route('/notifications/stats', methods=['GET'])
@token_required
def get_notification_stats(current_user):
    """Récupérer les statistiques des notifications"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Statistiques générales
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_read = false) as unread,
                COUNT(*) FILTER (WHERE is_read = true) as read,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as last_24h,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as last_7d
            FROM notifications 
            WHERE user_id = %s
        """, (current_user['id'],))
        
        general_stats = cursor.fetchone()
        
        # Statistiques par type
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM notifications 
            WHERE user_id = %s
            GROUP BY type
            ORDER BY count DESC
        """, (current_user['id'],))
        
        type_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'general': dict(general_stats),
            'by_type': [dict(stat) for stat in type_stats]
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur statistiques notifications: {str(e)}")
        return jsonify({'message': 'Erreur lors de la récupération des statistiques'}), 500

# ================================
# ROUTES OPTIONS POUR CORS
# ================================

@bp.route('/notifications', methods=['OPTIONS'])
def handle_notifications_options():
    return '', 200

@bp.route('/notifications/unread-count', methods=['OPTIONS'])
def handle_unread_count_options():
    return '', 200

@bp.route('/notifications/preferences', methods=['OPTIONS'])
def handle_preferences_options():
    return '', 200

@bp.route('/notifications/stats', methods=['OPTIONS'])
def handle_stats_options():
    return '', 200 