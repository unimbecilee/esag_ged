from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
import os
import uuid
import json
from datetime import datetime
from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
from .auth import token_required
import io
import base64
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('api_scan', __name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'scans')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf', 'tiff', 'bmp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Créer le dossier de uploads s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def enhance_image(image, settings):
    """Améliorer la qualité de l'image selon les paramètres"""
    try:
        # Conversion en RGB si nécessaire
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Ajustement automatique des niveaux
        if settings.get('autoEnhance', True):
            image = ImageOps.autocontrast(image)
            
            # Amélioration de la netteté
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)
            
            # Amélioration du contraste
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.1)
        
        # Gestion des modes de couleur
        mode = settings.get('mode', 'COULEUR')
        if mode == 'NIVEAUX_GRIS':
            image = image.convert('L')
        elif mode == 'NOIR_BLANC':
            image = image.convert('L')
            # Seuillage pour noir et blanc
            threshold = 128
            image = image.point(lambda p: p > threshold and 255)
        
        return image
    except Exception as e:
        logger.error(f"Erreur lors de l'amélioration de l'image: {str(e)}")
        return image

def perform_ocr(image_path, language='fra'):
    """Effectuer la reconnaissance optique de caractères"""
    try:
        # Configuration Tesseract
        custom_config = r'--oem 3 --psm 6'
        
        # Extraction du texte
        text = pytesseract.image_to_string(
            Image.open(image_path), 
            lang=language, 
            config=custom_config
        )
        
        return text.strip()
    except Exception as e:
        logger.error(f"Erreur OCR: {str(e)}")
        return ""

@bp.route('/scan/detect-device', methods=['GET'])
@token_required
def detect_device(current_user):
    """Détecter le type d'appareil et les capacités"""
    user_agent = request.headers.get('User-Agent', '').lower()
    
    is_mobile = any(device in user_agent for device in [
        'iphone', 'android', 'ipad', 'ipod', 'mobile', 'phone'
    ])
    
    has_camera = is_mobile  # Simplification - les mobiles ont généralement une caméra
    has_scanner = not is_mobile  # Les PC peuvent avoir des scanners
    
    return jsonify({
        'device_type': 'mobile' if is_mobile else 'desktop',
        'capabilities': {
            'camera': has_camera,
            'scanner': has_scanner,
            'recommended_method': 'camera' if is_mobile else 'scanner'
        },
        'instructions': {
            'camera': "Utilisez l'appareil photo pour capturer le document",
            'scanner': "Connectez votre scanner et numérisez le document",
            'mobile_redirect': "Pour utiliser la caméra, connectez-vous depuis un mobile"
        }
    })

@bp.route('/scan/camera', methods=['POST'])
@token_required
def scan_with_camera(current_user):
    """Numériser avec la caméra (mobile)"""
    try:
        # Vérifier si c'est un mobile
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(device in user_agent for device in [
            'iphone', 'android', 'ipad', 'ipod', 'mobile', 'phone'
        ])
        
        if not is_mobile:
            return jsonify({
                'error': 'La capture par caméra nécessite un appareil mobile',
                'redirect_message': 'Veuillez vous connecter depuis votre téléphone pour utiliser cette fonctionnalité'
            }), 400
        
        # Récupérer les données
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'Image requise'}), 400
        
        # Décoder l'image base64
        try:
            image_data = data['image'].split(',')[1]  # Supprimer le préfixe data:image/...
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return jsonify({'error': f'Image invalide: {str(e)}'}), 400
        
        # Paramètres de traitement
        settings = data.get('settings', {})
        title = data.get('title', f'Scan mobile {datetime.now().strftime("%Y%m%d_%H%M%S")}')
        description = data.get('description', '')
        
        # Améliorer l'image
        enhanced_image = enhance_image(image, settings)
        
        # Générer un nom de fichier unique
        file_extension = 'jpg'
        filename = f"camera_scan_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Sauvegarder l'image
        quality = settings.get('quality', 85)
        enhanced_image.save(file_path, 'JPEG', quality=quality, optimize=True)
        
        # OCR si demandé
        ocr_text = ""
        if settings.get('ocrEnabled', True):
            ocr_text = perform_ocr(file_path)
        
        # Sauvegarder en base de données
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            INSERT INTO numerisation (utilisateur_id, fichier_scanne, date_scan, 
                                    titre, description, texte_reconnu, methode_scan, parametres)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            current_user['id'], filename, title, description, 
            ocr_text, 'camera', json.dumps(settings)
        ))
        
        result = cursor.fetchone()
        scan_id = result['id'] if result else None
        conn.commit()
        cursor.close()
        conn.close()
        
        # Calculer la taille du fichier
        file_size = os.path.getsize(file_path)
        file_size_mb = round(file_size / (1024 * 1024), 2)
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'filename': filename,
            'size': f"{file_size_mb} MB",
            'pages': 1,
            'ocr_text': ocr_text if settings.get('ocrEnabled') else None,
            'preview_available': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur numérisation caméra: {str(e)}")
        return jsonify({'error': f'Erreur lors de la numérisation: {str(e)}'}), 500

