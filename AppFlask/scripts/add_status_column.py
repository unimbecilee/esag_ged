import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration de la base de données
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "ged_db"
DB_USER = "postgres"
DB_PASS = "postgres"

def db_connection():
    """Établit une connexion à la base de données"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"Erreur de connexion à la base de données: {str(e)}")
        return None

def add_status_column():
    """Ajoute la colonne status à la table utilisateur si elle n'existe pas déjà"""
    conn = db_connection()
    if conn is None:
        print("❌ Erreur de connexion à la base de données")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Vérifier si la colonne existe déjà
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'utilisateur' AND column_name = 'status'
        """)
        
        if cursor.fetchone() is None:
            print("🔄 La colonne status n'existe pas, ajout en cours...")
            
            # Ajouter la colonne status
            cursor.execute("""
                ALTER TABLE utilisateur 
                ADD COLUMN status VARCHAR(20) DEFAULT 'active'
            """)
            
            conn.commit()
            print("✅ Colonne status ajoutée avec succès")
        else:
            print("✅ La colonne status existe déjà")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la colonne status: {str(e)}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    add_status_column() 