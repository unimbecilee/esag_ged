from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

try:
    conn = db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Vérifier la structure de workflow_instance
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'workflow_instance'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    
    print('=== COLONNES workflow_instance ===')
    for col in columns:
        print(f'{col["column_name"]}: {col["data_type"]} (nullable: {col["is_nullable"]})')
    
    # Vérifier quelques données
    cursor.execute("SELECT COUNT(*) as count FROM workflow_instance")
    count = cursor.fetchone()
    print(f'\nNombre d\'instances: {count["count"]}')
    
    # Vérifier la structure de workflow
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'workflow'
        ORDER BY ordinal_position
    """)
    workflow_columns = cursor.fetchall()
    
    print('\n=== COLONNES workflow ===')
    for col in workflow_columns:
        print(f'{col["column_name"]}: {col["data_type"]} (nullable: {col["is_nullable"]})')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Erreur: {e}')
    import traceback
    traceback.print_exc() 