import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Configuration de base de données (même que dans AppFlask/db.py)
DATABASE_CONFIG = {
    'host': 'postgresql-thefau.alwaysdata.net',
    'dbname': 'thefau_archive',
    'user': 'thefau',
    'password': 'Passecale2002@',
    'port': 5432
}

def check_tables():
    """Vérifier les tables existantes et leur structure"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== TABLES EXISTANTES ===")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table['table_name']}")
        
        # Vérifier spécifiquement les tables utilisateur/rôle
        print("\n=== STRUCTURE TABLE UTILISATEUR ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'utilisateur'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"- {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
        # Vérifier les tables liées aux rôles
        print("\n=== TABLES CONTENANT 'ROLE' ===")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name ILIKE '%role%'
        """)
        
        role_tables = cursor.fetchall()
        for table in role_tables:
            print(f"- {table['table_name']}")
            
        # Vérifier les tables liées aux organisations/membres
        print("\n=== TABLES CONTENANT 'ORGANISATION' OU 'MEMBRE' ===")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name ILIKE '%organisation%' OR table_name ILIKE '%membre%')
        """)
        
        org_tables = cursor.fetchall()
        for table in org_tables:
            print(f"- {table['table_name']}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_tables() 