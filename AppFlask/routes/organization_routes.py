from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from AppFlask.db import db_connection
from AppFlask.api.auth import token_required
from datetime import datetime
import logging
from psycopg2.extras import RealDictCursor
from AppFlask.routes.history_routes import log_action

# Configuration du logging
logger = logging.getLogger(__name__)

# Créez un Blueprint pour les routes d'organisation
organization_bp = Blueprint('organization', __name__)

# Gestionnaire pour les requêtes OPTIONS
@organization_bp.route('/api/organizations', methods=['OPTIONS'])
@organization_bp.route('/api/organizations/<int:org_id>', methods=['OPTIONS'])
@organization_bp.route('/api/organizations/<int:org_id>/members', methods=['OPTIONS'])
@organization_bp.route('/api/organizations/<int:org_id>/documents', methods=['OPTIONS'])
@organization_bp.route('/api/organizations/<int:org_id>/documents/<int:doc_id>', methods=['OPTIONS'])
@organization_bp.route('/api/organizations/<int:org_id>/workflows', methods=['OPTIONS'])
def handle_options():
    return '', 200

@organization_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_organization_web():
    if request.method == 'POST':
        # Logique de création d'organisation ici
        # Par exemple, récupérer les données du formulaire:
        # organization_name = request.form.get('organization_name')
        # ... autres champs ...
        flash('Organisation créée avec succès!', 'success') # Exemple de message flash
        return redirect(url_for('dashboard.manage_preferences')) # Rediriger vers une page appropriée
    return render_template('organization/create_organization.html')

# Vous pouvez ajouter d'autres routes liées aux organisations ici
# Par exemple, pour lister les organisations, les modifier, etc.

@organization_bp.route('/api/organizations', methods=['GET'])
@token_required
def get_organizations(current_user):
    try:
        logger.info(f"Tentative de récupération des organisations pour l'utilisateur {current_user['id']}")
        logger.info(f"Rôle de l'utilisateur : {current_user['role']}")
        
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if current_user['role'].lower() == 'admin':
            logger.info("Utilisateur admin : récupération de toutes les organisations")
            # Requête simplifiée pour le débogage
            query = """
                SELECT * FROM organisation
                ORDER BY date_creation DESC
            """
            cursor.execute(query)
            logger.info("Requête SQL exécutée : " + query)
        else:
            logger.info("Utilisateur non-admin : récupération des organisations dont l'utilisateur est membre")
            query = """
                SELECT o.* FROM organisation o
                JOIN membre m ON o.id = m.organisation_id
                WHERE m.utilisateur_id = %s
                ORDER BY o.date_creation DESC
            """
            cursor.execute(query, (current_user['id'],))
            logger.info("Requête SQL exécutée avec ID utilisateur : " + str(current_user['id']))

        organizations = cursor.fetchall()
        logger.info(f"Nombre d'organisations trouvées : {len(organizations)}")
        
        # Log de la structure des données
        if organizations:
            logger.info("Structure de la première organisation :")
            for key, value in organizations[0].items():
                logger.info(f"  {key}: {type(value)}")
        else:
            logger.warning("Aucune organisation trouvée dans la base de données")

        cursor.close()
        conn.close()

        return jsonify(organizations)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des organisations: {str(e)}")
        logger.error("Détails de l'erreur:", exc_info=True)
        return jsonify({'message': str(e)}), 500

