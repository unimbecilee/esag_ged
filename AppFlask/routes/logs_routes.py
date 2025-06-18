from flask import Blueprint, jsonify, request
from flask_login import login_required
from AppFlask.api.auth import token_required
from AppFlask.services.logging_service import logging_service
from AppFlask.db import db_connection
import logging
import os
import traceback
from flask_cors import cross_origin
from psycopg2.extras import RealDictCursor
import random

logger = logging.getLogger(__name__)
logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/init', methods=['POST', 'OPTIONS'])
@cross_origin(origins=['http://localhost:3000'], methods=['POST', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])
@token_required
def initialize_logs_table(current_user):
    if request.method == 'OPTIONS':
        return '', 204
    """Initialise la table system_logs si elle n'existe pas."""
    try:
        logger.info("Début de l'initialisation de la table system_logs")
        
        # Vérifier si l'utilisateur est admin
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Tentative d'initialisation non autorisée par l'utilisateur {current_user['id']}")
            return jsonify({'message': 'Accès non autorisé'}), 403

        conn = db_connection()
        if not conn:
            logger.error("Impossible de se connecter à la base de données")
            return jsonify({
                'status': 'error',
                'message': 'Erreur de connexion à la base de données'
            }), 500

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        logger.info("Connexion à la base de données établie")

        # Vérifier si la table existe déjà
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'system_logs'
            )
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            # Créer la table
            cursor.execute("""
                CREATE TABLE system_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    level VARCHAR(10) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    user_id INTEGER,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    request_path TEXT,
                    request_method VARCHAR(10),
                    response_status INTEGER,
                    execution_time NUMERIC(10,2),
                    message TEXT,
                    additional_data JSONB
                )
            """)
            logger.info("Table system_logs créée avec succès")
        
        # Vérifier si la table contient déjà des données
        cursor.execute("SELECT COUNT(*) FROM system_logs")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Insérer des logs de test variés
            test_logs = [
                ('INFO', 'USER_LOGIN', current_user['id'], '192.168.1.1', 'Connexion réussie de l\'utilisateur', 200),
                ('WARNING', 'SECURITY_ALERT', current_user['id'], '192.168.1.2', 'Tentative de connexion échouée', 401),
                ('ERROR', 'SYSTEM_ERROR', current_user['id'], '192.168.1.3', 'Erreur lors du traitement de la requête', 500),
                ('INFO', 'DOCUMENT_CREATE', current_user['id'], '192.168.1.1', 'Nouveau document créé: Rapport 2025', 201),
                ('INFO', 'DOCUMENT_UPDATE', current_user['id'], '192.168.1.1', 'Document mis à jour: Rapport 2025', 200),
                ('WARNING', 'DOCUMENT_DELETE', current_user['id'], '192.168.1.1', 'Document supprimé: Ancien rapport', 200),
                ('INFO', 'USER_LOGOUT', current_user['id'], '192.168.1.1', 'Déconnexion de l\'utilisateur', 200),
                ('DEBUG', 'SYSTEM_CHECK', current_user['id'], '192.168.1.4', 'Vérification système périodique', 200),
                ('INFO', 'USER_UPDATE', current_user['id'], '192.168.1.1', 'Profil utilisateur mis à jour', 200),
                ('ERROR', 'API_ERROR', current_user['id'], '192.168.1.5', 'Erreur API externe', 503)
            ]
            
            for level, event_type, user_id, ip, message, status in test_logs:
                cursor.execute("""
                    INSERT INTO system_logs (
                        level, 
                        event_type, 
                        user_id, 
                        ip_address,
                        message,
                        response_status,
                        request_method,
                        execution_time
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    level,
                    event_type,
                    user_id,
                    ip,
                    message,
                    status,
                    'POST',
                    round(0.1 + random.random() * 2, 2)  # Temps d'exécution aléatoire entre 0.1 et 2.1 secondes
                ))
            
            conn.commit()
            logger.info("Logs de test insérés avec succès")
            
            return jsonify({
                'status': 'success',
                'message': 'Table system_logs initialisée avec des données de test',
                'logs_count': len(test_logs)
            })
        else:
            return jsonify({
                'status': 'success',
                'message': 'La table system_logs existe déjà et contient des données',
                'logs_count': count
            })

    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la table system_logs: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f"Erreur lors de l'initialisation: {str(e)}"
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        logger.info("Connexion à la base de données fermée")

@logs_bp.route('/', methods=['GET', 'OPTIONS'])
@cross_origin(origins=['http://localhost:3000'], methods=['GET', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])
@token_required
def get_logs(current_user):
    if request.method == 'OPTIONS':
        return '', 204
    """Récupère les logs système avec filtres."""
    try:
        # Vérifier si l'utilisateur est admin
        if current_user['role'].lower() != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403

        # Récupérer les paramètres de filtrage
        hours = request.args.get('hours', default=24, type=int)
        level = request.args.get('level')
        event_type = request.args.get('event_type')
        user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', default=100, type=int)

        # Récupérer les logs
        logs = logging_service.get_recent_logs(
            hours=hours,
            level=level,
            event_type=event_type,
            user_id=user_id,
            limit=limit
        )

        # Formater les logs pour le frontend
        formatted_logs = []
        for log_item in logs: # log_item is a dict
            formatted_logs.append({
                'id': log_item.get('id'),
                'timestamp': log_item.get('timestamp'), # Assuming it's already a string or None from logging_service
                'level': log_item.get('level'),
                'event_type': log_item.get('event_type'),
                'user_id': log_item.get('user_id'),
                'ip_address': log_item.get('ip_address'),
                'request_path': log_item.get('request_path'),
                'response_status': log_item.get('response_status'),
                'message': log_item.get('message'),
                'additional_data': log_item.get('additional_data')
            })

        return jsonify({
            'logs': formatted_logs,
            'total': len(formatted_logs)
        })

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des logs: {str(e)}")
        return jsonify({'message': 'Erreur lors de la récupération des logs'}), 500

@logs_bp.route('/summary', methods=['GET'])
@token_required
def get_logs_summary(current_user):
    """Récupère un résumé des logs système."""
    try:
        # Vérifier si l'utilisateur est admin
        if current_user['role'].lower() != 'admin':
            return jsonify({'message': 'Accès non autorisé'}), 403

        days = request.args.get('days', default=30, type=int)
        user_id = request.args.get('user_id', type=int)

        if user_id:
            # Récupérer le résumé pour un utilisateur spécifique
            summary = logging_service.get_user_activity_summary(user_id, days)
        else:
            # Récupérer un résumé global
            conn = db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    COUNT(*) as total_logs,
                    COUNT(DISTINCT user_id) as unique_users,
                    array_agg(DISTINCT level) as log_levels,
                    array_agg(DISTINCT event_type) as event_types
                FROM system_logs
                WHERE timestamp > NOW() - INTERVAL %s DAY
            """
            
            cursor.execute(query, (days,))
            result = cursor.fetchone()
            
            if result:
                summary = {
                    'total_logs': result[0],
                    'unique_users': result[1],
                    'log_levels': result[2],
                    'event_types': result[3]
                }
            else:
                summary = {}

            cursor.close()
            conn.close()

        return jsonify(summary)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération du résumé des logs: {str(e)}")
        return jsonify({'message': 'Erreur lors de la récupération du résumé des logs'}), 500

@logs_bp.route('/stats', methods=['GET', 'OPTIONS'])
@cross_origin(origins=['http://localhost:3000'], methods=['GET', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])
@token_required
def get_logs_stats(current_user):
    if request.method == 'OPTIONS':
        return '', 204

    try:
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Tentative d'accès non autorisé aux stats par l'utilisateur {current_user['id']}")
            return jsonify({'message': 'Accès non autorisé'}), 403

        days = request.args.get('days', default=30, type=int)
        logger.info(f"Récupération des stats pour les {days} derniers jours")

        conn = db_connection()
        if not conn:
            logger.error("Impossible de se connecter à la base de données")
            return jsonify({'message': 'Erreur de connexion à la base de données'}), 500

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Récupérer le nombre total de logs
            cursor.execute("""
                SELECT COUNT(*) 
                FROM system_logs 
                WHERE timestamp > NOW() - INTERVAL '%s days'
            """, (days,))
            
            result = cursor.fetchone()
            # Vérifier si le résultat est None ou vide
            if result is None:
                total_logs = 0
                logger.warning("La requête de comptage a retourné None")
            else:
                try:
                    total_logs = result['count'] if result and result['count'] is not None else 0
                    logger.info(f"Nombre total de logs trouvés: {total_logs}")
                except (IndexError, KeyError) as e:
                    total_logs = 0
                    logger.error(f"Erreur lors de l'accès au résultat: {str(e)}")
            
            if total_logs == 0:
                logger.info("Aucun log trouvé pour la période demandée")
                return jsonify({
                    'by_level': [],
                    'by_event': [],
                    'by_date': [],
                    'total_logs': 0
                })

            # Statistiques par niveau
            cursor.execute("""
                SELECT 
                    level,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT DATE(timestamp)) as days_with_events
                FROM system_logs
                WHERE timestamp > NOW() - INTERVAL '%s days'
                GROUP BY level
                ORDER BY count DESC
            """, (days,))
            
            level_stats = []
            for row in cursor.fetchall():
                if row:
                    level_stats.append({
                        'level': row['level'],
                        'count': row['count'],
                        'unique_users': row['unique_users'],
                        'days_with_events': row['days_with_events']
                    })
            
            # Statistiques par type d'événement
            cursor.execute("""
                SELECT 
                    event_type,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as unique_users,
                    array_agg(DISTINCT level) as levels
                FROM system_logs
                WHERE timestamp > NOW() - INTERVAL '%s days'
                GROUP BY event_type
                ORDER BY count DESC
            """, (days,))
            
            event_stats = []
            for row in cursor.fetchall():
                if row:
                    event_stats.append({
                        'event_type': row['event_type'],
                        'count': row['count'],
                        'unique_users': row['unique_users'],
                        'levels': row['levels'] if row['levels'] else []
                    })

            # Statistiques par jour
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as total_logs,
                    COUNT(DISTINCT user_id) as unique_users,
                    array_agg(DISTINCT level) as levels,
                    array_agg(DISTINCT event_type) as event_types
                FROM system_logs
                WHERE timestamp > NOW() - INTERVAL '%s days'
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, (days,))
            
            daily_stats = []
            for row in cursor.fetchall():
                if row and row['date'] is not None:
                    daily_stats.append({
                        'date': row['date'].strftime('%Y-%m-%d'),
                        'total_logs': row['total_logs'],
                        'unique_users': row['unique_users'],
                        'levels': row['levels'] if row['levels'] else [],
                        'event_types': row['event_types'] if row['event_types'] else []
                    })

            stats = {
                'by_level': level_stats,
                'by_event': event_stats,
                'by_date': daily_stats,
                'total_logs': total_logs
            }

            logger.info("Stats récupérées avec succès")
            return jsonify(stats)

        except Exception as e:
            logger.error(f"Erreur SQL lors de la récupération des stats: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'message': 'Erreur lors de la récupération des statistiques',
                'error': str(e)
            }), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'message': 'Erreur lors de la récupération des statistiques',
            'error': str(e)
        }), 500

