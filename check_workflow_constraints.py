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

def check_workflow_constraints():
    """Vérifier les contraintes de la table workflow"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("=== STRUCTURE TABLE WORKFLOW ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'workflow'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"- {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}) - Default: {col['column_default']}")
        
        print("\n=== CONTRAINTES TABLE WORKFLOW ===")
        cursor.execute("""
            SELECT 
                constraint_name,
                constraint_type,
                check_clause
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.check_constraints cc ON tc.constraint_name = cc.constraint_name
            WHERE tc.table_name = 'workflow'
            AND tc.table_schema = 'public'
        """)
        
        constraints = cursor.fetchall()
        for constraint in constraints:
            print(f"- {constraint['constraint_name']}: {constraint['constraint_type']}")
            if constraint['check_clause']:
                print(f"  Condition: {constraint['check_clause']}")
        
        print("\n=== DONNÉES EXISTANTES WORKFLOW ===")
        cursor.execute("SELECT * FROM workflow LIMIT 5")
        workflows = cursor.fetchall()
        
        if workflows:
            for workflow in workflows:
                print(f"- ID: {workflow['id']}, Nom: {workflow['nom']}, Statut: {workflow['statut']}")
        else:
            print("Aucun workflow existant")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_workflow_constraints() 