#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
import psycopg2.extras

def test_api_final():
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        print("=== TEST FINAL : API DOCUMENTS PAR DOSSIER ===")
        user_id = 6  # Admin ESAG
        
        # Test 1: Dossier "doc" (ID=1) - doit contenir 2 documents
        print(f"\n1. Dossier 'doc' (ID=1) pour utilisateur {user_id}:")
        query = """
            SELECT d.id, d.titre, d.dossier_id
            FROM document d 
            WHERE d.proprietaire_id = %s AND d.dossier_id = %s
            ORDER BY d.date_ajout DESC
        """
        cursor.execute(query, (user_id, 1))
        docs = cursor.fetchall()
        print(f"   → {len(docs)} document(s) trouvé(s)")
        for doc in docs:
            print(f"     - ID: {doc['id']}, Titre: {doc['titre']}")
        
        # Test 2: Dossier "doc1" (ID=3) - doit contenir 1 document
        print(f"\n2. Dossier 'doc1' (ID=3) pour utilisateur {user_id}:")
        cursor.execute(query, (user_id, 3))
        docs = cursor.fetchall()
        print(f"   → {len(docs)} document(s) trouvé(s)")
        for doc in docs:
            print(f"     - ID: {doc['id']}, Titre: {doc['titre']}")
        
        # Test 3: Dossier "doc2" (ID=2) - doit être vide
        print(f"\n3. Dossier 'doc2' (ID=2) pour utilisateur {user_id}:")
        cursor.execute(query, (user_id, 2))
        docs = cursor.fetchall()
        print(f"   → {len(docs)} document(s) trouvé(s)")
        for doc in docs:
            print(f"     - ID: {doc['id']}, Titre: {doc['titre']}")
        
        # Test 4: Documents à la racine (dossier_id IS NULL)
        print(f"\n4. Documents à la racine pour utilisateur {user_id}:")
        query_root = """
            SELECT d.id, d.titre, d.dossier_id
            FROM document d 
            WHERE d.proprietaire_id = %s AND d.dossier_id IS NULL
            ORDER BY d.date_ajout DESC
        """
        cursor.execute(query_root, (user_id,))
        docs = cursor.fetchall()
        print(f"   → {len(docs)} document(s) trouvé(s)")
        for doc in docs:
            print(f"     - ID: {doc['id']}, Titre: {doc['titre']}")
        
        print(f"\n=== RÉSUMÉ ATTENDU ===")
        print(f"- Dossier 'doc' : 2 documents")
        print(f"- Dossier 'doc1' : 1 document")
        print(f"- Dossier 'doc2' : 0 document")
        print(f"- Racine : 0 document (tous assignés à des dossiers)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    test_api_final() 