@logs_bp.route('/check-table', methods=['GET'])
@token_required
def check_logs_table(current_user):
    """Vérifie l'état de la table system_logs."""
    try:
        logger.info("Début de la vérification de la table system_logs")
        
        # Vérifier si l'utilisateur est admin
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Tentative d'accès non autorisé par l'utilisateur {current_user['id']}")
            return jsonify({'message': 'Accès non autorisé'}), 403

        conn = db_connection()
        if not conn:
            logger.error("Impossible de se connecter à la base de données")
            return jsonify({
                'status': 'error',
                'message': 'Erreur de connexion à la base de données'
            }), 500

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        logger.info("Connexion à la base de données établie")

        # Vérifier si la table existe
        check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'system_logs'
            );
        """
        logger.debug(f"Exécution de la requête: {check_query}")
        cursor.execute(check_query)
        table_exists = cursor.fetchone()[0]
        logger.info(f"La table system_logs existe: {table_exists}")

        if table_exists:
            try:
                # Compter le nombre d'entrées
                cursor.execute("SELECT COUNT(*) FROM system_logs")
                count = cursor.fetchone()[0]
                logger.info(f"Nombre total de logs: {count}")
                
                # Récupérer les 5 dernières entrées pour vérification
                cursor.execute("""
                    SELECT 
                        to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as timestamp,
                        level,
                        event_type,
                        message 
                    FROM system_logs 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                recent_logs = []
                for row in cursor.fetchall():
                    recent_logs.append({
                        'timestamp': row[0],
                        'level': row[1],
                        'event_type': row[2],
                        'message': row[3]
                    })
                logger.info(f"Récupération des logs récents réussie: {len(recent_logs)} entrées trouvées")
                
                return jsonify({
                    'status': 'success',
                    'table_exists': True,
                    'total_logs': count,
                    'recent_logs': recent_logs
                })
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des logs: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'status': 'error',
                    'message': f"Erreur lors de la récupération des logs: {str(e)}"
                }), 500
        else:
            return jsonify({
                'status': 'success',
                'table_exists': False,
                'message': 'La table system_logs n\'existe pas'
            })

    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la table: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': f"Erreur lors de la vérification de la table: {str(e)}"
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        logger.info("Connexion à la base de données fermée")