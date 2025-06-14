from flask import Blueprint, jsonify, request
from AppFlask.db import db_connection
from AppFlask.api.auth import token_required
import psycopg2.extras
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_db_connection():
    """Obtenir une connexion à la base de données"""
    return db_connection()

@api_bp.route('/documents', methods=['GET'])
@token_required
def get_documents(current_user):
    """Récupérer la liste des documents"""
    try:
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        user_id = current_user['id']
        user_role = current_user.get('role', '')
        
        # Query pour récupérer les documents
        query = """
            SELECT d.id, d.titre, d.description, d.fichier, d.taille, 
                   d.mime_type, d.date_ajout, d.categorie, d.proprietaire_id
            FROM Document d
            WHERE d.proprietaire_id = %s OR %s = 'Admin'
            ORDER BY d.date_ajout DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (user_id, user_role, limit, offset))
        documents = cursor.fetchall()
        
        # Compter le total
        cursor.execute("""
            SELECT COUNT(*) as total FROM Document d
            WHERE d.proprietaire_id = %s OR %s = 'Admin'
        """, (user_id, user_role))
        
        total = cursor.fetchone()['total']
        
        # Convertir les résultats
        docs_list = []
        for doc in documents:
            doc_dict = dict(doc)
            if doc_dict['date_ajout']:
                doc_dict['date_ajout'] = doc_dict['date_ajout'].isoformat()
            docs_list.append(doc_dict)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'documents': docs_list,
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        print(f"Erreur API documents: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des documents'}), 500

@api_bp.route('/batch-operations', methods=['GET'])
@token_required
def get_batch_operations(current_user):
    """Récupérer l'historique des opérations"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        query = """
            SELECT h.id, h.action_type as action, h.created_at as date_action, 
                   h.entity_id as document_id, h.entity_name as document_titre,
                   h.description, h.metadata,
                   u.nom as user_nom, u.prenom as user_prenom
            FROM history h
            LEFT JOIN utilisateur u ON h.user_id = u.id
            WHERE h.entity_type = 'document'
            ORDER BY h.created_at DESC
            LIMIT 50
        """
        
        cursor.execute(query)
        operations = cursor.fetchall()
        
        ops_list = []
        for op in operations:
            op_dict = dict(op)
            if op_dict['date_action']:
                op_dict['date_action'] = op_dict['date_action'].isoformat()
            ops_list.append(op_dict)
        
        cursor.close()
        conn.close()
        
        return jsonify({'operations': ops_list})
        
    except Exception as e:
        print(f"Erreur API batch-operations: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des opérations'}), 500

@api_bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Récupérer les informations de l'utilisateur connecté"""
    try:
        return jsonify({
            'id': current_user['id'],
            'role': current_user.get('role', ''),
            'nom': current_user.get('nom', ''),
            'prenom': current_user.get('prenom', ''),
            'email': current_user.get('email', ''),
            'authenticated': True
        })
    except Exception as e:
        print(f"Erreur API auth/me: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500 