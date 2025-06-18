import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import ArchiveRequestModal from './ArchiveRequestModal';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import { checkAuthToken } from '../../utils/errorHandling';

// Mock des hooks et fonctions
jest.mock('../../hooks/useAsyncOperation');
jest.mock('../../utils/errorHandling');

describe('ArchiveRequestModal', () => {
  const mockProps = {
    isOpen: true,
    onClose: jest.fn(),
    documentId: 123,
    documentTitle: 'Test Document',
    onArchiveRequested: jest.fn()
  };

  const mockExecuteOperation = jest.fn();
  const mockToast = jest.fn();

  beforeEach(() => {
    // Reset des mocks
    jest.clearAllMocks();
    
    // Mock de useAsyncOperation
    (useAsyncOperation as jest.Mock).mockReturnValue({
      executeOperation: mockExecuteOperation
    });
    
    // Mock de checkAuthToken
    (checkAuthToken as jest.Mock).mockReturnValue('fake-token');
    
    // Mock de fetch
    global.fetch = jest.fn().mockImplementation((url) => {
      if (url.includes('workflows/archivage')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 456 })
        });
      }
      if (url.includes('workflow-instances')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 789 })
        });
      }
      if (url.includes('documents/123/status')) {
        return Promise.resolve({
          ok: true
        });
      }
      return Promise.reject(new Error('Fetch non implémenté pour cette URL'));
    });
  });

  test('affiche correctement le modal avec le titre du document', () => {
    render(
      <ChakraProvider>
        <ArchiveRequestModal {...mockProps} />
      </ChakraProvider>
    );
    
    expect(screen.getByText('Demander l\'archivage du document')).toBeInTheDocument();
    expect(screen.getByText('Test Document')).toBeInTheDocument();
  });

  test('charge le workflow d\'archivage à l\'ouverture', async () => {
    render(
      <ChakraProvider>
        <ArchiveRequestModal {...mockProps} />
      </ChakraProvider>
    );
    
    expect(mockExecuteOperation).toHaveBeenCalled();
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('workflows/archivage'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer fake-token'
          })
        })
      );
    });
  });

  test('soumet la demande d\'archivage lorsque le bouton est cliqué', async () => {
    render(
      <ChakraProvider>
        <ArchiveRequestModal {...mockProps} />
      </ChakraProvider>
    );
    
    // Attendre que le workflow soit chargé
    await waitFor(() => {
      expect(mockExecuteOperation).toHaveBeenCalled();
    });
    
    // Saisir un commentaire
    const commentInput = screen.getByPlaceholderText('Précisez pourquoi ce document doit être archivé...');
    fireEvent.change(commentInput, { target: { value: 'Ceci est un test' } });
    
    // Cliquer sur le bouton de soumission
    const submitButton = screen.getByText('Soumettre la demande');
    fireEvent.click(submitButton);
    
    // Vérifier que la demande est soumise
    await waitFor(() => {
      expect(mockExecuteOperation).toHaveBeenCalledTimes(2);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('workflow-instances'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Ceci est un test')
        })
      );
    });
    
    // Vérifier que le statut du document est mis à jour
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('documents/123/status'),
        expect.objectContaining({
          method: 'PUT',
          body: expect.stringContaining('EN_ATTENTE_ARCHIVAGE')
        })
      );
    });
    
    // Vérifier que le callback est appelé
    await waitFor(() => {
      expect(mockProps.onClose).toHaveBeenCalled();
      expect(mockProps.onArchiveRequested).toHaveBeenCalled();
    });
  });

  test('affiche une alerte si le workflow n\'est pas disponible', async () => {
    // Modifier le mock pour simuler une erreur
    global.fetch = jest.fn().mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ message: 'Workflow non trouvé' })
      });
    });
    
    render(
      <ChakraProvider>
        <ArchiveRequestModal {...mockProps} />
      </ChakraProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Le workflow d\'archivage n\'est pas configuré. Veuillez contacter l\'administrateur.')).toBeInTheDocument();
    });
  });
}); 