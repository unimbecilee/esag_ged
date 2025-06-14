import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import logging

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

def create_validation_workflow():
    """
    Crée un modèle de workflow de validation interne avec deux étapes:
    1. Validation par le Chef de service
    2. Validation par le Directeur
    """
    conn = None
    try:
        # Connexion à la base de données
        logger.info("Connexion à la base de données...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si le workflow existe déjà
        cursor.execute("""
            SELECT id FROM workflow 
            WHERE nom = 'Validation interne simple'
            LIMIT 1
        """)
        
        existing_workflow = cursor.fetchone()
        
        if existing_workflow:
            workflow_id = existing_workflow['id']
            logger.info(f"Le workflow 'Validation interne simple' existe déjà (ID: {workflow_id})")
            
            # Supprimer les approbateurs existants et les étapes
            logger.info("Suppression des approbateurs existants...")
            cursor.execute("""
                DELETE FROM workflow_approbateur 
                WHERE etape_id IN (SELECT id FROM etapeworkflow WHERE workflow_id = %s)
            """, (workflow_id,))
            
            logger.info("Suppression des étapes existantes...")
            cursor.execute("DELETE FROM etapeworkflow WHERE workflow_id = %s", (workflow_id,))
            
            conn.commit()
        else:
            # Créer le nouveau workflow
            logger.info("Création du workflow 'Validation interne simple'...")
            cursor.execute("""
                INSERT INTO workflow (nom, description, date_creation, statut)
                VALUES ('Validation interne simple', 
                        'Processus de validation en deux étapes: Chef de service puis Directeur', 
                        NOW(), 
                        'en_cours')
                RETURNING id
            """)
            
            workflow_id = cursor.fetchone()['id']
            conn.commit()
            logger.info(f"Workflow créé avec l'ID: {workflow_id}")
        
        # Créer la première étape: Validation par le Chef de service
        logger.info("Création de l'étape 1: Validation par le Chef de service...")
        cursor.execute("""
            INSERT INTO etapeworkflow (workflow_id, nom, description, ordre, type_approbation, delai_max)
            VALUES (%s, 
                    'Validation par le Chef de service', 
                    'Première validation par un chef de service', 
                    1, 
                    'SIMPLE', 
                    2)
            RETURNING id
        """, (workflow_id,))
        
        etape1_id = cursor.fetchone()['id']
        
        # Trouver l'ID du rôle chef_de_service
        cursor.execute("SELECT id FROM role WHERE nom = 'chef_de_service'")
        role_chef = cursor.fetchone()
        
        if role_chef:
            # Ajouter le rôle chef_de_service comme approbateur de l'étape 1
            logger.info("Ajout du rôle chef_de_service comme approbateur de l'étape 1...")
            cursor.execute("""
                INSERT INTO workflow_approbateur (etape_id, role_id)
                VALUES (%s, %s)
            """, (etape1_id, role_chef['id']))
        else:
            logger.warning("Le rôle 'chef_de_service' n'existe pas dans la base de données")
        
        # Créer la deuxième étape: Validation par le Directeur
        logger.info("Création de l'étape 2: Validation par le Directeur...")
        cursor.execute("""
            INSERT INTO etapeworkflow (workflow_id, nom, description, ordre, type_approbation, delai_max)
            VALUES (%s, 
                    'Validation par le Directeur', 
                    'Validation finale par un directeur', 
                    2, 
                    'SIMPLE', 
                    3)
            RETURNING id
        """, (workflow_id,))
        
        etape2_id = cursor.fetchone()['id']
        
        # Trouver l'ID du rôle directeur
        cursor.execute("SELECT id FROM role WHERE nom = 'directeur'")
        role_directeur = cursor.fetchone()
        
        if role_directeur:
            # Ajouter le rôle directeur comme approbateur de l'étape 2
            logger.info("Ajout du rôle directeur comme approbateur de l'étape 2...")
            cursor.execute("""
                INSERT INTO workflow_approbateur (etape_id, role_id)
                VALUES (%s, %s)
            """, (etape2_id, role_directeur['id']))
        else:
            logger.warning("Le rôle 'directeur' n'existe pas dans la base de données")
        
        conn.commit()
        logger.info("Workflow de validation interne créé avec succès!")
        
        return workflow_id
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Erreur lors de la création du workflow: {e}")
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    workflow_id = create_validation_workflow()
    if workflow_id:
        print(f"Workflow créé avec succès (ID: {workflow_id})")
    else:
        print("Échec de la création du workflow")
        sys.exit(1) 