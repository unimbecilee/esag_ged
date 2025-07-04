#!/usr/bin/env python3
"""Script pour vérifier la configuration des workflows et des rôles"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def check_workflow_config():
    """Vérifie la configuration des workflows"""
    conn = db_connection()
    if not conn:
        print("❌ Impossible de se connecter à la base de données")
        return
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print('=== VERIFICATION DES ROLES ===')
        cursor.execute('SELECT * FROM role ORDER BY id')
        roles = cursor.fetchall()
        for role in roles:
            print(f'ID: {role["id"]}, Nom: {role["nom"]}')
        
        print('\n=== VERIFICATION DES UTILISATEURS ===')
        cursor.execute('SELECT id, nom, prenom, email, role FROM utilisateur ORDER BY id')
        users = cursor.fetchall()
        for user in users:
            print(f'ID: {user["id"]}, Nom: {user["nom"]} {user["prenom"]}, Email: {user["email"]}, Role: {user["role"]}')
        
        print('\n=== VERIFICATION DES WORKFLOWS ===')
        cursor.execute('SELECT * FROM workflow ORDER BY id')
        workflows = cursor.fetchall()
        for workflow in workflows:
            print(f'ID: {workflow["id"]}, Nom: {workflow["nom"]}, Statut: {workflow["statut"]}')
        
        print('\n=== VERIFICATION DES ETAPES DE WORKFLOW ===')
        cursor.execute('SELECT * FROM etapeworkflow ORDER BY workflow_id, ordre')
        etapes = cursor.fetchall()
        for etape in etapes:
            print(f'ID: {etape["id"]}, Workflow: {etape["workflow_id"]}, Nom: {etape["nom"]}, Ordre: {etape["ordre"]}')
        
        print('\n=== VERIFICATION DES APPROBATEURS ===')
        cursor.execute('SELECT wa.*, r.nom as role_nom FROM workflow_approbateur wa LEFT JOIN role r ON wa.role_id = r.id ORDER BY etape_id')
        approbateurs = cursor.fetchall()
        for app in approbateurs:
            print(f'Etape: {app["etape_id"]}, Role: {app["role_nom"]}, User: {app["utilisateur_id"]}')
        
        print('\n=== VERIFICATION DES INSTANCES DE WORKFLOW ===')
        cursor.execute('SELECT wi.*, d.titre as doc_titre FROM workflow_instance wi JOIN document d ON wi.document_id = d.id ORDER BY wi.id')
        instances = cursor.fetchall()
        for inst in instances:
            print(f'ID: {inst["id"]}, Doc: {inst["doc_titre"]}, Statut: {inst["statut"]}, Etape courante: {inst["etape_courante_id"]}')
        
        print('\n=== TEST POUR UN UTILISATEUR SPECIFIQUE ===')
        # Tester pour l'utilisateur connecté (supposons ID 1)
        user_id = 1
        cursor.execute('SELECT role FROM utilisateur WHERE id = %s', (user_id,))
        user_result = cursor.fetchone()
        if user_result:
            user_role = user_result['role']
            print(f'Utilisateur ID {user_id} a le rôle: {user_role}')
            
            # Tester la requête de get_pending_approvals
            cursor.execute("""
                SELECT DISTINCT 
                    wi.id as instance_id, 
                    wi.document_id, 
                    wi.date_debut,
                    wi.commentaire, 
                    d.titre as document_titre, 
                    d.fichier,
                    e.id as etape_id, 
                    e.nom as etape_nom, 
                    e.description as etape_description,
                    u.nom as initiateur_nom, 
                    u.prenom as initiateur_prenom,
                    COALESCE(d.priorite, 1) as priorite,
                    wi.date_fin as date_echeance
                FROM workflow_instance wi
                JOIN document d ON wi.document_id = d.id
                JOIN etapeworkflow e ON wi.etape_courante_id = e.id
                JOIN workflow_approbateur wa ON e.id = wa.etape_id
                LEFT JOIN role r ON wa.role_id = r.id
                JOIN utilisateur u ON wi.initiateur_id = u.id
                WHERE wi.statut = 'EN_COURS'
                AND (
                    LOWER(r.nom) = LOWER(%s) 
                    OR wa.utilisateur_id = %s
                    OR (LOWER(r.nom) = 'admin' AND LOWER(%s) = 'admin')
                )
                ORDER BY 
                    COALESCE(d.priorite, 1) DESC,
                    wi.date_debut ASC
            """, (user_role, user_id, user_role))
            
            pending = cursor.fetchall()
            print(f'Validations en attente pour cet utilisateur: {len(pending)}')
            for p in pending:
                print(f'  - Document: {p["document_titre"]}, Etape: {p["etape_nom"]}')
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    check_workflow_config() 