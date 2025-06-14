import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Text,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Card,
  CardBody,
  CardHeader,
  Flex,
  Skeleton,
  Alert,
  AlertIcon,
  useToast,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Grid,
  GridItem,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Icon
} from '@chakra-ui/react';
import {
  AddIcon,
  SearchIcon,
  EditIcon,
  DeleteIcon,
  ViewIcon,
  ChevronDownIcon
} from '@chakra-ui/icons';
import {
  FiPlay,
  FiPause,
  FiCheck,
  FiX,
  FiClock,
  FiUsers,
  FiFileText,
  FiBarChart
} from 'react-icons/fi';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import { checkAuthToken } from '../../utils/errorHandling';
import { API_URL } from '../../config';
import CreateWorkflowModal from './CreateWorkflowModal';
import WorkflowDetailsModal from './WorkflowDetailsModal';

// Helper component pour les icônes
const IconWrapper: React.FC<{ icon: any; color?: string }> = ({ icon: IconComponent, color }) => (
  <Icon as={IconComponent} color={color} />
);

interface WorkflowTemplate {
  id: number;
  nom: string;
  description: string;
  date_creation: string;
  statut: string | null;
  createur_nom: string;
  createur_prenom: string;
  instances_count: number;
}

interface WorkflowInstance {
  id: number;
  workflow_nom: string;
  document_titre: string;
  statut: string;
  etape_courante_nom: string;
  initiateur_nom: string;
  initiateur_prenom: string;
  date_debut: string;
  date_fin?: string;
}

interface PendingApproval {
  id: number;
  workflow_nom: string;
  document_titre: string;
  etape_courante_nom: string;
  initiateur_nom: string;
  initiateur_prenom: string;
  date_debut: string;
}

