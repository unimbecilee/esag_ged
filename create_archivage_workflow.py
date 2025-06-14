# -*- coding: utf-8 -*-
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import logging
from AppFlask.db import db_connection

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration de base de données (même que dans AppFlask/db.py)
DATABASE_CONFIG = {
    'host': 'postgresql-thefau.alwaysdata.net',
    'dbname': 'thefau_archive',
    'user': 'thefau',
    'password': 'Passecale2002@',
    'port': 5432
}

def create_archivage_workflow():
    """
    Crée un workflow d'archivage avec deux étapes :
    1. Validation par le chef de service
    2. Validation par l'archiviste
    """
    conn = db_connection()
    if not conn:
        print("Erreur: Impossible de se connecter à la base de données")
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si un workflow d'archivage existe déjà
        cursor.execute("""
            SELECT id FROM workflow WHERE nom LIKE %s
        """, ('%archivage%',))
        
        existing_workflow = cursor.fetchone()
        if existing_workflow:
            print(f"Un workflow d'archivage existe déjà avec l'ID {existing_workflow['id']}")
            return True
        
        # Vérifier la structure de la table workflow
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'workflow'
        """)
        
        columns = [row['column_name'] for row in cursor.fetchall()]
        print(f"Colonnes de la table workflow: {columns}")
        
        # Créer le workflow d'archivage en fonction des colonnes disponibles
        if 'est_actif' in columns:
            cursor.execute("""
                INSERT INTO workflow (nom, description, est_actif)
                VALUES ('Workflow d''Archivage', 'Processus de validation pour l''archivage de documents', TRUE)
                RETURNING id
            """)
        elif 'statut' in columns:
            cursor.execute("""
                INSERT INTO workflow (nom, description, statut)
                VALUES ('Workflow d''Archivage', 'Processus de validation pour l''archivage de documents', 'en_cours')
                RETURNING id
            """)
        else:
            cursor.execute("""
                INSERT INTO workflow (nom, description)
                VALUES ('Workflow d''Archivage', 'Processus de validation pour l''archivage de documents')
                RETURNING id
            """)
        
        workflow_id = cursor.fetchone()['id']
        print(f"Workflow d'archivage créé avec l'ID {workflow_id}")
        
        # Créer la première étape: Validation par le chef de service
        cursor.execute("""
            INSERT INTO etapeworkflow (workflow_id, nom, description, ordre, type_approbation, delai_max)
            VALUES (%s, 'Validation Chef de Service', 'Validation de la demande d''archivage par le chef de service', 1, 'UNANIMITE', 7)
            RETURNING id
        """, (workflow_id,))
        
        etape1_id = cursor.fetchone()['id']
        print(f"Étape 1 créée avec l'ID {etape1_id}")
        
        # Créer la deuxième étape: Validation par l'archiviste
        cursor.execute("""
            INSERT INTO etapeworkflow (workflow_id, nom, description, ordre, type_approbation, delai_max)
            VALUES (%s, 'Validation Archiviste', 'Validation finale et archivage par l''archiviste', 2, 'UNANIMITE', 7)
            RETURNING id
        """, (workflow_id,))
        
        etape2_id = cursor.fetchone()['id']
        print(f"Étape 2 créée avec l'ID {etape2_id}")
        
        # Ajouter les approbateurs pour chaque étape
        # Pour l'étape 1, on utilise le rôle "Chef de Service"
        cursor.execute("""
            SELECT id FROM role WHERE nom = 'Chef de Service'
        """)
        
        chef_role = cursor.fetchone()
        if chef_role:
            cursor.execute("""
                INSERT INTO workflow_approbateur (etape_id, role_id)
                VALUES (%s, %s)
            """, (etape1_id, chef_role['id']))
            print(f"Approbateur 'Chef de Service' ajouté pour l'étape 1")
        else:
            print("Attention: Rôle 'Chef de Service' non trouvé")
            # Créer le rôle si nécessaire
            cursor.execute("""
                INSERT INTO role (nom, description)
                VALUES ('Chef de Service', 'Chef de service pouvant approuver des documents')
                RETURNING id
            """)
            chef_role_id = cursor.fetchone()['id']
            cursor.execute("""
                INSERT INTO workflow_approbateur (etape_id, role_id)
                VALUES (%s, %s)
            """, (etape1_id, chef_role_id))
            print(f"Rôle 'Chef de Service' créé et ajouté comme approbateur pour l'étape 1")
        
        # Pour l'étape 2, on utilise le rôle "Archiviste"
        cursor.execute("""
            SELECT id FROM role WHERE nom = 'Archiviste'
        """)
        
        archiviste_role = cursor.fetchone()
        if archiviste_role:
            cursor.execute("""
                INSERT INTO workflow_approbateur (etape_id, role_id)
                VALUES (%s, %s)
            """, (etape2_id, archiviste_role['id']))
            print(f"Approbateur 'Archiviste' ajouté pour l'étape 2")
        else:
            print("Attention: Rôle 'Archiviste' non trouvé")
            # Créer le rôle si nécessaire
            cursor.execute("""
                INSERT INTO role (nom, description)
                VALUES ('Archiviste', 'Archiviste responsable de la validation finale des archivages')
                RETURNING id
            """)
            archiviste_role_id = cursor.fetchone()['id']
            cursor.execute("""
                INSERT INTO workflow_approbateur (etape_id, role_id)
                VALUES (%s, %s)
            """, (etape2_id, archiviste_role_id))
            print(f"Rôle 'Archiviste' créé et ajouté comme approbateur pour l'étape 2")
        
        # Valider les modifications
        conn.commit()
        print("Workflow d'archivage créé avec succès!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de la création du workflow d'archivage: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    success = create_archivage_workflow()
    sys.exit(0 if success else 1)
