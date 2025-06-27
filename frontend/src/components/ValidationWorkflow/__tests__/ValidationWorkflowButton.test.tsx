/**
 * Tests pour le composant ValidationWorkflowButton
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import ValidationWorkflowButton from '../ValidationWorkflowButton';
import validationWorkflowService from '../../../services/validationWorkflowService';
import { useAsyncOperation } from '../../../hooks/useAsyncOperation';

// Mocks
jest.mock('../../../services/validationWorkflowService');
jest.mock('../../../hooks/useAsyncOperation');

const mockValidationService = validationWorkflowService as jest.Mocked<typeof validationWorkflowService>;
const mockUseAsyncOperation = useAsyncOperation as jest.MockedFunction<typeof useAsyncOperation>;

const renderWithChakra = (component: React.ReactElement) => {
  return render(
    <ChakraProvider>
      {component}
    </ChakraProvider>
  );
};

describe('ValidationWorkflowButton', () => {
  const mockExecuteOperation = jest.fn();
  const mockOnWorkflowStarted = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAsyncOperation.mockReturnValue({
      executeOperation: mockExecuteOperation,
      resetState: jest.fn(),
      isLoading: false,
      error: null,
      isSuccess: false
    });
  });

  const defaultProps = {
    documentId: 1,
    documentTitle: 'Test Document',
    onWorkflowStarted: mockOnWorkflowStarted
  };

  describe('État initial', () => {
    it('affiche un spinner pendant la vérification du statut', () => {
      mockValidationService.canStartWorkflow.mockImplementation(() => new Promise(() => {}));
      
      renderWithChakra(<ValidationWorkflowButton {...defaultProps} />);
      
      expect(screen.getByText('Vérification...')).toBeInTheDocument();
    });

    it('affiche le bouton désactivé si un workflow est déjà en cours', async () => {
      mockValidationService.canStartWorkflow.mockResolvedValue(false);
      
      renderWithChakra(<ValidationWorkflowButton {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Workflow en cours')).toBeInTheDocument();
      });
      
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('affiche le bouton actif si aucun workflow n\'est en cours', async () => {
      mockValidationService.canStartWorkflow.mockResolvedValue(true);
      
      renderWithChakra(<ValidationWorkflowButton {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Demander validation')).toBeInTheDocument();
      });
      
      const button = screen.getByRole('button');
      expect(button).not.toBeDisabled();
    });
  });

  describe('Ouverture du modal', () => {
    beforeEach(async () => {
      mockValidationService.canStartWorkflow.mockResolvedValue(true);
      renderWithChakra(<ValidationWorkflowButton {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Demander validation')).toBeInTheDocument();
      });
    });

    it('ouvre le modal quand on clique sur le bouton', async () => {
      const button = screen.getByText('Demander validation');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Démarrer la validation du document')).toBeInTheDocument();
      });
      
      expect(screen.getByText('Test Document')).toBeInTheDocument();
      expect(screen.getByText('Processus de validation')).toBeInTheDocument();
    });

    it('affiche les informations du processus de validation', async () => {
      const button = screen.getByText('Demander validation');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Étape 1 :')).toBeInTheDocument();
        expect(screen.getByText('Étape 2 :')).toBeInTheDocument();
        expect(screen.getByText('Validation par un chef de service')).toBeInTheDocument();
        expect(screen.getByText('Validation finale par un directeur')).toBeInTheDocument();
      });
    });

    it('permet de saisir un commentaire', async () => {
      const button = screen.getByText('Demander validation');
      fireEvent.click(button);
      
      await waitFor(() => {
        const textarea = screen.getByPlaceholderText('Ajoutez un commentaire sur cette demande de validation...');
        expect(textarea).toBeInTheDocument();
        
        fireEvent.change(textarea, { target: { value: 'Commentaire de test' } });
        expect(textarea).toHaveValue('Commentaire de test');
      });
    });
  });

  describe('Démarrage du workflow', () => {
    beforeEach(async () => {
      mockValidationService.canStartWorkflow.mockResolvedValue(true);
      renderWithChakra(<ValidationWorkflowButton {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Demander validation')).toBeInTheDocument();
      });
      
      const button = screen.getByText('Demander validation');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Démarrer la validation du document')).toBeInTheDocument();
      });
    });

    it('démarre le workflow avec les bonnes données', async () => {
      const textarea = screen.getByPlaceholderText('Ajoutez un commentaire sur cette demande de validation...');
      fireEvent.change(textarea, { target: { value: 'Mon commentaire' } });
      
      mockExecuteOperation.mockImplementation(async (operation) => {
        return await operation();
      });
      
      mockValidationService.startValidationWorkflow.mockResolvedValue({
        instance_id: 1,
        workflow_id: 1,
        etape_courante_id: 1,
        status: 'EN_COURS',
        message: 'Workflow démarré'
      });
      
      const startButton = screen.getByText('Démarrer la validation');
      fireEvent.click(startButton);
      
      await waitFor(() => {
        expect(mockExecuteOperation).toHaveBeenCalled();
      });
      
      // Vérifier que le service a été appelé avec les bonnes données
      const operationCall = mockExecuteOperation.mock.calls[0][0];
      await operationCall();
      
      expect(mockValidationService.startValidationWorkflow).toHaveBeenCalledWith({
        document_id: 1,
        commentaire: 'Mon commentaire'
      });
    });

    it('ferme le modal après un démarrage réussi', async () => {
      mockExecuteOperation.mockImplementation(async (operation) => {
        return await operation();
      });
      
      mockValidationService.startValidationWorkflow.mockResolvedValue({
        instance_id: 1,
        workflow_id: 1,
        etape_courante_id: 1,
        status: 'EN_COURS',
        message: 'Workflow démarré'
      });
      
      const startButton = screen.getByText('Démarrer la validation');
      fireEvent.click(startButton);
      
      await waitFor(() => {
        expect(screen.queryByText('Démarrer la validation du document')).not.toBeInTheDocument();
      });
    });

    it('appelle onWorkflowStarted après un démarrage réussi', async () => {
      mockExecuteOperation.mockImplementation(async (operation) => {
        return await operation();
      });
      
      mockValidationService.startValidationWorkflow.mockResolvedValue({
        instance_id: 1,
        workflow_id: 1,
        etape_courante_id: 1,
        status: 'EN_COURS',
        message: 'Workflow démarré'
      });
      
      const startButton = screen.getByText('Démarrer la validation');
      fireEvent.click(startButton);
      
      await waitFor(() => {
        expect(mockOnWorkflowStarted).toHaveBeenCalled();
      });
    });
  });

  describe('Fermeture du modal', () => {
    beforeEach(async () => {
      mockValidationService.canStartWorkflow.mockResolvedValue(true);
      renderWithChakra(<ValidationWorkflowButton {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Demander validation')).toBeInTheDocument();
      });
      
      const button = screen.getByText('Demander validation');
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText('Démarrer la validation du document')).toBeInTheDocument();
      });
    });

    it('ferme le modal quand on clique sur Annuler', async () => {
      const cancelButton = screen.getByText('Annuler');
      fireEvent.click(cancelButton);
      
      await waitFor(() => {
        expect(screen.queryByText('Démarrer la validation du document')).not.toBeInTheDocument();
      });
    });

    it('remet à zéro le commentaire quand on ferme le modal', async () => {
      const textarea = screen.getByPlaceholderText('Ajoutez un commentaire sur cette demande de validation...');
      fireEvent.change(textarea, { target: { value: 'Test' } });
      
      const cancelButton = screen.getByText('Annuler');
      fireEvent.click(cancelButton);
      
      // Rouvrir le modal
      const button = screen.getByText('Demander validation');
      fireEvent.click(button);
      
      await waitFor(() => {
        const newTextarea = screen.getByPlaceholderText('Ajoutez un commentaire sur cette demande de validation...');
        expect(newTextarea).toHaveValue('');
      });
    });
  });

  describe('Gestion des erreurs', () => {
    it('gère les erreurs de vérification du statut', async () => {
      mockValidationService.canStartWorkflow.mockRejectedValue(new Error('Erreur réseau'));
      
      renderWithChakra(<ValidationWorkflowButton {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Workflow en cours')).toBeInTheDocument();
      });
      
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });
  });

  describe('Props disabled', () => {
    it('désactive le bouton quand disabled=true', async () => {
      mockValidationService.canStartWorkflow.mockResolvedValue(true);
      
      renderWithChakra(
        <ValidationWorkflowButton {...defaultProps} disabled={true} />
      );
      
      await waitFor(() => {
        const button = screen.getByRole('button');
        expect(button).toBeDisabled();
      });
    });
  });
}); 

