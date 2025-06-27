/**
 * Bouton pour démarrer un workflow de validation de document
 */

import React, { useState, useEffect } from 'react';
import {
  Button,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Textarea,
  VStack,
  Text,
  Alert,
  AlertIcon,
  AlertDescription,
  useToast,
  Icon,
  HStack,
  Box
} from '@chakra-ui/react';
import { FiPlay, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';
import { ValidationWorkflowButtonProps } from '../../types/workflow';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import validationWorkflowService from '../../services/validationWorkflowService';
import { asElementType } from '../../utils/iconUtils';

const ValidationWorkflowButton: React.FC<ValidationWorkflowButtonProps> = ({
  documentId,
  documentTitle,
  onWorkflowStarted,
  disabled = false
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [commentaire, setCommentaire] = useState('');
  const [canStartWorkflow, setCanStartWorkflow] = useState(false);
  const [isCheckingStatus, setIsCheckingStatus] = useState(true);
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  useEffect(() => {
    checkWorkflowStatus();
  }, [documentId]);

  const checkWorkflowStatus = async () => {
    setIsCheckingStatus(true);
    try {
      const canStart = await validationWorkflowService.canStartWorkflow(documentId);
      setCanStartWorkflow(canStart);
    } catch (error) {
      console.error('Erreur lors de la vérification du statut:', error);
      setCanStartWorkflow(false);
    } finally {
      setIsCheckingStatus(false);
    }
  };

  const handleStartWorkflow = async () => {
    await executeOperation(
      async () => {
        const result = await validationWorkflowService.startValidationWorkflow({
          document_id: documentId,
          commentaire: commentaire.trim()
        });

        toast({
          title: 'Workflow démarré',
          description: `Le workflow de validation a été démarré avec succès pour "${documentTitle}"`,
          status: 'success',
          duration: 5000,
          isClosable: true
        });

        setIsModalOpen(false);
        setCommentaire('');
        setCanStartWorkflow(false);
        onWorkflowStarted?.();

        return result;
      },
      {
        loadingMessage: 'Démarrage du workflow de validation...',
        errorMessage: 'Impossible de démarrer le workflow de validation'
      }
    );
  };

  const handleOpenModal = () => {
    setIsModalOpen(true);
    setCommentaire('');
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setCommentaire('');
  };

  if (isCheckingStatus) {
    return (
      <Button
        size="sm"
        variant="outline"
        isLoading
        loadingText="Vérification..."
        disabled
      >
        Validation
      </Button>
    );
  }

  if (!canStartWorkflow) {
    return (
      <Button
        size="sm"
        variant="outline"
        disabled
        leftIcon={<Icon as={asElementType(FiCheckCircle)} />}
        colorScheme="gray"
      >
        Workflow en cours
      </Button>
    );
  }

  return (
    <>
      <Button
        size="sm"
        colorScheme="blue"
        variant="outline"
        leftIcon={<Icon as={asElementType(FiPlay)} />}
        onClick={handleOpenModal}
        disabled={disabled}
        _hover={{ bg: 'blue.50' }}
      >
        Demander validation
      </Button>

      <Modal isOpen={isModalOpen} onClose={handleCloseModal} size="lg">
        <ModalOverlay />
        <ModalContent bg="#232946" color="white">
          <ModalHeader>
            <HStack>
              <Icon as={asElementType(FiPlay)} color="#3a8bfd" />
              <Text>Démarrer la validation du document</Text>
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

              {/* Informations sur le processus */}
              <Alert status="info" variant="left-accent" bg="#232946" borderColor="#3a8bfd">
                <AlertIcon color="#3a8bfd" />
                <Box>
                  <Text fontWeight="semibold">Processus de validation</Text>
                  <Text fontSize="sm">
                    Ce document sera soumis à un processus de validation en 2 étapes :
                  </Text>
                  <VStack align="start" mt={2} spacing={1}>
                    <Text fontSize="sm">• <strong>Étape 1 :</strong> Validation par un chef de service</Text>
                    <Text fontSize="sm">• <strong>Étape 2 :</strong> Validation finale par un directeur</Text>
                  </VStack>
                  <Text fontSize="sm" mt={2} color="gray.300">
                    Les approbateurs seront automatiquement notifiés à chaque étape.
                  </Text>
                </Box>
              </Alert>

              {/* Commentaire */}
              <FormControl>
                <FormLabel>Commentaire (optionnel)</FormLabel>
                <Textarea
                  value={commentaire}
                  onChange={(e) => setCommentaire(e.target.value)}
                  placeholder="Ajoutez un commentaire sur cette demande de validation..."
                  bg="#20243a"
                  borderColor="#232946"
                  resize="vertical"
                  rows={4}
                  _focus={{ borderColor: "#3a8bfd", boxShadow: "0 0 0 1.5px #3a8bfd" }}
                />
              </FormControl>

              {/* Avertissement */}
              <Alert status="warning" variant="left-accent" bg="#232946" borderColor="orange.400">
                <AlertIcon color="orange.400" />
                <AlertDescription>
                  Une fois démarré, le workflow ne peut pas être annulé. 
                  Le document sera marqué comme "En validation" jusqu'à la fin du processus.
                </AlertDescription>
              </Alert>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <HStack spacing={3}>
              <Button variant="ghost" onClick={handleCloseModal}>
                Annuler
              </Button>
              <Button 
                colorScheme="blue"
                leftIcon={<Icon as={asElementType(FiPlay)} />}
                onClick={handleStartWorkflow}
              >
                Démarrer la validation
              </Button>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default ValidationWorkflowButton; 

