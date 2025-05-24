import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Configuration de Cloudinary
config = cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

logger.info(f"Configuration Cloudinary : cloud_name={config.cloud_name}")

def upload_file(file_content, public_id=None, resource_type="auto"):
    """
    Upload un fichier vers Cloudinary
    
    Args:
        file_content: Le contenu du fichier
        public_id: ID public pour le fichier (optionnel)
        resource_type: Type de ressource ("auto", "image", "video", "raw")
    
    Returns:
        dict: Les informations de l'upload, incluant l'URL
    """
    try:
        logger.info(f"Début de l'upload vers Cloudinary - public_id: {public_id}, resource_type: {resource_type}")
        
        # Vérifier la configuration
        if not config.cloud_name or not config.api_key or not config.api_secret:
            logger.error("Configuration Cloudinary incomplète")
            raise ValueError("Configuration Cloudinary manquante")
            
        # Upload du fichier
        result = cloudinary.uploader.upload(
            file_content,
            public_id=public_id,
            resource_type=resource_type
        )
        
        logger.info(f"Upload réussi - URL: {result.get('url')}")
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload vers Cloudinary: {str(e)}")
        raise

def delete_file(public_id, resource_type="auto"):
    """
    Supprime un fichier de Cloudinary
    
    Args:
        public_id: L'ID public du fichier à supprimer
        resource_type: Type de ressource ("auto", "image", "video", "raw")
    
    Returns:
        bool: True si la suppression est réussie
    """
    try:
        logger.info(f"Tentative de suppression: public_id={public_id}")
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        logger.info(f"Résultat de la suppression: {result}")
        return result.get('result') == 'ok'
    except Exception as e:
        logger.error(f"Erreur lors de la suppression depuis Cloudinary: {str(e)}")
        raise Exception(f"Erreur lors de la suppression depuis Cloudinary: {str(e)}")

def get_file_url(public_id, resource_type="auto"):
    """
    Récupère l'URL d'un fichier
    
    Args:
        public_id: L'ID public du fichier
        resource_type: Type de ressource ("auto", "image", "video", "raw")
    
    Returns:
        str: L'URL sécurisée du fichier
    """
    try:
        url = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type=resource_type,
            secure=True
        )[0]
        logger.info(f"URL générée: {url}")
        return url
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'URL: {str(e)}")
        raise Exception(f"Erreur lors de la récupération de l'URL: {str(e)}") 