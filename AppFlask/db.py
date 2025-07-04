import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, unquote

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_database_url(url):
    parsed = urlparse(url)
    # Décodage du mot de passe pour les caractères spéciaux
    password = unquote(parsed.password) if parsed.password else None
    logger.info(f"Host: {parsed.hostname}")
    logger.info(f"Database: {parsed.path[1:]}")
    logger.info(f"User: {parsed.username}")
    # Ne pas logger le mot de passe en production
    logger.debug(f"Password: {'*' * (len(password) if password else 0)}")
    
    return {
        'dbname': parsed.path[1:],
        'user': parsed.username,
        'password': password,
        'host': parsed.hostname,
        'port': parsed.port
    }

def db_connection():
    try:
        # Priorité aux variables d'environnement pour le déploiement
        db_url = os.environ.get('DATABASE_URL') or "postgresql://thefau:Passecale2002@postgresql-thefau.alwaysdata.net:5432/thefau_archive"
        if not db_url:
            logger.error("DATABASE_URL non définie dans les variables d'environnement")
            return None

        db_config = parse_database_url(db_url)
        logger.info("Tentative de connexion avec les paramètres :")
        logger.info(f"Database: {db_config['dbname']}")
        logger.info(f"User: {db_config['user']}")
        
        # Tentative de connexion avec retry
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                connection = psycopg2.connect(
                    **db_config,
                    cursor_factory=RealDictCursor,
                    connect_timeout=10  # Timeout de connexion en secondes
                )
                
                if connection:
                    logger.info("Connexion réussie à PostgreSQL")
                    return connection
            except psycopg2.Error as e:
                last_error = e
                logger.warning(f"Tentative {retry_count + 1}/{max_retries} échouée: {e}")
                retry_count += 1
        
        # Si toutes les tentatives ont échoué
        logger.error(f"Échec de la connexion après {max_retries} tentatives. Dernière erreur: {last_error}")
        return None
            
    except psycopg2.Error as e:
        logger.error(f"Erreur PostgreSQL lors de la connexion : {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la connexion : {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
