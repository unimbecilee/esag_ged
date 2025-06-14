#!/usr/bin/env python3
"""
Script pour créer la table favoris dans la base de données ESAG GED
"""

import os
import sys
from AppFlask.db import db_connection

def create_favorites_table():
    """Créer la table favoris et ses index"""
    
    sql_script = """
    -- Créer la table favoris
    CREATE TABLE IF NOT EXISTS public.favoris (
        id SERIAL PRIMARY KEY,
        document_id INTEGER NOT NULL,
        utilisateur_id INTEGER NOT NULL,
        date_ajout TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES public.document(id) ON DELETE CASCADE,
        FOREIGN KEY (utilisateur_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE,
        UNIQUE(document_id, utilisateur_id)
    );

    -- Index pour optimiser les requêtes
    CREATE INDEX IF NOT EXISTS idx_favoris_document_id ON public.favoris USING btree (document_id);
    CREATE INDEX IF NOT EXISTS idx_favoris_utilisateur_id ON public.favoris USING btree (utilisateur_id);
    CREATE INDEX IF NOT EXISTS idx_favoris_date_ajout ON public.favoris USING btree (date_ajout DESC);

    -- Commentaires pour la documentation
    COMMENT ON TABLE public.favoris IS 'Table pour stocker les documents favoris des utilisateurs';
    COMMENT ON COLUMN public.favoris.document_id IS 'ID du document marqué comme favori';
    COMMENT ON COLUMN public.favoris.utilisateur_id IS 'ID de l''utilisateur qui a marqué le document comme favori';
    COMMENT ON COLUMN public.favoris.date_ajout IS 'Date et heure d''ajout aux favoris';
    """
    
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        print("Création de la table favoris...")
        cursor.execute(sql_script)
        conn.commit()
        
        print("✅ Table favoris créée avec succès!")
        print("✅ Index créés avec succès!")
        print("✅ Commentaires ajoutés avec succès!")
        
        # Vérifier que la table a été créée
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'favoris'
        """)
        
        if cursor.fetchone():
            print("✅ Vérification: La table favoris existe bien dans la base de données")
        else:
            print("❌ Erreur: La table favoris n'a pas été trouvée après création")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table favoris: {e}")
        sys.exit(1)

def check_table_exists():
    """Vérifier si la table favoris existe déjà"""
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'favoris'
        """)
        
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        
        return exists
        
    except Exception as e:
        print(f"Erreur lors de la vérification de la table: {e}")
        return False

if __name__ == "__main__":
    print("=== Configuration de la table favoris pour ESAG GED ===")
    
    # Vérifier si la table existe déjà
    if check_table_exists():
        print("ℹ️  La table favoris existe déjà dans la base de données")
        response = input("Voulez-vous continuer quand même ? (y/N): ")
        if response.lower() not in ['y', 'yes', 'oui']:
            print("Opération annulée")
            sys.exit(0)
    
    # Créer la table
    create_favorites_table()
    
    print("\n🎉 Configuration terminée!")
    print("Vous pouvez maintenant utiliser les fonctionnalités de favoris dans votre application ESAG GED.") 