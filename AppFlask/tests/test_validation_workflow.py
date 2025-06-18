"""
Tests pour le service de workflow de validation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
from AppFlask.services.validation_workflow_service import ValidationWorkflowService
from AppFlask.api.validation_workflow import bp as validation_bp

class TestValidationWorkflowService(unittest.TestCase):
    """Tests pour ValidationWorkflowService"""
    
    def setUp(self):
        self.service = ValidationWorkflowService()
        self.mock_conn = Mock()
        self.mock_cursor = Mock()
        self.mock_conn.cursor.return_value = self.mock_cursor
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    def test_get_or_create_workflow_existing(self, mock_db_connection):
        """Test récupération d'un workflow existant"""
        mock_db_connection.return_value = self.mock_conn
        self.mock_cursor.fetchone.return_value = {'id': 1}
        
        workflow_id = ValidationWorkflowService.get_or_create_workflow()
        
        self.assertEqual(workflow_id, 1)
        self.mock_cursor.execute.assert_called_once()
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    def test_get_or_create_workflow_new(self, mock_db_connection):
        """Test création d'un nouveau workflow"""
        mock_db_connection.return_value = self.mock_conn
        # Premier appel: workflow n'existe pas
        # Appels suivants: création du workflow et des étapes
        self.mock_cursor.fetchone.side_effect = [
            None,  # Workflow n'existe pas
            {'id': 1},  # ID du nouveau workflow
            {'id': 1},  # ID étape 1
            {'id': 2}   # ID étape 2
        ]
        
        workflow_id = ValidationWorkflowService.get_or_create_workflow()
        
        self.assertEqual(workflow_id, 1)
        self.mock_conn.commit.assert_called_once()
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    @patch('AppFlask.services.validation_workflow_service.History')
    def test_start_validation_workflow_success(self, mock_history, mock_db_connection):
        """Test démarrage réussi d'un workflow"""
        mock_db_connection.return_value = self.mock_conn
        
        # Mock des réponses de la base de données
        self.mock_cursor.fetchone.side_effect = [
            {'id': 1, 'titre': 'Test Document'},  # Document existe
            None,  # Pas de workflow en cours
            {'id': 1}  # Première étape
        ]
        
        with patch.object(self.service, 'get_or_create_workflow', return_value=1):
            with patch.object(self.service, '_notify_next_approvers'):
                result = self.service.start_validation_workflow(
                    document_id=1,
                    initiateur_id=1,
                    commentaire="Test"
                )
        
        self.assertTrue(result['instance_id'])
        self.assertEqual(result['status'], ValidationWorkflowService.STATUS_EN_COURS)
        self.mock_conn.commit.assert_called_once()
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    def test_start_validation_workflow_document_not_found(self, mock_db_connection):
        """Test démarrage avec document inexistant"""
        mock_db_connection.return_value = self.mock_conn
        self.mock_cursor.fetchone.return_value = None
        
        with self.assertRaises(Exception) as context:
            self.service.start_validation_workflow(
                document_id=999,
                initiateur_id=1,
                commentaire="Test"
            )
        
        self.assertIn("Document non trouvé", str(context.exception))
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    def test_start_validation_workflow_already_in_progress(self, mock_db_connection):
        """Test démarrage avec workflow déjà en cours"""
        mock_db_connection.return_value = self.mock_conn
        self.mock_cursor.fetchone.side_effect = [
            {'id': 1, 'titre': 'Test Document'},  # Document existe
            {'id': 1}  # Workflow déjà en cours
        ]
        
        with self.assertRaises(Exception) as context:
            self.service.start_validation_workflow(
                document_id=1,
                initiateur_id=1,
                commentaire="Test"
            )
        
        self.assertIn("workflow de validation est déjà en cours", str(context.exception))
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    @patch('AppFlask.services.validation_workflow_service.History')
    def test_process_approval_approve_intermediate_step(self, mock_history, mock_db_connection):
        """Test approbation d'une étape intermédiaire"""
        mock_db_connection.return_value = self.mock_conn
        
        # Mock instance en cours
        instance_data = {
            'id': 1,
            'workflow_id': 1,
            'document_id': 1,
            'etape_courante_id': 1,
            'document_titre': 'Test Doc',
            'etape_nom': 'Étape 1',
            'etape_ordre': 1
        }
        
        # Mock étape suivante
        etape_suivante = {'id': 2, 'nom': 'Étape 2'}
        
        self.mock_cursor.fetchone.side_effect = [
            instance_data,  # Instance
            etape_suivante  # Étape suivante
        ]
        
        with patch.object(self.service, '_can_user_approve_step', return_value=True):
            with patch.object(self.service, '_notify_next_approvers'):
                result = self.service.process_approval(
                    instance_id=1,
                    etape_id=1,
                    approbateur_id=1,
                    decision=ValidationWorkflowService.DECISION_APPROUVE,
                    commentaire="OK"
                )
        
        self.assertEqual(result['status'], ValidationWorkflowService.STATUS_EN_COURS)
        self.assertFalse(result['final'])
        self.assertEqual(result['etape_suivante_id'], 2)
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    @patch('AppFlask.services.validation_workflow_service.History')
    def test_process_approval_approve_final_step(self, mock_history, mock_db_connection):
        """Test approbation de la dernière étape"""
        mock_db_connection.return_value = self.mock_conn
        
        instance_data = {
            'id': 1,
            'workflow_id': 1,
            'document_id': 1,
            'etape_courante_id': 2,
            'document_titre': 'Test Doc',
            'etape_nom': 'Étape 2',
            'etape_ordre': 2
        }
        
        self.mock_cursor.fetchone.side_effect = [
            instance_data,  # Instance
            None  # Pas d'étape suivante
        ]
        
        with patch.object(self.service, '_can_user_approve_step', return_value=True):
            result = self.service.process_approval(
                instance_id=1,
                etape_id=2,
                approbateur_id=1,
                decision=ValidationWorkflowService.DECISION_APPROUVE,
                commentaire="Final OK"
            )
        
        self.assertEqual(result['status'], ValidationWorkflowService.STATUS_APPROUVE)
        self.assertTrue(result['final'])
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    @patch('AppFlask.services.validation_workflow_service.History')
    def test_process_approval_reject(self, mock_history, mock_db_connection):
        """Test rejet d'une étape"""
        mock_db_connection.return_value = self.mock_conn
        
        instance_data = {
            'id': 1,
            'workflow_id': 1,
            'document_id': 1,
            'etape_courante_id': 1,
            'document_titre': 'Test Doc',
            'etape_nom': 'Étape 1',
            'etape_ordre': 1
        }
        
        self.mock_cursor.fetchone.return_value = instance_data
        
        with patch.object(self.service, '_can_user_approve_step', return_value=True):
            result = self.service.process_approval(
                instance_id=1,
                etape_id=1,
                approbateur_id=1,
                decision=ValidationWorkflowService.DECISION_REJETE,
                commentaire="Non conforme"
            )
        
        self.assertEqual(result['status'], ValidationWorkflowService.STATUS_REJETE)
        self.assertTrue(result['final'])
        
    def test_process_approval_invalid_decision(self):
        """Test avec décision invalide"""
        with self.assertRaises(ValueError):
            self.service.process_approval(
                instance_id=1,
                etape_id=1,
                approbateur_id=1,
                decision="INVALID",
                commentaire=""
            )
            
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    def test_process_approval_unauthorized_user(self, mock_db_connection):
        """Test avec utilisateur non autorisé"""
        mock_db_connection.return_value = self.mock_conn
        
        instance_data = {
            'id': 1,
            'etape_courante_id': 1,
            'document_titre': 'Test Doc'
        }
        
        self.mock_cursor.fetchone.return_value = instance_data
        
        with patch.object(self.service, '_can_user_approve_step', return_value=False):
            with self.assertRaises(Exception) as context:
                self.service.process_approval(
                    instance_id=1,
                    etape_id=1,
                    approbateur_id=1,
                    decision=ValidationWorkflowService.DECISION_APPROUVE,
                    commentaire=""
                )
        
        self.assertIn("pas autorisé", str(context.exception))
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    def test_can_user_approve_step_by_role(self, mock_db_connection):
        """Test autorisation par rôle"""
        mock_db_connection.return_value = self.mock_conn
        
        self.mock_cursor.fetchone.side_effect = [
            {'role': 'chef_de_service'},  # Rôle utilisateur
            {'exists': True}  # Autorisation trouvée
        ]
        
        result = self.service._can_user_approve_step(1, 1)
        self.assertTrue(result)
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    def test_can_user_approve_step_unauthorized(self, mock_db_connection):
        """Test utilisateur non autorisé"""
        mock_db_connection.return_value = self.mock_conn
        
        self.mock_cursor.fetchone.side_effect = [
            {'role': 'Utilisateur'},  # Rôle utilisateur
            None  # Pas d'autorisation
        ]
        
        result = self.service._can_user_approve_step(1, 1)
        self.assertFalse(result)
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    def test_get_pending_approvals(self, mock_db_connection):
        """Test récupération des approbations en attente"""
        mock_db_connection.return_value = self.mock_conn
        
        user_data = {'role': 'chef_de_service'}
        pending_data = [
            {
                'instance_id': 1,
                'document_id': 1,
                'document_titre': 'Doc 1',
                'etape_nom': 'Validation Chef'
            },
            {
                'instance_id': 2,
                'document_id': 2,
                'document_titre': 'Doc 2',
                'etape_nom': 'Validation Chef'
            }
        ]
        
        self.mock_cursor.fetchone.return_value = user_data
        self.mock_cursor.fetchall.return_value = pending_data
        
        result = self.service.get_pending_approvals(1)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['document_titre'], 'Doc 1')
        
    @patch('AppFlask.services.validation_workflow_service.db_connection')
    def test_get_workflow_instance_details(self, mock_db_connection):
        """Test récupération des détails d'instance"""
        mock_db_connection.return_value = self.mock_conn
        
        instance_data = {
            'id': 1,
            'workflow_nom': 'Test Workflow',
            'document_titre': 'Test Doc'
        }
        
        self.mock_cursor.fetchone.return_value = instance_data
        self.mock_cursor.fetchall.side_effect = [[], []]  # Pas d'approbations ni d'étapes
        
        result = self.service.get_workflow_instance_details(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['instance']['workflow_nom'], 'Test Workflow')
        self.assertIsInstance(result['approbations'], list)
        self.assertIsInstance(result['etapes'], list)


