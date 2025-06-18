#!/usr/bin/env python3
"""
Script de test pour vérifier l'enregistrement des actions d'authentification
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

def test_db_connection():
    """Tester la connexion à la base de données"""
    try:
        # Utiliser la même configuration que dans AppFlask/db.py
        conn = psycopg2.connect(
            host='postgresql-thefau.alwaysdata.net',
            database='thefau_archive',
            user='thefau',
            password='Passecale2002@',
            port=5432
        )
        print("✅ Connexion à la base de données réussie")
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return None

def test_log_user_action(conn, user_id, action_type, description):
    """Tester l'enregistrement d'une action utilisateur"""
    try:
        cursor = conn.cursor()
        
        # Enregistrer dans la table history si user_id n'est pas None
        if user_id is not None:
            cursor.execute("""
                INSERT INTO history (action_type, entity_type, entity_id, entity_name, description, user_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (action_type, 'user', user_id, 'Action utilisateur', description, user_id))
            print(f"✅ Enregistrement dans history réussi pour user_id={user_id}")
        
        # Enregistrer dans system_logs
        level = 'WARNING' if 'FAILED' in action_type else 'INFO'
        cursor.execute("""
            INSERT INTO system_logs (timestamp, level, event_type, user_id, ip_address, 
                                   request_path, request_method, message, additional_data)
            VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
        """, (level, action_type, user_id, '127.0.0.1', '/auth/login', 'POST', description, '{}'))
        print(f"✅ Enregistrement dans system_logs réussi")
        
        conn.commit()
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'enregistrement: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

def check_recent_logs(conn):
    """Vérifier les logs récents"""
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n=== Dernières entrées dans history ===")
        cursor.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT 5")
        history_rows = cursor.fetchall()
        for row in history_rows:
            print(f"ID: {row['id']}, User: {row['user_id']}, Action: {row['action_type']}, Description: {row['description']}, Date: {row['created_at']}")
        
        print("\n=== Dernières entrées dans system_logs ===")
        cursor.execute("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 5")
        logs_rows = cursor.fetchall()
        for row in logs_rows:
            print(f"ID: {row['id']}, User: {row['user_id']}, Action: {row['event_type']}, Message: {row['message']}, IP: {row['ip_address']}, Date: {row['timestamp']}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des logs: {e}")

def main():
    print("🔍 Test de l'enregistrement des actions d'authentification")
    print("=" * 60)
    
    # Test de connexion
    conn = test_db_connection()
    if not conn:
        print("❌ Impossible de continuer sans connexion à la base de données")
        return
    
    # Vérifier les logs existants
    print("\n📋 Vérification des logs existants:")
    check_recent_logs(conn)
    
    # Test d'enregistrement d'une connexion réussie
    print("\n🧪 Test d'enregistrement d'une connexion réussie:")
    success = test_log_user_action(
        conn, 
        6,  # ID utilisateur admin existant
        'LOGIN_SUCCESS', 
        'Test de connexion réussie depuis le script de test'
    )
    
    # Test d'enregistrement d'une connexion échouée
    print("\n🧪 Test d'enregistrement d'une connexion échouée:")
    success = test_log_user_action(
        conn, 
        None,  # Pas d'utilisateur pour échec
        'LOGIN_FAILED', 
        'Test de connexion échouée depuis le script de test'
    )
    
    # Test d'enregistrement d'une déconnexion
    print("\n🧪 Test d'enregistrement d'une déconnexion:")
    success = test_log_user_action(
        conn, 
        6,  # ID utilisateur admin existant
        'LOGOUT', 
        'Test de déconnexion depuis le script de test'
    )
    
    # Vérifier les nouveaux logs
    print("\n📋 Vérification des nouveaux logs:")
    check_recent_logs(conn)
    
    conn.close()
    print("\n✅ Tests terminés")

if __name__ == "__main__":
    main() 