import React, { useEffect, useState } from "react";
import {
  Box,
  Flex,
  Text,
  Icon,
  Heading,
  Badge,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  VStack,
  HStack,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Avatar,
  AvatarGroup,
  Button,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Divider,
  useColorModeValue,
  Skeleton,
  SkeletonText,
  Tooltip,
  Container,
  Grid,
  GridItem,
  CircularProgress,
  CircularProgressLabel,
} from "@chakra-ui/react";
import {
  FiUsers,
  FiFileText,
  FiFolder,
  FiArchive,
  FiTrendingUp,
  FiTrendingDown,
  FiMoreVertical,
  FiDownload,
  FiEye,
  FiEdit,
  FiClock,
  FiActivity,
  FiPieChart,
  FiBarChart2,
  FiCalendar,
  FiRefreshCw,
  FiCheckCircle,
  FiXCircle,
  FiAlertCircle,
} from "react-icons/fi";
import { ElementType } from 'react';

interface Document {
  id: number;
  titre: string;
  type_document: string;
  taille: number;
  date_ajout: string;
  proprietaire_nom: string;
  proprietaire_prenom: string;
}

interface Activity {
  id: number;
  action: string;
  user: string;
  timestamp: string;
  type: 'upload' | 'download' | 'edit' | 'delete';
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState({
    users: 0,
    documents: 0,
    dossiers: 0,
    archives: 0,
    usersChange: 0,
    documentsChange: 0,
    dossiersChange: 0,
    archivesChange: 0,
  });
  const [recentDocs, setRecentDocs] = useState<Document[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [storageUsed, setStorageUsed] = useState(65);
  const [workflowStats, setWorkflowStats] = useState({
    completed: 12,
    inProgress: 5,
    pending: 3,
    rejected: 2,
  });

  // Couleurs améliorées pour un meilleur contraste
  const bgCard = useColorModeValue('#1a2036', '#1a2036'); // Plus foncé pour un meilleur contraste
  const borderColor = useColorModeValue('#2d3757', '#2d3757'); // Plus visible

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([
      fetchStats(),
      fetchRecentDocs(),
      fetchActivities(),
      fetchStorage(),
    ]);
    setLoading(false);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const [usersRes, docsRes, foldersRes, archivesRes] = await Promise.all([
        fetch("http://localhost:5000/api/users/count", { headers }),
        fetch("http://localhost:5000/api/documents/count", { headers }),
        fetch("http://localhost:5000/api/folders/count", { headers }),
        fetch("http://localhost:5000/api/archives/count", { headers }),
      ]);

      const [users, documents, dossiers, archives] = await Promise.all([
        usersRes.json(),
        docsRes.json(),
        foldersRes.json(),
        archivesRes.json(),
      ]);

      setStats({
        users: users.count || 5,
        documents: documents.count || 3,
        dossiers: dossiers.count || 3,
        archives: archives.count || 3,
        usersChange: 12,
        documentsChange: -5,
        dossiersChange: 8,
        archivesChange: 15,
      });
    } catch (e) {
      console.error("Erreur lors du chargement des statistiques:", e);
      // Données de démonstration
      setStats({
        users: 5,
        documents: 3,
        dossiers: 3,
        archives: 3,
        usersChange: 12,
        documentsChange: -5,
        dossiersChange: 8,
        archivesChange: 15,
      });
    }
  };

  const fetchRecentDocs = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch("http://localhost:5000/api/documents/recent", {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await res.json();
      if (Array.isArray(data)) {
        setRecentDocs(data);
      } else {
        setRecentDocs([]);
      }
    } catch (e) {
      console.error("Error fetching recent documents:", e);
      setRecentDocs([]);
    }
  };

  const fetchActivities = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/api/documents/recent-activities', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await res.json();
      if (data.activities && Array.isArray(data.activities)) {
        setActivities(data.activities.map((a: any) => ({
          id: a.id,
          action: a.action,
          user: a.user,
          timestamp: a.timestamp,
          type: a.type
        })));
      } else {
        setActivities([]);
      }
    } catch (e) {
      setActivities([]);
    }
  };

  const fetchStorage = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/api/documents/my', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const docs = await res.json();
      let total = 0;
      if (Array.isArray(docs)) {
        total = docs.reduce((acc, doc) => acc + (doc.taille || 0), 0);
      }
      // Supposons 10 Go max
      setStorageUsed(Math.round((total / (10 * 1024 * 1024 * 1024)) * 100));
    } catch (e) {
      setStorageUsed(0);
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'upload': return FiDownload;
      case 'download': return FiDownload;
      case 'edit': return FiEdit;
      case 'delete': return FiXCircle;
      default: return FiActivity;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'upload': return 'green';
      case 'download': return 'blue';
      case 'edit': return 'orange';
      case 'delete': return 'red';
      default: return 'gray';
    }
  };

  const statCards = [
    { 
      title: "Utilisateurs", 
      value: stats.users, 
      icon: FiUsers, 
      color: "blue",
      change: stats.usersChange,
      bgGradient: "linear(to-r, blue.500, blue.700)"
    },
    { 
      title: "Documents", 
      value: stats.documents, 
      icon: FiFileText, 
      color: "green",
      change: stats.documentsChange,
      bgGradient: "linear(to-r, green.500, green.700)"
    },
    { 
      title: "Dossiers", 
      value: stats.dossiers, 
      icon: FiFolder, 
      color: "purple",
      change: stats.dossiersChange,
      bgGradient: "linear(to-r, purple.500, purple.700)"
    },
    { 
      title: "Archives", 
      value: stats.archives, 
      icon: FiArchive, 
      color: "orange",
      change: stats.archivesChange,
      bgGradient: "linear(to-r, orange.500, orange.700)"
    },
  ];

  const handleVoirToutDocs = () => {
    window.location.href = '/my-documents';
  };

  const handleGererStockage = () => {
    window.location.href = '/settings';
  };

  const handleVoirDetails = (type: string) => {
    if (type === 'Utilisateurs') window.location.href = '/users';
    if (type === 'Documents') window.location.href = '/my-documents';
    if (type === 'Dossiers') window.location.href = '/my-documents';
    if (type === 'Archives') window.location.href = '/trash';
  };

  const handleDocAction = (action: string, doc: any) => {
    if (action === 'Aperçu') window.open(`/api/documents/${doc.id}`, '_blank');
    if (action === 'Télécharger') window.open(`/api/documents/${doc.id}/download`, '_blank');
    if (action === 'Modifier') window.location.href = `/edit-document/${doc.id}`;
  };

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* En-tête */}
        <Flex justify="space-between" align="center" mb={4}>
          <Box>
            <Heading color="white" size="xl" mb={2} fontWeight="bold">
              Tableau de bord
            </Heading>
            <Text color="gray.300" fontSize="lg">
              Bienvenue ! Voici un aperçu de votre espace de travail
            </Text>
          </Box>
          <HStack spacing={3}>
            <Button
              leftIcon={<Icon as={FiCalendar as ElementType} />}
              variant="solid"
              colorScheme="blue"
              size="md"
              boxShadow="md"
            >
              Aujourd'hui
            </Button>
            <IconButton
              icon={<Icon as={FiRefreshCw as ElementType} boxSize={5} />}
              aria-label="Actualiser"
              variant="solid"
              colorScheme="blue"
              onClick={handleRefresh}
              isLoading={refreshing}
              size="md"
              boxShadow="md"
            />
          </HStack>
        </Flex>

        {/* Cartes de statistiques */}
        <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={6}>
          {statCards.map((stat, index) => (
            <Card
              key={index}
              bg={bgCard}
              borderWidth="1px"
              borderColor={borderColor}
              overflow="hidden"
              transition="all 0.3s"
              _hover={{ transform: "translateY(-4px)", shadow: "lg" }}
              boxShadow="lg"
              borderRadius="xl"
            >
              <Box bgGradient={stat.bgGradient} h="4px" />
              <CardBody p={5}>
                <Stat>
                  <HStack justify="space-between" mb={3}>
                    <Icon as={stat.icon as ElementType} boxSize={10} color={`${stat.color}.400`} />
                    <Menu>
                      <MenuButton
                        as={IconButton}
                        icon={<Icon as={FiMoreVertical as ElementType} />}
                        variant="ghost"
                        size="sm"
                        color="white"
                        _hover={{ bg: "whiteAlpha.200" }}
                      />
                      <MenuList>
                        <MenuItem icon={<Icon as={FiEye as ElementType} />} onClick={() => handleVoirDetails(stat.title)}>Voir détails</MenuItem>
                        <MenuItem icon={<Icon as={FiDownload as ElementType} />}>Exporter</MenuItem>
                      </MenuList>
                    </Menu>
                  </HStack>
                  <StatLabel color="gray.300" fontSize="md">{stat.title}</StatLabel>
                  <StatNumber fontSize="4xl" color="white" fontWeight="bold">
                    {loading ? <Skeleton height="40px" /> : stat.value}
                  </StatNumber>
                  {!loading && (
                    <StatHelpText fontSize="md">
                      <StatArrow type={stat.change >= 0 ? 'increase' : 'decrease'} />
                      <Text as="span" fontWeight="medium">{Math.abs(stat.change)}%</Text> ce mois
                    </StatHelpText>
                  )}
                </Stat>
              </CardBody>
            </Card>
          ))}
        </SimpleGrid>

        <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap={6}>
          {/* Documents récents */}
          <GridItem>
            <Card bg={bgCard} borderWidth="1px" borderColor={borderColor} boxShadow="lg" borderRadius="xl">
              <CardHeader py={5} px={6}>
                <Flex justify="space-between" align="center">
                  <HStack spacing={3}>
                    <Icon as={FiClock as ElementType} color="blue.400" boxSize={6} />
                    <Heading size="md" color="white" fontWeight="bold">Documents récents</Heading>
                  </HStack>
                  <Button size="sm" variant="solid" colorScheme="blue" onClick={handleVoirToutDocs}>
                    Voir tout
                  </Button>
                </Flex>
              </CardHeader>
              <CardBody pt={0} px={6} pb={6}>
                <VStack spacing={4} align="stretch">
                  {loading ? (
                    <>
                      <Skeleton height="80px" borderRadius="lg" />
                      <Skeleton height="80px" borderRadius="lg" />
                      <Skeleton height="80px" borderRadius="lg" />
                    </>
                  ) : recentDocs.length > 0 ? (
                    recentDocs.slice(0, 5).map((doc) => (
                      <Card
                        key={doc.id}
                        bg="#2a3657"
                        p={4}
                        transition="all 0.2s"
                        _hover={{ bg: "#374369", transform: "translateX(4px)" }}
                        cursor="pointer"
                        boxShadow="md"
                        borderRadius="lg"
                      >
                        <HStack justify="space-between">
                          <HStack spacing={4}>
                            <Box
                              bg={`${doc.type_document === 'pdf' ? 'red' : 'blue'}.500`}
                              p={3}
                              borderRadius="lg"
                              boxShadow="md"
                            >
                              <Icon as={FiFileText as ElementType} color="white" boxSize={6} />
                            </Box>
                            <VStack align="start" spacing={1}>
                              <Text fontWeight="bold" color="white" noOfLines={1} fontSize="md">
                                {doc.titre}
                              </Text>
                              <HStack spacing={2}>
                                <Badge colorScheme="blue" variant="solid" borderRadius="md" px={2} py={1}>
                                  {doc.type_document?.toUpperCase()}
                                </Badge>
                                <Text fontSize="sm" color="gray.300" fontWeight="medium">
                                  {(doc.taille / 1024 / 1024).toFixed(1)} MB
                                </Text>
                              </HStack>
                              <Text fontSize="xs" color="gray.400">
                                {doc.proprietaire_prenom} {doc.proprietaire_nom} • {new Date(doc.date_ajout).toLocaleDateString('fr-FR')}
                              </Text>
                            </VStack>
                          </HStack>
                          <Menu>
                            <MenuButton
                              as={IconButton}
                              icon={<Icon as={FiMoreVertical as ElementType} />}
                              variant="ghost"
                              size="sm"
                              color="white"
                              _hover={{ bg: "whiteAlpha.200" }}
                            />
                            <MenuList>
                              <MenuItem icon={<Icon as={FiEye as ElementType} />} onClick={() => handleDocAction('Aperçu', doc)}>Aperçu</MenuItem>
                              <MenuItem icon={<Icon as={FiDownload as ElementType} />} onClick={() => handleDocAction('Télécharger', doc)}>Télécharger</MenuItem>
                              <MenuItem icon={<Icon as={FiEdit as ElementType} />} onClick={() => handleDocAction('Modifier', doc)}>Modifier</MenuItem>
                            </MenuList>
                          </Menu>
                        </HStack>
                      </Card>
                    ))
                  ) : (
                    <Box textAlign="center" py={8}>
                      <Icon as={FiFileText as ElementType} boxSize={14} color="gray.400" mb={4} />
                      <Text color="gray.400" fontSize="lg">Aucun document récent</Text>
                    </Box>
                  )}
                </VStack>
              </CardBody>
            </Card>
          </GridItem>

          {/* Panneau latéral */}
          <GridItem>
            <VStack spacing={6}>
              {/* Stockage */}
              <Card bg={bgCard} borderWidth="1px" borderColor={borderColor} w="full" boxShadow="lg" borderRadius="xl">
                <CardHeader py={5} px={6}>
                  <HStack spacing={3}>
                    <Icon as={FiPieChart as ElementType} color="purple.400" boxSize={6} />
                    <Heading size="md" color="white" fontWeight="bold">Stockage</Heading>
                  </HStack>
                </CardHeader>
                <CardBody pt={0} px={6} pb={6}>
                  <VStack spacing={5}>
                    <CircularProgress
                      value={storageUsed}
                      size="140px"
                      thickness="10px"
                      color="purple.400"
                      trackColor="#2a3657"
                    >
                      <CircularProgressLabel color="white" fontSize="2xl" fontWeight="bold">
                        {storageUsed}%
                      </CircularProgressLabel>
                    </CircularProgress>
                    <Text color="gray.300" fontSize="md" fontWeight="medium">
                      6.5 GB utilisés sur 10 GB
                    </Text>
                    <Button size="md" colorScheme="purple" variant="solid" w="full" boxShadow="md" onClick={handleGererStockage}>
                      Gérer le stockage
                    </Button>
                  </VStack>
                </CardBody>
              </Card>

              {/* Activité récente */}
              <Card bg={bgCard} borderWidth="1px" borderColor={borderColor} w="full" boxShadow="lg" borderRadius="xl">
                <CardHeader py={5} px={6}>
                  <HStack spacing={3}>
                    <Icon as={FiActivity as ElementType} color="green.400" boxSize={6} />
                    <Heading size="md" color="white" fontWeight="bold">Activité récente</Heading>
                  </HStack>
                </CardHeader>
                <CardBody pt={0} px={6} pb={6}>
                  <VStack spacing={4} align="stretch">
                    {activities.map((activity) => (
                      <HStack key={activity.id} spacing={3} bg="#2a3657" p={3} borderRadius="lg">
                        <Icon
                          as={getActivityIcon(activity.type) as ElementType}
                          color={`${getActivityColor(activity.type)}.400`}
                          boxSize={5}
                        />
                        <VStack align="start" spacing={0} flex={1}>
                          <Text fontSize="sm" color="white">
                            <Text as="span" fontWeight="bold">{activity.user}</Text>
                            {' '}{activity.action}
                          </Text>
                          <Text fontSize="xs" color="gray.400">
                            {activity.timestamp}
                          </Text>
                        </VStack>
                      </HStack>
                    ))}
                  </VStack>
                </CardBody>
              </Card>
            </VStack>
          </GridItem>
        </Grid>

        {/* Statut des workflows */}
        <Card bg={bgCard} borderWidth="1px" borderColor={borderColor} boxShadow="lg" borderRadius="xl">
          <CardHeader py={5} px={6}>
            <Flex justify="space-between" align="center">
              <HStack spacing={3}>
                <Icon as={FiBarChart2 as ElementType} color="orange.400" boxSize={6} />
                <Heading size="md" color="white" fontWeight="bold">Statut des workflows</Heading>
              </HStack>
              <Button size="sm" variant="solid" colorScheme="orange">
                Voir détails
              </Button>
            </Flex>
          </CardHeader>
          <CardBody pt={0} px={6} pb={6}>
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={5}>
              <VStack
                bg="green.900"
                p={5}
                borderRadius="xl"
                borderWidth="1px"
                borderColor="green.700"
                transition="all 0.2s"
                _hover={{ bg: "green.800", transform: "translateY(-2px)" }}
                cursor="pointer"
                boxShadow="md"
              >
                <Icon as={FiCheckCircle as ElementType} color="green.400" boxSize={8} />
                <Text fontSize="3xl" fontWeight="bold" color="white">
                  {workflowStats.completed}
                </Text>
                <Text fontSize="md" color="green.400" fontWeight="medium">Terminés</Text>
              </VStack>
              
              <VStack
                bg="blue.900"
                p={5}
                borderRadius="xl"
                borderWidth="1px"
                borderColor="blue.700"
                transition="all 0.2s"
                _hover={{ bg: "blue.800", transform: "translateY(-2px)" }}
                cursor="pointer"
                boxShadow="md"
              >
                <Icon as={FiActivity as ElementType} color="blue.400" boxSize={8} />
                <Text fontSize="3xl" fontWeight="bold" color="white">
                  {workflowStats.inProgress}
                </Text>
                <Text fontSize="md" color="blue.400" fontWeight="medium">En cours</Text>
              </VStack>
              
              <VStack
                bg="yellow.900"
                p={5}
                borderRadius="xl"
                borderWidth="1px"
                borderColor="yellow.700"
                transition="all 0.2s"
                _hover={{ bg: "yellow.800", transform: "translateY(-2px)" }}
                cursor="pointer"
                boxShadow="md"
              >
                <Icon as={FiAlertCircle as ElementType} color="yellow.400" boxSize={8} />
                <Text fontSize="3xl" fontWeight="bold" color="white">
                  {workflowStats.pending}
                </Text>
                <Text fontSize="md" color="yellow.400" fontWeight="medium">En attente</Text>
              </VStack>
              
              <VStack
                bg="red.900"
                p={5}
                borderRadius="xl"
                borderWidth="1px"
                borderColor="red.700"
                transition="all 0.2s"
                _hover={{ bg: "red.800", transform: "translateY(-2px)" }}
                cursor="pointer"
                boxShadow="md"
              >
                <Icon as={FiXCircle as ElementType} color="red.400" boxSize={8} />
                <Text fontSize="3xl" fontWeight="bold" color="white">
                  {workflowStats.rejected}
                </Text>
                <Text fontSize="md" color="red.400" fontWeight="medium">Rejetés</Text>
              </VStack>
            </SimpleGrid>
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default Dashboard;