@organization_bp.route('/api/organizations', methods=['POST'])
@token_required
def create_organization(current_user):
    try:
        data = request.get_json()
        if not data:
            logger.error("Aucune donnée JSON reçue")
            return jsonify({'message': 'Aucune donnée reçue'}), 400

        nom = data.get('nom')
        if not nom:
            logger.error("Le nom de l'organisation est manquant")
            return jsonify({'message': 'Le nom de l\'organisation est requis'}), 400

        description = data.get('description', '')
        adresse = data.get('adresse', '')
        email_contact = data.get('email_contact', '')
        telephone_contact = data.get('telephone_contact', '')
        statut = data.get('statut', 'ACTIVE')

        logger.info(f"Tentative de création d'organisation: {nom}")
        logger.debug(f"Données reçues: {data}")

        conn = db_connection()
        cursor = conn.cursor()

        # Vérifier si une organisation avec le même nom existe déjà
        cursor.execute("SELECT id FROM organisation WHERE LOWER(nom) = LOWER(%s)", (nom,))
        if cursor.fetchone():
            logger.warning(f"Une organisation avec le nom '{nom}' existe déjà")
            return jsonify({'message': 'Une organisation avec ce nom existe déjà'}), 400

        try:
            # Créer l'organisation
            cursor.execute("""
                INSERT INTO organisation (
                    nom, description, adresse, email_contact, 
                    telephone_contact, statut, date_creation
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (nom, description, adresse, email_contact, telephone_contact, 
                  statut, datetime.now()))
            
            org_id = cursor.fetchone()[0]

            # Ajouter le créateur comme membre administrateur
            cursor.execute("""
                INSERT INTO membre (organisation_id, utilisateur_id, role, date_ajout)
                VALUES (%s, %s, 'ADMIN', %s)
            """, (org_id, current_user['id'], datetime.now()))

            conn.commit()
            logger.info(f"Organisation '{nom}' créée avec succès (ID: {org_id})")

            # Log de l'action de création
            log_action(
                user_id=current_user['id'],
                action_type="CREATE",
                entity_type="ORGANISATION",
                entity_id=org_id,
                entity_name=nom,
                description=f"Création de l'organisation {nom}",
                metadata=data
            )

            return jsonify({
                'message': 'Organisation créée avec succès',
                'id': org_id
            }), 201

        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur SQL lors de la création de l'organisation: {str(e)}")
            return jsonify({'message': f'Erreur lors de la création de l\'organisation: {str(e)}'}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        logger.error(f"Erreur lors de la création de l'organisation: {str(e)}")
        return jsonify({'message': f'Erreur lors de la création de l\'organisation: {str(e)}'}), 500

@organization_bp.route('/api/organizations/<int:org_id>', methods=['PUT'])
@token_required
def update_organization(current_user, org_id):
    try:
        conn = db_connection()
        cursor = conn.cursor()

        # Vérifier les permissions
        cursor.execute("""
            SELECT role FROM membre 
            WHERE organisation_id = %s AND utilisateur_id = %s
        """, (org_id, current_user['id']))
        
        membre = cursor.fetchone()
        if not membre and current_user['role'].lower() != 'admin':
            return jsonify({'message': 'Permission refusée'}), 403

        data = request.get_json()
        nom = data.get('nom')
        description = data.get('description')
        adresse = data.get('adresse')
        email_contact = data.get('email_contact')
        telephone_contact = data.get('telephone_contact')
        statut = data.get('statut')

        if not nom:
            return jsonify({'message': 'Le nom de l\'organisation est requis'}), 400

        # Vérifier si le nouveau nom n'est pas déjà utilisé
        cursor.execute("""
            SELECT id FROM organisation 
            WHERE LOWER(nom) = LOWER(%s) AND id != %s
        """, (nom, org_id))
        if cursor.fetchone():
            return jsonify({'message': 'Une organisation avec ce nom existe déjà'}), 400

        # Mettre à jour l'organisation
        cursor.execute("""
            UPDATE organisation 
            SET nom = %s, description = %s, adresse = %s, 
                email_contact = %s, telephone_contact = %s, statut = %s
            WHERE id = %s
        """, (nom, description, adresse, email_contact, telephone_contact, 
              statut, org_id))

        conn.commit()
        cursor.close()
        conn.close()

        # Log de l'action de modification
        log_action(
            user_id=current_user['id'],
            action_type="UPDATE",
            entity_type="ORGANISATION",
            entity_id=org_id,
            entity_name=nom,
            description=f"Modification de l'organisation {nom}",
            metadata={
                "old_data": {
                    "nom": nom,
                    "description": description,
                    "adresse": adresse,
                    "email_contact": email_contact,
                    "telephone_contact": telephone_contact,
                    "statut": statut
                },
                "new_data": {
                    "nom": nom,
                    "description": description,
                    "adresse": adresse,
                    "email_contact": email_contact,
                    "telephone_contact": telephone_contact,
                    "statut": statut
                }
            }
        )

        return jsonify({'message': 'Organisation mise à jour avec succès'})

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'organisation: {str(e)}")
        return jsonify({'message': str(e)}), 500

@organization_bp.route('/api/organizations/<int:org_id>', methods=['DELETE'])
@token_required
def delete_organization(current_user, org_id):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Vérifier les permissions
        if current_user['role'].lower() != 'admin':
            cursor.execute("""
                SELECT role FROM membre 
                WHERE organisation_id = %s AND utilisateur_id = %s AND role = 'ADMIN'
            """, (org_id, current_user['id']))
            
            if not cursor.fetchone():
                return jsonify({'message': 'Permission refusée'}), 403

        # Récupérer les données de l'organisation avant suppression
        cursor.execute("""
            SELECT * FROM organisation WHERE id = %s
        """, (org_id,))
        organization = cursor.fetchone()
        
        if not organization:
            return jsonify({'message': 'Organisation non trouvée'}), 404

        # Déplacer vers la corbeille
        cursor.execute("""
            SELECT move_to_trash(%s, 'organisation', %s::jsonb, %s)
        """, (org_id, jsonify(organization).get_data().decode('utf-8'), current_user['id']))

        # Supprimer les membres
        cursor.execute("DELETE FROM membre WHERE organisation_id = %s", (org_id,))
        
        # Supprimer l'organisation
        cursor.execute("DELETE FROM organisation WHERE id = %s", (org_id,))

        conn.commit()
        cursor.close()
        conn.close()

        # Log de l'action de suppression
        log_action(
            user_id=current_user['id'],
            action_type="DELETE",
            entity_type="ORGANISATION",
            entity_id=org_id,
            entity_name=organization['nom'],
            description=f"Suppression de l'organisation {organization['nom']}",
            metadata=organization
        )

        return jsonify({'message': 'Organisation déplacée vers la corbeille'})

    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'organisation: {str(e)}")
        return jsonify({'message': str(e)}), 500

@organization_bp.route('/api/organizations/<int:org_id>/members', methods=['GET'])
@token_required
def get_organization_members(current_user, org_id):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Vérifier si l'utilisateur est membre ou admin
        if current_user['role'].lower() != 'admin':
            cursor.execute("""
                SELECT id FROM membre 
                WHERE organisation_id = %s AND utilisateur_id = %s
            """, (org_id, current_user['id']))
            
            if not cursor.fetchone():
                return jsonify({'message': 'Permission refusée'}), 403

        # Récupérer les membres
        cursor.execute("""
            SELECT 
                u.id,
                u.nom,
                u.prenom,
                u.email,
                m.role,
                TO_CHAR(m.date_ajout, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as date_ajout
            FROM membre m
            JOIN utilisateur u ON m.utilisateur_id = u.id
            WHERE m.organisation_id = %s
            ORDER BY m.date_ajout DESC
        """, (org_id,))

        members = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(members)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des membres: {str(e)}")
        return jsonify({'message': str(e)}), 500

@organization_bp.route('/api/organizations/<int:org_id>/documents', methods=['GET'])
@token_required
def get_organization_documents(current_user, org_id):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Vérifier si l'utilisateur est membre ou admin
        if current_user['role'].lower() != 'admin':
            cursor.execute("""
                SELECT id FROM membre 
                WHERE organisation_id = %s AND utilisateur_id = %s
            """, (org_id, current_user['id']))
            
            if not cursor.fetchone():
                return jsonify({'message': 'Permission refusée'}), 403

        # Récupérer les documents
        cursor.execute("""
            SELECT 
                d.id,
                d.nom,
                d.type,
                TO_CHAR(do.date_ajout, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as date_ajout,
                CONCAT(u.prenom, ' ', u.nom) as ajoute_par
            FROM document_organisation do
            JOIN document d ON do.document_id = d.id
            JOIN utilisateur u ON do.ajoute_par = u.id
            WHERE do.organisation_id = %s
            ORDER BY do.date_ajout DESC
        """, (org_id,))

        documents = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(documents)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des documents: {str(e)}")
        return jsonify({'message': str(e)}), 500

@organization_bp.route('/api/organizations/<int:org_id>/documents', methods=['POST'])
@token_required
def add_document_to_organization(current_user, org_id):
    try:
        data = request.get_json()
        document_id = data.get('document_id')

        if not document_id:
            return jsonify({'message': 'ID du document requis'}), 400

        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Vérifier si l'utilisateur est membre ou admin
        if current_user['role'].lower() != 'admin':
            cursor.execute("""
                SELECT id FROM membre 
                WHERE organisation_id = %s AND utilisateur_id = %s
            """, (org_id, current_user['id']))
            
            if not cursor.fetchone():
                return jsonify({'message': 'Permission refusée'}), 403

        # Ajouter le document
        cursor.execute("""
            INSERT INTO document_organisation (document_id, organisation_id, ajoute_par)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (document_id, org_id, current_user['id']))

        new_doc_org_id = cursor.fetchone()['id']
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Document ajouté avec succès',
            'id': new_doc_org_id
        }), 201

    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du document: {str(e)}")
        return jsonify({'message': str(e)}), 500

