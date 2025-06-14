from flask import Blueprint, request, jsonify
from AppFlask.db import db_connection
from .auth import token_required, log_user_action
from psycopg2.extras import RealDictCursor

bp = Blueprint('api_document_ocr', __name__)

def has_permission(doc_id, user_id, required_permission='lecture'):
    """Vérifier les permissions de l'utilisateur sur un document"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer le propriétaire
        cursor.execute("SELECT proprietaire_id FROM document WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()

        if doc is None:
            cursor.close()
            conn.close()
            return False

        # L'utilisateur est propriétaire → tous les droits
        if doc['proprietaire_id'] == int(user_id):
            cursor.close()
            conn.close()
            return True

        # Sinon, vérifier dans la table partage
        cursor.execute("""
            SELECT permissions FROM partage
            WHERE document_id = %s AND utilisateur_id = %s
        """, (doc_id, user_id))
        partage = cursor.fetchone()

        cursor.close()
        conn.close()

        if not partage:
            return False

        # Vérifier les droits
        if required_permission == 'lecture':
            return True
        elif required_permission == 'edition' and partage['permissions'] in ('édition', 'admin'):
            return True
        elif required_permission == 'admin' and partage['permissions'] == 'admin':
            return True

        return False

    except Exception as e:
        print(f"Erreur dans has_permission: {e}")
        return False

@bp.route('/documents/<int:doc_id>/ocr', methods=['POST'])
@token_required
def extract_ocr_text(current_user, doc_id):
    """Extraire le texte d'un document via OCR"""
    try:
        user_id = current_user['id']
        
        # Vérifier les permissions
        if not has_permission(doc_id, user_id, 'lecture'):
            return jsonify({'error': 'Accès non autorisé'}), 403

        # Récupérer les paramètres
        data = request.get_json() or {}
        language = data.get('language', 'fra')  # Français par défaut

        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Récupérer les informations du document
        cursor.execute("""
            SELECT titre, fichier, cloudinary_url, mime_type 
            FROM document 
            WHERE id = %s
        """, (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        conn.close()

        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404

        # Vérifier si le document supporte l'OCR
        if not document['mime_type'] or not document['mime_type'].startswith(('image/', 'application/pdf')):
            return jsonify({'error': 'Ce type de document ne supporte pas l\'OCR'}), 400

        # Simuler l'extraction OCR (fonctionnalité basique)
        # En réalité, il faudrait télécharger le fichier depuis Cloudinary et utiliser Tesseract
        
        # Texte simulé selon la langue
        language_texts = {
            'fra': f"Texte extrait du document '{document['titre']}' (simulation)\n\nCeci est un exemple de texte extrait par OCR depuis le document.\nLangue détectée: Français\nConfiance: 85.5%\n\nLe contenu de ce document a été analysé et le texte suivant a été identifié:\n- Titre: {document['titre']}\n- Type MIME: {document['mime_type']}\n- Traitement OCR effectué avec succès",
            'eng': f"Text extracted from document '{document['titre']}' (simulation)\n\nThis is an example of text extracted by OCR from the document.\nDetected language: English\nConfidence: 85.5%\n\nThe content of this document has been analyzed and the following text was identified:\n- Title: {document['titre']}\n- MIME type: {document['mime_type']}\n- OCR processing completed successfully",
            'spa': f"Texto extraído del documento '{document['titre']}' (simulación)\n\nEste es un ejemplo de texto extraído por OCR del documento.\nIdioma detectado: Español\nConfianza: 85.5%\n\nEl contenido de este documento ha sido analizado y se identificó el siguiente texto:\n- Título: {document['titre']}\n- Tipo MIME: {document['mime_type']}\n- Procesamiento OCR completado exitosamente"
        }
        
        extracted_text = language_texts.get(language, language_texts['fra'])
        confidence = 85.5
        
        # Enregistrer l'action
        log_user_action(
            user_id,
            'DOCUMENT_OCR',
            f"Extraction OCR du document '{document['titre']}' (ID: {doc_id}) en {language}",
            request
        )

        return jsonify({
            'success': True,
            'text': extracted_text,
            'confidence': confidence,
            'language': language,
            'document_title': document['titre'],
            'pages_processed': 1,
            'processing_time': 2.3
        }), 200

    except Exception as e:
        print(f"Erreur lors de l'extraction OCR: {e}")
        return jsonify({'error': 'Erreur lors de l\'extraction OCR'}), 500 