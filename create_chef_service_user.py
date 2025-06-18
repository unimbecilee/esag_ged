#!/usr/bin/env python3
"""
Script pour créer un utilisateur chef de service pour les tests de workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor
import bcrypt

def create_chef_service_user():
    """Crée un utilisateur chef de service pour les tests"""
    
    conn = db_connection()
    if not conn:
        print("❌ Erreur de connexion à la base de données")
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT id FROM utilisateur WHERE email = %s", ('chef@esag.com',))
        if cursor.fetchone():
            print("✅ Utilisateur chef de service existe déjà")
            return True
        
        # Créer le mot de passe hashé
        password = "password123"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Créer l'utilisateur
        cursor.execute("""
            INSERT INTO utilisateur (nom, prenom, email, mot_de_passe, role, date_creation)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            'Chef',
            'Service',
            'chef@esag.com',
            hashed_password,
            'chef_de_service'
        ))
        
        user_id = cursor.fetchone()['id']
        conn.commit()
        
        print(f"✅ Utilisateur chef de service créé avec l'ID: {user_id}")
        print(f"   Email: chef@esag.com")
        print(f"   Mot de passe: {password}")
        print(f"   Rôle: chef_de_service")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_roles():
    """Vérifie que les rôles nécessaires existent"""
    
    conn = db_connection()
    if not conn:
        print("❌ Erreur de connexion à la base de données")
        return False
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier les rôles
        cursor.execute("SELECT nom FROM role WHERE nom IN ('chef_de_service', 'Admin')")
        roles = cursor.fetchall()
        
        existing_roles = [role['nom'] for role in roles]
        
        if 'chef_de_service' not in existing_roles:
            print("⚠️ Rôle 'chef_de_service' manquant")
            cursor.execute("INSERT INTO role (nom, description) VALUES ('chef_de_service', 'Chef de service')")
            print("✅ Rôle 'chef_de_service' créé")
        
        if 'Admin' not in existing_roles:
            print("⚠️ Rôle 'Admin' manquant")
            cursor.execute("INSERT INTO role (nom, description) VALUES ('Admin', 'Administrateur')")
            print("✅ Rôle 'Admin' créé")
        
        conn.commit()
        print("✅ Vérification des rôles terminée")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erreur lors de la vérification des rôles: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🔧 Configuration des utilisateurs pour les tests de workflow")
    print("=" * 60)
    
    # Vérifier les rôles
    if verify_roles():
        # Créer l'utilisateur chef de service
        if create_chef_service_user():
            print("\n✅ Configuration terminée avec succès")
        else:
            print("\n❌ Échec de la configuration")
    else:
        print("\n❌ Échec de la vérification des rôles") 