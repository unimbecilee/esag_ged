#!/usr/bin/env python3
"""Script pour vérifier les instances de workflow"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def check_workflow_instances():
    """Vérifie les instances de workflow"""
    conn = db_connection()
    if not conn:
        print("❌ Impossible de se connecter à la base de données")
        return
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print('=== VERIFICATION DES INSTANCES DE WORKFLOW ===')
        
        # Vérifier les instances EN_COURS
        cursor.execute("""
            SELECT wi.id, wi.statut, wi.date_debut, d.titre as document_titre,
                   e.nom as etape_nom, u.nom as initiateur_nom
            FROM workflow_instance wi
            JOIN document d ON wi.document_id = d.id
            JOIN etapeworkflow e ON wi.etape_courante_id = e.id
            JOIN utilisateur u ON wi.initiateur_id = u.id
            WHERE wi.statut = 'EN_COURS'
            ORDER BY wi.date_debut DESC
        """)
        
        instances = cursor.fetchall()
        print(f"Nombre d'instances EN_COURS: {len(instances)}")
        
        for inst in instances:
            print(f"  ID: {inst['id']}, Doc: {inst['document_titre']}, Etape: {inst['etape_nom']}")
        
        # Vérifier les approbateurs configurés
        print('\n=== VERIFICATION DES APPROBATEURS ===')
        cursor.execute("""
            SELECT wa.etape_id, wa.role_id, wa.utilisateur_id, r.nom as role_nom
            FROM workflow_approbateur wa
            LEFT JOIN role r ON wa.role_id = r.id
            ORDER BY wa.etape_id
        """)
        
        approbateurs = cursor.fetchall()
        print(f"Nombre d'approbateurs configurés: {len(approbateurs)}")
        
        for app in approbateurs:
            print(f"  Etape: {app['etape_id']}, Role: {app['role_nom']}, User: {app['utilisateur_id']}")
        
        # Vérifier les utilisateurs avec le rôle chef_de_service
        print('\n=== VERIFICATION DES CHEFS DE SERVICE ===')
        cursor.execute("""
            SELECT id, nom, prenom, email, role
            FROM utilisateur
            WHERE role = 'chef_de_service'
        """)
        
        chefs = cursor.fetchall()
        print(f"Nombre de chefs de service: {len(chefs)}")
        
        for chef in chefs:
            print(f"  ID: {chef['id']}, Nom: {chef['nom']} {chef['prenom']}, Email: {chef['email']}")
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    check_workflow_instances() 