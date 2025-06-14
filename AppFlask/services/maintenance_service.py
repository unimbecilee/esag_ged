from AppFlask.db import db_connection
import logging
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)

class MaintenanceService:
    def __init__(self):
        self.cleanup_thread = None
        self.stop_cleanup = False

    def start_cleanup_scheduler(self):
        """Démarre le thread de nettoyage des logs."""
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            self.stop_cleanup = False
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
            self.cleanup_thread.daemon = True
            self.cleanup_thread.start()
            logger.info("Service de nettoyage des logs démarré")

    def stop_cleanup_scheduler(self):
        """Arrête le thread de nettoyage des logs."""
        self.stop_cleanup = True
        if self.cleanup_thread:
            self.cleanup_thread.join()
            logger.info("Service de nettoyage des logs arrêté")

    def _cleanup_loop(self):
        """Boucle principale du thread de nettoyage."""
        while not self.stop_cleanup:
            try:
                self._perform_cleanup()
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage des logs : {str(e)}")
            
            # Attendre 24 heures avant la prochaine vérification
            for _ in range(24 * 60):  # 24 heures * 60 minutes
                if self.stop_cleanup:
                    break
                time.sleep(60)  # Attendre 1 minute

    def _perform_cleanup(self):
        """Exécute la fonction de nettoyage des logs."""
        try:
            conn = db_connection()
            cursor = conn.cursor()

            # Compter les logs avant nettoyage
            cursor.execute("SELECT COUNT(*) FROM system_logs")
            before_count = cursor.fetchone()[0]

            # Exécuter le nettoyage
            cursor.execute("SELECT cleanup_old_logs()")
            
            # Compter les logs après nettoyage
            cursor.execute("SELECT COUNT(*) FROM system_logs")
            after_count = cursor.fetchone()[0]

            deleted_count = before_count - after_count
            
            logger.info(f"Nettoyage des logs terminé : {deleted_count} logs supprimés")
            
            conn.commit()
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des logs : {str(e)}")
            if 'conn' in locals():
                conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

# Instance globale du service de maintenance
maintenance_service = MaintenanceService() 