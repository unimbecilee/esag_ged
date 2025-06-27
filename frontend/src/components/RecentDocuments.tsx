import React, { useState, useEffect } from "react";
import {
  Box,
  Heading,
  Flex,
  Spinner,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Button,
  Text,
  Icon,
  VStack,
  HStack,
  Input,
  Select,
  Card,
  CardHeader,
  CardBody,
  useToast,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from "@chakra-ui/react";
import {
  FiClock,
  FiEye,
  FiDownload,
  FiEdit,
  FiShare2,
  FiTrash2,
  FiFilter,
  FiSearch,
  FiRefreshCw,
  FiUpload,
} from "react-icons/fi";
import { ElementType } from "react";
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';
import { ActionMenu } from "./Document/ActionMenu";

interface RecentActivity {
  id: number;
  document_id: number;
  document_title: string;
  document_type: string;
  action: 'VIEW' | 'DOWNLOAD' | 'EDIT' | 'SHARE' | 'DELETE' | 'UPLOAD';
  action_description: string;
  user: string;
  timestamp: string;
  size: string;
}

const RecentDocuments: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<string>("");
  const [filterAction, setFilterAction] = useState<string>("");

  useEffect(() => {
    fetchRecentActivities();
  }, []);

  const fetchRecentActivities = async () => {
    setIsLoading(true);
    try {
      const result = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/api/documents/recent-activities`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });

          if (!response.ok) {
            throw new Error('Erreur lors de la récupération de l\'historique');
          }

          const data = await response.json();
          console.log('Activités récentes reçues:', data);
          return data.activities || [];
        },
        {
          loadingMessage: "Chargement de l'historique...",
          errorMessage: "Impossible de charger l'historique"
        }
      );

      if (result) {
        setActivities(result);
      }
    } catch (err) {
      console.error("Erreur lors du chargement des activités récentes:", err);
      // Données de test pour le développement
      setActivities([
        {
          id: 1,
          document_id: 101,
          document_title: "Rapport Mensuel Janvier 2024",
          document_type: "PDF",
          action: "VIEW",
          action_description: "Document consulté",
          user: "Jean Dupont",
          timestamp: "2024-01-15T10:30:00Z",
          size: "2.5 MB"
        },
        {
          id: 2,
          document_id: 102,
          document_title: "Contrat Client ABC",
          document_type: "DOC",
          action: "DOWNLOAD",
          action_description: "Document téléchargé",
          user: "Marie Martin",
          timestamp: "2024-01-15T09:15:00Z",
          size: "1.2 MB"
        },
        {
          id: 3,
          document_id: 103,
          document_title: "Présentation Projet X",
          document_type: "PPT",
          action: "EDIT",
          action_description: "Document modifié",
          user: "Pierre Durand",
          timestamp: "2024-01-14T16:45:00Z",
          size: "5.8 MB"
        },
        {
          id: 4,
          document_id: 104,
          document_title: "Facture F-2024-001",
          document_type: "PDF",
          action: "SHARE",
          action_description: "Document partagé avec l'équipe comptabilité",
          user: "Sophie Bernard",
          timestamp: "2024-01-14T14:20:00Z",
          size: "456 KB"
        },
        {
          id: 5,
          document_id: 105,
          document_title: "Budget Prévisionnel 2024",
          document_type: "XLS",
          action: "VIEW",
          action_description: "Document consulté",
          user: "Marc Leblanc",
          timestamp: "2024-01-14T11:10:00Z",
          size: "980 KB"
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearHistory = async () => {
    try {
      await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/api/documents/recent-activities`, {
            method: 'DELETE',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });

          if (!response.ok) {
            throw new Error('Erreur lors de la suppression de l\'historique');
          }
        },
        {
          loadingMessage: "Suppression de l'historique...",
          successMessage: "Historique supprimé avec succès",
          errorMessage: "Impossible de supprimer l'historique"
        }
      );

      setActivities([]);
    } catch (err) {
      // En cas d'erreur de l'API, on vide quand même localement
      setActivities([]);
      toast({
        title: "Historique vidé",
        description: "L'historique local a été vidé",
        status: "info",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const getFilteredActivities = () => {
    return activities.filter(activity => {
      const matchesSearch = activity.document_title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          activity.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          activity.action_description.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesType = !filterType || activity.document_type === filterType;
      const matchesAction = !filterAction || activity.action === filterAction;
      
      return matchesSearch && matchesType && matchesAction;
    });
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const activityTime = new Date(timestamp);
    const diffInHours = Math.floor((now.getTime() - activityTime.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return "Il y a moins d'une heure";
    if (diffInHours === 1) return "Il y a 1 heure";
    if (diffInHours < 24) return `Il y a ${diffInHours} heures`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays === 1) return "Hier";
    if (diffInDays < 7) return `Il y a ${diffInDays} jours`;
    
    return activityTime.toLocaleDateString('fr-FR');
  };

  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case 'VIEW': return 'blue';
      case 'DOWNLOAD': return 'green';
      case 'EDIT': return 'orange';
      case 'SHARE': return 'purple';
      case 'DELETE': return 'red';
      case 'UPLOAD': return 'teal';
      default: return 'gray';
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'VIEW': return FiEye;
      case 'DOWNLOAD': return FiDownload;
      case 'EDIT': return FiEdit;
      case 'SHARE': return FiShare2;
      case 'DELETE': return FiTrash2;
      case 'UPLOAD': return FiUpload;
      default: return FiClock;
    }
  };

  if (isLoading) {
    return (
      <Box p={5}>
        <Flex justify="center" align="center" h="50vh">
          <Spinner color="#3a8bfd" size="xl" />
        </Flex>
      </Box>
    );
  }

  const filteredActivities = getFilteredActivities();

  return (
    <Box p={5}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          <Icon as={FiClock as ElementType} mr={3} color="#3a8bfd" />
          Documents Récents
        </Heading>
        <HStack>
          <Button
            leftIcon={<Icon as={FiRefreshCw as ElementType} />}
            onClick={fetchRecentActivities}
            variant="outline"
            borderColor="#3a445e"
            color="white"
            _hover={{ bg: "rgba(58, 139, 253, 0.1)" }}
          >
            Actualiser
          </Button>
          <Button
            leftIcon={<Icon as={FiTrash2 as ElementType} />}
            colorScheme="red"
            variant="outline"
            onClick={clearHistory}
          >
            Vider l'historique
          </Button>
        </HStack>
      </Flex>

      {/* Filtres */}
      <Card bg="#2a3657" borderColor="#3a445e" mb={6}>
        <CardHeader>
          <Heading size="md" color="white">
            <Icon as={FiFilter as ElementType} mr={2} />
            Filtres
          </Heading>
        </CardHeader>
        <CardBody>
          <HStack spacing={4} wrap="wrap">
            <Box minW="200px">
              <Text color="gray.400" fontSize="sm" mb={2}>Recherche</Text>
              <Input
                placeholder="Rechercher..."
                bg="#1c2338"
                color="white"
                borderColor="#3a445e"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </Box>
            <Box minW="150px">
              <Text color="gray.400" fontSize="sm" mb={2}>Type de document</Text>
              <Select
                bg="#1c2338"
                color="white"
                borderColor="#3a445e"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="">Tous les types</option>
                <option value="PDF">PDF</option>
                <option value="DOC">DOC/DOCX</option>
                <option value="XLS">XLS/XLSX</option>
                <option value="PPT">PowerPoint</option>
                <option value="IMG">Images</option>
              </Select>
            </Box>
            <Box minW="150px">
              <Text color="gray.400" fontSize="sm" mb={2}>Action</Text>
              <Select
                bg="#1c2338"
                color="white"
                borderColor="#3a445e"
                value={filterAction}
                onChange={(e) => setFilterAction(e.target.value)}
              >
                <option value="">Toutes les actions</option>
                <option value="VIEW">Consultation</option>
                <option value="DOWNLOAD">Téléchargement</option>
                <option value="EDIT">Modification</option>
                <option value="SHARE">Partage</option>
                <option value="DELETE">Suppression</option>
              </Select>
            </Box>
          </HStack>
        </CardBody>
      </Card>

      {/* Tableau des activités */}
      <Card bg="#2a3657" borderColor="#3a445e">
        <CardBody>
          {filteredActivities.length === 0 ? (
            <Flex
              justify="center"
              align="center"
              direction="column"
              h="200px"
              color="gray.400"
            >
              <Icon as={FiClock as ElementType} boxSize={12} mb={4} />
              <Text>Aucune activité récente</Text>
              <Text fontSize="sm">Les documents consultés apparaîtront ici</Text>
            </Flex>
          ) : (
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th color="gray.400">Document</Th>
                  <Th color="gray.400">Action</Th>
                  <Th color="gray.400">Description</Th>
                  <Th color="gray.400">Utilisateur</Th>
                  <Th color="gray.400">Quand</Th>
                  <Th color="gray.400">Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredActivities.map((activity) => (
                  <Tr key={activity.id}>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <Text color="white" fontWeight="bold">
                          {activity.document_title}
                        </Text>
                        <HStack>
                          <Badge colorScheme="blue" variant="subtle">
                            {activity.document_type}
                          </Badge>
                          <Text color="gray.400" fontSize="xs">
                            {activity.size}
                          </Text>
                        </HStack>
                      </VStack>
                    </Td>
                    <Td>
                      <Badge 
                        colorScheme={getActionBadgeColor(activity.action)}
                        variant="solid"
                      >
                        <Icon as={getActionIcon(activity.action) as ElementType} mr={1} />
                        {activity.action}
                      </Badge>
                    </Td>
                    <Td>
                      <Text color="gray.300" fontSize="sm">
                        {activity.action_description}
                      </Text>
                    </Td>
                    <Td>
                      <Text color="white">
                        {activity.user}
                      </Text>
                    </Td>
                    <Td>
                      <Text color="gray.400" fontSize="sm">
                        {formatTimeAgo(activity.timestamp)}
                      </Text>
                    </Td>
                    <Td>
                      <ActionMenu
                        document={{
                          id: activity.document_id,
                          titre: activity.document_title,
                          type_document: activity.document_type,
                          taille_formatee: activity.size,
                          date_creation: activity.timestamp,
                        }}
                        onUpdate={() => {}}
                        onDelete={() => {}}
                      />
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>

      {filteredActivities.length > 0 && (
        <Alert status="info" bg="#1c2338" borderColor="#3a445e" mt={4}>
          <AlertIcon color="#3a8bfd" />
          <Box>
            <AlertTitle>Activité récente!</AlertTitle>
            <AlertDescription>
              {filteredActivities.length} activité(s) trouvée(s) sur les 30 derniers jours.
            </AlertDescription>
          </Box>
        </Alert>
      )}
    </Box>
  );
};

export default RecentDocuments;