@organization_bp.route('/api/organizations/<int:org_id>/documents/<int:doc_id>', methods=['DELETE'])
@token_required
def remove_document_from_organization(current_user, org_id, doc_id):
    try:
        conn = db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Vérifier si l'utilisateur est membre ou admin
        if current_user['role'].lower() != 'admin':
            cursor.execute("""
                SELECT id FROM membre 
                WHERE organisation_id = %s AND utilisateur_id = %s AND role = 'ADMIN'
            """, (org_id, current_user['id']))
            
            if not cursor.fetchone():
                return jsonify({'message': 'Permission refusée'}), 403

        # Supprimer le document
        cursor.execute("""
            DELETE FROM document_organisation
            WHERE organisation_id = %s AND document_id = %s
            RETURNING id
        """, (org_id, doc_id))

        deleted = cursor.fetchone()
        if not deleted:
            return jsonify({'message': 'Document non trouvé'}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Document retiré avec succès'}), 200

    except Exception as e:
        logger.error(f"Erreur lors de la suppression du document: {str(e)}")
        return jsonify({'message': str(e)}), 500

@organization_bp.route('/api/organizations/<int:org_id>/workflows', methods=['GET'])
@token_required
def get_organization_workflows(current_user, org_id):
    try:
        conn = db_connection()
        cursor = conn.cursor(dictionary=True)

        # Vérifier si l'utilisateur est membre ou admin
        if current_user['role'].lower() != 'admin':
            cursor.execute("""
                SELECT id FROM membre 
                WHERE organisation_id = %s AND utilisateur_id = %s
            """, (org_id, current_user['id']))
            
            if not cursor.fetchone():
                return jsonify({'message': 'Permission refusée'}), 403

        # Récupérer les workflows
        cursor.execute("""
            SELECT 
                w.id,
                w.nom,
                w.description,
                TO_CHAR(w.date_creation, 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as date_creation
            FROM workflow w
            JOIN workflow_organisation wo ON w.id = wo.workflow_id
            WHERE wo.organisation_id = %s
            ORDER BY w.date_creation DESC
        """, (org_id,))

        workflows = cursor.fetchall()

        # Pour chaque workflow, récupérer ses étapes
        for workflow in workflows:
            cursor.execute("""
                SELECT 
                    e.id,
                    e.nom,
                    e.description,
                    e.ordre,
                    array_agg(CONCAT(u.prenom, ' ', u.nom)) as responsables
                FROM etape e
                LEFT JOIN etape_responsable er ON e.id = er.etape_id
                LEFT JOIN utilisateur u ON er.utilisateur_id = u.id
                WHERE e.workflow_id = %s
                GROUP BY e.id, e.nom, e.description, e.ordre
                ORDER BY e.ordre
            """, (workflow['id'],))
            
            workflow['etapes'] = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(workflows)

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des workflows: {str(e)}")
        return jsonify({'message': str(e)}), 500