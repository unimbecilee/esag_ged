import psycopg2

# Configuration de la base de données
DATABASE_CONFIG = {
    'host': 'postgresql-thefau.alwaysdata.net',
    'dbname': 'thefau_archive',
    'user': 'thefau',
    'password': 'Passecale2002@',
    'port': 5432
}

def update_role_constraint():
    """Met à jour la contrainte de rôle pour accepter tous les rôles définis dans le frontend"""
    try:
        # Connexion à la base de données
        print("Connexion à la base de données...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Liste des rôles à accepter
        roles = [
            'Admin', 'Utilisateur',  # Valeurs originales (casse exacte)
            'admin', 'utilisateur',  # Valeurs en minuscules
            'chef_de_service',       # Nouveaux rôles
            'validateur',
            'archiviste'
        ]
        
        # Création de la liste pour la clause IN
        roles_str = ', '.join(f"'{role}'" for role in roles)
        
        # Suppression de l'ancienne contrainte
        print("Suppression de l'ancienne contrainte...")
        cursor.execute('ALTER TABLE utilisateur DROP CONSTRAINT IF EXISTS utilisateur_role_check')
        
        # Création de la nouvelle contrainte
        print("Création de la nouvelle contrainte...")
        query = f"ALTER TABLE utilisateur ADD CONSTRAINT utilisateur_role_check CHECK (role IN ({roles_str}))"
        print(f"Exécution de la requête: {query}")
        cursor.execute(query)
        
        # Validation des modifications
        conn.commit()
        print("✅ Contrainte mise à jour avec succès")
        
        # Vérification de la nouvelle contrainte
        cursor.execute("""
            SELECT pg_get_constraintdef(c.oid) 
            FROM pg_constraint c 
            JOIN pg_class t ON c.conrelid = t.oid 
            WHERE t.relname = 'utilisateur' 
            AND c.conname = 'utilisateur_role_check'
        """)
        result = cursor.fetchone()
        if result:
            print(f"Nouvelle contrainte: {result[0]}")
        else:
            print("⚠️ Impossible de vérifier la nouvelle contrainte")
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour de la contrainte: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    update_role_constraint() 