const WorkflowManagement: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const { isOpen: isCreateModalOpen, onOpen: onCreateModalOpen, onClose: onCreateModalClose } = useDisclosure();
  const { isOpen: isDetailsModalOpen, onOpen: onDetailsModalOpen, onClose: onDetailsModalClose } = useDisclosure();

  // États principaux
  const [workflowTemplates, setWorkflowTemplates] = useState<WorkflowTemplate[]>([]);
  const [workflowInstances, setWorkflowInstances] = useState<WorkflowInstance[]>([]);
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<number | null>(null);

  // États de filtrage
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Statistiques
  const [stats, setStats] = useState({
    totalWorkflows: 0,
    activeInstances: 0,
    pendingApprovals: 0,
    completedToday: 0
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    
    await executeOperation(
      async () => {
        const token = checkAuthToken();

        // Charger les modèles de workflow
        const templatesResponse = await fetch(`${API_URL}/workflows`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (templatesResponse.ok) {
          const templates = await templatesResponse.json();
          setWorkflowTemplates(templates);
        }

        // Charger les approbations en attente
        const approvalsResponse = await fetch(`${API_URL}/workflow-instances/pending`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (approvalsResponse.ok) {
          const approvals = await approvalsResponse.json();
          setPendingApprovals(approvals);
        }

        // Calculer les statistiques
        const totalWorkflows = workflowTemplates.length;
        const pendingApprovalsCount = pendingApprovals.length;
        
        setStats({
          totalWorkflows,
          activeInstances: 0, // À implémenter
          pendingApprovals: pendingApprovalsCount,
          completedToday: 0 // À implémenter
        });
      },
      {
        loadingMessage: "Chargement des workflows...",
        errorMessage: "Impossible de charger les workflows"
      }
    );
    
    setIsLoading(false);
  };

  const handleViewWorkflowDetails = (workflowId: number) => {
    setSelectedWorkflowId(workflowId);
    onDetailsModalOpen();
  };

  const handleDeleteWorkflow = async (workflowId: number) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        const response = await fetch(`${API_URL}/workflows/${workflowId}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Erreur lors de la suppression');
        }

        // Mettre à jour la liste des workflows
        setWorkflowTemplates(workflowTemplates.filter(w => w.id !== workflowId));
        
        toast({
          title: 'Succès',
          description: 'Workflow supprimé avec succès',
          status: 'success',
          duration: 5000,
          isClosable: true
        });
      },
      {
        loadingMessage: "Suppression du workflow...",
        errorMessage: "Impossible de supprimer le workflow"
      }
    );
  };

  const handleApprove = async (instanceId: number) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        const response = await fetch(`${API_URL}/workflow-instances/${instanceId}/approve`, {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({})
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Erreur lors de l\'approbation');
        }

        toast({
          title: 'Succès',
          description: 'Étape approuvée avec succès',
          status: 'success',
          duration: 5000,
          isClosable: true
        });

        loadData();
      },
      {
        loadingMessage: "Approbation en cours...",
        errorMessage: "Impossible d'approuver l'étape"
      }
    );
  };

  const handleReject = async (instanceId: number) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        const response = await fetch(`${API_URL}/workflow-instances/${instanceId}/reject`, {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({})
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Erreur lors du rejet');
        }

        toast({
          title: 'Workflow rejeté',
          description: 'L\'étape a été rejetée',
          status: 'warning',
          duration: 5000,
          isClosable: true
        });

        loadData();
      },
      {
        loadingMessage: "Rejet en cours...",
        errorMessage: "Impossible de rejeter l'étape"
      }
    );
  };

  const getStatusBadgeColor = (status: string | null) => {
    if (!status) return 'gray';
    switch (status.toUpperCase()) {
      case 'EN_COURS': return 'blue';
      case 'TERMINE': return 'green';
      case 'REJETE': return 'red';
      case 'ANNULE': return 'gray';
      case 'ACTIVE': return 'green';
      case 'INACTIVE': return 'gray';
      default: return 'gray';
    }
  };

  const filteredTemplates = workflowTemplates.filter(template => {
    const matchesSearch = template.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || (template.statut && template.statut.toLowerCase() === statusFilter.toLowerCase());
    return matchesSearch && matchesStatus;
  });

  return (
    <Box p={6}>
      <VStack spacing={6} align="stretch">
        {/* En-tête */}
        <Flex justify="space-between" align="center">
          <Heading color="white">Gestion des workflows</Heading>
          <Button
            leftIcon={<AddIcon />}
            colorScheme="blue"
            onClick={onCreateModalOpen}
          >
            Nouveau workflow
          </Button>
        </Flex>

        {/* Statistiques */}
        <Grid templateColumns="repeat(4, 1fr)" gap={4}>
          <GridItem>
            <Card bg="#20243a" borderColor="#3a8bfd">
              <CardBody>
                <Stat>
                  <StatLabel color="white">Workflows totaux</StatLabel>
                  <StatNumber color="#3a8bfd">{stats.totalWorkflows}</StatNumber>
                  <StatHelpText color="gray.400">Modèles créés</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </GridItem>
          
          <GridItem>
            <Card bg="#20243a" borderColor="#3a8bfd">
              <CardBody>
                <Stat>
                  <StatLabel color="white">Instances actives</StatLabel>
                  <StatNumber color="orange.400">{stats.activeInstances}</StatNumber>
                  <StatHelpText color="gray.400">En cours</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </GridItem>
          
          <GridItem>
            <Card bg="#20243a" borderColor="#3a8bfd">
              <CardBody>
                <Stat>
                  <StatLabel color="white">En attente d'approbation</StatLabel>
                  <StatNumber color="yellow.400">{stats.pendingApprovals}</StatNumber>
                  <StatHelpText color="gray.400">À traiter</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </GridItem>
          
          <GridItem>
            <Card bg="#20243a" borderColor="#3a8bfd">
              <CardBody>
                <Stat>
                  <StatLabel color="white">Terminés aujourd'hui</StatLabel>
                  <StatNumber color="green.400">{stats.completedToday}</StatNumber>
                  <StatHelpText color="gray.400">Workflows complétés</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </GridItem>
        </Grid>

        {/* Onglets principaux */}
        <Tabs colorScheme="blue" variant="enclosed">
          <TabList>
            <Tab color="white" _selected={{ color: "white", bg: "#3a8bfd" }}>
              Modèles de workflows
            </Tab>
            <Tab color="white" _selected={{ color: "white", bg: "#3a8bfd" }}>
              Mes approbations ({pendingApprovals.length})
            </Tab>
            <Tab color="white" _selected={{ color: "white", bg: "#3a8bfd" }}>
              Instances actives
            </Tab>
          </TabList>

          <TabPanels>
            {/* Onglet Modèles de workflows */}
            <TabPanel p={0} pt={4}>
              <VStack spacing={4} align="stretch">
                {/* Filtres */}
                <HStack spacing={4}>
                  <InputGroup flex={1}>
                    <InputLeftElement pointerEvents="none">
                      <SearchIcon color="gray.300" />
                    </InputLeftElement>
                    <Input
                      placeholder="Rechercher un workflow..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      bg="#20243a"
                      color="white"
                    />
                  </InputGroup>
                  
                  <Select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    bg="#20243a"
                    color="white"
                    w="200px"
                  >
                    <option value="all">Tous les statuts</option>
                    <option value="active">Actif</option>
                    <option value="inactive">Inactif</option>
                  </Select>
                </HStack>

                {/* Table des workflows */}
                <Box bg="#20243a" borderRadius="lg" overflow="hidden">
                  {isLoading ? (
                    <VStack p={6} spacing={4}>
                      {[...Array(5)].map((_, i) => (
                        <Skeleton key={i} height="60px" width="100%" />
                      ))}
                    </VStack>
                  ) : filteredTemplates.length === 0 ? (
                    <Box textAlign="center" py={8}>
                      <Text color="gray.400">Aucun workflow trouvé</Text>
                    </Box>
                  ) : (
                    <Table variant="simple">
                      <Thead bg="#232946">
                        <Tr>
                          <Th color="white">Nom</Th>
                          <Th color="white">Description</Th>
                          <Th color="white">Créateur</Th>
                          <Th color="white">Statut</Th>
                          <Th color="white">Instances</Th>
                          <Th color="white">Créé le</Th>
                          <Th color="white">Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {filteredTemplates.map((workflow) => (
                          <Tr key={workflow.id}>
                            <Td color="white" fontWeight="semibold">
                              {workflow.nom}
                            </Td>
                            <Td color="gray.300" maxW="300px" isTruncated>
                              {workflow.description || 'Aucune description'}
                            </Td>
                            <Td color="white">
                              {workflow.createur_prenom} {workflow.createur_nom}
                            </Td>
                            <Td>
                              <Badge colorScheme={getStatusBadgeColor(workflow.statut)}>
                                {workflow.statut || 'Non défini'}
                              </Badge>
                            </Td>
                            <Td color="white">
                              <Badge variant="outline" colorScheme="blue">
                                {workflow.instances_count}
                              </Badge>
                            </Td>
                            <Td color="gray.300">
                              {new Date(workflow.date_creation).toLocaleDateString('fr-FR')}
                            </Td>
                            <Td>
                              <Menu>
                                <MenuButton
                                  as={IconButton}
                                  icon={<ChevronDownIcon />}
                                  variant="ghost"
                                  colorScheme="blue"
                                  size="sm"
                                />
                                <MenuList bg="#232946" borderColor="#3a8bfd">
                                  <MenuItem 
                                    icon={<ViewIcon />}
                                    bg="#232946" 
                                    color="white"
                                    _hover={{ bg: "#20243a" }}
                                    onClick={() => handleViewWorkflowDetails(workflow.id)}
                                  >
                                    Voir les détails
                                  </MenuItem>
                                  <MenuItem 
                                    icon={<EditIcon />}
                                    bg="#232946" 
                                    color="white"
                                    _hover={{ bg: "#20243a" }}
                                  >
                                    Modifier
                                  </MenuItem>
                                  <MenuItem 
                                    icon={<DeleteIcon />}
                                    bg="#232946" 
                                    color="red.400"
                                    _hover={{ bg: "#20243a" }}
                                    onClick={() => handleDeleteWorkflow(workflow.id)}
                                  >
                                    Supprimer
                                  </MenuItem>
                                </MenuList>
                              </Menu>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  )}
                </Box>
              </VStack>
            </TabPanel>

            {/* Onglet Mes approbations */}
            <TabPanel p={0} pt={4}>
              <Box bg="#20243a" borderRadius="lg" overflow="hidden">
                {isLoading ? (
                  <VStack p={6} spacing={4}>
                    {[...Array(3)].map((_, i) => (
                      <Skeleton key={i} height="80px" width="100%" />
                    ))}
                  </VStack>
                ) : pendingApprovals.length === 0 ? (
                  <Box textAlign="center" py={8}>
                    <Text color="gray.400" mb={2}>Aucune approbation en attente</Text>
                    <Text color="gray.500" fontSize="sm">
                      Les documents nécessitant votre approbation apparaîtront ici
                    </Text>
                  </Box>
                ) : (
                  <Table variant="simple">
                    <Thead bg="#232946">
                      <Tr>
                        <Th color="white">Document</Th>
                        <Th color="white">Workflow</Th>
                        <Th color="white">Étape courante</Th>
                        <Th color="white">Initiateur</Th>
                        <Th color="white">Depuis</Th>
                        <Th color="white">Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {pendingApprovals.map((approval) => (
                        <Tr key={approval.id}>
                          <Td color="white" fontWeight="semibold">
                            <HStack>
                              <IconWrapper icon={FiFileText} />
                              <Text>{approval.document_titre}</Text>
                            </HStack>
                          </Td>
                          <Td color="gray.300">{approval.workflow_nom}</Td>
                          <Td>
                            <Badge colorScheme="yellow" variant="outline">
                              {approval.etape_courante_nom}
                            </Badge>
                          </Td>
                          <Td color="white">
                            {approval.initiateur_prenom} {approval.initiateur_nom}
                          </Td>
                          <Td color="gray.300">
                            {new Date(approval.date_debut).toLocaleDateString('fr-FR')}
                          </Td>
                          <Td>
                            <HStack spacing={2}>
                              <Button
                                size="sm"
                                colorScheme="green"
                                leftIcon={<IconWrapper icon={FiCheck} />}
                                onClick={() => handleApprove(approval.id)}
                              >
                                Approuver
                              </Button>
                              <Button
                                size="sm"
                                colorScheme="red"
                                variant="outline"
                                leftIcon={<IconWrapper icon={FiX} />}
                                onClick={() => handleReject(approval.id)}
                              >
                                Rejeter
                              </Button>
                            </HStack>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                )}
              </Box>
            </TabPanel>

            {/* Onglet Instances actives */}
            <TabPanel p={0} pt={4}>
              <Box bg="#20243a" borderRadius="lg" p={6}>
                <Text color="gray.400" textAlign="center">
                  Fonctionnalité à implémenter : liste des instances de workflow actives
                </Text>
              </Box>
            </TabPanel>
          </TabPanels>
        </Tabs>

        {/* Modal de création */}
        <CreateWorkflowModal
          isOpen={isCreateModalOpen}
          onClose={onCreateModalClose}
          onWorkflowCreated={loadData}
        />

        {/* Modal de détails */}
        <WorkflowDetailsModal
          isOpen={isDetailsModalOpen}
          onClose={onDetailsModalClose}
          workflowId={selectedWorkflowId}
        />
      </VStack>
    </Box>
  );
};

export default WorkflowManagement; 