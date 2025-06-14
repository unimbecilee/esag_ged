import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration de base de données
DATABASE_CONFIG = {
    'host': 'postgresql-thefau.alwaysdata.net',
    'dbname': 'thefau_archive',
    'user': 'thefau',
    'password': 'Passecale2002@',
    'port': 5432
}

def check_workflow_status_constraint():
    """Vérifier la contrainte sur le statut du workflow"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Vérifier la contrainte
        cursor.execute("""
            SELECT pg_get_constraintdef(oid) as constraint_def
            FROM pg_constraint
            WHERE conname = 'workflow_statut_check'
        """)
        
        constraint = cursor.fetchone()
        if constraint:
            print(f"Contrainte: {constraint[0]}")
        else:
            print("Contrainte non trouvée")
        
        # Vérifier la structure de la colonne
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'workflow' AND column_name = 'statut'
        """)
        
        column = cursor.fetchone()
        if column:
            print(f"\nColonne: {column[0]}")
            print(f"Type: {column[1]}")
            print(f"Nullable: {column[2]}")
            print(f"Default: {column[3]}")
        
        # Vérifier les valeurs existantes
        cursor.execute("SELECT id, nom, statut FROM workflow")
        workflows = cursor.fetchall()
        
        print("\nWorkflows existants:")
        for workflow in workflows:
            print(f"- ID: {workflow[0]}, Nom: {workflow[1]}, Statut: {workflow[2]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_workflow_status_constraint() 