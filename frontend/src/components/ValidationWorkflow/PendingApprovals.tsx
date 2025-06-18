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
  Select
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
  FiAlertCircle
} from 'react-icons/fi';
import { PendingApprovalsProps, PendingApproval, ProcessApprovalRequest } from '../../types/workflow';
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
    setIsLoading(true);
    
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/validation-workflow/pending`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
          const data = await response.json();
          setApprovals(data.data || []);
        }
      },
      {
        loadingMessage: "Chargement des validations en attente...",
        errorMessage: "Impossible de charger les validations"
      }
    );
    
    setIsLoading(false);
  };

  const handleApprovalClick = (approval: PendingApproval) => {
    setSelectedApproval(approval);
    setDecision('');
    setComment('');
    onOpen();
  };

  const handleSubmitDecision = async () => {
    if (!selectedApproval || !decision) return;

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/validation-workflow/approve`, {
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
        } else {
          throw new Error('Erreur lors de l\'enregistrement');
        }
      },
      {
        loadingMessage: "Enregistrement de la décision...",
        errorMessage: "Impossible d'enregistrer la décision"
      }
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

  if (isLoading) {
    return (
      <Flex justify="center" align="center" h="200px">
        <Spinner size="lg" color="#3a8bfd" />
      </Flex>
    );
  }

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="md" color="white">
          Validations en attente ({approvals.length})
        </Heading>
        <Button
          leftIcon={<Icon as={asElementType(FiClock)} />}
          variant="outline"
          size="sm"
          onClick={loadPendingApprovals}
        >
          Actualiser
        </Button>
      </Flex>

      {approvals.length === 0 ? (
        <Alert status="info">
          <AlertIcon />
          Aucune validation en attente
        </Alert>
      ) : (
        <VStack spacing={4} align="stretch">
          {approvals.map((approval) => (
            <Card
              key={`${approval.instance_id}-${approval.etape_id}`}
              bg="#2a3657"
              borderColor={isOverdue(approval.date_echeance) ? "red.500" : "#3a445e"}
              borderWidth="1px"
              cursor="pointer"
              onClick={() => handleApprovalClick(approval)}
              _hover={{
                transform: "translateY(-2px)",
                boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                borderColor: "#3a8bfd"
              }}
              transition="all 0.2s"
            >
              <CardBody>
                <VStack align="stretch" spacing={3}>
                  <Flex justify="space-between" align="start">
                    <VStack align="start" spacing={1} flex={1}>
                      <HStack spacing={2} wrap="wrap">
                        <Heading size="sm" color="white">
                          {approval.document_titre}
                        </Heading>
                        <Badge colorScheme={getPriorityColor(approval.priorite)}>
                          {getPriorityLabel(approval.priorite)}
                        </Badge>
                        {isOverdue(approval.date_echeance) && (
                          <Badge colorScheme="red">
                            <Icon as={asElementType(FiAlertCircle)} mr={1} />
                            En retard
                          </Badge>
                        )}
                      </HStack>
                      
                      <Text fontSize="sm" color="gray.300">
                        {approval.workflow_nom} - {approval.etape_nom}
                      </Text>
                      
                      <HStack spacing={4} fontSize="xs" color="gray.400">
                        <HStack>
                          <Icon as={asElementType(FiUser)} />
                          <Text>{approval.initiateur_prenom} {approval.initiateur_nom}</Text>
                        </HStack>
                        <HStack>
                          <Icon as={asElementType(FiCalendar)} />
                          <Text>{formatDate(approval.date_creation)}</Text>
                        </HStack>
                        {approval.date_echeance && (
                          <HStack>
                            <Icon as={asElementType(FiClock)} />
                            <Text>Échéance: {formatDate(approval.date_echeance)}</Text>
                          </HStack>
                        )}
                      </HStack>
                    </VStack>
                    
                    <HStack>
                      <Button
                        size="sm"
                        colorScheme="green"
                        leftIcon={<Icon as={asElementType(FiCheck)} />}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedApproval(approval);
                          setDecision('APPROUVE');
                          setComment('');
                          onOpen();
                        }}
                      >
                        Approuver
                      </Button>
                      <Button
                        size="sm"
                        colorScheme="red"
                        leftIcon={<Icon as={asElementType(FiX)} />}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedApproval(approval);
                          setDecision('REJETE');
                          setComment('');
                          onOpen();
                        }}
                      >
                        Rejeter
                      </Button>
                    </HStack>
                  </Flex>
                  
                  {approval.description && (
                    <Text fontSize="sm" color="gray.300" fontStyle="italic">
                      {approval.description}
                    </Text>
                  )}
                </VStack>
              </CardBody>
            </Card>
          ))}
        </VStack>
      )}

      {/* Modal de confirmation */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent bg="#2a3657" color="white">
          <ModalHeader>
            {decision === 'APPROUVE' ? 'Approuver' : 'Rejeter'} le document
          </ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            {selectedApproval && (
              <VStack spacing={4} align="stretch">
                <Box p={3} bg="#1a2332" borderRadius="md">
                  <Text fontWeight="bold">{selectedApproval.document_titre}</Text>
                  <Text fontSize="sm" color="gray.400">
                    {selectedApproval.workflow_nom} - {selectedApproval.etape_nom}
                  </Text>
                  <Text fontSize="sm" color="gray.400">
                    Initié par {selectedApproval.initiateur_prenom} {selectedApproval.initiateur_nom}
                  </Text>
                </Box>
                
                <FormControl>
                  <FormLabel>Commentaire (optionnel)</FormLabel>
                  <Textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder={`Ajouter un commentaire pour ${decision === 'APPROUVE' ? 'l\'approbation' : 'le rejet'}...`}
                    bg="#1a2332"
                    borderColor="#3a445e"
                    _focus={{ borderColor: "#3a8bfd" }}
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
              leftIcon={<Icon as={asElementType(decision === 'APPROUVE' ? FiCheck : FiX)} />}
            >
              {decision === 'APPROUVE' ? 'Approuver' : 'Rejeter'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default PendingApprovals; 