class TestValidationWorkflowAPI(unittest.TestCase):
    """Tests pour les endpoints API"""
    
    def setUp(self):
        from AppFlask import create_app
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock du service
        self.mock_service = Mock()
        
    def _get_auth_headers(self):
        """Retourne les headers d'authentification pour les tests"""
        return {
            'Authorization': 'Bearer test_token',
            'Content-Type': 'application/json'
        }
        
    @patch('AppFlask.api.validation_workflow.validation_service')
    @patch('AppFlask.api.validation_workflow.token_required')
    def test_start_validation_workflow_success(self, mock_token_required, mock_service):
        """Test démarrage réussi de workflow via API"""
        # Mock de l'authentification
        mock_token_required.side_effect = lambda f: lambda *args, **kwargs: f({'id': 1, 'role': 'Utilisateur'}, *args, **kwargs)
        
        # Mock du service
        mock_service.start_validation_workflow.return_value = {
            'instance_id': 1,
            'workflow_id': 1,
            'status': 'EN_COURS'
        }
        
        response = self.client.post(
            '/validation-workflow/start',
            headers=self._get_auth_headers(),
            data=json.dumps({
                'document_id': 1,
                'commentaire': 'Test workflow'
            })
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['instance_id'], 1)
        
    @patch('AppFlask.api.validation_workflow.validation_service')
    @patch('AppFlask.api.validation_workflow.token_required')
    def test_start_validation_workflow_missing_document_id(self, mock_token_required, mock_service):
        """Test démarrage avec document_id manquant"""
        mock_token_required.side_effect = lambda f: lambda *args, **kwargs: f({'id': 1}, *args, **kwargs)
        
        response = self.client.post(
            '/validation-workflow/start',
            headers=self._get_auth_headers(),
            data=json.dumps({'commentaire': 'Test'})
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('document_id', data['message'])
        
    @patch('AppFlask.api.validation_workflow.validation_service')
    @patch('AppFlask.api.validation_workflow.token_required')
    def test_process_approval_success(self, mock_token_required, mock_service):
        """Test traitement réussi d'approbation via API"""
        mock_token_required.side_effect = lambda f: lambda *args, **kwargs: f({'id': 1, 'role': 'chef_de_service'}, *args, **kwargs)
        
        mock_service.process_approval.return_value = {
            'status': 'EN_COURS',
            'message': 'Étape approuvée',
            'final': False
        }
        
        response = self.client.post(
            '/validation-workflow/approve',
            headers=self._get_auth_headers(),
            data=json.dumps({
                'instance_id': 1,
                'etape_id': 1,
                'decision': 'APPROUVE',
                'commentaire': 'Validation OK'
            })
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
    @patch('AppFlask.api.validation_workflow.validation_service')
    @patch('AppFlask.api.validation_workflow.token_required')
    def test_process_approval_invalid_decision(self, mock_token_required, mock_service):
        """Test avec décision invalide"""
        mock_token_required.side_effect = lambda f: lambda *args, **kwargs: f({'id': 1}, *args, **kwargs)
        
        response = self.client.post(
            '/validation-workflow/approve',
            headers=self._get_auth_headers(),
            data=json.dumps({
                'instance_id': 1,
                'etape_id': 1,
                'decision': 'INVALID',
                'commentaire': ''
            })
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        
    @patch('AppFlask.api.validation_workflow.validation_service')
    @patch('AppFlask.api.validation_workflow.token_required')
    def test_get_pending_approvals(self, mock_token_required, mock_service):
        """Test récupération des approbations en attente"""
        mock_token_required.side_effect = lambda f: lambda *args, **kwargs: f({'id': 1, 'role': 'chef_de_service'}, *args, **kwargs)
        
        mock_service.get_pending_approvals.return_value = [
            {'instance_id': 1, 'document_titre': 'Doc 1'},
            {'instance_id': 2, 'document_titre': 'Doc 2'}
        ]
        
        response = self.client.get(
            '/validation-workflow/pending',
            headers=self._get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 2)


if __name__ == '__main__':
    unittest.main() 