@bp.route('/scan/scanner', methods=['POST'])
@token_required
def scan_with_scanner(current_user):
    """Numériser avec un scanner physique"""
    try:
        # Vérifier le fichier uploadé
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Fichier invalide ou type non supporté'}), 400
        
        # Vérifier la taille
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'Fichier trop volumineux (max 50MB)'}), 400
        
        # Récupérer les paramètres
        settings_json = request.form.get('settings', '{}')
        try:
            settings = json.loads(settings_json)
        except:
            settings = {}
        
        title = request.form.get('title', f'Scan {datetime.now().strftime("%Y%m%d_%H%M%S")}')
        description = request.form.get('description', '')
        
        # Générer un nom de fichier sécurisé
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        filename = f"scanner_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Sauvegarder le fichier
        file.save(file_path)
        
        # Traitement de l'image si c'est une image
        if file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            try:
                image = Image.open(file_path)
                enhanced_image = enhance_image(image, settings)
                
                # Sauvegarder l'image améliorée
                quality = settings.get('quality', 85)
                if file_extension in ['jpg', 'jpeg']:
                    enhanced_image.save(file_path, 'JPEG', quality=quality, optimize=True)
                else:
                    enhanced_image.save(file_path)
            except Exception as e:
                logger.warning(f"Impossible de traiter l'image: {str(e)}")
        
        # OCR si demandé
        ocr_text = ""
        if settings.get('ocrEnabled', True) and file_extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
            ocr_text = perform_ocr(file_path)
        
        # Sauvegarder en base de données
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            INSERT INTO numerisation (utilisateur_id, fichier_scanne, date_scan, 
                                    titre, description, texte_reconnu, methode_scan, parametres)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            current_user['id'], filename, title, description, 
            ocr_text, 'scanner', json.dumps(settings)
        ))
        
        result = cursor.fetchone()
        scan_id = result['id'] if result else None
        conn.commit()
        cursor.close()
        conn.close()
        
        # Informations du fichier final
        final_file_size = os.path.getsize(file_path)
        file_size_mb = round(final_file_size / (1024 * 1024), 2)
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'filename': filename,
            'size': f"{file_size_mb} MB",
            'pages': 1,  # TODO: Détecter le nombre de pages pour les PDFs
            'ocr_text': ocr_text if settings.get('ocrEnabled') else None,
            'preview_available': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur numérisation scanner: {str(e)}")
        return jsonify({'error': f'Erreur lors de la numérisation: {str(e)}'}), 500

