import React, { useEffect, useState } from 'react';
import { Box } from '@chakra-ui/react';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import { checkAuthToken } from '../utils/errorHandling';
import { API_URL } from '../config';

interface Document {
  id: number;
  titre: string;
  // ... autres propriétés
}

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const { executeOperation } = useAsyncOperation();

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    const result = await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/documents`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la récupération des documents');
        }

        return await response.json();
      },
      {
        loadingMessage: "Chargement des documents...",
        errorMessage: "Impossible de charger les documents"
      }
    );

    if (result) {
      setDocuments(result);
    }
  };

  const handleUpload = async (file: File) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/documents/upload`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        });

        if (!response.ok) {
          throw new Error('Erreur lors du téléchargement');
        }

        await fetchDocuments(); // Rafraîchir la liste
      },
      {
        loadingMessage: "Téléchargement du document...",
        successMessage: "Document téléchargé avec succès",
        errorMessage: "Impossible de télécharger le document"
      }
    );
  };

  const handleDelete = async (documentId: number) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/documents/${documentId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la suppression');
        }

        await fetchDocuments(); // Rafraîchir la liste
      },
      {
        loadingMessage: "Suppression du document...",
        successMessage: "Document supprimé avec succès",
        errorMessage: "Impossible de supprimer le document"
      }
    );
  };

  return (
    <Box>
      {/* Votre interface utilisateur ici */}
    </Box>
  );
};

export default Documents; 

