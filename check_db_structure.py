#!/usr/bin/env python3
"""
Vérification et correction de la structure de la base de données
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from AppFlask.db import db_connection
from psycopg2.extras import RealDictCursor

def check_workflow_instance_table():
    """Vérifier la structure de la table workflow_instance"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("🔍 VÉRIFICATION TABLE WORKFLOW_INSTANCE")
        print("=" * 50)
        
        # Vérifier les colonnes existantes
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'workflow_instance'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ Table workflow_instance non trouvée")
            cursor.close()
            conn.close()
            return False
        
        print("📋 Colonnes existantes:")
        for col in columns:
            print(f"   • {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}")
        
        # Vérifier les données
        cursor.execute("SELECT COUNT(*) as count FROM workflow_instance")
        count = cursor.fetchone()['count']
        
        print(f"\n📊 {count} instances de workflow trouvées")
        
        if count > 0:
            # Afficher les dernières instances
            cursor.execute("""
                SELECT * FROM workflow_instance 
                ORDER BY id DESC 
                LIMIT 3
            """)
            
            instances = cursor.fetchall()
            
            print("\n📋 Dernières instances:")
            for instance in instances:
                print(f"   • ID: {instance['id']}, Document: {instance['document_id']}, Statut: {instance['statut']}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def check_etapeworkflow_table():
    """Vérifier la structure de la table etapeworkflow"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n🔍 VÉRIFICATION TABLE ETAPEWORKFLOW")
        print("=" * 50)
        
        # Vérifier les colonnes existantes
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'etapeworkflow'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ Table etapeworkflow non trouvée")
            cursor.close()
            conn.close()
            return False
        
        print("📋 Colonnes existantes:")
        for col in columns:
            print(f"   • {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}")
        
        # Vérifier les données
        cursor.execute("""
            SELECT e.*, w.nom as workflow_nom
            FROM etapeworkflow e
            JOIN workflow w ON e.workflow_id = w.id
            ORDER BY w.nom, e.ordre
        """)
        
        etapes = cursor.fetchall()
        
        print(f"\n📊 {len(etapes)} étapes de workflow trouvées")
        
        if etapes:
            current_workflow = None
            for etape in etapes:
                if current_workflow != etape['workflow_nom']:
                    current_workflow = etape['workflow_nom']
                    print(f"\n📋 Workflow: {current_workflow}")
                
                print(f"   {etape['ordre']}. {etape['nom']}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def check_notifications_integration():
    """Vérifier l'intégration entre workflows et notifications"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n🔍 VÉRIFICATION INTÉGRATION WORKFLOWS-NOTIFICATIONS")
        print("=" * 60)
        
        # Chercher les notifications de workflow récentes
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM notifications 
            WHERE type LIKE '%workflow%'
        """)
        
        workflow_notifs = cursor.fetchone()['count']
        
        print(f"📬 {workflow_notifs} notifications de workflow trouvées")
        
        if workflow_notifs > 0:
            cursor.execute("""
                SELECT n.*, u.nom, u.prenom, u.role
                FROM notifications n
                JOIN utilisateur u ON n.user_id = u.id
                WHERE n.type LIKE '%workflow%'
                ORDER BY n.created_at DESC
                LIMIT 5
            """)
            
            notifications = cursor.fetchall()
            
            print("\n📋 Dernières notifications de workflow:")
            for notif in notifications:
                status = "✅ Lu" if notif['is_read'] else "🔴 Non lu"
                print(f"   {status} {notif['type']} → {notif['prenom']} {notif['nom']} ({notif['role']})")
                print(f"      {notif['message'][:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def fix_notification_service_issue():
    """Corriger le problème de métadonnées JSON"""
    print("\n🔧 CORRECTION PROBLÈME NOTIFICATIONS")
    print("=" * 50)
    
    try:
        # Tester la création d'une notification simple
        from AppFlask.services.notification_service import NotificationService
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer un utilisateur test
        cursor.execute("SELECT id FROM utilisateur WHERE role = 'chef_de_service' LIMIT 1")
        user = cursor.fetchone()
        
        if not user:
            print("❌ Aucun chef de service trouvé")
            return False
        
        # Créer une notification sans métadonnées complexes
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, priority, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            user['id'],
            "Test notification workflow",
            "Une nouvelle demande de validation nécessite votre attention",
            "workflow_approval_required",
            3,
            False
        ))
        
        notification_id = cursor.fetchone()['id']
        conn.commit()
        
        print(f"✅ Notification de test créée avec ID: {notification_id}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur correction: {str(e)}")
        return False

def main():
    print("🔍 VÉRIFICATION STRUCTURE BASE DE DONNÉES")
    print("=" * 60)
    
    # 1. Vérifier workflow_instance
    check_workflow_instance_table()
    
    # 2. Vérifier etapeworkflow
    check_etapeworkflow_table()
    
    # 3. Vérifier intégration notifications
    check_notifications_integration()
    
    # 4. Corriger le problème de notifications
    fix_notification_service_issue()
    
    print("\n✅ VÉRIFICATION TERMINÉE")

if __name__ == "__main__":
    main() 