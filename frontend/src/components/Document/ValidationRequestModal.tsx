import React, { useState, ElementType } from "react";
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
import { FiCheckCircle, FiSend } from 'react-icons/fi';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import { checkAuthToken } from '../../utils/errorHandling';
import config from '../../config';

interface ValidationRequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number;
  documentTitle: string;
  onValidationRequested?: () => void;
}

/**
 * Composant modal pour demander la validation d'un document
 */
const ValidationRequestModal: React.FC<ValidationRequestModalProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  onValidationRequested
}) => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  const [comment, setComment] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Démarre le workflow de validation pour le document
   */
  const handleRequestValidation = async () => {
    setIsLoading(true);

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        // Utiliser le système de validation automatique
        const response = await fetch(`${config.API_URL}/api/validation-workflow/start`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            document_id: documentId,
            commentaire: comment.trim() || "Demande de validation"
          })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.message || 'Erreur lors de la demande de validation');
        }

        const result = await response.json();
        console.log('🔍 Workflow de validation démarré:', result);

        toast({
          title: 'Succès',
          description: 'Demande de validation soumise avec succès. Le workflow a été démarré.',
          status: 'success',
          duration: 5000,
          isClosable: true
        });

        handleClose();
        onValidationRequested?.();
      },
      {
        loadingMessage: "Soumission de la demande de validation...",
        errorMessage: "Impossible de soumettre la demande de validation"
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
            <Icon as={FiCheckCircle as ElementType} color="#3a8bfd" />
            <Text>Demander la validation du document</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody pb={6}>
          <VStack spacing={6} align="stretch">
            {/* Document concerné */}
            <Box>
              <Text fontSize="sm" color="gray.400" mb={2}>Document concerné</Text>
              <Box bg="#20243a" p={3} borderRadius="md" border="1px solid #3a8bfd">
                <Text fontWeight="semibold">{documentTitle}</Text>
              </Box>
            </Box>

            {/* Commentaire */}
            <FormControl>
              <FormLabel>Motif de la demande de validation (optionnel)</FormLabel>
              <Textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Précisez pourquoi ce document doit être validé..."
                bg="#20243a"
                resize="vertical"
                rows={4}
              />
            </FormControl>

            {/* Informations sur le processus */}
            <Alert status="info" variant="left-accent">
              <AlertIcon />
              <Box>
                <Text fontWeight="semibold">Processus de validation</Text>
                <Text fontSize="sm">
                  Cette demande sera soumise à validation par votre chef de service, 
                  puis par l'administrateur. Vous serez notifié des décisions.
                </Text>
              </Box>
            </Alert>

            {/* Boutons d'action */}
            <HStack justifyContent="flex-end" pt={4}>
              <Button variant="ghost" onClick={handleClose}>
                Annuler
              </Button>
              <Button 
                colorScheme="green"
                leftIcon={<Icon as={FiSend as ElementType} />}
                onClick={handleRequestValidation}
                isLoading={isLoading}
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

export default ValidationRequestModal; 