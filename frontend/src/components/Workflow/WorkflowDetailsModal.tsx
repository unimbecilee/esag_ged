import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  Button,
  Box,
  Text,
  VStack,
  HStack,
  Badge,
  Divider,
  Heading,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Grid,
  GridItem,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Icon,
  useToast,
  Skeleton
} from '@chakra-ui/react';
import { 
  FiUsers, 
  FiCalendar, 
  FiClock, 
  FiCheckCircle, 
  FiXCircle,
  FiAlertCircle
} from 'react-icons/fi';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import { checkAuthToken } from '../../utils/errorHandling';
import { API_URL } from '../../config';

// Helper component pour les icônes
const IconWrapper: React.FC<{ icon: any; color?: string }> = ({ icon: IconComponent, color }) => (
  <Icon as={IconComponent} color={color} />
);

interface WorkflowEtape {
  id: number;
  nom: string;
  description: string;
  ordre: number;
  type_approbation: string;
  delai_max?: number;
  approbateurs_count: number;
}

interface WorkflowDetails {
  id: number;
  nom: string;
  description: string;
  date_creation: string;
  statut: string;
  createur_nom: string;
  createur_prenom: string;
  instances_count: number;
  etapes: WorkflowEtape[];
}

interface WorkflowDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowId: number | null;
}

const WorkflowDetailsModal: React.FC<WorkflowDetailsModalProps> = ({ 
  isOpen, 
  onClose, 
  workflowId 
}) => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const [workflow, setWorkflow] = useState<WorkflowDetails | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen && workflowId) {
      loadWorkflowDetails(workflowId);
    }
  }, [isOpen, workflowId]);

  const loadWorkflowDetails = async (id: number) => {
    setIsLoading(true);

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        // Charger les détails du workflow
        console.log(`Chargement des détails du workflow ${id}`);
        const workflowResponse = await fetch(`${API_URL}/api/workflows/${id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!workflowResponse.ok) {
          throw new Error('Erreur lors du chargement des détails du workflow');
        }
        
        const workflowData = await workflowResponse.json();
        console.log('Détails du workflow chargés:', workflowData);
        
        // Charger les étapes du workflow
        console.log(`Chargement des étapes du workflow ${id}`);
        const etapesResponse = await fetch(`${API_URL}/api/workflows/${id}/etapes`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        console.log('Statut de la réponse étapes:', etapesResponse.status);
        if (!etapesResponse.ok) {
          const errorText = await etapesResponse.text();
          console.error('Erreur étapes:', errorText);
          throw new Error('Erreur lors du chargement des étapes du workflow');
        }
        
        const etapesData = await etapesResponse.json();
        console.log('Étapes chargées:', etapesData);
        
        // Combiner les données
        setWorkflow({
          ...workflowData,
          etapes: etapesData
        });
      },
      {
        errorMessage: "Impossible de charger les détails du workflow"
      }
    );
    
    setIsLoading(false);
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

  const handleClose = () => {
    setWorkflow(null);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent bg="#232946" color="white">
        <ModalHeader>
          {isLoading ? (
            <Skeleton height="30px" width="200px" />
          ) : (
            <HStack>
              <IconWrapper icon={FiClock} color="#3a8bfd" />
              <Text>Détails du workflow</Text>
            </HStack>
          )}
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody pb={6}>
          {isLoading ? (
            <VStack spacing={4} align="stretch">
              <Skeleton height="40px" />
              <Skeleton height="20px" />
              <Skeleton height="100px" />
              <Skeleton height="200px" />
            </VStack>
          ) : workflow ? (
            <VStack spacing={6} align="stretch">
              {/* En-tête du workflow */}
              <Box>
                <Heading size="md" mb={2}>{workflow.nom}</Heading>
                <Text color="gray.300">{workflow.description || 'Aucune description'}</Text>
              </Box>
              
              {/* Informations générales */}
              <Grid templateColumns="repeat(3, 1fr)" gap={4}>
                <GridItem>
                  <Stat>
                    <StatLabel color="gray.400">Statut</StatLabel>
                    <StatNumber>
                      <Badge colorScheme={workflow.statut === 'ACTIVE' ? 'green' : 'gray'} fontSize="0.9em">
                        {workflow.statut || 'Non défini'}
                      </Badge>
                    </StatNumber>
                  </Stat>
                </GridItem>
                
                <GridItem>
                  <Stat>
                    <StatLabel color="gray.400">Créé par</StatLabel>
                    <StatNumber fontSize="md" color="white">
                      {workflow.createur_prenom} {workflow.createur_nom}
                    </StatNumber>
                    <StatHelpText>
                      {new Date(workflow.date_creation).toLocaleDateString('fr-FR')}
                    </StatHelpText>
                  </Stat>
                </GridItem>
                
                <GridItem>
                  <Stat>
                    <StatLabel color="gray.400">Instances</StatLabel>
                    <StatNumber color="#3a8bfd">{workflow.instances_count}</StatNumber>
                    <StatHelpText>utilisations totales</StatHelpText>
                  </Stat>
                </GridItem>
              </Grid>
              
              <Divider />
              
              {/* Étapes du workflow */}
              <Box>
                <Heading size="sm" mb={4}>
                  Étapes du workflow ({workflow.etapes?.length || 0})
                </Heading>
                
                {workflow.etapes?.length > 0 ? (
                  <VStack spacing={4} align="stretch">
                    {workflow.etapes.map((etape, index) => (
                      <Box 
                        key={etape.id}
                        bg="#20243a" 
                        p={4} 
                        borderRadius="md"
                        borderLeft="4px solid"
                        borderLeftColor="#3a8bfd"
                      >
                        <HStack justify="space-between" mb={2}>
                          <HStack>
                            <Badge colorScheme="blue">Étape {etape.ordre}</Badge>
                            <Text fontWeight="semibold">{etape.nom}</Text>
                          </HStack>
                          <Badge colorScheme={getTypeApproColor(etape.type_approbation)}>
                            {getTypeApproLabel(etape.type_approbation)}
                          </Badge>
                        </HStack>
                        
                        {etape.description && (
                          <Text color="gray.300" fontSize="sm" mb={3}>
                            {etape.description}
                          </Text>
                        )}
                        
                        <HStack mt={2} spacing={4}>
                          <HStack>
                            <IconWrapper icon={FiUsers} color="gray.400" />
                            <Text color="gray.300" fontSize="sm">
                              {etape.approbateurs_count} approbateur{etape.approbateurs_count > 1 ? 's' : ''}
                            </Text>
                          </HStack>
                          
                          {etape.delai_max && (
                            <HStack>
                              <IconWrapper icon={FiClock} color="gray.400" />
                              <Text color="gray.300" fontSize="sm">
                                {etape.delai_max} jour{etape.delai_max > 1 ? 's' : ''}
                              </Text>
                            </HStack>
                          )}
                        </HStack>
                      </Box>
                    ))}
                  </VStack>
                ) : (
                  <Box textAlign="center" py={4} bg="#20243a" borderRadius="md">
                    <IconWrapper icon={FiAlertCircle} color="gray.400" />
                    <Text color="gray.400" mt={2}>Ce workflow ne contient aucune étape</Text>
                  </Box>
                )}
              </Box>
            </VStack>
          ) : (
            <Box textAlign="center" py={6}>
              <Text color="gray.400">Aucun workflow sélectionné</Text>
            </Box>
          )}
        </ModalBody>
        
        <ModalFooter>
          <Button onClick={handleClose}>
            Fermer
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default WorkflowDetailsModal; 


