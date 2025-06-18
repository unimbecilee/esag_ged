from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

try:
    conn = db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Vérifier workflow_approbateur
    cursor.execute("""
        SELECT column_name, data_type FROM information_schema.columns 
        WHERE table_name = 'workflow_approbateur' 
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    
    print('=== COLONNES workflow_approbateur ===')
    for col in columns:
        print(f'{col["column_name"]}: {col["data_type"]}')
    
    # Vérifier les valeurs enum
    try:
        cursor.execute("SELECT unnest(enum_range(NULL::statut_workflow))")
        statuts = cursor.fetchall()
        print('\n=== VALEURS ENUM statut_workflow ===')
        for s in statuts:
            print(f'{s["unnest"]}')
    except Exception as e:
        print(f'\nErreur enum statut_workflow: {e}')
    
    # Vérifier si workflow_approbateur existe et a des données
    cursor.execute("SELECT COUNT(*) as count FROM workflow_approbateur")
    count = cursor.fetchone()
    print(f'\nNombre d\'approbateurs: {count["count"]}')
    
    # Vérifier etapeworkflow
    cursor.execute("SELECT COUNT(*) as count FROM etapeworkflow")
    count = cursor.fetchone()
    print(f'Nombre d\'étapes: {count["count"]}')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Erreur: {e}')
    import traceback
    traceback.print_exc() 