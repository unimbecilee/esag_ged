#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
import psycopg2.extras

def check_database():
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        print("=== VÉRIFICATION DES DOCUMENTS ===")
        cursor.execute("SELECT id, titre, dossier_id FROM document ORDER BY id")
        documents = cursor.fetchall()
        
        for doc in documents:
            print(f"Document ID: {doc['id']}, Titre: {doc['titre']}, Dossier ID: {doc['dossier_id']}")
        
        print("\n=== VÉRIFICATION DES DOSSIERS ===")
        cursor.execute("SELECT id, titre FROM dossier ORDER BY id")
        folders = cursor.fetchall()
        
        for folder in folders:
            print(f"Dossier ID: {folder['id']}, Titre: {folder['titre']}")
        
        print("\n=== VÉRIFICATION DES ASSOCIATIONS ===")
        cursor.execute("""
            SELECT d.titre as dossier_titre, COUNT(doc.id) as nb_documents
            FROM dossier d
            LEFT JOIN document doc ON d.id = doc.dossier_id
            GROUP BY d.id, d.titre
            ORDER BY d.id
        """)
        associations = cursor.fetchall()
        
        for assoc in associations:
            print(f"Dossier '{assoc['dossier_titre']}': {assoc['nb_documents']} document(s)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_database() 