#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
import psycopg2.extras

def check_users_and_docs():
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        print("=== VÉRIFICATION DES UTILISATEURS ===")
        cursor.execute("SELECT id, nom, prenom, email FROM utilisateur ORDER BY id")
        users = cursor.fetchall()
        
        for user in users:
            print(f"Utilisateur ID: {user['id']}, Nom: {user['nom']}, Prénom: {user['prenom']}, Email: {user['email']}")
        
        print("\n=== VÉRIFICATION DES DOCUMENTS ET PROPRIÉTAIRES ===")
        cursor.execute("""
            SELECT d.id, d.titre, d.proprietaire_id, d.dossier_id, 
                   u.nom, u.prenom 
            FROM document d 
            LEFT JOIN utilisateur u ON d.proprietaire_id = u.id
            ORDER BY d.id
        """)
        documents = cursor.fetchall()
        
        for doc in documents:
            print(f"Doc ID: {doc['id']}, Titre: {doc['titre']}, Propriétaire: {doc['proprietaire_id']} ({doc['nom']} {doc['prenom']}), Dossier: {doc['dossier_id']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_users_and_docs() 