import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Select,
  useToast,
  VStack,
  Text,
  Box,
  Icon,
} from '@chakra-ui/react';
import { FiFile } from 'react-icons/fi';
import { ElementType } from 'react';

// Créer un composant d'icône personnalisé
const FileIcon = (props: any) => <Icon as={FiFile as ElementType} {...props} />;

interface Document {
  id: number;
  nom: string;
  type: string;
  date_creation: string;
}

interface AddDocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  organizationId: number;
}

const AddDocumentModal: React.FC<AddDocumentModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  organizationId
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    if (isOpen) {
      fetchAvailableDocuments();
    }
  }, [isOpen]);

  const fetchAvailableDocuments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('https://web-production-ae27.up.railway.app/api/documents/available', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la récupération des documents');
      }

      const data = await response.json();
      setDocuments(data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger la liste des documents',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  };

  const handleSubmit = async () => {
    if (!selectedDocument) {
      toast({
        title: 'Erreur',
        description: 'Veuillez sélectionner un document',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
      return;
    }

    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`https://web-production-ae27.up.railway.app/api/organizations/${organizationId}/documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_id: parseInt(selectedDocument)
        })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'ajout du document');
      }

      toast({
        title: 'Succès',
        description: 'Document ajouté avec succès',
        status: 'success',
        duration: 5000,
        isClosable: true
      });

      onSuccess();
      onClose();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible d\'ajouter le document',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent bg="#1a1f37">
        <ModalHeader color="white">Ajouter un document</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            {documents.length === 0 ? (
              <Box textAlign="center" py={4}>
                <FileIcon boxSize={8} color="gray.400" mb={2} />
                <Text color="white">Aucun document disponible</Text>
              </Box>
            ) : (
              <FormControl>
                <FormLabel color="white">Document</FormLabel>
                <Select
                  value={selectedDocument}
                  onChange={(e) => setSelectedDocument(e.target.value)}
                  placeholder="Sélectionner un document"
                  bg="#20243a"
                  color="white"
                >
                  {documents.map((doc) => (
                    <option key={doc.id} value={doc.id}>
                      {`${doc.nom} (${doc.type})`}
                    </option>
                  ))}
                </Select>
              </FormControl>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Annuler
          </Button>
          <Button
            colorScheme="blue"
            onClick={handleSubmit}
            isLoading={isLoading}
            isDisabled={documents.length === 0}
          >
            Ajouter
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default AddDocumentModal; 

