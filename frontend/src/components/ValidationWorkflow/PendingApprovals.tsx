/**
 * Composant pour afficher et traiter les approbations en attente
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardBody,
  Badge,
  Button,
  Icon,
  Divider,
  Alert,
  AlertIcon,
  AlertDescription,
  Spinner,
  Center,
  useToast,
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
  ButtonGroup,
  Flex,
  Spacer,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useDisclosure,
  Select,
  Tooltip,
  Progress
} from '@chakra-ui/react';
import {
  FiClock,
  FiCheckCircle,
  FiXCircle,
  FiUser,
  FiCalendar,
  FiFileText,
  FiRefreshCw,
  FiCheck,
  FiX,
  FiAlertCircle,
  FiUsers
} from 'react-icons/fi';
import { PendingApprovalsProps, PendingApproval } from '../../types/workflow';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import validationWorkflowService from '../../services/validationWorkflowService';
import { asElementType } from '../../utils/iconUtils';
import { checkAuthToken } from '../../utils/errorHandling';
import { API_URL } from '../../config';

interface ApprovalModalData {
  approval: PendingApproval;
  decision: 'APPROUVE' | 'REJETE';
}

const PendingApprovals: React.FC<PendingApprovalsProps> = ({
  userId,
  onApprovalProcessed
}) => {
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<PendingApproval | null>(null);
  const [decision, setDecision] = useState<'APPROUVE' | 'REJETE' | ''>('');
  const [comment, setComment] = useState('');
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

  useEffect(() => {
    loadPendingApprovals();
  }, [userId]);

  const loadPendingApprovals = async () => {
    console.log('🔍 loadPendingApprovals: Début du chargement des validations en attente');
    console.log('🔍 userId:', userId);
    setIsLoading(true);
    
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        console.log('🔍 Token récupéré:', token ? 'Présent' : 'Absent');
        
        const url = `${API_URL}/api/validation-workflow/pending`;
        console.log('🔍 URL appelée:', url);
        
        const response = await fetch(url, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        console.log('🔍 Réponse API:', response.status, response.statusText);
        
        if (response.ok) {
          const data = await response.json();
          console.log('🔍 Données reçues:', data);
          setApprovals(data.data || []);
        } else {
          console.error('❌ Erreur API:', response.status, response.statusText);
          const errorText = await response.text();
          console.error('❌ Détails erreur:', errorText);
          throw new Error('Erreur lors du chargement des validations');
        }
      },
      {
        loadingMessage: "Chargement des validations en attente...",
        errorMessage: "Impossible de charger les validations",
        onError: (error) => {
          toast({
            title: "Erreur de chargement",
            description: error.message,
            status: "error",
            duration: 5000,
            isClosable: true,
          });
        }
      }
    );
    
    setIsLoading(false);
    console.log('🔍 loadPendingApprovals: Fin du chargement');
  };

  const handleApprovalClick = (approval: PendingApproval) => {
    setSelectedApproval(approval);
    setDecision('');
    setComment('');
    onOpen();
  };

  const handleSubmitDecision = async () => {
    if (!selectedApproval || !decision) {
      toast({
        title: "Erreur",
        description: "Veuillez sélectionner une décision",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/validation-workflow/approve`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            instance_id: selectedApproval.instance_id,
            etape_id: selectedApproval.etape_id,
            decision: decision,
            commentaire: comment
          })
        });

        if (response.ok) {
          toast({
            title: "Décision enregistrée",
            description: `Document ${decision === 'APPROUVE' ? 'approuvé' : 'rejeté'} avec succès`,
            status: "success",
            duration: 5000,
            isClosable: true,
          });
          
          onClose();
          loadPendingApprovals();
          if (onApprovalProcessed) {
            onApprovalProcessed();
          }
        } else {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Erreur lors de l\'enregistrement');
        }
      },
      {
        loadingMessage: "Enregistrement de la décision...",
        errorMessage: "Impossible d'enregistrer la décision"
      }
    );
  };

  const getApprovalTypeInfo = (type: string) => {
    switch (type) {
      case 'SIMPLE':
        return {
          icon: FiCheck,
          label: 'Approbation simple',
          description: 'Une seule approbation requise',
          color: 'green'
        };
      case 'MULTIPLE':
        return {
          icon: FiUsers,
          label: 'Approbation multiple',
          description: 'Plusieurs approbations requises',
          color: 'blue'
        };
      case 'PARALLELE':
        return {
          icon: FiUsers,
          label: 'Approbation parallèle',
          description: 'Approbations simultanées requises',
          color: 'purple'
        };
      default:
        return {
          icon: FiAlertCircle,
          label: 'Type inconnu',
          description: 'Type d\'approbation non reconnu',
          color: 'gray'
        };
    }
  };

  const renderApprovalProgress = (approval: PendingApproval) => {
    const progress = (approval.approbations_count / approval.approbations_necessaires) * 100;
    return (
      <Tooltip
        label={`${approval.approbations_count}/${approval.approbations_necessaires} approbation(s)`}
        placement="top"
      >
        <Box w="100%">
          <Progress
            value={progress}
            size="sm"
            colorScheme={progress >= 100 ? "green" : "blue"}
            borderRadius="full"
          />
          <Text fontSize="sm" mt={1}>
            {approval.approbations_count}/{approval.approbations_necessaires} approbation(s)
          </Text>
        </Box>
      </Tooltip>
    );
  };

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 4: return 'red';
      case 3: return 'orange';
      case 2: return 'yellow';
      default: return 'blue';
    }
  };

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 4: return 'Urgent';
      case 3: return 'Haute';
      case 2: return 'Normale';
      default: return 'Basse';
    }
  };

  const isOverdue = (dateEcheance: string | undefined) => {
    if (!dateEcheance) return false;
    return new Date(dateEcheance) < new Date();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const createTestWorkflow = async () => {
    console.log('🔍 Création d\'un workflow de test...');
    
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/validation-workflow/create-test`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('🔍 Workflow de test créé:', data);
          toast({
            title: "Workflow de test créé",
            description: data.message,
            status: "success",
            duration: 5000,
            isClosable: true,
          });
          
          // Recharger les validations
          loadPendingApprovals();
        } else {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Erreur lors de la création du workflow de test');
        }
      },
      {
        loadingMessage: "Création du workflow de test...",
        errorMessage: "Impossible de créer le workflow de test"
      }
    );
  };

  if (isLoading) {
    return (
      <Flex justify="center" align="center" h="200px">
        <Spinner size="lg" color="#3a8bfd" />
      </Flex>
    );
  }

  if (!approvals.length) {
    return (
      <Alert status="info" borderRadius="md">
        <AlertIcon />
        <AlertDescription>Aucune validation en attente</AlertDescription>
      </Alert>
    );
  }

  return (
    <VStack spacing={4} align="stretch" w="100%">
      <Flex align="center" mb={4}>
        <Heading size="md">Validations en attente ({approvals.length})</Heading>
        <Spacer />
        <Button
          leftIcon={<Icon as={FiRefreshCw} />}
          onClick={loadPendingApprovals}
          colorScheme="blue"
          variant="outline"
          size="sm"
        >
          Actualiser
        </Button>
      </Flex>

      {approvals.map((approval) => {
        const typeInfo = getApprovalTypeInfo(approval.type_approbation);
        const isLate = isOverdue(approval.date_echeance);

        return (
          <Card key={`${approval.instance_id}-${approval.etape_id}`} variant="outline">
            <CardBody>
              <VStack align="stretch" spacing={3}>
                <Flex align="center" justify="space-between">
                  <HStack>
                    <Icon as={FiFileText} color="blue.500" boxSize={5} />
                    <Text fontWeight="bold">{approval.document_titre}</Text>
                    <Tooltip label={typeInfo.description}>
                      <Badge colorScheme={typeInfo.color} variant="subtle">
                        <HStack spacing={1}>
                          <Icon as={typeInfo.icon} />
                          <Text>{typeInfo.label}</Text>
                        </HStack>
                      </Badge>
                    </Tooltip>
                  </HStack>
                  {isLate && (
                    <Badge colorScheme="red">
                      <HStack spacing={1}>
                        <Icon as={FiClock} />
                        <Text>En retard</Text>
                      </HStack>
                    </Badge>
                  )}
                </Flex>

                <Divider />

                <HStack spacing={4}>
                  <VStack align="start" flex={1}>
                    <Text fontSize="sm" color="gray.600">
                      <Icon as={FiUser} mr={2} />
                      Initiateur: {approval.initiateur_nom} {approval.initiateur_prenom}
                    </Text>
                    <Text fontSize="sm" color="gray.600">
                      <Icon as={FiCalendar} mr={2} />
                      Date début: {formatDate(approval.date_debut)}
                    </Text>
                  </VStack>

                  <VStack align="start" flex={1}>
                    <Text fontSize="sm" color="gray.600">
                      Étape: {approval.etape_nom}
                    </Text>
                    {renderApprovalProgress(approval)}
                  </VStack>
                </HStack>

                <ButtonGroup spacing={2} alignSelf="flex-end">
                  <Button
                    leftIcon={<Icon as={FiXCircle} />}
                    colorScheme="red"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setDecision('REJETE');
                      handleApprovalClick(approval);
                    }}
                  >
                    Rejeter
                  </Button>
                  <Button
                    leftIcon={<Icon as={FiCheckCircle} />}
                    colorScheme="green"
                    onClick={() => {
                      setDecision('APPROUVE');
                      handleApprovalClick(approval);
                    }}
                    size="sm"
                  >
                    Approuver
                  </Button>
                </ButtonGroup>
              </VStack>
            </CardBody>
          </Card>
        );
      })}

      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {decision === 'APPROUVE' ? 'Approuver le document' : 'Rejeter le document'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedApproval && (
              <VStack align="stretch" spacing={4}>
                <Text>
                  Document : <strong>{selectedApproval.document_titre}</strong>
                </Text>
                <Text>
                  Étape : <strong>{selectedApproval.etape_nom}</strong>
                </Text>
                <FormControl>
                  <FormLabel>Commentaire</FormLabel>
                  <Textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Ajouter un commentaire (optionnel)"
                  />
                </FormControl>
              </VStack>
            )}
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Annuler
            </Button>
            <Button
              colorScheme={decision === 'APPROUVE' ? 'green' : 'red'}
              onClick={handleSubmitDecision}
            >
              {decision === 'APPROUVE' ? 'Approuver' : 'Rejeter'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  );
};

export default PendingApprovals; 


