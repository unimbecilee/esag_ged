import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration de base de données (même que dans AppFlask/db.py)
DATABASE_CONFIG = {
    'host': 'postgresql-thefau.alwaysdata.net',
    'dbname': 'thefau_archive',
    'user': 'thefau',
    'password': 'Passecale2002@',
    'port': 5432
}

def check_workflow_tables():
    """Vérifier les tables de workflow et leurs relations"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== TABLES WORKFLOW ===")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name ILIKE '%workflow%'
            ORDER BY table_name
        """)
        
        workflow_tables = cursor.fetchall()
        for table in workflow_tables:
            print(f"- {table['table_name']}")
        
        # Vérifier la table utilisateur
        print("\n=== TABLE UTILISATEUR (EXISTE-T-ELLE?) ===")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name = 'utilisateur'
        """)
        
        user_table = cursor.fetchall()
        if user_table:
            print("✓ Table utilisateur existe")
        else:
            print("✗ Table utilisateur n'existe pas")
            
        # Chercher la vraie table des utilisateurs
        print("\n=== TABLES CONTENANT 'USER' ===")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name ILIKE '%user%'
        """)
        
        user_tables = cursor.fetchall()
        for table in user_tables:
            print(f"- {table['table_name']}")
            
        # Vérifier la structure de la table membre
        print("\n=== STRUCTURE TABLE MEMBRE ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'membre'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"- {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_workflow_tables() 