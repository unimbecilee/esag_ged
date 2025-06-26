"""
API pour le partage de documents
"""

from flask import Blueprint, request, jsonify
from psycopg2.extras import RealDictCursor
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

from ..db import db_connection
from ..auth import token_required

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

document_sharing_bp = Blueprint('document_sharing', __name__)

# Types de permissions disponibles
PERMISSIONS_DISPONIBLES = [
    'lecture',
    'téléchargement', 
    'modification',
    'commentaire',
    'partage_supplementaire'
]

@document_sharing_bp.route('/documents/<int:document_id>/share', methods=['POST'])
@token_required
def create_share(current_user, document_id: int):
    """
    Créer un nouveau partage de document
    
    Body JSON:
    {
        "destinataires": [
            {
                "type": "utilisateur|role|organisation",
                "id": "id_or_name",
                "nom": "nom_affichage"
            }
        ],
        "permissions": ["lecture", "téléchargement"],
        "date_expiration": "2024-12-31T23:59:59", // optionnel
        "commentaire": "Message optionnel"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
            
        destinataires = data.get('destinataires', [])
        permissions = data.get('permissions', ['lecture'])
        date_expiration = data.get('date_expiration')
        commentaire = data.get('commentaire', '')
        
        # Validation
        if not destinataires:
            return jsonify({'error': 'Au moins un destinataire requis'}), 400
            
        if not permissions:
            return jsonify({'error': 'Au moins une permission requise'}), 400
            
        # Vérifier que les permissions sont valides
        permissions_invalides = [p for p in permissions if p not in PERMISSIONS_DISPONIBLES]
        if permissions_invalides:
            return jsonify({
                'error': f'Permissions invalides: {permissions_invalides}',
                'permissions_disponibles': PERMISSIONS_DISPONIBLES
            }), 400
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier que l'utilisateur a le droit de partager ce document
        cursor.execute("""
            SELECT id, proprietaire_id FROM document 
            WHERE id = %s AND (proprietaire_id = %s OR %s IN (
                SELECT utilisateur_id FROM partage_document 
                WHERE document_id = %s AND 'partage_supplementaire' = ANY(permissions)
                AND actif = TRUE
                AND (date_expiration IS NULL OR date_expiration > CURRENT_TIMESTAMP)
            ))
        """, (document_id, current_user['id'], current_user['id'], document_id))
        
        document = cursor.fetchone()
        if not document:
            return jsonify({'error': 'Document non trouvé ou accès non autorisé'}), 404
        
        partages_crees = []
        
        # Traiter la date d'expiration
        date_exp_parsed = None
        if date_expiration:
            try:
                date_exp_parsed = datetime.fromisoformat(date_expiration.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Format de date d\'expiration invalide'}), 400
        
        # Créer les partages pour chaque destinataire
        for destinataire in destinataires:
            type_dest = destinataire.get('type')
            id_dest = destinataire.get('id')
            
            if not type_dest or not id_dest:
                continue
                
            # Préparer les paramètres selon le type de destinataire
            utilisateur_id = None
            role_nom = None
            organisation_id = None
            
            if type_dest == 'utilisateur':
                utilisateur_id = int(id_dest)
                # Vérifier que l'utilisateur existe
                cursor.execute("SELECT id FROM utilisateur WHERE id = %s", (utilisateur_id,))
                if not cursor.fetchone():
                    return jsonify({'error': f'Utilisateur {id_dest} non trouvé'}), 400
                    
            elif type_dest == 'role':
                role_nom = str(id_dest)
                # Vérifier que le rôle existe
                cursor.execute("SELECT nom FROM role WHERE nom = %s", (role_nom,))
                if not cursor.fetchone():
                    return jsonify({'error': f'Rôle {role_nom} non trouvé'}), 400
                    
            elif type_dest == 'organisation':
                organisation_id = int(id_dest)
                # Vérifier que l'organisation existe
                cursor.execute("SELECT id FROM organisation WHERE id = %s", (organisation_id,))
                if not cursor.fetchone():
                    return jsonify({'error': f'Organisation {id_dest} non trouvée'}), 400
            else:
                return jsonify({'error': f'Type de destinataire invalide: {type_dest}'}), 400
            
            # Vérifier s'il existe déjà un partage actif identique
            cursor.execute("""
                SELECT id FROM partage_document 
                WHERE document_id = %s 
                AND utilisateur_id IS NOT DISTINCT FROM %s
                AND role_nom IS NOT DISTINCT FROM %s
                AND organisation_id IS NOT DISTINCT FROM %s
                AND actif = TRUE
            """, (document_id, utilisateur_id, role_nom, organisation_id))
            
            partage_existant = cursor.fetchone()
            
            if partage_existant:
                # Mettre à jour le partage existant
                cursor.execute("""
                    UPDATE partage_document 
                    SET permissions = %s, 
                        date_expiration = %s,
                        commentaire = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING *
                """, (permissions, date_exp_parsed, commentaire, partage_existant['id']))
                
                partage = cursor.fetchone()
                partages_crees.append({
                    'id': partage['id'],
                    'action': 'mis_a_jour',
                    'destinataire': destinataire
                })
            else:
                # Créer un nouveau partage
                cursor.execute("""
                    INSERT INTO partage_document 
                    (document_id, utilisateur_id, role_nom, organisation_id, 
                     permissions, createur_id, date_expiration, commentaire)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (document_id, utilisateur_id, role_nom, organisation_id,
                      permissions, current_user['id'], date_exp_parsed, commentaire))
                
                partage = cursor.fetchone()
                partages_crees.append({
                    'id': partage['id'],
                    'action': 'cree',
                    'destinataire': destinataire
                })
        
        conn.commit()
        
        # Envoyer des notifications (optionnel)
        # TODO: Implémenter l'envoi de notifications
        
        return jsonify({
            'success': True,
            'message': f'{len(partages_crees)} partage(s) traité(s)',
            'partages': partages_crees
        }), 201
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du partage: {e}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@document_sharing_bp.route('/documents/<int:document_id>/shares', methods=['GET'])
@token_required
def get_document_shares(current_user, document_id: int):
    """Récupérer tous les partages d'un document"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier que l'utilisateur a accès au document
        cursor.execute("""
            SELECT proprietaire_id FROM document WHERE id = %s
        """, (document_id,))
        
        document = cursor.fetchone()
        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404
            
        # Seul le propriétaire peut voir tous les partages
        if document['proprietaire_id'] != current_user['id']:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        # Récupérer tous les partages actifs
        cursor.execute("""
            SELECT * FROM partage_document_details
            WHERE document_id = %s
            ORDER BY date_partage DESC
        """, (document_id,))
        
        partages = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'partages': [dict(partage) for partage in partages]
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des partages: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@document_sharing_bp.route('/shares/<int:share_id>', methods=['DELETE'])
@token_required
def revoke_share(current_user, share_id: int):
    """Révoquer un partage"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier que l'utilisateur peut révoquer ce partage
        cursor.execute("""
            SELECT p.*, d.proprietaire_id
            FROM partage_document p
            JOIN document d ON p.document_id = d.id
            WHERE p.id = %s
        """, (share_id,))
        
        partage = cursor.fetchone()
        if not partage:
            return jsonify({'error': 'Partage non trouvé'}), 404
            
        # Seul le créateur du partage ou le propriétaire du document peut le révoquer
        if partage['createur_id'] != current_user['id'] and partage['proprietaire_id'] != current_user['id']:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        # Désactiver le partage
        cursor.execute("""
            UPDATE partage_document 
            SET actif = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (share_id,))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Partage révoqué avec succès'
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la révocation du partage: {e}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@document_sharing_bp.route('/shares/<int:share_id>', methods=['PUT'])
@token_required
def update_share(current_user, share_id: int):
    """Modifier un partage existant"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
            
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier que l'utilisateur peut modifier ce partage
        cursor.execute("""
            SELECT p.*, d.proprietaire_id
            FROM partage_document p
            JOIN document d ON p.document_id = d.id
            WHERE p.id = %s
        """, (share_id,))
        
        partage = cursor.fetchone()
        if not partage:
            return jsonify({'error': 'Partage non trouvé'}), 404
            
        if partage['createur_id'] != current_user['id'] and partage['proprietaire_id'] != current_user['id']:
            return jsonify({'error': 'Accès non autorisé'}), 403
        
        # Préparer les mises à jour
        updates = []
        params = []
        
        if 'permissions' in data:
            permissions = data['permissions']
            permissions_invalides = [p for p in permissions if p not in PERMISSIONS_DISPONIBLES]
            if permissions_invalides:
                return jsonify({
                    'error': f'Permissions invalides: {permissions_invalides}'
                }), 400
            updates.append("permissions = %s")
            params.append(permissions)
        
        if 'date_expiration' in data:
            date_expiration = data['date_expiration']
            if date_expiration:
                try:
                    date_exp_parsed = datetime.fromisoformat(date_expiration.replace('Z', '+00:00'))
                    updates.append("date_expiration = %s")
                    params.append(date_exp_parsed)
                except ValueError:
                    return jsonify({'error': 'Format de date invalide'}), 400
            else:
                updates.append("date_expiration = NULL")
        
        if 'commentaire' in data:
            updates.append("commentaire = %s")
            params.append(data['commentaire'])
            
        if 'actif' in data:
            updates.append("actif = %s")
            params.append(data['actif'])
        
        if not updates:
            return jsonify({'error': 'Aucune modification spécifiée'}), 400
        
        # Effectuer la mise à jour
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(share_id)
        
        query = f"""
            UPDATE partage_document 
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING *
        """
        
        cursor.execute(query, params)
        partage_modifie = cursor.fetchone()
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Partage modifié avec succès',
            'partage': dict(partage_modifie)
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la modification du partage: {e}")
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@document_sharing_bp.route('/shared-documents', methods=['GET'])
@token_required
def get_shared_documents(current_user):
    """Récupérer tous les documents partagés avec l'utilisateur actuel"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer le rôle et l'organisation de l'utilisateur
        cursor.execute("""
            SELECT role, organisation_id FROM utilisateur WHERE id = %s
        """, (current_user['id'],))
        
        user_info = cursor.fetchone()
        if not user_info:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        user_role = user_info['role']
        user_org_id = user_info['organisation_id']
        
        # Récupérer tous les documents partagés avec cet utilisateur
        cursor.execute("""
            SELECT DISTINCT
                d.*,
                p.permissions,
                p.date_partage,
                p.date_expiration,
                p.commentaire as partage_commentaire,
                p.createur_id,
                CONCAT(createur.prenom, ' ', createur.nom) as partage_par,
                CASE 
                    WHEN p.utilisateur_id IS NOT NULL THEN 'utilisateur'
                    WHEN p.role_nom IS NOT NULL THEN 'role'
                    WHEN p.organisation_id IS NOT NULL THEN 'organisation'
                END as type_partage
            FROM document d
            JOIN partage_document p ON d.id = p.document_id
            JOIN utilisateur createur ON p.createur_id = createur.id
            WHERE p.actif = TRUE
            AND (p.date_expiration IS NULL OR p.date_expiration > CURRENT_TIMESTAMP)
            AND (
                p.utilisateur_id = %s OR
                p.role_nom = %s OR
                p.organisation_id = %s
            )
            AND d.proprietaire_id != %s  -- Exclure ses propres documents
            ORDER BY p.date_partage DESC
        """, (current_user['id'], user_role, user_org_id, current_user['id']))
        
        documents = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'documents': [dict(doc) for doc in documents],
            'total': len(documents)
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents partagés: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@document_sharing_bp.route('/documents/<int:document_id>/permissions', methods=['GET'])  
@token_required
def check_document_permissions(current_user, document_id: int):
    """Vérifier les permissions d'un utilisateur sur un document"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérifier si l'utilisateur est propriétaire
        cursor.execute("""
            SELECT proprietaire_id FROM document WHERE id = %s
        """, (document_id,))
        
        document = cursor.fetchone()
        if not document:
            return jsonify({'error': 'Document non trouvé'}), 404
        
        permissions = []
        is_owner = document['proprietaire_id'] == current_user['id']
        
        if is_owner:
            # Le propriétaire a toutes les permissions
            permissions = PERMISSIONS_DISPONIBLES.copy()
        else:
            # Vérifier les permissions via les partages
            cursor.execute("""
                SELECT DISTINCT unnest(p.permissions) as permission
                FROM partage_document p
                JOIN utilisateur u ON u.id = %s
                WHERE p.document_id = %s
                AND p.actif = TRUE
                AND (p.date_expiration IS NULL OR p.date_expiration > CURRENT_TIMESTAMP)
                AND (
                    p.utilisateur_id = %s OR
                    p.role_nom = u.role OR
                    p.organisation_id = u.organisation_id
                )
            """, (current_user['id'], document_id, current_user['id']))
            
            permissions = [row['permission'] for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'permissions': permissions,
            'is_owner': is_owner,
            'document_id': document_id
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des permissions: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@document_sharing_bp.route('/sharing/users', methods=['GET'])
@token_required
def get_users_for_sharing(current_user):
    """Récupérer la liste des utilisateurs pour le partage"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Récupérer tous les utilisateurs sauf l'utilisateur actuel
        cursor.execute("""
            SELECT id, nom, prenom, email, role, organisation_id
            FROM utilisateur 
            WHERE id != %s
            ORDER BY nom, prenom
        """, (current_user['id'],))
        
        users = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'users': [dict(user) for user in users]
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@document_sharing_bp.route('/sharing/roles', methods=['GET'])
@token_required
def get_roles_for_sharing(current_user):
    """Récupérer la liste des rôles pour le partage"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT nom, description FROM role ORDER BY nom")
        roles = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'roles': [dict(role) for role in roles]
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des rôles: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@document_sharing_bp.route('/sharing/organizations', methods=['GET'])
@token_required
def get_organizations_for_sharing(current_user):
    """Récupérer la liste des organisations pour le partage"""
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT id, nom, description FROM organisation ORDER BY nom")
        organizations = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'organizations': [dict(org) for org in organizations]
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des organisations: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close() 
