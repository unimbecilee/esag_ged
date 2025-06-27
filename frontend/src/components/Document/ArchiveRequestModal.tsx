import React, { useState, useEffect, ElementType } from "react";
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Textarea,
  Text,
  Alert,
  AlertIcon,
  Box,
  useToast,
  Icon
} from '@chakra-ui/react';
import { FiArchive, FiClock } from 'react-icons/fi';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import { checkAuthToken } from '../../utils/errorHandling';
import config from '../../config';

interface ArchiveRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number;
  documentTitle: string;
  onArchiveRequested?: () => void;
}

/**
 * Composant modal pour demander l'archivage d'un document
 */
const ArchiveRequestModal: React.FC<ArchiveRequestModalProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  onArchiveRequested
}) => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  const [workflowId, setWorkflowId] = useState<number | null>(null);
  const [comment, setComment] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadArchiveWorkflow();
    }
  }, [isOpen]);

  /**
   * Charge le workflow d'archivage depuis l'API
   */
  const loadArchiveWorkflow = async () => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        const response = await fetch(`${config.API_URL}/workflows/archivage`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
          throw new Error('Erreur lors du chargement du workflow d\'archivage');
        }

        const data = await response.json();
        setWorkflowId(data.id);
      },
      {
        loadingMessage: "Chargement du workflow d'archivage...",
        errorMessage: "Impossible de charger le workflow d'archivage"
      }
    );
  };

  /**
   * D�marre le workflow d'archivage pour le document
   */
  const handleRequestArchive = async () => {
    if (!workflowId) {
      toast({
        title: 'Erreur',
        description: 'Le workflow d\'archivage n\'est pas disponible',
        status: 'error',
        duration: 3000,
        isClosable: true
      });
      return;
    }

    setIsLoading(true);

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        const response = await fetch(`${config.API_URL}/workflow-instances`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            workflow_id: workflowId,
            document_id: documentId,
            commentaire: comment.trim() || "Demande d'archivage"
          })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.message || 'Erreur lors de la demande d\'archivage');
        }

        // Mettre � jour le statut du document
        const updateResponse = await fetch(`${config.API_URL}/documents/${documentId}/status`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            statut: 'EN_ATTENTE_ARCHIVAGE'
          })
        });

        if (!updateResponse.ok) {
          console.warn('Le statut du document n\'a pas pu être mis à jour');
        }

        // Envoyer les notifications aux responsables d'archivage
        try {
          const notificationResponse = await fetch(`${config.API_URL}/notifications/archive-request`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              document_id: documentId,
              document_title: documentTitle,
              comment: comment.trim()
            })
          });
          
          if (notificationResponse.ok) {
            console.log('Notifications d\'archivage envoyées');
          }
        } catch (error) {
          console.warn('Erreur lors de l\'envoi des notifications:', error);
        }

        toast({
          title: 'Succès',
          description: 'Demande d\'archivage soumise avec succès. Les responsables ont été notifiés.',
          status: 'success',
          duration: 5000,
          isClosable: true
        });

        handleClose();
        onArchiveRequested?.();
      },
      {
        loadingMessage: "Soumission de la demande d'archivage...",
        errorMessage: "Impossible de soumettre la demande d'archivage"
      }
    );

    setIsLoading(false);
  };

  const handleClose = () => {
    setComment('');
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg">
      <ModalOverlay />
      <ModalContent bg="#232946" color="white">
        <ModalHeader>
          <HStack>
            <Icon as={FiArchive as ElementType} color="#3a8bfd" />
            <Text>Demander l'archivage du document</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody pb={6}>
          <VStack spacing={6} align="stretch">
            {/* Document concern� */}
            <Box>
              <Text fontSize="sm" color="gray.400" mb={2}>Document concern�</Text>
              <Box bg="#20243a" p={3} borderRadius="md" border="1px solid #3a8bfd">
                <Text fontWeight="semibold">{documentTitle}</Text>
              </Box>
            </Box>

            {!workflowId && (
              <Alert status="error">
                <AlertIcon />
                Le workflow d'archivage n'est pas configur�. Veuillez contacter l'administrateur.
              </Alert>
            )}

            {/* Commentaire */}
            <FormControl>
              <FormLabel>Motif de la demande d'archivage (optionnel)</FormLabel>
              <Textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Pr�cisez pourquoi ce document doit �tre archiv�..."
                bg="#20243a"
                resize="vertical"
                rows={4}
              />
            </FormControl>

            {/* Informations sur le processus */}
            <Alert status="info" variant="left-accent">
              <AlertIcon />
              <Box>
                <Text fontWeight="semibold">Processus d'archivage</Text>
                <Text fontSize="sm">
                  Cette demande sera soumise � validation par votre chef de service, 
                  puis par l'archiviste. Une fois approuv�e, le document sera archiv�.
                </Text>
              </Box>
            </Alert>

            {/* Boutons d'action */}
            <HStack justifyContent="flex-end" pt={4}>
              <Button variant="ghost" onClick={handleClose}>
                Annuler
              </Button>
              <Button 
                colorScheme="blue"
                leftIcon={<Icon as={FiClock as ElementType} />}
                onClick={handleRequestArchive}
                isLoading={isLoading}
                isDisabled={!workflowId}
              >
                Soumettre la demande
              </Button>
            </HStack>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default ArchiveRequestModal;

