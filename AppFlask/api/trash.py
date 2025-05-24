from flask import jsonify, request
from AppFlask.api import api_bp
from AppFlask.db import db_connection
from .auth import token_required

@api_bp.route('/trash', methods=['GET'])
@token_required
def get_trash(current_user):
    conn = db_connection()
    if conn is None:
        return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        documents = db.session.query(
                Document,
                User.nom.label('proprietaire_nom'),
                User.prenom.label('proprietaire_prenom')
            ).outerjoin(User, Document.proprietaire_id == User.id
            ).filter(
                Document.proprietaire_id == current_user.id,
                Document.corbeille == True
            ).order_by(Document.date_creation.desc()).all()
        documents = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(documents)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api_bp.route('/trash/<int:doc_id>/restore', methods=['POST'])
@token_required
def restore_document(current_user, doc_id):
    conn = db_connection()
    if conn is None:
        return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor()
        db.session.query(Document).filter(
                Document.id == doc_id,
                Document.proprietaire_id == current_user.id
            ).update({'corbeille': False})
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Document restauré avec succès'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@api_bp.route('/trash/<int:doc_id>', methods=['DELETE'])
@token_required
def delete_permanently(current_user, doc_id):
    conn = db_connection()
    if conn is None:
        return jsonify({'message': 'Erreur de connexion à la base de données'}), 500
    
    try:
        cursor = conn.cursor()
        db.session.query(Document).filter(
                Document.id == doc_id,
                Document.proprietaire_id == current_user.id,
                Document.corbeille == True
            ).delete()
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Document supprimé définitivement'})
    except Exception as e:
        return jsonify({'message': str(e)}), 500