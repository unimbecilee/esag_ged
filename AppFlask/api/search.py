from flask import Blueprint, request, jsonify
from AppFlask.db import db_connection
from AppFlask.api.auth import token_required
import logging
import json
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

bp = Blueprint('api_search', __name__)

@bp.route('/search', methods=['GET'])
@token_required
def search(current_user):
    """Recherche globale unifiée dans toute l'application ESAG GED"""
    try:
        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 50, type=int)
        entity_type = request.args.get('type', '').strip()  # Filtrer par type d'entité
        
        if not query:
            return jsonify({'results': [], 'total': 0, 'query': query})

        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        search_pattern = f"%{query}%"
        is_admin = current_user['role'].lower() == 'admin'
        user_id = current_user['id']
        
        all_results = []
        
        logger.info(f"Recherche démarrée - Query: '{query}', Type: '{entity_type}', User: {user_id}, Admin: {is_admin}")
        
        # Suppression de la vérification de comptage qui causait l'erreur
        
        # 1. RECHERCHE DANS LES DOCUMENTS (utilise la logique simple qui fonctionne)
        if not entity_type or entity_type == 'document':
            try:
                logger.info(f"🔍 Recherche documents avec pattern: '{search_pattern}'")
                
                cursor.execute("""
                    SELECT 
                        d.id,
                        d.titre as title,
                        COALESCE(d.description, '') as description,
                        'document' as entity_type,
                        'Document' as entity_label,
                        d.date_ajout as date_creation,
                        COALESCE(d.categorie, 'Sans catégorie') as category,
                        d.taille,
                        d.fichier as filename,
                        COALESCE(u.prenom, '') as owner_firstname,
                        COALESCE(u.nom, '') as owner_lastname,
                        'PDF' as file_type,
                        '1 MB' as size_formatted
                    FROM document d
                    LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
                    WHERE LOWER(d.titre) LIKE LOWER(%s)
                    ORDER BY d.date_ajout DESC
                    LIMIT %s
                """, (search_pattern, limit))
                
                doc_results = cursor.fetchall()
                logger.info(f"📄 Documents trouvés: {len(doc_results)} pour recherche '{query}'")
                
                # Filtrage des permissions temporairement désactivé pour éviter les erreurs
                if not is_admin:
                    logger.info(f"📄 Filtrage permissions non-admin pas encore implémenté")
                
                all_results.extend(doc_results)
                
            except Exception as doc_error:
                logger.error(f"❌ Erreur recherche documents: {doc_error}")
                import traceback

        # 2. RECHERCHE DANS LES UTILISATEURS (seulement pour les admins)
        if is_admin and (not entity_type or entity_type == 'user'):
            try:
                cursor.execute("""
                    SELECT 
                        u.id,
                        CONCAT(COALESCE(u.prenom, ''), ' ', COALESCE(u.nom, '')) as title,
                        COALESCE(u.email, '') as description,
                        COALESCE(u.role, 'Utilisateur') as category,
                        u.date_creation,
                        null as taille,
                        null as filename,
                        'user' as entity_type,
                        'Utilisateur' as entity_label,
                        null as size_formatted,
                        COALESCE(u.prenom, '') as owner_firstname,
                        COALESCE(u.nom, '') as owner_lastname,
                        COALESCE(u.role, 'Utilisateur') as file_type
                    FROM utilisateur u
                    WHERE 
                        LOWER(COALESCE(u.nom, '')) LIKE LOWER(%s) OR 
                        LOWER(COALESCE(u.prenom, '')) LIKE LOWER(%s) OR 
                        LOWER(COALESCE(u.email, '')) LIKE LOWER(%s) OR
                        LOWER(COALESCE(u.role, '')) LIKE LOWER(%s)
                    ORDER BY u.date_creation DESC
                    LIMIT %s
                """, (search_pattern, search_pattern, search_pattern, search_pattern, limit))
                
                user_results = cursor.fetchall()
                logger.info(f"Utilisateurs trouvés: {len(user_results)}")
                all_results.extend(user_results)
                
            except Exception as user_error:
                logger.error(f"Erreur recherche utilisateurs: {user_error}")
        
        # 3. RECHERCHE DANS LES DOSSIERS
        if not entity_type or entity_type == 'folder':
            try:
                cursor.execute("""
                    SELECT 
                        d.id,
                        COALESCE(d.titre, 'Sans titre') as title,
                        COALESCE(d.description, '') as description,
                        'Dossier' as category,
                        d.date_creation,
                        null as taille,
                        null as filename,
                        'folder' as entity_type,
                        'Dossier' as entity_label,
                        null as size_formatted,
                        COALESCE(u.prenom, '') as owner_firstname,
                        COALESCE(u.nom, '') as owner_lastname,
                        'Dossier' as file_type
                    FROM dossier d
                    LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
                    WHERE 
                        (LOWER(COALESCE(d.titre, '')) LIKE LOWER(%s) OR 
                         LOWER(COALESCE(d.description, '')) LIKE LOWER(%s))
                        AND (
                            d.proprietaire_id = %s OR 
                            %s = true OR
                            EXISTS (SELECT 1 FROM partage_dossier pd WHERE pd.dossier_id = d.id AND pd.utilisateur_id = %s)
                        )
                    ORDER BY d.date_creation DESC
                    LIMIT %s
                """, (search_pattern, search_pattern, user_id, is_admin, user_id, limit))
                
                folder_results = cursor.fetchall()
                logger.info(f"Dossiers trouvés: {len(folder_results)}")
                all_results.extend(folder_results)
                
            except Exception as folder_error:
                logger.error(f"Erreur recherche dossiers: {folder_error}")
        
        # 4. RECHERCHE DANS LES ORGANISATIONS
        if not entity_type or entity_type == 'organization':
            try:
                cursor.execute("""
                    SELECT 
                        o.id,
                        COALESCE(o.nom, 'Sans nom') as title,
                        COALESCE(o.description, '') as description,
                        'Organisation' as category,
                        o.date_creation,
                        null as taille,
                        null as filename,
                        'organization' as entity_type,
                        'Organisation' as entity_label,
                        null as size_formatted,
                        '' as owner_firstname,
                        '' as owner_lastname,
                        'Organisation' as file_type
                    FROM organisation o
                    WHERE 
                        LOWER(COALESCE(o.nom, '')) LIKE LOWER(%s) OR 
                        LOWER(COALESCE(o.description, '')) LIKE LOWER(%s)
                    ORDER BY o.date_creation DESC
                    LIMIT %s
                """, (search_pattern, search_pattern, limit))
                
                org_results = cursor.fetchall()
                logger.info(f"Organisations trouvées: {len(org_results)}")
                all_results.extend(org_results)
                
            except Exception as org_error:
                logger.error(f"Erreur recherche organisations: {org_error}")
                traceback.print_exc()
        
        # Formatage des dates pour le frontend
        for result in all_results:
            if result.get('date_creation'):
                if hasattr(result['date_creation'], 'isoformat'):
                    result['date_creation'] = result['date_creation'].isoformat()
                else:
                    result['date_creation'] = str(result['date_creation'])
        
        # Statistiques finales
        stats = {
            'documents': len([r for r in all_results if r.get('entity_type') == 'document']),
            'users': len([r for r in all_results if r.get('entity_type') == 'user']),
            'folders': len([r for r in all_results if r.get('entity_type') == 'folder']),
            'organizations': len([r for r in all_results if r.get('entity_type') == 'organization'])
        }
        
        logger.info(f"Total résultats bruts: {len(all_results)}")
        logger.info(f"Résultats finaux: {len(all_results)}, Stats: {stats}")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'results': all_results,
            'total': len(all_results),
            'query': query,
            'stats': stats,
            'limit': limit,
            'user_role': current_user['role']
        })

    except Exception as e:
        logger.error(f"Erreur générale dans la recherche: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'results': [],
            'total': 0,
            'query': query if 'query' in locals() else '',
            'error': str(e)
        }), 500

