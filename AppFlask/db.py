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
    logger.debug(f"Password: {password}")
    
    return {
        'dbname': parsed.path[1:],
        'user': parsed.username,
        'password': password,
        'host': parsed.hostname,
        'port': parsed.port
    }

def db_connection():
    try:
        # URL de connexion directe pour le débogage
        db_url = "postgresql://thefau:Passecale2002@@postgresql-thefau.alwaysdata.net:5432/thefau_archive"
        if not db_url:
            logger.error("DATABASE_URL non définie dans les variables d'environnement")
            return None

        db_config = parse_database_url(db_url)
        logger.info("Tentative de connexion avec les paramètres :")
        logger.info(f"Host: {db_config['host']}")
        logger.info(f"Database: {db_config['dbname']}")
        logger.info(f"User: {db_config['user']}")
        
        connection = psycopg2.connect(
            **db_config,
            cursor_factory=RealDictCursor
        )
        
        if connection:
            logger.info("Connexion réussie à PostgreSQL")
            return connection
        else:
            logger.error("La connexion n'a pas pu être établie")
            return None
            
    except psycopg2.Error as e:
        logger.error(f"Erreur PostgreSQL lors de la connexion : {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la connexion : {e}")
        return None
