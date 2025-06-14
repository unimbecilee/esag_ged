# -*- coding: utf-8 -*-
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

def apply_archive_columns():
    """
    Ajoute les colonnes nécessaires à la gestion de l'archivage dans la table document
    """
    conn = None
    try:
        # Connexion à la base de données
        logger.info("Connexion à la base de données...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier et ajouter la colonne est_archive
        logger.info("Vérification de la colonne est_archive...")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'document' AND column_name = 'est_archive'
        """)
        
        if not cursor.fetchone():
            logger.info("Ajout de la colonne est_archive...")
            cursor.execute("ALTER TABLE document ADD COLUMN est_archive BOOLEAN DEFAULT FALSE")
        else:
            logger.info("La colonne est_archive existe déjà")
        
        # Vérifier et ajouter la colonne date_archivage
        logger.info("Vérification de la colonne date_archivage...")
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'document' AND column_name = 'date_archivage'
        """)
        
        if not cursor.fetchone():
            logger.info("Ajout de la colonne date_archivage...")
            cursor.execute("ALTER TABLE document ADD COLUMN date_archivage TIMESTAMP")
        else:
            logger.info("La colonne date_archivage existe déjà")
        
        # Vérifier la contrainte sur la colonne statut
        logger.info("Vérification de la contrainte sur la colonne statut...")
        cursor.execute("""
            SELECT constraint_name
            FROM information_schema.constraint_column_usage
            WHERE table_name = 'document' AND column_name = 'statut'
        """)
        
        constraint = cursor.fetchone()
        
        if constraint:
            # Récupérer les valeurs actuelles de la contrainte
            constraint_name = constraint['constraint_name']
            logger.info(f"Modification de la contrainte {constraint_name}...")
            
            # Supprimer la contrainte existante
            cursor.execute(f"ALTER TABLE document DROP CONSTRAINT IF EXISTS {constraint_name}")
            
            # Ajouter une nouvelle contrainte avec la valeur ARCHIVE
            cursor.execute(f"""
                ALTER TABLE document ADD CONSTRAINT {constraint_name}
                CHECK (statut IN ('BROUILLON', 'EN_VALIDATION', 'APPROUVE', 'REJETE', 'ARCHIVE'))
            """)
        else:
            logger.info("Ajout d'une nouvelle contrainte sur la colonne statut...")
            cursor.execute("""
                ALTER TABLE document ADD CONSTRAINT document_statut_check
                CHECK (statut IN ('BROUILLON', 'EN_VALIDATION', 'APPROUVE', 'REJETE', 'ARCHIVE'))
            """)
        
        # Créer la table workflow_notification si elle n'existe pas
        logger.info("Vérification de la table workflow_notification...")
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = 'workflow_notification'
        """)
        
        if not cursor.fetchone():
            logger.info("Création de la table workflow_notification...")
            cursor.execute("""
                CREATE TABLE workflow_notification (
                    id SERIAL PRIMARY KEY,
                    instance_id INTEGER NOT NULL REFERENCES workflow_instance(id) ON DELETE CASCADE,
                    etape_id INTEGER NOT NULL REFERENCES etapeworkflow(id),
                    utilisateur_id INTEGER NOT NULL REFERENCES utilisateur(id),
                    message TEXT NOT NULL,
                    date_creation TIMESTAMP NOT NULL DEFAULT NOW(),
                    lu BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            
            # Ajouter un index pour accélérer les requêtes sur les notifications non lues
            logger.info("Ajout d'un index sur les notifications non lues...")
            cursor.execute("""
                CREATE INDEX idx_workflow_notification_utilisateur_lu
                ON workflow_notification(utilisateur_id, lu)
            """)
        else:
            logger.info("La table workflow_notification existe déjà")
        
        conn.commit()
        logger.info("Modifications de la base de données terminées avec succès!")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Erreur lors de la modification de la base de données: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    success = apply_archive_columns()
    if success:
        print("Colonnes d'archivage ajoutées avec succès!")
    else:
        print("Échec de l'ajout des colonnes d'archivage")
        sys.exit(1) 