import React, { useState, useEffect } from 'react';
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
  Select,
  Textarea,
  Text,
  Alert,
  AlertIcon,
  Box,
  Badge,
  Divider,
  useToast,
  Icon
} from '@chakra-ui/react';
import { FiPlay, FiUsers, FiClock } from 'react-icons/fi';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import { checkAuthToken } from '../../utils/errorHandling';
import { API_URL } from '../../config';

// Helper component pour les icônes
const IconWrapper: React.FC<{ icon: any; color?: string }> = ({ icon: IconComponent, color }) => (
  <Icon as={IconComponent} color={color} />
);

interface WorkflowTemplate {
  id: number;
  nom: string;
  description: string;
  statut: string;
  etapes?: Array<{
    nom: string;
    description: string;
    type_approbation: string;
    delai_max?: number;
    approbateurs_count: number;
  }>;
}

interface StartWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number;
  documentTitle: string;
  onWorkflowStarted?: () => void;
}

const StartWorkflowModal: React.FC<StartWorkflowModalProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  onWorkflowStarted
}) => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  const [workflows, setWorkflows] = useState<WorkflowTemplate[]>([]);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string>('');
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowTemplate | null>(null);
  const [comment, setComment] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadWorkflows();
    }
  }, [isOpen]);

  useEffect(() => {
    if (selectedWorkflowId) {
      loadWorkflowDetails(parseInt(selectedWorkflowId));
    } else {
      setSelectedWorkflow(null);
    }
  }, [selectedWorkflowId]);

  const loadWorkflows = async () => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        const response = await fetch(`${API_URL}/api/workflows`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
          throw new Error('Erreur lors du chargement des workflows');
        }

        const data = await response.json();
        setWorkflows(data.filter((w: WorkflowTemplate) => w.statut === 'ACTIVE'));
      },
      {
        loadingMessage: "Chargement des workflows...",
        errorMessage: "Impossible de charger les workflows"
      }
    );
  };

  const loadWorkflowDetails = async (workflowId: number) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        const response = await fetch(`${API_URL}/api/workflows/${workflowId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
          throw new Error('Erreur lors du chargement des détails');
        }

        const data = await response.json();
        setSelectedWorkflow(data);
      },
      {
        errorMessage: "Impossible de charger les détails du workflow"
      }
    );
  };

  const handleStartWorkflow = async () => {
    if (!selectedWorkflowId) {
      toast({
        title: 'Erreur',
        description: 'Veuillez sélectionner un workflow',
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
        
        const response = await fetch(`${API_URL}/api/documents/${documentId}/workflows`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            workflow_id: parseInt(selectedWorkflowId),
            commentaire: comment.trim() || undefined
          })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Erreur lors du démarrage du workflow');
        }

        toast({
          title: 'Succès',
          description: 'Workflow démarré avec succès',
          status: 'success',
          duration: 5000,
          isClosable: true
        });

        handleClose();
        onWorkflowStarted?.();
      },
      {
        loadingMessage: "Démarrage du workflow...",
        errorMessage: "Impossible de démarrer le workflow"
      }
    );

    setIsLoading(false);
  };

  const handleClose = () => {
    setSelectedWorkflowId('');
    setSelectedWorkflow(null);
    setComment('');
    onClose();
  };

  const getTypeApproLabel = (type: string) => {
    switch (type) {
      case 'SIMPLE': return 'Simple';
      case 'MULTIPLE': return 'Multiple';
      case 'PARALLELE': return 'Parallèle';
      default: return type;
    }
  };

  const getTypeApproColor = (type: string) => {
    switch (type) {
      case 'SIMPLE': return 'green';
      case 'MULTIPLE': return 'blue';
      case 'PARALLELE': return 'orange';
      default: return 'gray';
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="xl">
      <ModalOverlay />
      <ModalContent bg="#232946" color="white">
        <ModalHeader>
          <HStack>
            <IconWrapper icon={FiPlay} color="#3a8bfd" />
            <Text>Démarrer un workflow</Text>
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

            {/* Sélection du workflow */}
            <FormControl>
              <FormLabel>Workflow à utiliser *</FormLabel>
              <Select
                value={selectedWorkflowId}
                onChange={(e) => setSelectedWorkflowId(e.target.value)}
                placeholder="Sélectionnez un workflow..."
                bg="#20243a"
              >
                {workflows.map((workflow) => (
                  <option key={workflow.id} value={workflow.id}>
                    {workflow.nom}
                  </option>
                ))}
              </Select>
              {workflows.length === 0 && (
                <Alert status="warning" mt={2}>
                  <AlertIcon />
                  Aucun workflow actif disponible
                </Alert>
              )}
            </FormControl>

            {/* Détails du workflow sélectionné */}
            {selectedWorkflow && (
              <Box bg="#20243a" p={4} borderRadius="md" border="1px solid #444">
                <VStack spacing={4} align="stretch">
                  <Box>
                    <Text fontWeight="semibold" mb={2}>{selectedWorkflow.nom}</Text>
                    {selectedWorkflow.description && (
                      <Text fontSize="sm" color="gray.300">
                        {selectedWorkflow.description}
                      </Text>
                    )}
                  </Box>

                  {selectedWorkflow.etapes && selectedWorkflow.etapes.length > 0 && (
                    <>
                      <Divider />
                      <Box>
                        <Text fontSize="sm" fontWeight="semibold" mb={3}>
                          Étapes du processus ({selectedWorkflow.etapes.length})
                        </Text>
                        <VStack spacing={3} align="stretch">
                          {selectedWorkflow.etapes.map((etape, index) => (
                            <Box
                              key={index}
                              bg="#232946"
                              p={3}
                              borderRadius="md"
                              border="1px solid #333"
                            >
                              <HStack justify="space-between" align="flex-start" mb={2}>
                                <VStack align="flex-start" spacing={1}>
                                  <HStack>
                                    <Badge size="sm" colorScheme="blue">
                                      Étape {index + 1}
                                    </Badge>
                                    <Text fontSize="sm" fontWeight="semibold">
                                      {etape.nom}
                                    </Text>
                                  </HStack>
                                  {etape.description && (
                                    <Text fontSize="xs" color="gray.400">
                                      {etape.description}
                                    </Text>
                                  )}
                                </VStack>
                                <VStack align="flex-end" spacing={1}>
                                  <Badge
                                    size="sm"
                                    colorScheme={getTypeApproColor(etape.type_approbation)}
                                  >
                                    {getTypeApproLabel(etape.type_approbation)}
                                  </Badge>
                                </VStack>
                              </HStack>
                              
                              <HStack spacing={4} fontSize="xs" color="gray.400">
                                <HStack>
                                  <IconWrapper icon={FiUsers} />
                                  <Text>{etape.approbateurs_count} approbateur(s)</Text>
                                </HStack>
                                {etape.delai_max && (
                                  <HStack>
                                    <IconWrapper icon={FiClock} />
                                    <Text>{etape.delai_max}h max</Text>
                                  </HStack>
                                )}
                              </HStack>
                            </Box>
                          ))}
                        </VStack>
                      </Box>
                    </>
                  )}
                </VStack>
              </Box>
            )}

            {/* Commentaire optionnel */}
            <FormControl>
              <FormLabel>Commentaire (optionnel)</FormLabel>
              <Textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Ajoutez un commentaire pour expliquer le contexte..."
                bg="#20243a"
                rows={3}
              />
            </FormControl>

            {/* Boutons d'action */}
            <HStack justify="flex-end" pt={4}>
              <Button variant="ghost" onClick={handleClose}>
                Annuler
              </Button>
              <Button
                colorScheme="blue"
                leftIcon={<IconWrapper icon={FiPlay} />}
                onClick={handleStartWorkflow}
                isLoading={isLoading}
                isDisabled={!selectedWorkflowId || workflows.length === 0}
              >
                Démarrer le workflow
              </Button>
            </HStack>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default StartWorkflowModal; 



