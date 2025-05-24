from flask import Blueprint, request, jsonify
from AppFlask.db import db_connection
from AppFlask.api.auth import token_required
import logging

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)

@search_bp.route('/api/search', methods=['GET'])
@token_required
def search(current_user):
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify([])

        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        results = []

        # Recherche dans les documents
        cursor.execute("""
            SELECT 
                'document' as type,
                id,
                titre,
                CASE
                    WHEN LOWER(fichier) LIKE '%.pdf' THEN 'PDF'
                    WHEN LOWER(fichier) LIKE '%.doc' OR LOWER(fichier) LIKE '%.docx' THEN 'Word'
                    WHEN LOWER(fichier) LIKE '%.xls' OR LOWER(fichier) LIKE '%.xlsx' THEN 'Excel'
                    WHEN LOWER(fichier) LIKE '%.jpg' OR LOWER(fichier) LIKE '%.jpeg' OR 
                         LOWER(fichier) LIKE '%.png' OR LOWER(fichier) LIKE '%.gif' THEN 'Image'
                    WHEN LOWER(fichier) LIKE '%.txt' THEN 'Texte'
                    ELSE 'Autre'
                END as type_document,
                CASE 
                    WHEN taille < 1024 THEN CONCAT(ROUND(taille::numeric, 2)::text, ' B')
                    WHEN taille < 1048576 THEN CONCAT(ROUND((taille::numeric/1024), 2)::text, ' KB')
                    WHEN taille < 1073741824 THEN CONCAT(ROUND((taille::numeric/1048576), 2)::text, ' MB')
                    ELSE CONCAT(ROUND((taille::numeric/1073741824), 2)::text, ' GB')
                END as taille_formatee,
                TO_CHAR(date_ajout, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as date_creation
            FROM document 
            WHERE 
                (LOWER(titre) LIKE LOWER(%s) OR 
                LOWER(description) LIKE LOWER(%s)) AND
                (proprietaire_id = %s OR 
                id IN (SELECT document_id FROM partage WHERE utilisateur_id = %s) OR
                %s)
            LIMIT 5
        """, (f"%{query}%", f"%{query}%", current_user['id'], current_user['id'], current_user['role'].lower() == 'admin'))
        
        document_results = cursor.fetchall()
        results.extend(document_results)

        # Recherche dans les utilisateurs (seulement pour les admins)
        if current_user['role'].lower() == 'admin':
            cursor.execute("""
                SELECT 
                    'utilisateur' as type,
                    id,
                    nom,
                    prenom,
                    email
                FROM utilisateur 
                WHERE 
                    LOWER(nom) LIKE LOWER(%s) OR 
                    LOWER(prenom) LIKE LOWER(%s) OR 
                    LOWER(email) LIKE LOWER(%s)
                LIMIT 5
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            
            user_results = cursor.fetchall()
            results.extend(user_results)

        # Recherche dans les dossiers
        cursor.execute("""
            SELECT 
                'dossier' as type,
                id,
                titre,
                description
            FROM dossier 
            WHERE 
                (LOWER(titre) LIKE LOWER(%s) OR 
                LOWER(description) LIKE LOWER(%s)) AND
                (proprietaire_id = %s OR 
                id IN (SELECT dossier_id FROM partage_dossier WHERE utilisateur_id = %s) OR
                %s)
            LIMIT 5
        """, (f"%{query}%", f"%{query}%", current_user['id'], current_user['id'], current_user['role'].lower() == 'admin'))
        
        folder_results = cursor.fetchall()
        results.extend(folder_results)

        cursor.close()
        conn.close()

        return jsonify(results)

    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {str(e)}")
        return jsonify({'message': str(e)}), 500