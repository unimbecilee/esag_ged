from flask import Blueprint, request, jsonify, send_file, current_app
from ..db import db_connection
from ..api.auth import token_required
from ..services.document_processing_service import DocumentProcessingService
from psycopg2.extras import RealDictCursor
import os
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('document_processing', __name__, url_prefix='/api/documents')

# Instancier le service de traitement
processing_service = DocumentProcessingService()

@bp.route('/<int:doc_id>/ocr', methods=['POST'])
@token_required
def perform_ocr(current_user, doc_id):
    """Effectuer la reconnaissance optique de caractères sur un document"""
    try:
        # Récupérer les paramètres
        data = request.get_json() or {}
        language = data.get('language', 'fra')  # français par défaut
        
        # Vérifier l'existence du document et les permissions
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT d.*, u.nom as proprietaire_nom, u.prenom as proprietaire_prenom
            FROM document d
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            WHERE d.id = %s
        """, (doc_id,))
        
        document = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        # Vérifier les permissions (propriétaire ou partage)
        if document['proprietaire_id'] != current_user['id']:
            # Vérifier le partage
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT permissions FROM partage 
                WHERE document_id = %s AND utilisateur_id = %s
            """, (doc_id, current_user['id']))
            partage = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not partage:
                return jsonify({'error': 'Accès non autorisé'}), 403
        
        # Construire le chemin du fichier
        file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), document['fichier'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        # Effectuer l'OCR
        ocr_result = processing_service.perform_ocr(file_path, language)
        
        if 'error' in ocr_result:
            return jsonify({'error': ocr_result['error']}), 500
        
        # Sauvegarder le résultat dans la base de données
        conn = db_connection()
        cursor = conn.cursor()
        
        # Mettre à jour les métadonnées du document
        metadata = json.loads(document.get('metadonnees', '{}'))
        metadata['ocr'] = ocr_result
        
        cursor.execute("""
            UPDATE document 
            SET metadonnees = %s, derniere_modification = NOW()
            WHERE id = %s
        """, (json.dumps(metadata), doc_id))
        
        # Enregistrer dans l'historique
        cursor.execute("""
            INSERT INTO historique (action, entite_type, entite_id, utilisateur_id, details, date_action)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, ('OCR_PERFORMED', 'document', doc_id, current_user['id'], 
              json.dumps({'language': language, 'confidence': ocr_result.get('confidence', 0)})))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'OCR effectué avec succès',
            'result': ocr_result
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de l'OCR: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:doc_id>/preview', methods=['GET'])
@token_required
def get_document_preview(current_user, doc_id):
    """Générer et récupérer l'aperçu d'un document"""
    try:
        page = request.args.get('page', 1, type=int)
        regenerate = request.args.get('regenerate', 'false').lower() == 'true'
        
        # Vérifier l'existence du document et les permissions
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        # Vérifier les permissions
        if document['proprietaire_id'] != current_user['id']:
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT permissions FROM partage 
                WHERE document_id = %s AND utilisateur_id = %s
            """, (doc_id, current_user['id']))
            partage = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not partage:
                return jsonify({'error': 'Accès non autorisé'}), 403
        
        # Construire le chemin du fichier
        file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), document['fichier'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        # Générer l'aperçu
        preview_path = processing_service.generate_preview(file_path, page)
        
        if not preview_path or not os.path.exists(preview_path):
            return jsonify({'error': 'Impossible de générer l\'aperçu'}), 500
        
        return send_file(preview_path, as_attachment=False, mimetype='image/png')
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de l'aperçu: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:doc_id>/thumbnail', methods=['GET'])
@token_required
def get_document_thumbnail(current_user, doc_id):
    """Générer et récupérer la miniature d'un document"""
    try:
        size_param = request.args.get('size', '200x200')
        regenerate = request.args.get('regenerate', 'false').lower() == 'true'
        
        # Parser la taille
        try:
            width, height = map(int, size_param.split('x'))
            size = (width, height)
        except:
            size = (200, 200)
        
        # Vérifier l'existence du document
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        # Construire le chemin du fichier
        file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), document['fichier'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        # Générer la miniature
        thumbnail_path = processing_service.generate_thumbnail(file_path, size)
        
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            return jsonify({'error': 'Impossible de générer la miniature'}), 500
        
        return send_file(thumbnail_path, as_attachment=False, mimetype='image/png')
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la miniature: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:doc_id>/metadata', methods=['GET'])
@token_required
def get_document_metadata(current_user, doc_id):
    """Extraire et récupérer les métadonnées détaillées d'un document"""
    try:
        regenerate = request.args.get('regenerate', 'false').lower() == 'true'
        
        # Vérifier l'existence du document et les permissions
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        # Vérifier les permissions
        if document['proprietaire_id'] != current_user['id']:
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT permissions FROM partage 
                WHERE document_id = %s AND utilisateur_id = %s
            """, (doc_id, current_user['id']))
            partage = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not partage:
                return jsonify({'error': 'Accès non autorisé'}), 403
        
        # Si les métadonnées existent déjà et qu'on ne force pas la régénération
        existing_metadata = json.loads(document.get('metadonnees', '{}'))
        if existing_metadata and not regenerate:
            return jsonify({
                'message': 'Métadonnées récupérées',
                'metadata': existing_metadata
            }), 200
        
        # Construire le chemin du fichier
        file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), document['fichier'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        # Extraire les métadonnées
        metadata = processing_service.extract_metadata(file_path)
        
        if 'error' in metadata:
            return jsonify({'error': metadata['error']}), 500
        
        # Sauvegarder dans la base de données
        processing_service.update_document_metadata(doc_id, metadata)
        
        return jsonify({
            'message': 'Métadonnées extraites avec succès',
            'metadata': metadata
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des métadonnées: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:doc_id>/convert', methods=['POST'])
@token_required
def convert_document(current_user, doc_id):
    """Convertir un document vers un autre format"""
    try:
        data = request.get_json()
        if not data or 'target_format' not in data:
            return jsonify({'error': 'Format cible requis'}), 400
        
        target_format = data['target_format'].lower()
        
        # Vérifier l'existence du document et les permissions
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        # Vérifier les permissions (propriétaire ou édition)
        if document['proprietaire_id'] != current_user['id']:
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT permissions FROM partage 
                WHERE document_id = %s AND utilisateur_id = %s AND permissions IN ('édition', 'admin')
            """, (doc_id, current_user['id']))
            partage = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not partage:
                return jsonify({'error': 'Permissions insuffisantes'}), 403
        
        # Construire le chemin du fichier
        file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), document['fichier'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        # Effectuer la conversion
        converted_path = processing_service.convert_document(file_path, target_format)
        
        if not converted_path:
            return jsonify({'error': 'Conversion non supportée ou échec'}), 400
        
        # Créer un nouveau document ou remplacer l'existant selon le choix
        create_new = data.get('create_new', True)
        
        if create_new:
            # Créer un nouveau document
            converted_filename = os.path.basename(converted_path)
            new_title = f"{document['titre']}_converted"
            
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO document (titre, description, fichier, taille, categorie, 
                                    proprietaire_id, date_ajout, derniere_modification)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, (new_title, f"Conversion de {document['titre']} vers {target_format.upper()}", 
                  converted_filename, os.path.getsize(converted_path), target_format.upper(),
                  current_user['id']))
            
            new_doc_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'message': 'Document converti avec succès',
                'new_document_id': new_doc_id,
                'converted_path': converted_path
            }), 200
        else:
            # Remplacer le document existant
            return jsonify({
                'message': 'Conversion terminée',
                'converted_path': converted_path
            }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la conversion: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:doc_id>/analyze', methods=['POST'])
@token_required
def analyze_document(current_user, doc_id):
    """Analyser un document de manière complète (métadonnées + OCR + miniature + aperçu)"""
    try:
        data = request.get_json() or {}
        language = data.get('language', 'fra')
        include_ocr = data.get('include_ocr', True)
        
        # Vérifier l'existence du document et les permissions
        conn = db_connection()
        if not conn:
            return jsonify({'error': 'Erreur de connexion à la base de données'}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM document WHERE id = %s", (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        # Vérifier les permissions
        if document['proprietaire_id'] != current_user['id']:
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT permissions FROM partage 
                WHERE document_id = %s AND utilisateur_id = %s
            """, (doc_id, current_user['id']))
            partage = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not partage:
                return jsonify({'error': 'Accès non autorisé'}), 403
        
        # Construire le chemin du fichier
        file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), document['fichier'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Fichier non trouvé'}), 404
        
        analysis_result = {
            'document_id': doc_id,
            'analyzed_at': processing_service.processing_service.datetime.now().isoformat() if hasattr(processing_service, 'processing_service') else None,
            'metadata': None,
            'thumbnail_generated': False,
            'preview_generated': False,
            'ocr_result': None
        }
        
        # 1. Extraire les métadonnées
        try:
            metadata = processing_service.extract_metadata(file_path)
            if 'error' not in metadata:
                analysis_result['metadata'] = metadata
                processing_service.update_document_metadata(doc_id, metadata)
            else:
                logger.warning(f"Erreur métadonnées: {metadata['error']}")
        except Exception as e:
            logger.warning(f"Erreur extraction métadonnées: {str(e)}")
        
        # 2. Générer la miniature
        try:
            thumbnail_path = processing_service.generate_thumbnail(file_path)
            analysis_result['thumbnail_generated'] = bool(thumbnail_path)
        except Exception as e:
            logger.warning(f"Erreur génération miniature: {str(e)}")
        
        # 3. Générer l'aperçu
        try:
            preview_path = processing_service.generate_preview(file_path)
            analysis_result['preview_generated'] = bool(preview_path)
        except Exception as e:
            logger.warning(f"Erreur génération aperçu: {str(e)}")
        
        # 4. Effectuer l'OCR si demandé
        if include_ocr:
            try:
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                    ocr_result = processing_service.perform_ocr(file_path, language)
                    if 'error' not in ocr_result:
                        analysis_result['ocr_result'] = ocr_result
                        
                        # Mettre à jour les métadonnées avec l'OCR
                        if analysis_result['metadata']:
                            analysis_result['metadata']['ocr'] = ocr_result
                            processing_service.update_document_metadata(doc_id, analysis_result['metadata'])
                    else:
                        logger.warning(f"Erreur OCR: {ocr_result['error']}")
            except Exception as e:
                logger.warning(f"Erreur OCR: {str(e)}")
        
        # Enregistrer dans l'historique
        try:
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO historique (action, entite_type, entite_id, utilisateur_id, details, date_action)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, ('DOCUMENT_ANALYZED', 'document', doc_id, current_user['id'], 
                  json.dumps({
                      'include_ocr': include_ocr,
                      'metadata_extracted': bool(analysis_result['metadata']),
                      'thumbnail_generated': analysis_result['thumbnail_generated'],
                      'preview_generated': analysis_result['preview_generated'],
                      'ocr_performed': bool(analysis_result['ocr_result'])
                  })))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Erreur sauvegarde historique: {str(e)}")
        
        return jsonify({
            'message': 'Analyse du document terminée',
            'result': analysis_result
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse du document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/batch-analyze', methods=['POST'])
@token_required
def batch_analyze_documents(current_user):
    """Analyser plusieurs documents en lot"""
    try:
        data = request.get_json()
        if not data or 'document_ids' not in data:
            return jsonify({'error': 'Liste des IDs de documents requise'}), 400
        
        document_ids = data['document_ids']
        language = data.get('language', 'fra')
        include_ocr = data.get('include_ocr', True)
        
        if not isinstance(document_ids, list) or not document_ids:
            return jsonify({'error': 'Liste des IDs de documents invalide'}), 400
        
        results = []
        errors = []
        
        for doc_id in document_ids:
            try:
                # Vérifier l'existence du document et les permissions
                conn = db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT * FROM document WHERE id = %s", (doc_id,))
                document = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if not document:
                    errors.append({'document_id': doc_id, 'error': 'Document non trouvé'})
                    continue
                
                # Vérifier les permissions
                if document['proprietaire_id'] != current_user['id']:
                    conn = db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT permissions FROM partage 
                        WHERE document_id = %s AND utilisateur_id = %s
                    """, (doc_id, current_user['id']))
                    partage = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    if not partage:
                        errors.append({'document_id': doc_id, 'error': 'Accès non autorisé'})
                        continue
                
                # Construire le chemin du fichier
                file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), document['fichier'])
                
                if not os.path.exists(file_path):
                    errors.append({'document_id': doc_id, 'error': 'Fichier non trouvé'})
                    continue
                
                # Analyser le document
                doc_result = {
                    'document_id': doc_id,
                    'title': document['titre'],
                    'metadata_extracted': False,
                    'thumbnail_generated': False,
                    'preview_generated': False,
                    'ocr_performed': False
                }
                
                # Métadonnées
                try:
                    metadata = processing_service.extract_metadata(file_path)
                    if 'error' not in metadata:
                        processing_service.update_document_metadata(doc_id, metadata)
                        doc_result['metadata_extracted'] = True
                except:
                    pass
                
                # Miniature
                try:
                    thumbnail_path = processing_service.generate_thumbnail(file_path)
                    doc_result['thumbnail_generated'] = bool(thumbnail_path)
                except:
                    pass
                
                # Aperçu
                try:
                    preview_path = processing_service.generate_preview(file_path)
                    doc_result['preview_generated'] = bool(preview_path)
                except:
                    pass
                
                # OCR
                if include_ocr:
                    try:
                        file_ext = os.path.splitext(file_path)[1].lower()
                        if file_ext in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                            ocr_result = processing_service.perform_ocr(file_path, language)
                            doc_result['ocr_performed'] = 'error' not in ocr_result
                    except:
                        pass
                
                results.append(doc_result)
                
            except Exception as e:
                errors.append({'document_id': doc_id, 'error': str(e)})
        
        return jsonify({
            'message': f'Analyse en lot terminée. {len(results)} succès, {len(errors)} erreurs.',
            'results': results,
            'errors': errors
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse en lot: {str(e)}")
        return jsonify({'error': str(e)}), 500