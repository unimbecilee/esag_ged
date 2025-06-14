import psycopg2
import os
import sys
import logging
from psycopg2.extras import RealDictCursor

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

def execute_sql_file(filename):
    """Exécuter un fichier SQL"""
    try:
        logger.info(f"Exécution du fichier SQL: {filename}")
        
        # Lire le contenu du fichier
        with open(filename, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Connexion à la base de données
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Exécuter le script SQL
        cursor.execute(sql_content)
        conn.commit()
        
        logger.info(f"Fichier SQL {filename} exécuté avec succès")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du fichier SQL {filename}: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def check_roles():
    """Vérifier et créer les rôles nécessaires s'ils n'existent pas"""
    try:
        logger.info("Vérification des rôles...")
        
        # Connexion à la base de données
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si la table role existe
        cursor.execute("""
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'role'
        """)
        
        if not cursor.fetchone():
            logger.warning("La table 'role' n'existe pas")
            return False
        
        # Vérifier si les rôles nécessaires existent
        roles_needed = ['chef_de_service', 'directeur']
        for role_name in roles_needed:
            cursor.execute("SELECT id FROM role WHERE nom = %s", (role_name,))
            role = cursor.fetchone()
            
            if not role:
                logger.info(f"Création du rôle '{role_name}'...")
                cursor.execute("""
                    INSERT INTO role (nom, description)
                    VALUES (%s, %s)
                """, (role_name, f"Rôle {role_name} pour le workflow"))
        
        conn.commit()
        logger.info("Rôles vérifiés et créés si nécessaire")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des rôles: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def setup_workflow_system():
    """Configurer le système de workflow"""
    try:
        # Exécuter les scripts SQL
        if not execute_sql_file('create_document_status_field.sql'):
            return False
            
        if not execute_sql_file('create_workflow_notification_table.sql'):
            return False
        
        # Vérifier et créer les rôles nécessaires
        if not check_roles():
            return False
        
        # Exécuter le script de création du workflow
        from create_validation_workflow import create_validation_workflow
        workflow_id = create_validation_workflow()
        
        if not workflow_id:
            logger.error("Échec de la création du workflow")
            return False
        
        logger.info(f"Système de workflow configuré avec succès (Workflow ID: {workflow_id})")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la configuration du système de workflow: {e}")
        return False

if __name__ == "__main__":
    if setup_workflow_system():
        print("Configuration du système de workflow terminée avec succès")
    else:
        print("Échec de la configuration du système de workflow")
        sys.exit(1) 