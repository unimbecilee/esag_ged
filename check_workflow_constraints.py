from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

try:
    conn = db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Vérifier les statuts existants
    cursor.execute("SELECT DISTINCT statut FROM workflow WHERE statut IS NOT NULL")
    statuts = cursor.fetchall()
    
    print('=== STATUTS WORKFLOW EXISTANTS ===')
    for s in statuts:
        print(f'Statut: "{s["statut"]}"')
    
    # Vérifier les contraintes
    cursor.execute("""
        SELECT constraint_name, check_clause 
        FROM information_schema.check_constraints 
        WHERE constraint_name LIKE '%workflow%'
    """)
    constraints = cursor.fetchall()
    
    print('\n=== CONTRAINTES SUR WORKFLOW ===')
    for c in constraints:
        print(f'Contrainte: {c["constraint_name"]}')
        print(f'Clause: {c["check_clause"]}')
    
    # Essayer d'insérer un workflow avec différents statuts
    test_statuts = ['actif', 'ACTIF', 'active', 'ACTIVE', 'enabled', 'ENABLED']
    
    print('\n=== TEST DES STATUTS ===')
    for statut in test_statuts:
        try:
            cursor.execute("""
                INSERT INTO workflow (nom, description, statut) 
                VALUES (%s, %s, %s)
            """, (f'Test {statut}', 'Test workflow', statut))
            print(f'✅ Statut "{statut}" accepté')
            # Rollback pour ne pas garder le test
            conn.rollback()
            break
        except Exception as e:
            print(f'❌ Statut "{statut}" rejeté: {str(e)[:100]}...')
            conn.rollback()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Erreur: {e}')
    import traceback
    traceback.print_exc() 