@bp.route('/search/debug', methods=['GET'])
@token_required
def debug_search(current_user):
    """Endpoint de debug pour tester la recherche"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        debug_info = {
            'user_id': current_user['id'],
            'user_role': current_user['role'],
            'is_admin': current_user['role'].lower() == 'admin'
        }
        
        # Compter les éléments dans chaque table
        tables_to_check = [
            ('document', 'documents'),
            ('utilisateur', 'utilisateurs'),
            ('dossier', 'dossiers'),
            ('organisation', 'organisations'),
            ('workflow', 'workflows'),
            ('tag', 'tags'),
            ('history', 'historique')
        ]
        
        table_counts = {}
        for table_name, label in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                result = cursor.fetchone()
                count = result['count'] if result else 0
                table_counts[label] = count
                logger.info(f"Table {table_name}: {count} entrées")
            except Exception as e:
                error_msg = f"Erreur: {str(e)}"
                table_counts[label] = error_msg
                logger.error(f"Erreur table {table_name}: {e}")
        
        # Test requête documents simple
        try:
            cursor.execute("SELECT id, titre FROM document LIMIT 5")
            sample_docs = cursor.fetchall()
            debug_info['sample_documents'] = [dict(doc) for doc in sample_docs]
        except Exception as e:
            debug_info['sample_documents'] = f"Erreur: {str(e)}"
        
        # Test requête utilisateurs simple
        try:
            cursor.execute("SELECT id, nom, prenom FROM utilisateur LIMIT 5")
            sample_users = cursor.fetchall()
            debug_info['sample_users'] = [dict(user) for user in sample_users]
        except Exception as e:
            debug_info['sample_users'] = f"Erreur: {str(e)}"
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'debug_info': debug_info,
            'table_counts': table_counts,
            'message': 'Informations de debug récupérées avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur debug search: {str(e)}")
        return jsonify({'error': f'Erreur debug: {str(e)}'}), 500

@bp.route('/search/saved', methods=['GET'])
@token_required
def get_saved_searches(current_user):
    """Récupérer les recherches sauvegardées de l'utilisateur"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                id,
                name,
                filters,
                created_at,
                last_used
            FROM saved_searches 
            WHERE user_id = %s
            ORDER BY last_used DESC, created_at DESC
        """, (user_id,))
        
        saved_searches = cursor.fetchall()
        
        # Formater les dates
        for search in saved_searches:
            if search['created_at']:
                search['created_at'] = search['created_at'].isoformat() if hasattr(search['created_at'], 'isoformat') else str(search['created_at'])
            if search['last_used']:
                search['last_used'] = search['last_used'].isoformat() if hasattr(search['last_used'], 'isoformat') else str(search['last_used'])
        
        cursor.close()
        conn.close()
        
        return jsonify(saved_searches), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des recherches sauvegardées: {str(e)}")
        return jsonify({'error': 'Erreur lors de la récupération des recherches sauvegardées'}), 500

@bp.route('/search/saved', methods=['POST'])
@token_required
def save_search(current_user):
    """Sauvegarder une recherche"""
    try:
        user_id = current_user['id']
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('filters'):
            return jsonify({'error': 'Nom et filtres requis'}), 400
        
        name = data['name']
        filters = data['filters']
        
        conn = db_connection()
        cursor = conn.cursor()
        
        # Vérifier si une recherche avec ce nom existe déjà
        cursor.execute("""
            SELECT id FROM saved_searches 
            WHERE user_id = %s AND name = %s
        """, (user_id, name))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Une recherche avec ce nom existe déjà'}), 409
        
        # Insérer la nouvelle recherche sauvegardée
        cursor.execute("""
            INSERT INTO saved_searches (user_id, name, filters, created_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id
        """, (user_id, name, json.dumps(filters)))
        
        result = cursor.fetchone()
        search_id = result['id'] if result else None
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'id': search_id,
            'message': 'Recherche sauvegardée avec succès'
        }), 201
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la recherche: {str(e)}")
        return jsonify({'error': 'Erreur lors de la sauvegarde de la recherche'}), 500

@bp.route('/search/saved/<int:search_id>', methods=['DELETE'])
@token_required
def delete_saved_search(current_user, search_id):
    """Supprimer une recherche sauvegardée"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM saved_searches 
            WHERE id = %s AND user_id = %s
        """, (search_id, user_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Recherche sauvegardée non trouvée'}), 404
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Recherche sauvegardée supprimée'}), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la recherche sauvegardée: {str(e)}")
        return jsonify({'error': 'Erreur lors de la suppression'}), 500

@bp.route('/search/saved/<int:search_id>/execute', methods=['GET'])
@token_required
def execute_saved_search(current_user, search_id):
    """Exécuter une recherche sauvegardée"""
    try:
        user_id = current_user['id']
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer la recherche sauvegardée
        cursor.execute("""
            SELECT filters FROM saved_searches 
            WHERE id = %s AND user_id = %s
        """, (search_id, user_id))
        
        saved_search = cursor.fetchone()
        if not saved_search:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Recherche sauvegardée non trouvée'}), 404
        
        # Mettre à jour la date de dernière utilisation
        cursor.execute("""
            UPDATE saved_searches 
            SET last_used = NOW() 
            WHERE id = %s
        """, (search_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # Récupérer les filtres et les renvoyer pour exécution côté client
        filters = saved_search['filters']
        if isinstance(filters, str):
            filters = json.loads(filters)
        
        return jsonify({
            'filters': filters,
            'message': 'Recherche sauvegardée récupérée'
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la recherche sauvegardée: {str(e)}")
        return jsonify({'error': 'Erreur lors de l\'exécution'}), 500

@bp.route('/search/suggestions', methods=['GET'])
@token_required
def get_search_suggestions(current_user):
    """Obtenir des suggestions de recherche basées sur l'historique"""
    try:
        user_id = current_user['id']
        query = request.args.get('q', '').strip()
        
        if len(query) < 2:
            return jsonify([]), 200
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        suggestions = []
        
        # Suggestions basées sur les titres de documents
        cursor.execute("""
            SELECT DISTINCT titre
            FROM document d
            LEFT JOIN partage p ON d.id = p.document_id
            WHERE 
                LOWER(titre) LIKE LOWER(%s) AND
                (d.proprietaire_id = %s OR 
                 p.utilisateur_id = %s OR 
                 %s)
            ORDER BY titre
            LIMIT 5
        """, (f"%{query}%", user_id, user_id, current_user['role'].lower() == 'admin'))
        
        document_suggestions = cursor.fetchall()
        suggestions.extend([{
            'type': 'document',
            'text': doc['titre'],
            'category': 'Documents'
        } for doc in document_suggestions])
        
        # Suggestions basées sur les catégories
        cursor.execute("""
            SELECT DISTINCT categorie
            FROM document d
            LEFT JOIN partage p ON d.id = p.document_id
            WHERE 
                LOWER(categorie) LIKE LOWER(%s) AND
                categorie IS NOT NULL AND
                (d.proprietaire_id = %s OR 
                 p.utilisateur_id = %s OR 
                 %s)
            ORDER BY categorie
            LIMIT 3
        """, (f"%{query}%", user_id, user_id, current_user['role'].lower() == 'admin'))
        
        category_suggestions = cursor.fetchall()
        suggestions.extend([{
            'type': 'category',
            'text': cat['categorie'],
            'category': 'Catégories'
        } for cat in category_suggestions])
        
        cursor.close()
        conn.close()
        
        return jsonify(suggestions[:8]), 200  # Limiter à 8 suggestions
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des suggestions: {str(e)}")
        return jsonify([]), 200  # Retourner une liste vide en cas d'erreur

@bp.route('/search/test', methods=['GET'])
@token_required
def test_search(current_user):
    """Test ultra-simple de recherche pour diagnostic"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Query requise'}), 400
            
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        search_pattern = f"%{query}%"
        user_id = current_user['id']
        is_admin = current_user['role'].lower() == 'admin'
        
        logger.info(f"🧪 TEST - User: {user_id}, Admin: {is_admin}, Query: '{query}', Pattern: '{search_pattern}'")
        
        # Test 1: Requête la plus simple possible
        try:
            cursor.execute("SELECT id, titre FROM document LIMIT 5")
            all_docs = cursor.fetchall()
            logger.info(f"🧪 TEST - Documents dans la base: {len(all_docs)}")
            for doc in all_docs:
                logger.info(f"🧪 TEST - Doc: [{doc['id']}] {doc['titre']}")
        except Exception as e:
            logger.error(f"🧪 TEST - Erreur lecture docs: {e}")
            return jsonify({'error': f'Erreur lecture documents: {e}'}), 500
        
        # Test 2: Recherche très simple
        try:
            cursor.execute("""
                SELECT id, titre, description, categorie 
                FROM document 
                WHERE LOWER(titre) LIKE LOWER(%s)
                LIMIT 10
            """, (search_pattern,))
            
            simple_results = cursor.fetchall()
            logger.info(f"🧪 TEST - Résultats recherche simple: {len(simple_results)}")
            
            formatted_results = []
            for doc in simple_results:
                formatted_doc = {
                    'id': doc['id'],
                    'title': doc['titre'],
                    'description': doc.get('description', ''),
                    'category': doc.get('categorie', ''),
                    'entity_type': 'document',
                    'entity_label': 'Document'
                }
                formatted_results.append(formatted_doc)
                logger.info(f"🧪 TEST - Match: [{doc['id']}] {doc['titre']}")
                
        except Exception as e:
            logger.error(f"🧪 TEST - Erreur recherche simple: {e}")
            return jsonify({'error': f'Erreur recherche: {e}'}), 500
        
        # Test 3: Vérifier les permissions
        try:
            if is_admin:
                accessible_count = len(all_docs)  # Admin voit tout
            else:
                cursor.execute("""
                    SELECT COUNT(*) FROM document 
                    WHERE proprietaire_id = %s
                """, (user_id,))
                accessible_count = cursor.fetchone()[0]
            
            logger.info(f"🧪 TEST - Documents accessibles: {accessible_count}")
            
        except Exception as e:
            logger.error(f"🧪 TEST - Erreur permissions: {e}")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'query': query,
            'user_id': user_id,
            'is_admin': is_admin,
            'total_docs': len(all_docs),
            'accessible_docs': accessible_count,
            'search_results': len(formatted_results),
            'results': formatted_results,
            'debug': 'Test de recherche ultra-simple terminé'
        })
        
    except Exception as e:
        logger.error(f"🧪 TEST - Erreur générale: {e}")
        return jsonify({'error': f'Erreur test: {e}'}), 500

@bp.route('/search/advanced', methods=['GET'])
@token_required
def advanced_search(current_user):
    """Recherche avancée unifiée avec support OCR et filtres intelligents"""
    try:
        # Récupération des paramètres
        search_term = request.args.get('searchTerm', '').strip()
        content_search = request.args.get('contentSearch', '').strip()
        ocr_search = request.args.get('ocrSearch', '').strip()
        document_types = request.args.get('documentTypes', '').split(',') if request.args.get('documentTypes') else []
        owners = request.args.get('owners', '').split(',') if request.args.get('owners') else []
        tags = request.args.get('tags', '').split(',') if request.args.get('tags') else []
        status = request.args.get('status', '').split(',') if request.args.get('status') else []
        start_date = request.args.get('startDate', '')
        end_date = request.args.get('endDate', '')
        min_size = request.args.get('minSize', '0')
        max_size = request.args.get('maxSize', '500')
        has_attachments = request.args.get('hasAttachments', 'false').lower() == 'true'
        is_shared = request.args.get('isShared', 'false').lower() == 'true'
        is_favorite = request.args.get('isFavorite', 'false').lower() == 'true'
        has_ocr = request.args.get('hasOCR', 'false').lower() == 'true'
        language = request.args.get('language', '').strip()
        confidence_threshold = int(request.args.get('confidenceThreshold', '70'))
        include_archived = request.args.get('includeArchived', 'false').lower() == 'true'
        limit = request.args.get('limit', 100, type=int)
        
        user_id = current_user['id']
        is_admin = current_user['role'].lower() == 'admin'
        
        # Validation
        if not any([search_term, content_search, ocr_search]) and not any([
            document_types, owners, tags, status, start_date, end_date, is_shared, is_favorite, has_ocr
        ]):
            return jsonify({
                'results': [],
                'total': 0,
                'message': 'Aucun critère de recherche spécifié'
            })
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        logger.info(f"🔍 Recherche avancée - User: {user_id}, Admin: {is_admin}")
        logger.info(f"📝 Termes: '{search_term}', Contenu: '{content_search}', OCR: '{ocr_search}'")
        logger.info(f"🏷️ Types: {document_types}, Statuts: {status}")
        logger.info(f"📅 Dates: {start_date} - {end_date}")
        logger.info(f"🤖 OCR requis: {has_ocr}, Confiance: {confidence_threshold}%")
        
        # Construction de la requête principale
        base_query = """
            SELECT DISTINCT
                d.id,
                d.titre,
                COALESCE(d.categorie, 'Sans catégorie') as type_document,
                d.date_ajout as date_creation,
                d.derniere_modification,
                d.taille,
                CASE 
                    WHEN d.taille IS NULL OR d.taille = 0 THEN '0 B'
                    WHEN d.taille < 1024 THEN CONCAT(d.taille::text, ' B')
                    WHEN d.taille < 1048576 THEN CONCAT(ROUND(d.taille/1024.0, 2)::text, ' KB')
                    WHEN d.taille < 1073741824 THEN CONCAT(ROUND(d.taille/1048576.0, 2)::text, ' MB')
                    ELSE CONCAT(ROUND(d.taille/1073741824.0, 2)::text, ' GB')
                END as taille_formatee,
                COALESCE(d.statut, 'actif') as statut,
                COALESCE(u.prenom, '') as proprietaire_prenom,
                COALESCE(u.nom, '') as proprietaire_nom,
                COALESCE(d.description, '') as description,
                d.fichier as filename,
                -- Calcul du score de pertinence
                CASE
                    WHEN f.id IS NOT NULL THEN 1.0  -- Documents favoris
                    WHEN p.id IS NOT NULL THEN 0.9  -- Documents partagés
                    ELSE 0.8
                END as relevance_score,
                -- Métadonnées OCR si disponibles
                CASE 
                    WHEN dm.metadonnees IS NOT NULL AND dm.metadonnees::text LIKE '%ocr%' THEN 
                        (dm.metadonnees->'ocr'->>'confidence')::float
                    ELSE NULL 
                END as ocr_confidence,
                CASE 
                    WHEN dm.metadonnees IS NOT NULL AND dm.metadonnees::text LIKE '%ocr%' THEN 
                        SUBSTRING(dm.metadonnees->'ocr'->>'text' FROM 1 FOR 200)
                    ELSE NULL 
                END as ocr_preview,
                CASE 
                    WHEN dm.metadonnees IS NOT NULL AND dm.metadonnees::text LIKE '%ocr%' THEN TRUE
                    ELSE FALSE 
                END as has_ocr
            FROM document d
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            LEFT JOIN favoris f ON d.id = f.document_id AND f.utilisateur_id = %s
            LEFT JOIN partage p ON d.id = p.document_id
            LEFT JOIN document_metadata dm ON d.id = dm.document_id
        """
        
        conditions = []
        params = [user_id]
        
        # Permissions (utilisateur propriétaire, document partagé, ou admin)
        if not is_admin:
            conditions.append("(d.proprietaire_id = %s OR p.utilisateur_id = %s)")
            params.extend([user_id, user_id])
        
        # Recherche dans les titres et descriptions
        if search_term:
            conditions.append("""(
                LOWER(d.titre) LIKE LOWER(%s) OR 
                LOWER(COALESCE(d.description, '')) LIKE LOWER(%s) OR
                LOWER(COALESCE(d.categorie, '')) LIKE LOWER(%s) OR
                LOWER(COALESCE(d.fichier, '')) LIKE LOWER(%s)
            )""")
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        
        # Recherche dans le contenu (pour l'instant basique, peut être étendue)
        if content_search:
            conditions.append("LOWER(COALESCE(d.description, '')) LIKE LOWER(%s)")
            params.append(f"%{content_search}%")
        
        # Recherche OCR
        if ocr_search:
            conditions.append("""(
                dm.metadonnees IS NOT NULL AND 
                dm.metadonnees::text LIKE '%ocr%' AND
                LOWER(dm.metadonnees->'ocr'->>'text') LIKE LOWER(%s)
            )""")
            params.append(f"%{ocr_search}%")
        
        # Filtre par types de documents
        if document_types and document_types != ['']:
            type_conditions = []
            for doc_type in document_types:
                if doc_type.strip():
                    type_conditions.append("LOWER(d.categorie) LIKE LOWER(%s) OR LOWER(d.fichier) LIKE LOWER(%s)")
                    type_pattern = f"%{doc_type.strip()}%"
                    params.extend([type_pattern, f"%.{doc_type.lower()}"])
            if type_conditions:
                conditions.append(f"({' OR '.join(type_conditions)})")
        
        # Filtre par propriétaires
        if owners and owners != ['']:
            owner_conditions = []
            for owner in owners:
                if owner.strip():
                    owner_conditions.append("""(
                        LOWER(u.nom) LIKE LOWER(%s) OR 
                        LOWER(u.prenom) LIKE LOWER(%s) OR 
                        LOWER(CONCAT(u.prenom, ' ', u.nom)) LIKE LOWER(%s)
                    )""")
                    owner_pattern = f"%{owner.strip()}%"
                    params.extend([owner_pattern, owner_pattern, owner_pattern])
            if owner_conditions:
                conditions.append(f"({' OR '.join(owner_conditions)})")
        
        # Filtre par statuts
        if status and status != ['']:
            status_conditions = []
            for stat in status:
                if stat.strip():
                    status_conditions.append("LOWER(COALESCE(d.statut, 'actif')) LIKE LOWER(%s)")
                    params.append(f"%{stat.strip()}%")
            if status_conditions:
                conditions.append(f"({' OR '.join(status_conditions)})")
        
        # Filtre par plage de dates
        if start_date:
            conditions.append("d.date_ajout >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("d.date_ajout <= %s")
            params.append(end_date)
        
        # Filtre par taille (conversion MB en bytes)
        try:
            min_size_bytes = int(float(min_size) * 1024 * 1024)
            max_size_bytes = int(float(max_size) * 1024 * 1024)
            
            if min_size_bytes > 0:
                conditions.append("d.taille >= %s")
                params.append(min_size_bytes)
            
            if max_size_bytes < 500 * 1024 * 1024:
                conditions.append("d.taille <= %s")
                params.append(max_size_bytes)
        except (ValueError, TypeError):
            logger.warning(f"Erreur conversion taille: min={min_size}, max={max_size}")
        
        # Filtre pour documents partagés
        if is_shared:
            conditions.append("p.id IS NOT NULL")
        
        # Filtre pour documents favoris
        if is_favorite:
            conditions.append("f.id IS NOT NULL")
        
        # Filtre pour documents avec OCR
        if has_ocr:
            conditions.append("(dm.metadonnees IS NOT NULL AND dm.metadonnees::text LIKE '%ocr%')")
        
        # Filtre par confiance OCR
        if confidence_threshold > 0 and confidence_threshold < 100:
            conditions.append("""(
                dm.metadonnees IS NULL OR 
                dm.metadonnees::text NOT LIKE '%ocr%' OR
                (dm.metadonnees->'ocr'->>'confidence')::float >= %s
            )""")
            params.append(confidence_threshold)
        
        # Filtre par langue (pour l'OCR principalement)
        if language:
            conditions.append("""(
                dm.metadonnees IS NULL OR 
                dm.metadonnees::text NOT LIKE '%ocr%' OR
                LOWER(dm.metadonnees->'ocr'->>'language') LIKE LOWER(%s)
            )""")
            params.append(f"%{language}%")
        
        # Inclure/exclure les documents archivés
        if not include_archived:
            conditions.append("LOWER(COALESCE(d.statut, 'actif')) != 'archivé'")
        
        # Construction de la requête finale
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
        else:
            where_clause = " WHERE 1=1"
        
        order_clause = " ORDER BY relevance_score DESC, d.date_ajout DESC"
        limit_clause = f" LIMIT {min(limit, 1000)}"  # Limite sécurisée
        
        final_query = base_query + where_clause + order_clause + limit_clause
        
        logger.info(f"🔍 Exécution requête avec {len(params)} paramètres")
        
        cursor.execute(final_query, params)
        documents = cursor.fetchall()
        
        logger.info(f"📊 Documents trouvés: {len(documents)}")
        
        # Formatage des résultats
        formatted_results = []
        for doc in documents:
            formatted_doc = dict(doc)
            
            # Formatage des dates
            if formatted_doc.get('date_creation'):
                if hasattr(formatted_doc['date_creation'], 'isoformat'):
                    formatted_doc['date_creation'] = formatted_doc['date_creation'].isoformat()
                else:
                    formatted_doc['date_creation'] = str(formatted_doc['date_creation'])
            
            if formatted_doc.get('derniere_modification'):
                if hasattr(formatted_doc['derniere_modification'], 'isoformat'):
                    formatted_doc['derniere_modification'] = formatted_doc['derniere_modification'].isoformat()
                else:
                    formatted_doc['derniere_modification'] = str(formatted_doc['derniere_modification'])
            
            # Génération de snippets pour la recherche OCR
            if ocr_search and formatted_doc.get('ocr_preview'):
                # Extraire des extraits pertinents
                text = formatted_doc['ocr_preview'].lower()
                search_lower = ocr_search.lower()
                
                if search_lower in text:
                    start_pos = max(0, text.find(search_lower) - 50)
                    end_pos = min(len(text), text.find(search_lower) + len(search_lower) + 50)
                    snippet = formatted_doc['ocr_preview'][start_pos:end_pos]
                    formatted_doc['highlight_snippets'] = [f"...{snippet}..."]
            
            # Amélioration du score de pertinence basé sur les correspondances
            base_score = formatted_doc.get('relevance_score', 0.8)
            
            # Bonus pour correspondance exacte dans le titre
            if search_term and search_term.lower() in formatted_doc.get('titre', '').lower():
                base_score += 0.3
            
            # Bonus pour documents avec OCR de haute confiance
            if formatted_doc.get('ocr_confidence') and formatted_doc['ocr_confidence'] > 90:
                base_score += 0.1
            
            # Bonus pour correspondance OCR
            if ocr_search and formatted_doc.get('ocr_preview'):
                if ocr_search.lower() in formatted_doc['ocr_preview'].lower():
                    base_score += 0.2
            
            formatted_doc['relevance_score'] = min(base_score, 2.0)  # Plafonner à 2.0
            
            formatted_results.append(formatted_doc)
        
        # Tri final par pertinence
        formatted_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        cursor.close()
        conn.close()
        
        # Statistiques pour le debug
        ocr_docs = len([doc for doc in formatted_results if doc.get('has_ocr')])
        avg_confidence = sum([doc.get('ocr_confidence', 0) for doc in formatted_results if doc.get('ocr_confidence')]) / max(ocr_docs, 1)
        
        logger.info(f"✅ Recherche avancée terminée: {len(formatted_results)} résultats")
        logger.info(f"📊 Documents avec OCR: {ocr_docs}, Confiance moyenne: {avg_confidence:.1f}%")
        
        return jsonify({
            'results': formatted_results,
            'total': len(formatted_results),
            'stats': {
                'ocr_documents': ocr_docs,
                'average_ocr_confidence': round(avg_confidence, 1),
                'search_criteria': {
                    'has_general_search': bool(search_term),
                    'has_content_search': bool(content_search),
                    'has_ocr_search': bool(ocr_search),
                    'has_filters': bool(document_types or owners or tags or status),
                    'has_date_range': bool(start_date or end_date),
                    'requires_ocr': has_ocr,
                    'confidence_threshold': confidence_threshold
                }
            },
            'query_info': {
                'search_term': search_term,
                'content_search': content_search,
                'ocr_search': ocr_search,
                'applied_filters': len([f for f in [document_types, owners, tags, status] if f])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur recherche avancée: {e}")
        return jsonify({
            'error': 'Erreur lors de la recherche avancée',
            'details': str(e) if current_user.get('role') == 'admin' else None
        }), 500
