from flask import Blueprint, request, redirect, url_for, flash, session, render_template, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import pytesseract
from PIL import Image
from AppFlask.db import db_connection

# Configuration Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Blueprint
scan_bp = Blueprint('scan', __name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route GET pour afficher l’interface de numérisation
@scan_bp.route('/', methods=['GET'])
def scan_document():
    return render_template('scan_document.html')

# ✅ Route POST pour envoyer une image à numériser
@scan_bp.route('/', methods=['POST'])
def upload_scan():
    if 'scan' not in request.files:
        flash('Aucun fichier reçu', 'danger')
        return redirect(url_for('scan.scan_document'))

    file = request.files['scan']
    user_id = session.get('user_id')

    if file.filename == '' or not allowed_file(file.filename):
        flash('Fichier non valide ou type non autorisé', 'danger')
        return redirect(url_for('scan.scan_document'))

    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)

        conn = db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO Numerisation (utilisateur_id, fichier_scanne, date_scan)
            VALUES (%s, %s, NOW())
        """
        cursor.execute(query, (user_id, unique_filename))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Document numérisé avec succès', 'success')
        return redirect(url_for('scan.scanned_files'))
    except Exception as e:
        flash(f'Erreur lors de la numérisation : {str(e)}', 'danger')
        return redirect(url_for('scan.scan_document'))

# ✅ Liste des fichiers numérisés
@scan_bp.route('/scanned-files')
def scanned_files():
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Numerisation")
        scanned_files = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('scanned_files.html', scanned_files=scanned_files)
    except Exception as e:
        flash(f'Erreur lors de la récupération des fichiers numérisés : {str(e)}', 'danger')
        return redirect(url_for('dashboard.home'))

# Extraire le texte d’un scan
@scan_bp.route('/extract-text/<int:scan_id>', methods=['POST'])
def extract_text(scan_id):
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT fichier_scanne FROM Numerisation WHERE id = %s", (scan_id,))
        scan = cursor.fetchone()

        if not scan:
            flash('Fichier numérisé introuvable', 'danger')
            return redirect(url_for('scan.scanned_files'))

        filepath = os.path.join(UPLOAD_FOLDER, scan['fichier_scanne'])

        if not os.path.exists(filepath):
            flash('Fichier non trouvé sur le serveur', 'danger')
            return redirect(url_for('scan.scanned_files'))

        image = Image.open(filepath)
        extracted_text = pytesseract.image_to_string(image, lang='fra')

        update_query = "UPDATE Numerisation SET texte_reconnu = %s WHERE id = %s"
        cursor.execute(update_query, (extracted_text, scan_id))
        conn.commit()

        cursor.close()
        conn.close()

        flash('Texte extrait avec succès', 'success')
        return redirect(url_for('scan.view_scanned_file', scan_id=scan_id))
    except Exception as e:
        flash(f'Erreur lors de l\'extraction : {str(e)}', 'danger')
        return redirect(url_for('scan.scanned_files'))

# Affichage d’un fichier numérisé
@scan_bp.route('/scanned/<int:scan_id>')
def view_scanned_file(scan_id):
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Numerisation WHERE id = %s", (scan_id,))
        scan = cursor.fetchone()
        cursor.close()
        conn.close()

        if not scan:
            flash("Fichier non trouvé", "danger")
            return redirect(url_for('scan.scanned_files'))

        return render_template('scanned_file_detail.html', scan=scan)
    except Exception as e:
        flash(f'Erreur lors de l\'affichage : {str(e)}', 'danger')
        return redirect(url_for('scan.scanned_files'))
