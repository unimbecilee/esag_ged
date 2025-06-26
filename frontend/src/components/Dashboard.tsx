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
  FiBell,
} from "react-icons/fi";
import { ElementType } from 'react';
import { useAuthStatus } from "../hooks/useAuthStatus";
import PendingApprovals from './ValidationWorkflow/PendingApprovals';

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

interface Notification {
  id: number;
  titre: string;
  message: string;
  type: 'info' | 'warning' | 'success' | 'error';
  timestamp: string;
  read: boolean;
}

const Dashboard: React.FC = () => {
  const { user } = useAuthStatus();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState({
    users: 0,
    documents: 0,
    dossiers: 0,
    archives: 0,
  });
  const [recentDocs, setRecentDocs] = useState<Document[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [workflowStats, setWorkflowStats] = useState({
    completed: 12,
    inProgress: 5,
    pending: 3,
    rejected: 2,
  });
  const [workflowStatsLoading, setWorkflowStatsLoading] = useState(false);

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
      fetchNotifications(),
      fetchWorkflowStats(),
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
      });
    } catch (e) {
      console.error("Erreur lors du chargement des statistiques:", e);
      // Données de démonstration
      setStats({
        users: 5,
        documents: 3,
        dossiers: 3,
        archives: 3,
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

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Récupérer les notifications et le compteur séparément
      const [notificationsRes, unreadCountRes] = await Promise.all([
        fetch('http://localhost:5000/api/notifications', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch('http://localhost:5000/api/notifications/unread-count', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
      ]);
      
      if (notificationsRes.ok) {
        const notificationsData = await notificationsRes.json();
        if (notificationsData.notifications && Array.isArray(notificationsData.notifications)) {
          setNotifications(notificationsData.notifications);
        } else {
          setNotifications([]);
        }
      }
      
      if (unreadCountRes.ok) {
        const unreadData = await unreadCountRes.json();
        setUnreadNotifications(unreadData.unread_count || 0);
      } else {
        setUnreadNotifications(0);
      }
    } catch (e) {
      // Données de test pour le développement
      const testNotifications: Notification[] = [
        {
          id: 1,
          titre: "Nouveau document partagé",
          message: "Un document a été partagé avec vous par Marie Martin",
          type: "info" as const,
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // Il y a 2 heures
          read: false
        },
        {
          id: 2,
          titre: "Validation requise",
          message: "Un document est en attente de votre validation",
          type: "warning" as const,
          timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // Il y a 4 heures
          read: false
        },
        {
          id: 3,
          titre: "Document approuvé",
          message: "Votre document 'Rapport mensuel' a été approuvé",
          type: "success" as const,
          timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // Hier
          read: true
        },
        {
          id: 4,
          titre: "Stockage presque plein",
          message: "Votre espace de stockage est utilisé à 85%",
          type: "warning" as const,
          timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // Il y a 2 jours
          read: true
        }
      ];
      setNotifications(testNotifications);
      setUnreadNotifications(testNotifications.filter(n => !n.read).length);
      }
  };

  const fetchWorkflowStats = async () => {
    setWorkflowStatsLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // Utiliser les bonnes APIs comme dans WorkflowManagement
      const statsResponse = await fetch(`http://localhost:5000/api/workflow-stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        
        // Utiliser les données de l'API workflow-stats
        setWorkflowStats({
          completed: statsData.statusBreakdown?.TERMINE || 0,
          inProgress: statsData.statusBreakdown?.EN_COURS || 0,
          pending: statsData.pendingApprovals || 0,
          rejected: statsData.statusBreakdown?.REJETE || 0,
        });
      } else {
        console.warn("Erreur API workflow-stats:", statsResponse.status);
        // Données par défaut en cas d'erreur
        setWorkflowStats({
          completed: 0,
          inProgress: 0,
          pending: 0,
          rejected: 0,
        });
      }
    } catch (e) {
      console.error("Erreur lors du chargement des statistiques des workflows:", e);
      // Données par défaut en cas d'erreur
      setWorkflowStats({
        completed: 0,
        inProgress: 0,
        pending: 0,
        rejected: 0,
      });
    } finally {
      setWorkflowStatsLoading(false);
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

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success': return FiCheckCircle;
      case 'warning': return FiAlertCircle;
      case 'error': return FiXCircle;
      default: return FiBell;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success': return 'green';
      case 'warning': return 'yellow';
      case 'error': return 'red';
      default: return 'blue';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const notifTime = new Date(timestamp);
    const diffInHours = Math.floor((now.getTime() - notifTime.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return "Il y a moins d'une heure";
    if (diffInHours === 1) return "Il y a 1 heure";
    if (diffInHours < 24) return `Il y a ${diffInHours} heures`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays === 1) return "Hier";
    if (diffInDays < 7) return `Il y a ${diffInDays} jours`;
    
    return notifTime.toLocaleDateString('fr-FR');
  };

  const statCards = [
    { 
      title: "Utilisateurs", 
      value: stats.users, 
      icon: FiUsers, 
      color: "blue",
      bgGradient: "linear(to-r, blue.500, blue.700)"
    },
    { 
      title: "Documents", 
      value: stats.documents, 
      icon: FiFileText, 
      color: "green",
      bgGradient: "linear(to-r, green.500, green.700)"
    },
    { 
      title: "Dossiers", 
      value: stats.dossiers, 
      icon: FiFolder, 
      color: "purple",
      bgGradient: "linear(to-r, purple.500, purple.700)"
    },
    { 
      title: "Archives", 
      value: stats.archives, 
      icon: FiArchive, 
      color: "orange",
      bgGradient: "linear(to-r, orange.500, orange.700)"
    },
  ];

  const handleVoirToutDocs = () => {
    window.location.href = '/my-documents';
  };

  const handleVoirNotifications = () => {
    window.location.href = '/notifications';
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
              {/* Notifications non lues */}
              <Card bg={bgCard} borderWidth="1px" borderColor={borderColor} w="full" boxShadow="lg" borderRadius="xl">
                <CardHeader py={5} px={6}>
                  <HStack spacing={3}>
                    <Icon as={FiBell as ElementType} color="blue.400" boxSize={6} />
                    <Heading size="md" color="white" fontWeight="bold">Notifications</Heading>
                    {unreadNotifications > 0 && (
                      <Badge colorScheme="red" borderRadius="full" fontSize="xs" px={2}>
                        {unreadNotifications}
                      </Badge>
                    )}
                  </HStack>
                </CardHeader>
                <CardBody pt={0} px={6} pb={6}>
                  <VStack spacing={5}>
                    <Box
                      w="full"
                      textAlign="center"
                      bg="blue.900"
                      p={6}
                      borderRadius="xl"
                      borderWidth="1px"
                      borderColor="blue.700"
                    >
                      <Icon as={FiBell as ElementType} boxSize={12} color="blue.400" mb={3} />
                      <Text fontSize="3xl" fontWeight="bold" color="white" mb={2}>
                        {unreadNotifications}
                      </Text>
                      <Text color="blue.400" fontSize="md" fontWeight="medium">
                        Notifications non lues
                      </Text>
                    </Box>
                    
                    {notifications.length > 0 && (
                      <Box
                        w="full"
                        maxHeight="200px"
                        overflowY="auto"
                        css={{
                          '&::-webkit-scrollbar': {
                            width: '4px',
                          },
                          '&::-webkit-scrollbar-track': {
                            background: '#2a3657',
                            borderRadius: '2px',
                          },
                          '&::-webkit-scrollbar-thumb': {
                            background: '#4a5568',
                            borderRadius: '2px',
                          },
                          '&::-webkit-scrollbar-thumb:hover': {
                            background: '#60a5fa',
                          },
                          scrollbarWidth: 'thin',
                          scrollbarColor: '#4a5568 #2a3657',
                        }}
                      >
                        <VStack spacing={3} align="stretch">
                          {notifications.slice(0, 5).map((notification) => (
                            <HStack
                              key={notification.id}
                              spacing={3}
                              bg={notification.read ? "#2a3657" : "rgba(59, 130, 246, 0.1)"}
                              p={3}
                              borderRadius="lg"
                              borderLeft="3px solid"
                              borderLeftColor={`${getNotificationColor(notification.type)}.400`}
                            >
                              <Icon
                                as={getNotificationIcon(notification.type) as ElementType}
                                color={`${getNotificationColor(notification.type)}.400`}
                                boxSize={4}
                              />
                              <VStack align="start" spacing={1} flex={1}>
                                <Text fontSize="sm" color="white" fontWeight={notification.read ? "normal" : "bold"}>
                                  {notification.titre}
                                </Text>
                                <Text fontSize="xs" color="gray.400" noOfLines={2}>
                                  {notification.message}
                                </Text>
                                <Text fontSize="xs" color="gray.500">
                                  {formatTimeAgo(notification.timestamp)}
                    </Text>
                              </VStack>
                            </HStack>
                          ))}
                        </VStack>
                      </Box>
                    )}
                    
                    <Button 
                      size="md" 
                      colorScheme="blue" 
                      variant="solid" 
                      w="full" 
                      boxShadow="md" 
                      onClick={handleVoirNotifications}
                    >
                      Voir toutes les notifications
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
                  <Box
                    maxHeight="300px"
                    overflowY="auto"
                    css={{
                      '&::-webkit-scrollbar': {
                        width: '6px',
                      },
                      '&::-webkit-scrollbar-track': {
                        background: '#2a3657',
                        borderRadius: '3px',
                      },
                      '&::-webkit-scrollbar-thumb': {
                        background: '#4a5568',
                        borderRadius: '3px',
                      },
                      '&::-webkit-scrollbar-thumb:hover': {
                        background: '#68d391',
                      },
                      scrollbarWidth: 'thin',
                      scrollbarColor: '#4a5568 #2a3657',
                    }}
                  >
                  <VStack spacing={4} align="stretch">
                      {activities.length > 0 ? (
                        activities.map((activity) => (
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
                        ))
                      ) : (
                        <Box textAlign="center" py={8}>
                          <Icon as={FiActivity as ElementType} boxSize={12} color="gray.400" mb={4} />
                          <Text color="gray.400" fontSize="md">Aucune activité récente</Text>
                          <Text color="gray.500" fontSize="sm">Les activités apparaîtront ici</Text>
                        </Box>
                      )}
                  </VStack>
                  </Box>
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
                {workflowStatsLoading && (
                  <Skeleton height="20px" width="80px" />
                )}
              </HStack>
              <HStack spacing={2}>
                <IconButton
                  aria-label="Actualiser les statistiques"
                  icon={<Icon as={FiRefreshCw as ElementType} />}
                  size="sm"
                  variant="ghost"
                  color="white"
                  isLoading={workflowStatsLoading}
                  onClick={fetchWorkflowStats}
                  _hover={{ bg: "whiteAlpha.200" }}
                />
              <Button size="sm" variant="solid" colorScheme="orange">
                Voir détails
              </Button>
              </HStack>
            </Flex>
          </CardHeader>
          <CardBody pt={0} px={6} pb={6}>
            {workflowStatsLoading ? (
              <SimpleGrid columns={{ base: 2, md: 4 }} spacing={5}>
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} height="120px" borderRadius="xl" />
                ))}
              </SimpleGrid>
            ) : (
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
                  <Text fontSize="md" color="green.400" fontWeight="medium">Approuvés</Text>
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
            )}
          </CardBody>
        </Card>
      </VStack>
    </Container>
  );
};

export default Dashboard;
