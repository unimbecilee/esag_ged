#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
import psycopg2.extras

def move_documents_to_folder():
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        print("=== DÉPLACEMENT DE DOCUMENTS VERS LE DOSSIER 'doc' ===")
        
        # Déplacer les documents 1 et 2 vers le dossier 'doc' (id=1)
        cursor.execute("""
            UPDATE document 
            SET dossier_id = 1 
            WHERE id IN (1, 2)
        """)
        
        # Déplacer le document 3 vers le dossier 'doc1' (id=3)
        cursor.execute("""
            UPDATE document 
            SET dossier_id = 3 
            WHERE id = 3
        """)
        
        conn.commit()
        
        print("✅ Documents déplacés avec succès !")
        
        # Vérifier le résultat
        print("\n=== VÉRIFICATION APRÈS DÉPLACEMENT ===")
        cursor.execute("""
            SELECT d.titre as dossier_titre, doc.titre as document_titre
            FROM dossier d
            LEFT JOIN document doc ON d.id = doc.dossier_id
            ORDER BY d.id, doc.id
        """)
        
        results = cursor.fetchall()
        current_folder = None
        
        for result in results:
            if current_folder != result['dossier_titre']:
                current_folder = result['dossier_titre']
                print(f"\nDossier '{current_folder}':")
            
            if result['document_titre']:
                print(f"  - {result['document_titre']}")
            else:
                print("  (vide)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    move_documents_to_folder() 