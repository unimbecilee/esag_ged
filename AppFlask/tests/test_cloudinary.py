import cloudinary
import cloudinary.uploader
import cloudinary.api
import logging
import os
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_cloudinary_connection():
    try:
        logger.info("Début du test de connexion Cloudinary")
        
        # Configuration de Cloudinary
        config = cloudinary.config(
            cloud_name="dhzibf7tu",
            api_key="129899192135474",
            api_secret="NzKdF2R_wCXwBuiz0cp3fvmE8y0",
            secure=True
        )
        
        # 1. Test de base de la configuration
        logger.info("1. Vérification de la configuration")
        print(f"Configuration Cloudinary :")
        print(f"Cloud name: {config.cloud_name}")
        print(f"API Key: {config.api_key}")

        # 2. Test de l'API - Ping
        logger.info("2. Test de l'API - Ping")
        ping_result = cloudinary.api.ping()
        print("\nRésultat du ping :")
        print(f"Status: {ping_result.get('status', 'N/A')}")

        # 3. Test d'upload d'une image test
        logger.info("3. Test d'upload")
        test_file = "test_image.txt"
        
        # Créer un fichier test temporaire
        with open(test_file, "w") as f:
            f.write(f"Test Cloudinary {datetime.now()}")

        # Upload du fichier
        upload_result = cloudinary.uploader.upload(
            test_file,
            public_id="test_upload",
            resource_type="raw"
        )
        print("\nRésultat de l'upload :")
        print(f"Public ID: {upload_result['public_id']}")
        print(f"URL: {upload_result['url']}")

        # 4. Suppression du fichier test
        logger.info("4. Nettoyage - Suppression du fichier uploadé")
        delete_result = cloudinary.uploader.destroy(
            "test_upload",
            resource_type="raw"
        )
        print("\nSuppression du fichier :")
        print(f"Résultat: {delete_result['result']}")

        # Nettoyage local
        if os.path.exists(test_file):
            os.remove(test_file)

        logger.info("✅ Tests terminés avec succès")
        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {str(e)}")
        print(f"\nErreur détaillée:")
        print(str(e))
        return False

if __name__ == "__main__":
    test_cloudinary_connection() 