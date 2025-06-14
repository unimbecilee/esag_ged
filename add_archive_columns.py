from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
import sys

def add_archive_columns():
    """
    Ajoute les colonnes nécessaires à la table document pour l'archivage :
    - est_archive (boolean) : indique si le document est archivé
    - date_archivage (timestamp) : date à laquelle le document a été archivé
    
    Ajoute également 'ARCHIVE' comme valeur possible pour le statut du document
    """
    conn = db_connection()
    if not conn:
        print("Erreur: Impossible de se connecter à la base de données")
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si la colonne est_archive existe déjà
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'document' AND column_name = 'est_archive'
        """)
        
        if not cursor.fetchone():
            print("Ajout de la colonne est_archive à la table document...")
            cursor.execute("""
                ALTER TABLE document
                ADD COLUMN est_archive BOOLEAN DEFAULT FALSE
            """)
            print("Colonne est_archive ajoutée avec succès")
        else:
            print("La colonne est_archive existe déjà")
        
        # Vérifier si la colonne date_archivage existe déjà
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'document' AND column_name = 'date_archivage'
        """)
        
        if not cursor.fetchone():
            print("Ajout de la colonne date_archivage à la table document...")
            cursor.execute("""
                ALTER TABLE document
                ADD COLUMN date_archivage TIMESTAMP
            """)
            print("Colonne date_archivage ajoutée avec succès")
        else:
            print("La colonne date_archivage existe déjà")
        
        # Vérifier le type de la colonne statut
        cursor.execute("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'document' AND column_name = 'statut'
        """)
        
        statut_type = cursor.fetchone()
        if statut_type:
            print(f"Type de la colonne statut: {statut_type['data_type']}")
            
            if statut_type['data_type'] == 'USER-DEFINED':
                # C'est probablement un enum, vérifions si ARCHIVE est une valeur possible
                cursor.execute("""
                    SELECT pg_enum.enumlabel
                    FROM pg_type 
                    JOIN pg_enum ON pg_enum.enumtypid = pg_type.oid
                    JOIN pg_attribute ON pg_attribute.atttypid = pg_type.oid
                    JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
                    WHERE pg_class.relname = 'document' 
                    AND pg_attribute.attname = 'statut'
                    AND pg_enum.enumlabel = 'ARCHIVE'
                """)
                
                if not cursor.fetchone():
                    print("Tentative d'ajout de la valeur ARCHIVE au type enum...")
                    try:
                        # Récupérer le nom du type enum
                        cursor.execute("""
                            SELECT pg_type.typname
                            FROM pg_type 
                            JOIN pg_attribute ON pg_attribute.atttypid = pg_type.oid
                            JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
                            WHERE pg_class.relname = 'document' 
                            AND pg_attribute.attname = 'statut'
                        """)
                        
                        enum_type = cursor.fetchone()
                        if enum_type:
                            enum_name = enum_type['typname']
                            cursor.execute(f"""
                                ALTER TYPE {enum_name} ADD VALUE 'ARCHIVE' IF NOT EXISTS
                            """)
                            print(f"Valeur ARCHIVE ajoutée au type {enum_name}")
                        else:
                            print("Impossible de déterminer le nom du type enum")
                    except Exception as e:
                        print(f"Erreur lors de l'ajout de la valeur ARCHIVE: {str(e)}")
                        print("Ajout de la valeur ARCHIVE ignoré")
                else:
                    print("La valeur ARCHIVE existe déjà dans le type enum")
            else:
                # C'est probablement une chaîne de caractères, pas besoin de modifier le type
                print("La colonne statut n'est pas de type enum, pas besoin d'ajouter la valeur ARCHIVE")
        else:
            print("Colonne statut non trouvée")
        
        conn.commit()
        print("Modifications terminées avec succès")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de l'ajout des colonnes d'archivage: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    success = add_archive_columns()
    sys.exit(0 if success else 1) 