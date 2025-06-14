#!/usr/bin/env python3
"""
Script pour créer les tables de recherche dans la base de données ESAG GED
"""

import os
import sys
from AppFlask.db import db_connection

def create_search_tables():
    """Créer les tables de recherche et leurs index"""
    
    sql_script = """
    -- Table pour les recherches sauvegardées
    CREATE TABLE IF NOT EXISTS public.saved_searches (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        name VARCHAR(255) NOT NULL,
        filters JSONB NOT NULL,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES public.utilisateur(id) ON DELETE CASCADE,
        UNIQUE(user_id, name)
    );

    -- Index pour optimiser les requêtes
    CREATE INDEX IF NOT EXISTS idx_saved_searches_user_id ON public.saved_searches USING btree (user_id);
    CREATE INDEX IF NOT EXISTS idx_saved_searches_name ON public.saved_searches USING btree (name);
    CREATE INDEX IF NOT EXISTS idx_saved_searches_created_at ON public.saved_searches USING btree (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_saved_searches_last_used ON public.saved_searches USING btree (last_used DESC);
    CREATE INDEX IF NOT EXISTS idx_saved_searches_filters ON public.saved_searches USING gin (filters);

    -- Index pour améliorer les performances de recherche
    CREATE INDEX IF NOT EXISTS idx_document_titre_gin ON public.document USING gin (to_tsvector('french', titre));
    CREATE INDEX IF NOT EXISTS idx_document_description_gin ON public.document USING gin (to_tsvector('french', description));
    CREATE INDEX IF NOT EXISTS idx_document_categorie ON public.document USING btree (categorie);

    -- Commentaires pour la documentation
    COMMENT ON TABLE public.saved_searches IS 'Table pour stocker les recherches sauvegardées des utilisateurs';
    COMMENT ON COLUMN public.saved_searches.user_id IS 'ID de l''utilisateur propriétaire de la recherche';
    COMMENT ON COLUMN public.saved_searches.name IS 'Nom donné à la recherche sauvegardée';
    COMMENT ON COLUMN public.saved_searches.filters IS 'Filtres de recherche au format JSON';
    COMMENT ON COLUMN public.saved_searches.created_at IS 'Date de création de la recherche sauvegardée';
    COMMENT ON COLUMN public.saved_searches.last_used IS 'Date de dernière utilisation de la recherche';
    """
    
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        print("Création des tables de recherche...")
        cursor.execute(sql_script)
        conn.commit()
        
        print("✅ Table saved_searches créée avec succès!")
        print("✅ Index de recherche créés avec succès!")
        print("✅ Index d'optimisation pour les documents créés!")
        print("✅ Commentaires ajoutés avec succès!")
        
        # Vérifier que les tables ont été créées
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('saved_searches')
        """)
        
        tables = cursor.fetchall()
        if tables:
            print(f"✅ Vérification: {len(tables)} table(s) de recherche créée(s)")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("❌ Erreur: Aucune table de recherche trouvée après création")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables de recherche: {e}")
        sys.exit(1)

def check_tables_exist():
    """Vérifier si les tables de recherche existent déjà"""
    try:
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'saved_searches'
        """)
        
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        
        return exists
        
    except Exception as e:
        print(f"Erreur lors de la vérification des tables: {e}")
        return False

if __name__ == "__main__":
    print("=== Configuration des fonctionnalités de recherche pour ESAG GED ===")
    
    # Vérifier si les tables existent déjà
    if check_tables_exist():
        print("ℹ️  Les tables de recherche existent déjà dans la base de données")
        response = input("Voulez-vous continuer quand même ? (y/N): ")
        if response.lower() not in ['y', 'yes', 'oui']:
            print("Opération annulée")
            sys.exit(0)
    
    # Créer les tables
    create_search_tables()
    
    print("\n🎉 Configuration terminée!")
    print("Fonctionnalités de recherche disponibles :")
    print("  - Recherche simple avec suggestions")
    print("  - Recherche avancée avec filtres multiples")
    print("  - Sauvegarde et réutilisation de recherches")
    print("  - Index optimisés pour de meilleures performances")
    print("\nVous pouvez maintenant utiliser toutes les fonctionnalités de recherche dans ESAG GED.") 