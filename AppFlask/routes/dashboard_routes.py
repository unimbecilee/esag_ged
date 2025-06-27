from flask import Blueprint, request, redirect, url_for, flash, session, jsonify
import json
from AppFlask.db import db_connection
from flask_login import login_required, current_user
from AppFlask.api.auth import token_required
import logging
import psycopg2.extras

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

# @dashboard_bp.route('/')
# def home():
#     return render_template('dashboard.html')

@dashboard_bp.route('/dashboard/preferences', methods=['GET', 'POST'])
@login_required
def manage_preferences():
    user_id = session.get('user_id')

    if not user_id:
        flash("Vous devez être connecté pour accéder aux préférences")
        return redirect(url_for('auth.login'))

    conn = db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        dark_mode = request.form.get('dark_mode') == 'on'
        preferences = {"dark_mode": dark_mode}

        update_query = """
            INSERT INTO TableauDeBord (utilisateur_id, preferences)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE preferences = VALUES(preferences)
        """
        cursor.execute(update_query, (user_id, json.dumps(preferences)))
        conn.commit()
        flash("Préférences mises à jour avec succès")

    cursor.execute("SELECT preferences FROM TableauDeBord WHERE utilisateur_id = %s", (user_id,))
    result = cursor.fetchone()
    preferences = result['preferences'] if result else {}

    cursor.close()
    conn.close()

    return render_template('preferences.html', preferences=preferences)

