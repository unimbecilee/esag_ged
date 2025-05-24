from flask import Blueprint, request, render_template, redirect, flash
from AppFlask.db import db_connection

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()

    if not query:
        flash('Veuillez entrer un terme de recherche')
        return redirect('/documents')

    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # Recherche dans les documents
        doc_query = """
            SELECT 'document' AS type, id, titre, description, date_ajout
            FROM Document
            WHERE titre LIKE %s OR description LIKE %s
        """
        search_term = f"%{query}%"
        cursor.execute(doc_query, (search_term, search_term))
        documents = cursor.fetchall()

        # Recherche dans les textes extraits via OCR
        ocr_query = """
            SELECT 'ocr' AS type, n.id, d.titre, n.texte_reconnu, n.date_scan
            FROM Numerisation n
            JOIN Document d ON n.document_id = d.id
            WHERE n.texte_reconnu LIKE %s
        """
        cursor.execute(ocr_query, (search_term,))
        ocr_results = cursor.fetchall()

        results = documents + ocr_results
        cursor.close()
        conn.close()

        return render_template('search_results.html', results=results, query=query)
    except Exception as e:
        flash(f'Erreur lors de la recherche : {str(e)}')
        return redirect('/documents')