@bp.route('/scan/list', methods=['GET'])
@token_required
def list_scanned_documents(current_user):
    """Récupérer la liste des documents numérisés"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Compter le total
        cursor.execute("""
            SELECT COUNT(*) as count FROM numerisation WHERE utilisateur_id = %s
        """, (current_user['id'],))
        result = cursor.fetchone()
        total = result['count'] if result else 0
        
        # Récupérer les documents
        cursor.execute("""
            SELECT id, fichier_scanne, date_scan, titre, description, 
                   texte_reconnu, methode_scan, parametres
            FROM numerisation 
            WHERE utilisateur_id = %s 
            ORDER BY date_scan DESC 
            LIMIT %s OFFSET %s
        """, (current_user['id'], per_page, offset))
        
        scans = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Formater les résultats
        scanned_docs = []
        for scan in scans:
            # Calculer la taille du fichier
            file_path = os.path.join(UPLOAD_FOLDER, scan[1])
            file_size = 0
            if os.path.exists(file_path):
                file_size = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            
            scanned_docs.append({
                'id': scan[0],
                'filename': scan[1],
                'date_scan': scan[2].isoformat() if scan[2] else None,
                'title': scan[3],
                'description': scan[4],
                'has_ocr': bool(scan[5]),
                'method': scan[6],
                'size': f"{file_size} MB",
                'pages': 1  # TODO: Implémenter la détection du nombre de pages
            })
        
        return jsonify({
            'scanned_documents': scanned_docs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération des scans: {str(e)}")
        return jsonify({'error': f'Erreur lors de la récupération: {str(e)}'}), 500

@bp.route('/scan/<int:scan_id>/save-to-ged', methods=['POST'])
@token_required
def save_scan_to_ged(current_user, scan_id):
    """Sauvegarder un document numérisé dans le GED"""
    try:
        data = request.get_json() or {}
        
        # Récupérer le document numérisé
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT fichier_scanne, titre, description, texte_reconnu
            FROM numerisation 
            WHERE id = %s AND utilisateur_id = %s
        """, (scan_id, current_user['id']))
        
        scan = cursor.fetchone()
        if not scan:
            return jsonify({'error': 'Document numérisé non trouvé'}), 404
        
        # Déplacer le fichier vers le dossier principal des documents
        scan_file_path = os.path.join(UPLOAD_FOLDER, scan[0])
        if not os.path.exists(scan_file_path):
            return jsonify({'error': 'Fichier numérisé non trouvé'}), 404
        
        # Générer un nouveau nom pour le GED
        file_extension = scan[0].rsplit('.', 1)[1]
        new_filename = f"ged_{uuid.uuid4().hex}.{file_extension}"
        ged_file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), new_filename)
        
        # Copier le fichier
        import shutil
        shutil.copy2(scan_file_path, ged_file_path)
        
        # Calculer la taille
        file_size = os.path.getsize(ged_file_path)
        
        # Insérer dans la table document
        title = data.get('title', scan[1])
        description = data.get('description', scan[2])
        
        cursor.execute("""
            INSERT INTO document (nom, fichier, taille, type_mime, date_creation, 
                                proprietaire_id, description, contenu_texte)
            VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s)
            RETURNING id
        """, (
            title, new_filename, file_size, 
            f"image/{file_extension}" if file_extension != 'pdf' else 'application/pdf',
            current_user['id'], description, scan[3]
        ))
        
        result = cursor.fetchone()
        document_id = result['id'] if result else None
        
        # Marquer le scan comme intégré
        cursor.execute("""
            UPDATE numerisation 
            SET document_id = %s, integre_ged = TRUE 
            WHERE id = %s
        """, (document_id, scan_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'document_id': document_id,
            'message': 'Document sauvegardé dans le GED avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde GED: {str(e)}")
        return jsonify({'error': f'Erreur lors de la sauvegarde: {str(e)}'}), 500

@bp.route('/scan/<int:scan_id>', methods=['DELETE'])
@token_required
def delete_scan(current_user, scan_id):
    """Supprimer un document numérisé"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer les infos du scan
        cursor.execute("""
            SELECT fichier_scanne FROM numerisation 
            WHERE id = %s AND utilisateur_id = %s
        """, (scan_id, current_user['id']))
        
        scan = cursor.fetchone()
        if not scan:
            return jsonify({'error': 'Document numérisé non trouvé'}), 404
        
        # Supprimer le fichier
        file_path = os.path.join(UPLOAD_FOLDER, scan[0])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Supprimer de la base
        cursor.execute("DELETE FROM numerisation WHERE id = %s", (scan_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Document supprimé avec succès'})
        
    except Exception as e:
        logger.error(f"Erreur suppression scan: {str(e)}")
        return jsonify({'error': f'Erreur lors de la suppression: {str(e)}'}), 500
 