@dashboard_bp.route('/api/users/count', methods=['GET'])
@token_required
def get_users_count(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("SELECT COUNT(*) as count FROM utilisateur")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur lors du comptage des utilisateurs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/documents/count', methods=['GET'])
@token_required
def get_documents_count(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM document d
            LEFT JOIN trash c ON d.id = c.item_id AND c.item_type = 'document'
            WHERE c.id IS NULL
        """)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur lors du comptage des documents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/folders/count', methods=['GET'])
@token_required
def get_folders_count(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("SELECT COUNT(*) as count FROM dossier")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur lors du comptage des dossiers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/archives/count', methods=['GET'])
@token_required
def get_archives_count(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM document d
            LEFT JOIN trash c ON d.id = c.item_id AND c.item_type = 'document'
            WHERE c.id IS NULL
        """)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erreur lors du comptage des archives: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/documents/recent', methods=['GET'])
@token_required
def get_recent_documents(current_user):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT 
                d.id,
                d.titre,
                COALESCE(NULLIF(REGEXP_REPLACE(d.fichier, '^.*\.', ''), ''), 'Inconnu') as type_document,
                d.taille,
                TO_CHAR(date_trunc('minute', d.date_ajout), 'DD/MM/YYYY HH24:MI') as date_ajout,
                u.nom as proprietaire_nom,
                u.prenom as proprietaire_prenom
            FROM document d
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            LEFT JOIN trash c ON d.id = c.item_id AND c.item_type = 'document'
            WHERE c.id IS NULL
            ORDER BY d.date_ajout DESC
            LIMIT 10
        """)
        documents = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(documents)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents récents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/documents/my', methods=['GET'])
@token_required
def get_my_documents(current_user):
    try:
        # Récupérer les paramètres
        dossier_id = request.args.get('dossier_id')
        admin_mode = request.args.get('admin_mode', 'false').lower() == 'true'
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Log des informations de l'utilisateur courant
        logger.info(f"Utilisateur connecté - ID: {current_user['id']}, Role: {current_user.get('role', 'non défini')}")
        logger.info(f"Paramètre dossier_id reçu: '{dossier_id}', admin_mode: {admin_mode}")
        
        # Vérifier si l'utilisateur est admin
        cursor.execute("""
            SELECT id, role, nom, prenom 
            FROM utilisateur 
            WHERE id = %s
        """, (current_user['id'],))
        user_info = cursor.fetchone()
        
        is_admin = user_info and user_info['role'].lower() == 'admin'
        logger.info(f"Est admin ? {is_admin}")
        
        # Si admin_mode est demandé mais l'utilisateur n'est pas admin, ignorer
        if admin_mode and not is_admin:
            admin_mode = False
            logger.info("Mode admin demandé mais utilisateur pas admin - basculement en mode normal")
        
        # Convertir dossier_id
        filter_by_folder = False
        if dossier_id is not None and dossier_id != '':
            try:
                dossier_id = int(dossier_id)
                filter_by_folder = True
            except ValueError:
                filter_by_folder = False
                
        logger.info(f"dossier_id après conversion: {dossier_id}, filter_by_folder: {filter_by_folder}")
        
        # Construire la requête
        query = """
            SELECT 
                d.id,
                d.titre,
                d.fichier,
                d.proprietaire_id,
                d.dossier_id,
                COALESCE(NULLIF(REGEXP_REPLACE(d.fichier, '^.*\.', ''), ''), 'Inconnu') as type_document,
                d.taille,
                CASE 
                    WHEN d.taille IS NULL THEN 'N/A'
                    WHEN d.taille < 1024 THEN d.taille || ' o'
                    WHEN d.taille < 1048576 THEN ROUND(d.taille::numeric/1024, 2) || ' Ko'
                    WHEN d.taille < 1073741824 THEN ROUND(d.taille::numeric/1048576, 2) || ' Mo'
                    ELSE ROUND(d.taille::numeric/1073741824, 2) || ' Go'
                END as taille_formatee,
                d.date_ajout,
                d.derniere_modification,
                d.description,
                u.nom as proprietaire_nom,
                u.prenom as proprietaire_prenom,
                u.role as proprietaire_role,
                CASE 
                    WHEN c.id IS NOT NULL THEN 'Trash'
                    ELSE 'Actif'
                END as statut
            FROM document d
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            LEFT JOIN trash c ON d.id = c.item_id AND c.item_type = 'document'
            WHERE c.id IS NULL
        """
        
        params = []
        
        # Filtrage par propriétaire selon le mode
        if admin_mode:
            logger.info("Mode admin activé - affichage de tous les documents")
        else:
            query += " AND d.proprietaire_id = %s"
            params.append(current_user['id'])
            logger.info(f"Mode normal - filtrage par propriétaire_id: {current_user['id']}")
        
        # Filtrer par dossier si spécifié
        if filter_by_folder:
            if dossier_id == 0:  # Convention : 0 = racine
                query += " AND d.dossier_id IS NULL"
                logger.info("Filtrage: documents à la racine (dossier_id IS NULL)")
            else:
                query += " AND d.dossier_id = %s"
                params.append(dossier_id)
                logger.info(f"Filtrage par dossier_id: {dossier_id}")
        else:
            logger.info("Aucun filtrage par dossier")
        
        # Ordre
        query += " ORDER BY d.derniere_modification DESC NULLS LAST"
        
        # Exécuter la requête
        cursor.execute(query, tuple(params))
        documents = cursor.fetchall()
        
        logger.info(f"Nombre de documents trouvés : {len(documents)}")
        
        # Formater les données
        for doc in documents:
            if doc['type_document']:
                doc['type_document'] = doc['type_document'].upper()
            
            # Convertir les dates
            if doc['date_ajout']:
                doc['date_creation'] = doc['date_ajout'].isoformat()
            else:
                doc['date_creation'] = None
                
            if doc['derniere_modification']:
                doc['derniere_modification'] = doc['derniere_modification'].isoformat()  
            else:
                doc['derniere_modification'] = None
                
            del doc['date_ajout']
            
            logger.info(f"Document: {doc['titre']} - Propriétaire: {doc['proprietaire_nom']} {doc['proprietaire_prenom']} (ID: {doc['proprietaire_id']}) - Dossier: {doc['dossier_id']}")
        
        cursor.close()
        conn.close()
        
        return jsonify(documents)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents: {str(e)}")
        return jsonify({'error': str(e)}), 500
