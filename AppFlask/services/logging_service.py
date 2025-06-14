from AppFlask.db import db_connection
import logging
from datetime import datetime
from flask import request, g
import json
import time
from typing import Optional, Any, Dict
from psycopg2.extras import Json

class LoggingService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _get_request_info(self) -> Dict[str, Any]:
        """Récupère les informations de la requête HTTP actuelle."""
        if not request:
            return {}
        
        return {
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string if request.user_agent else None,
            'path': request.path,
            'method': request.method
        }

    def _format_additional_data(self, data: Any) -> Dict:
        """Formate les données additionnelles pour le stockage JSON."""
        if isinstance(data, dict):
            return data
        elif data is None:
            return {}
        else:
            return {'data': str(data)}

    def log_event(self, 
                 level: str,
                 event_type: str,
                 message: str,
                 user_id: Optional[int] = None,
                 additional_data: Any = None,
                 response_status: Optional[int] = None,
                 execution_time: Optional[float] = None) -> None:
        """
        Enregistre un événement dans la base de données.
        
        Args:
            level: Niveau de log (INFO, WARNING, ERROR, etc.)
            event_type: Type d'événement (LOGIN, LOGOUT, FILE_UPLOAD, etc.)
            message: Message descriptif
            user_id: ID de l'utilisateur concerné (optionnel)
            additional_data: Données supplémentaires à logger (optionnel)
            response_status: Code de statut HTTP (optionnel)
            execution_time: Temps d'exécution en ms (optionnel)
        """
        try:
            self.logger.info("Attempting to get DB connection in log_event...")
            conn = db_connection()
            if conn is None:
                self.logger.error("Failed to get DB connection in log_event.")
                return
            self.logger.info("DB connection successful in log_event.")
            cursor = conn.cursor()
            self.logger.info("DB cursor created in log_event.")

            request_info = self._get_request_info()
            formatted_data = self._format_additional_data(additional_data)

            query = """
                INSERT INTO system_logs (
                    level,
                    event_type,
                    user_id,
                    ip_address,
                    user_agent,
                    request_path,
                    request_method,
                    response_status,
                    execution_time,
                    message,
                    additional_data
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

            cursor.execute(query, (
                level,
                event_type,
                user_id,
                request_info.get('ip_address'),
                request_info.get('user_agent'),
                request_info.get('path'),
                request_info.get('method'),
                response_status,
                execution_time,
                message,
                Json(formatted_data)
            ))

            self.logger.info(f"Attempting to execute log query: {query} with params: {(level, event_type, user_id, request_info.get('ip_address'), request_info.get('user_agent'), request_info.get('path'), request_info.get('method'), response_status, execution_time, message, Json(formatted_data))}")
            cursor.execute(query, (
                level,
                event_type,
                user_id,
                request_info.get('ip_address'),
                request_info.get('user_agent'),
                request_info.get('path'),
                request_info.get('method'),
                response_status,
                execution_time,
                message,
                Json(formatted_data)
            ))
            self.logger.info("Log query executed. Attempting to commit...")
            conn.commit()
            self.logger.info("Commit successful in log_event.")

        except Exception as e:
            import traceback
            self.logger.error(f"Exception in log_event: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_recent_logs(self, hours=24, level=None, event_type=None, user_id=None, limit=100):
        """Récupère les logs récents avec filtrage."""
        try:
            self.logger.info("Attempting to get DB connection in log_event...")
            conn = db_connection()
            if conn is None:
                self.logger.error("Failed to get DB connection in log_event.")
                return
            self.logger.info("DB connection successful in log_event.")
            cursor = conn.cursor()
            self.logger.info("DB cursor created in log_event.")

            # Construction de la requête avec filtres
            query_parts = [
                "SELECT id, timestamp, level, event_type, user_id, ip_address, request_path, response_status, message, additional_data",
                "FROM system_logs",
                "WHERE timestamp > NOW() - INTERVAL %s hours"
            ]
            params = [hours]

            # Ajout des filtres conditionnels
            if level:
                query_parts.append("AND level = %s")
                params.append(level)
            if event_type:
                # Gérer les types d'événements multiples séparés par des virgules
                event_types = [et.strip() for et in event_type.split(',') if et.strip()]
                if event_types:
                    event_type_placeholders = ', '.join(['%s'] * len(event_types))
                    query_parts.append(f"AND event_type IN ({event_type_placeholders})")
                    params.extend(event_types)
            if user_id:
                query_parts.append("AND user_id = %s")
                params.append(user_id)

            # Ajout de l'ordre et de la limite
            query_parts.append("ORDER BY timestamp DESC LIMIT %s")
            params.append(limit)

            final_query = ' '.join(query_parts)
            self.logger.info(f"Executing query: {final_query} with params: {params}")

            cursor.execute(final_query, tuple(params))
            logs_raw = cursor.fetchall()
            self.logger.info(f"Fetched {len(logs_raw)} logs from DB.")

            # Formater les résultats
            formatted_logs = []
            for log_row in logs_raw:
                formatted_logs.append({
                    'id': log_row['id'],
                    'timestamp': log_row['timestamp'].isoformat() if log_row['timestamp'] else None,
                    'level': log_row['level'],
                    'event_type': log_row['event_type'],
                    'user_id': log_row['user_id'],
                    'ip_address': log_row['ip_address'],
                    'request_path': log_row['request_path'],
                    'response_status': log_row['response_status'],
                    'message': log_row['message'],
                    'additional_data': log_row['additional_data']
                })

            cursor.close()
            conn.close()

            return formatted_logs

        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des logs: {str(e)}")
            return []

    def get_user_activity_summary(self, user_id: int, days: int = 30) -> Dict:
        """
        Récupère un résumé de l'activité d'un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            days: Nombre de jours à analyser
        
        Returns:
            Dictionnaire contenant le résumé d'activité
        """
        try:
            self.logger.info("Attempting to get DB connection in log_event...")
            conn = db_connection()
            if conn is None:
                self.logger.error("Failed to get DB connection in log_event.")
                return
            self.logger.info("DB connection successful in log_event.")
            cursor = conn.cursor()
            self.logger.info("DB cursor created in log_event.")

            query = """
                SELECT 
                    COUNT(*) as total_actions,
                    COUNT(DISTINCT DATE(timestamp)) as active_days,
                    array_agg(DISTINCT event_type) as event_types,
                    MAX(timestamp) as last_activity
                FROM system_logs
                WHERE user_id = %s
                AND timestamp > NOW() - INTERVAL %s DAY
            """

            cursor.execute(query, (user_id, days))
            result = cursor.fetchone()

            if result:
                return {
                    'total_actions': result[0],
                    'active_days': result[1],
                    'event_types': result[2],
                    'last_activity': result[3]
                }
            return {}

        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du résumé d'activité: {str(e)}")
            return {}
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

# Instance globale du service de logging
logging_service = LoggingService()