from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for
from flask_login import login_required
from AppFlask.api.auth import token_required
import logging
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Configuration du logging
logger = logging.getLogger(__name__)

history_bp = Blueprint('history', __name__)

# Gestionnaire pour les requêtes OPTIONS
@history_bp.route('/api/history', methods=['OPTIONS'])
@history_bp.route('/api/history/stats', methods=['OPTIONS'])
def handle_history_options():
    return '', 200

@history_bp.route('/api/history', methods=['GET'])
@token_required
def get_history(current_user):
    conn = None
    cursor = None
    try:
        # Paramètres de pagination et filtrage
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)  # Changé à 50 pour correspondre au frontend
        action_type = request.args.get('action_type')
        entity_type = request.args.get('entity_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        search = request.args.get('search')

        logger.info(f"Paramètres reçus: page={page}, per_page={per_page}, action_type={action_type}, "
                   f"entity_type={entity_type}, start_date={start_date}, end_date={end_date}, "
                   f"user_id={user_id}, search={search}")

        # Construction de la requête de base
        query = """
            SELECT 
                h.id,
                h.action_type,
                h.entity_type,
                h.entity_id,
                h.entity_name,
                h.description,
                h.metadata,
                h.created_at,
                CONCAT(u.prenom, ' ', u.nom) as user_name
            FROM history h
            LEFT JOIN utilisateur u ON h.user_id = u.id
            WHERE 1=1
        """
        params = []

        # Ajout des filtres
        if action_type:
            query += " AND h.action_type = %s"
            params.append(action_type)
        if entity_type:
            query += " AND h.entity_type = %s"
            params.append(entity_type)
        if start_date:
            query += " AND DATE(h.created_at) >= %s"
            params.append(start_date)
        if end_date:
            query += " AND DATE(h.created_at) <= %s"
            params.append(end_date)
        if user_id:
            query += " AND h.user_id = %s"
            params.append(user_id)
        if search:
            query += " AND (h.entity_name ILIKE %s OR h.description ILIKE %s)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        logger.info(f"Requête SQL construite: {query}")
        logger.info(f"Paramètres SQL: {params}")

        # Établir la connexion et créer le curseur
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Compter le nombre total d'entrées
        count_query = f"SELECT COUNT(*) as total FROM ({query}) AS count_query"
        cursor.execute(count_query, params)
        count_result = cursor.fetchone()
        total_count = count_result['total'] if count_result else 0

        # Ajouter la pagination
        query += " ORDER BY h.created_at DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * per_page
        params.extend([per_page, offset])

        # Exécuter la requête principale
        cursor.execute(query, params)
        history_entries = cursor.fetchall()

        # Formater les résultats pour correspondre à l'interface HistoryItem du frontend
        items = []
        for entry in history_entries:
            formatted_entry = {
                'id': entry['id'],
                'action_type': entry['action_type'],
                'entity_type': entry['entity_type'],
                'entity_id': entry['entity_id'],
                'entity_name': entry['entity_name'],
                'description': entry['description'],
                'created_at': entry['created_at'].isoformat() if entry['created_at'] else None,
                'user_name': entry['user_name'],
                'metadata': entry['metadata']
            }
            items.append(formatted_entry)

        logger.info(f"Nombre d'entrées trouvées: {len(items)}")

        return jsonify({
            'items': items,
            'pages': (total_count + per_page - 1) // per_page,
            'current_page': page,
            'total': total_count
        })

    except Exception as e:
        logger.error(f"Erreur dans get_history: {str(e)}", exc_info=True)
        return jsonify({'error': "Erreur lors de la récupération de l'historique"}), 500
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("Connexion à la base de données fermée")

@history_bp.route('/api/history/stats', methods=['GET'])
@token_required
def get_history_stats(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Statistiques globales
        cursor.execute("SELECT COUNT(*) as total_actions FROM history")
        total_actions = cursor.fetchone()['total_actions']

        # Actions par type
        cursor.execute("""
            SELECT action_type, COUNT(*) as count
            FROM history
            GROUP BY action_type
            ORDER BY count DESC
        """)
        actions_by_type = {row['action_type']: row['count'] for row in cursor.fetchall()}

        # Entités par type
        cursor.execute("""
            SELECT entity_type, COUNT(*) as count
            FROM history
            GROUP BY entity_type
            ORDER BY count DESC
        """)
        entities_by_type = {row['entity_type']: row['count'] for row in cursor.fetchall()}

        cursor.close()
        conn.close()

        return jsonify({
            'total_actions': total_actions,
            'actions_by_type': actions_by_type,
            'entities_by_type': entities_by_type
        }), 200

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
        return jsonify({'error': str(e)}), 500

@history_bp.route('/api/history/check', methods=['GET'])
@token_required
def check_history_table(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        # Vérifier si la table history existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'history'
            );
        """)
        
        exists = cursor.fetchone()[0]
        
        if exists:
            # Vérifier si la table contient des données
            cursor.execute("SELECT COUNT(*) FROM history")
            count = cursor.fetchone()[0]
            
            return jsonify({
                'table_exists': True,
                'records_count': count
            })
        else:
            return jsonify({
                'table_exists': False,
                'message': 'La table history n\'existe pas'
            })
            
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la table history: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@history_bp.route('/api/history/migrate', methods=['POST'])
@token_required
def migrate_history(current_user):
    """
    Route pour migrer les données de l'ancienne table Historique vers la nouvelle table history
    """
    if current_user['role'].lower() != 'admin':
        return jsonify({'message': 'Permission refusée'}), 403

    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Compter les entrées avant migration
        cursor.execute("SELECT COUNT(*) FROM Historique")
        old_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM history")
        initial_new_count = cursor.fetchone()[0]

        # Exécuter la migration
        with open('AppFlask/sql/migrate_history.sql', 'r') as file:
            migration_sql = file.read()
            cursor.execute(migration_sql)

        # Compter les entrées après migration
        cursor.execute("SELECT COUNT(*) FROM history")
        final_new_count = cursor.fetchone()[0]
        
        migrated_count = final_new_count - initial_new_count

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Migration terminée avec succès',
            'old_records': old_count,
            'migrated_records': migrated_count,
            'total_new_records': final_new_count
        })

    except Exception as e:
        logger.error(f"Erreur lors de la migration de l'historique: {str(e)}")
        return jsonify({'error': str(e)}), 500

def log_action(user_id, action_type, entity_type, entity_id, entity_name, description, metadata=None):
    """
    Fonction utilitaire pour enregistrer une action dans l'historique
    """
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO history (
                action_type,
                entity_type,
                entity_id,
                entity_name,
                description,
                metadata,
                user_id,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """
        
        cursor.execute(query, (
            action_type,
            entity_type,
            entity_id,
            entity_name,
            description,
            metadata,
            user_id
        ))
        
        history_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return history_id
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement de l'historique: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return None 