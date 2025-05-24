import { useEffect, useState } from 'react';
import { Table, Thead, Tbody, Tr, Th, Td, Box, IconButton, useToast } from '@chakra-ui/react';
import { ViewIcon, DownloadIcon } from '@chakra-ui/icons';
import api from '../services/api';

interface Document {
  id: number;
  titre: string;
  description: string;
  categorie: string;
  cloudinary_url: string;
  date_ajout: string;
  taille: number;
  taille_formatee: string;
  proprietaire_nom?: string;
  proprietaire_prenom?: string;
}

export default function DocumentList() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const toast = useToast();

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/api/documents/recent');
      setDocuments(response.data);
    } catch (error) {
      console.error('Erreur lors de la récupération des documents:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de charger la liste des documents',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleView = (url: string) => {
    if (url) {
      window.open(url, '_blank');
    } else {
      toast({
        title: 'Erreur',
        description: 'URL du document non disponible',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleDownload = (url: string) => {
    if (url) {
      window.open(url, '_blank');
    } else {
      toast({
        title: 'Erreur',
        description: 'URL du document non disponible',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Box overflowX="auto">
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Titre</Th>
            <Th>Description</Th>
            <Th>Type</Th>
            <Th>Date d'ajout</Th>
            <Th>Taille</Th>
            <Th>Propriétaire</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {documents.map((doc) => (
            <Tr key={doc.id}>
              <Td>{doc.titre}</Td>
              <Td>{doc.description}</Td>
              <Td>{doc.categorie}</Td>
              <Td>{formatDate(doc.date_ajout)}</Td>
              <Td>{doc.taille_formatee}</Td>
              <Td>{doc.proprietaire_prenom} {doc.proprietaire_nom}</Td>
              <Td>
                <IconButton
                  aria-label="Voir le document"
                  icon={<ViewIcon />}
                  colorScheme="green"
                  size="sm"
                  mr={2}
                  onClick={() => handleView(doc.cloudinary_url)}
                />
                <IconButton
                  aria-label="Télécharger le document"
                  icon={<DownloadIcon />}
                  colorScheme="blue"
                  size="sm"
                  onClick={() => handleDownload(doc.cloudinary_url)}
                />
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
}