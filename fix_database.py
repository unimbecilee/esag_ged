#!/usr/bin/env python3
"""
Script pour corriger la base de données en ajoutant la colonne dossier_id manquante
"""

import sys
import os

# Ajouter le chemin vers le module AppFlask
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    """
    Ajoute la colonne dossier_id à la table document si elle n'existe pas
    """
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        logger.info("Connexion à la base de données réussie")
        
        # Vérifier si la colonne dossier_id existe déjà
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='document' AND column_name='dossier_id'
        """)
        
        if cursor.fetchone():
            logger.info("La colonne dossier_id existe déjà dans la table document")
            return
        
        logger.info("Ajout de la colonne dossier_id à la table document...")
        
        # Ajouter la colonne dossier_id
        cursor.execute("""
            ALTER TABLE document 
            ADD COLUMN dossier_id INTEGER REFERENCES dossier(id) ON DELETE SET NULL
        """)
        
        # Créer un index pour améliorer les performances
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_dossier_id 
            ON document(dossier_id)
        """)
        
        conn.commit()
        
        logger.info("✅ Colonne dossier_id ajoutée avec succès !")
        logger.info("✅ Index idx_document_dossier_id créé !")
        
        # Vérifier que la colonne a été ajoutée
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='document' AND column_name='dossier_id'
        """)
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Vérification : {result}")
        
        cursor.close()
        conn.close()
        
        logger.info("🎉 Base de données corrigée avec succès !")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction : {str(e)}")
        raise

if __name__ == "__main__":
    fix_database() 