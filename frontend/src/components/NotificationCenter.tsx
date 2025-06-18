import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Flex,
  Heading,
  Text,
  VStack,
  HStack,
  Badge,
  Button,
  IconButton,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Icon,
  Alert,
  AlertIcon,
  Spinner,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Switch,
  FormControl,
  FormLabel,
  Divider,
  useDisclosure,
  Tooltip,
  Progress,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  useColorModeValue
} from '@chakra-ui/react';
import NotificationModal from './NotificationModal';
import { Notification, NotificationStats, NotificationPreferences } from '../types/notifications';
import {
  FiBell,
  FiBellOff,
  FiCheck,
  FiX,
  FiMoreVertical,
  FiEye,
  FiTrash2,
  FiSettings,
  FiRefreshCw,
  FiFilter,
  FiMail,
  FiMessageSquare,
  FiFileText,
  FiUsers,
  FiClock,
  FiTrendingUp
} from 'react-icons/fi';
import { asElementType } from '../utils/iconUtils';
import config from '../config';
import { useAsyncOperation } from '../hooks/useAsyncOperation';



const NotificationCenter: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterType, setFilterType] = useState<string>('all');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const { isOpen: isPrefsOpen, onOpen: onPrefsOpen, onClose: onPrefsClose } = useDisclosure();
  const { isOpen: isNotificationModalOpen, onOpen: onNotificationModalOpen, onClose: onNotificationModalClose } = useDisclosure();
  
  // Couleurs adaptatives
  const bgColor = useColorModeValue('white', '#181c2f');
  const cardBg = useColorModeValue('gray.50', '#2a3657');
  const borderColor = useColorModeValue('gray.200', '#3a445e');

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'document_uploaded':
      case 'document_updated':
        return FiFileText;
      case 'document_shared':
        return FiUsers;
      case 'document_commented':
        return FiMessageSquare;
      case 'workflow_assigned':
        return FiClock;
      case 'user_mentioned':
        return FiBell;
      case 'system_maintenance':
        return FiSettings;
      default:
        return FiBell;
    }
  };

  const getNotificationColor = (type: string, priority: number) => {
    if (priority >= 4) return 'red';
    if (priority >= 3) return 'orange';
    
    switch (type) {
      case 'document_uploaded':
      case 'document_updated':
        return 'blue';
      case 'document_shared':
        return 'purple';
      case 'document_commented':
        return 'green';
      case 'workflow_assigned':
        return 'yellow';
      case 'user_mentioned':
        return 'pink';
      case 'system_maintenance':
        return 'gray';
      default:
        return 'blue';
    }
  };

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 4: return { label: 'Urgent', color: 'red' };
      case 3: return { label: 'Haute', color: 'orange' };
      case 2: return { label: 'Normale', color: 'blue' };
      case 1: return { label: 'Basse', color: 'gray' };
      default: return { label: 'Normale', color: 'blue' };
    }
  };

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page: currentPage.toString(),
        per_page: '20',
        unread_only: showUnreadOnly.toString(),
        ...(filterType !== 'all' && { type: filterType })
      });

      const response = await fetch(
        `${config.API_URL}/notifications?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
        setTotalPages(Math.ceil(data.total / 20));
      } else {
        throw new Error('Erreur lors du chargement des notifications');
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les notifications',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  }, [currentPage, showUnreadOnly, filterType, toast]);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/notifications/unread-count`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUnreadCount(data.unread_count || 0);
      }
    } catch (error) {
      console.error('Erreur unread count:', error);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/notifications/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Erreur stats:', error);
    }
  }, []);

  const fetchPreferences = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/notifications/preferences`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences(data.preferences);
      }
    } catch (error) {
      console.error('Erreur préférences:', error);
    }
  }, []);

  const handleMarkAsRead = async (notificationId: number) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/notifications/${notificationId}/read`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        fetchNotifications();
        fetchUnreadCount();
      } else {
        throw new Error('Erreur lors du marquage');
      }
    }, {
      successMessage: 'Notification marquée comme lue',
      errorMessage: 'Erreur lors du marquage'
    });
  };

  const handleMarkAllAsRead = async () => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/notifications/mark-all-read`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        fetchNotifications();
        fetchUnreadCount();
      } else {
        throw new Error('Erreur lors du marquage');
      }
    }, {
      loadingMessage: 'Marquage en cours...',
      successMessage: 'Toutes les notifications marquées comme lues',
      errorMessage: 'Erreur lors du marquage'
    });
  };

  const handleDeleteNotification = async (notificationId: number) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/notifications/${notificationId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        fetchNotifications();
        fetchUnreadCount();
      } else {
        throw new Error('Erreur lors de la suppression');
      }
    }, {
      successMessage: 'Notification supprimée',
      errorMessage: 'Erreur lors de la suppression'
    });
  };

  const handleNotificationClick = (notification: Notification) => {
    setSelectedNotification(notification);
    onNotificationModalOpen();
  };

  const handleNotificationUpdated = () => {
    fetchNotifications();
    fetchUnreadCount();
  };

  const handleCloseNotificationModal = () => {
    onNotificationModalClose();
    setSelectedNotification(null);
  };

  const handleUpdatePreferences = async (newPreferences: Partial<NotificationPreferences>) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/notifications/preferences`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(newPreferences)
        }
      );

      if (response.ok) {
        setPreferences(prev => ({ ...prev, ...newPreferences } as NotificationPreferences));
        onPrefsClose();
      } else {
        throw new Error('Erreur lors de la mise à jour');
      }
    }, {
      successMessage: 'Préférences mises à jour',
      errorMessage: 'Erreur lors de la mise à jour'
    });
  };

  // Polling pour les nouvelles notifications
  useEffect(() => {
    const interval = setInterval(() => {
      fetchUnreadCount();
    }, 30000); // Vérifier toutes les 30 secondes

    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();
    fetchStats();
    fetchPreferences();
  }, [fetchNotifications, fetchUnreadCount, fetchStats, fetchPreferences]);

  useEffect(() => {
    setCurrentPage(1);
  }, [filterType, showUnreadOnly]);

  return (
    <Box p={6} bg={bgColor} minH="100vh" color="white">
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          <Flex align="center" gap={3}>
            <Icon as={asElementType(FiBell)} color="#3a8bfd" />
            Centre de Notifications
            {unreadCount > 0 && (
              <Badge colorScheme="red" borderRadius="full" px={2}>
                {unreadCount}
              </Badge>
            )}
          </Flex>
        </Heading>
        
        <HStack spacing={3}>
          <Tooltip label="Préférences de notification">
            <IconButton
              icon={<Icon as={asElementType(FiSettings)} />}
              variant="outline"
              onClick={onPrefsOpen}
              aria-label="Préférences"
            />
          </Tooltip>
          
          <Button
            leftIcon={<Icon as={asElementType(FiRefreshCw)} />}
            variant="outline"
            onClick={() => {
              fetchNotifications();
              fetchUnreadCount();
              fetchStats();
            }}
          >
            Actualiser
          </Button>
          
          {unreadCount > 0 && (
            <Button
              leftIcon={<Icon as={asElementType(FiCheck)} />}
              colorScheme="green"
              onClick={handleMarkAllAsRead}
            >
              Tout marquer comme lu
            </Button>
          )}
        </HStack>
      </Flex>

      <Tabs variant="enclosed" colorScheme="blue">
        <TabList>
          <Tab>Notifications</Tab>
          <Tab>Statistiques</Tab>
        </TabList>

        <TabPanels>
          {/* Onglet Notifications */}
          <TabPanel>
            <VStack align="stretch" spacing={4}>
              {/* Filtres */}
              <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
                <HStack spacing={4}>
                  <FormControl display="flex" alignItems="center" w="auto">
                    <FormLabel htmlFor="unread-only" mb="0" fontSize="sm">
                      Non lues seulement
                    </FormLabel>
                    <Switch
                      id="unread-only"
                      isChecked={showUnreadOnly}
                      onChange={(e) => setShowUnreadOnly(e.target.checked)}
                      colorScheme="blue"
                    />
                  </FormControl>
                  
                  <Menu>
                    <MenuButton as={Button} rightIcon={<Icon as={asElementType(FiFilter)} />} size="sm">
                      Type: {filterType === 'all' ? 'Tous' : filterType}
                    </MenuButton>
                    <MenuList bg={cardBg} borderColor={borderColor}>
                      <MenuItem onClick={() => setFilterType('all')}>Tous</MenuItem>
                      <MenuItem onClick={() => setFilterType('document_uploaded')}>Documents ajoutés</MenuItem>
                      <MenuItem onClick={() => setFilterType('document_shared')}>Documents partagés</MenuItem>
                      <MenuItem onClick={() => setFilterType('document_commented')}>Commentaires</MenuItem>
                      <MenuItem onClick={() => setFilterType('workflow_assigned')}>Workflows</MenuItem>
                      <MenuItem onClick={() => setFilterType('user_mentioned')}>Mentions</MenuItem>
                    </MenuList>
                  </Menu>
                </HStack>
              </Flex>

              {/* Liste des notifications */}
              {loading ? (
                <Flex justify="center" py={8}>
                  <Spinner color="#3a8bfd" />
                </Flex>
              ) : notifications.length === 0 ? (
                <Alert status="info" bg={cardBg} color="white">
                  <AlertIcon color="#3a8bfd" />
                  {showUnreadOnly 
                    ? "Aucune notification non lue" 
                    : "Aucune notification"
                  }
                </Alert>
              ) : (
                <VStack align="stretch" spacing={3}>
                  {notifications.map((notification) => {
                    const priorityInfo = getPriorityLabel(notification.priority);
                    const NotificationIcon = getNotificationIcon(notification.type);
                    
                    return (
                      <Box
                        key={notification.id}
                        p={4}
                        bg={notification.is_read ? "transparent" : cardBg}
                        border="1px solid"
                        borderColor={notification.is_read ? borderColor : "#3a8bfd"}
                        borderRadius="lg"
                        position="relative"
                        cursor="pointer"
                        onClick={() => handleNotificationClick(notification)}
                        _hover={{
                          transform: "translateY(-2px)",
                          boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                          borderColor: "#3a8bfd"
                        }}
                        transition="all 0.2s"
                      >
                        <Flex justify="space-between" align="start">
                          <HStack align="start" spacing={3} flex={1}>
                            <Icon 
                              as={asElementType(NotificationIcon)} 
                              color={getNotificationColor(notification.type, notification.priority)}
                              boxSize={5}
                              mt={1}
                            />
                            
                            <VStack align="start" spacing={1} flex={1}>
                              <HStack spacing={2} wrap="wrap">
                                <Text 
                                  fontWeight={notification.is_read ? "normal" : "bold"}
                                  fontSize="md"
                                >
                                  {notification.title}
                                </Text>
                                
                                <Badge 
                                  colorScheme={getNotificationColor(notification.type, notification.priority)}
                                  size="sm"
                                >
                                  {notification.type.replace('_', ' ')}
                                </Badge>
                                
                                {notification.priority > 2 && (
                                  <Badge colorScheme={priorityInfo.color} size="sm">
                                    {priorityInfo.label}
                                  </Badge>
                                )}
                                
                                {!notification.is_read && (
                                  <Badge colorScheme="blue" size="sm">
                                    Nouveau
                                  </Badge>
                                )}
                              </HStack>
                              
                              <Text 
                                color="gray.300" 
                                fontSize="sm"
                                fontWeight={notification.is_read ? "normal" : "medium"}
                              >
                                {notification.message}
                              </Text>
                              
                              {notification.document_title && (
                                <Text fontSize="xs" color="gray.400">
                                  📄 {notification.document_title}
                                </Text>
                              )}
                              
                              <Text fontSize="xs" color="gray.500">
                                {formatDate(notification.created_at)}
                              </Text>
                            </VStack>
                          </HStack>
                          
                          <Menu>
                            <MenuButton
                              as={IconButton}
                              icon={<Icon as={asElementType(FiMoreVertical)} />}
                              variant="ghost"
                              size="sm"
                            />
                            <MenuList bg={cardBg} borderColor={borderColor}>
                              {!notification.is_read && (
                                <MenuItem
                                  icon={<Icon as={asElementType(FiEye)} />}
                                  onClick={() => handleMarkAsRead(notification.id)}
                                >
                                  Marquer comme lu
                                </MenuItem>
                              )}
                              <MenuItem
                                icon={<Icon as={asElementType(FiTrash2)} />}
                                onClick={() => handleDeleteNotification(notification.id)}
                                color="red.400"
                              >
                                Supprimer
                              </MenuItem>
                            </MenuList>
                          </Menu>
                        </Flex>
                      </Box>
                    );
                  })}
                </VStack>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <Flex justify="center" align="center" gap={2} mt={6}>
                  <Button
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    isDisabled={currentPage === 1}
                  >
                    Précédent
                  </Button>
                  
                  <Text fontSize="sm">
                    Page {currentPage} sur {totalPages}
                  </Text>
                  
                  <Button
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    isDisabled={currentPage === totalPages}
                  >
                    Suivant
                  </Button>
                </Flex>
              )}
            </VStack>
          </TabPanel>

          {/* Onglet Statistiques */}
          <TabPanel>
            {stats ? (
              <VStack align="stretch" spacing={6}>
                {/* Statistiques générales */}
                <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
                  <Stat bg={cardBg} p={4} borderRadius="lg">
                    <StatLabel>Total</StatLabel>
                    <StatNumber>{stats.general.total}</StatNumber>
                    <StatHelpText>notifications</StatHelpText>
                  </Stat>
                  
                  <Stat bg={cardBg} p={4} borderRadius="lg">
                    <StatLabel>Non lues</StatLabel>
                    <StatNumber color="red.400">{stats.general.unread}</StatNumber>
                    <StatHelpText>à traiter</StatHelpText>
                  </Stat>
                  
                  <Stat bg={cardBg} p={4} borderRadius="lg">
                    <StatLabel>Cette semaine</StatLabel>
                    <StatNumber color="blue.400">{stats.general.last_week}</StatNumber>
                    <StatHelpText>
                      <StatArrow type="increase" />
                      nouvelles
                    </StatHelpText>
                  </Stat>
                  
                  <Stat bg={cardBg} p={4} borderRadius="lg">
                    <StatLabel>Ce mois</StatLabel>
                    <StatNumber color="green.400">{stats.general.last_month}</StatNumber>
                    <StatHelpText>au total</StatHelpText>
                  </Stat>
                </SimpleGrid>

                {/* Répartition par type */}
                <Box bg={cardBg} p={4} borderRadius="lg">
                  <Heading size="md" mb={4}>Répartition par type (30 derniers jours)</Heading>
                  <VStack align="stretch" spacing={2}>
                    {stats.by_type.map((typeStat) => (
                      <Flex key={typeStat.type} justify="space-between" align="center">
                        <Text>{typeStat.type.replace('_', ' ')}</Text>
                        <HStack>
                          <Progress 
                            value={(typeStat.count / stats.general.last_month) * 100} 
                            size="sm" 
                            w="100px"
                            colorScheme="blue"
                          />
                          <Text fontSize="sm" minW="30px">{typeStat.count}</Text>
                        </HStack>
                      </Flex>
                    ))}
                  </VStack>
                </Box>
              </VStack>
            ) : (
              <Flex justify="center" py={8}>
                <Spinner color="#3a8bfd" />
              </Flex>
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* Modal des préférences */}
      <Modal isOpen={isPrefsOpen} onClose={onPrefsClose} size="lg">
        <ModalOverlay />
        <ModalContent bg={cardBg} color="white">
          <ModalHeader>Préférences de notification</ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            {preferences && (
              <VStack align="stretch" spacing={4}>
                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel htmlFor="email-notifs" mb="0">
                    <VStack align="start" spacing={0}>
                      <Text>Notifications par email</Text>
                      <Text fontSize="sm" color="gray.400">Recevoir les notifications par email</Text>
                    </VStack>
                  </FormLabel>
                  <Switch
                    id="email-notifs"
                    isChecked={preferences.email_notifications}
                    onChange={(e) => setPreferences(prev => 
                      prev ? { ...prev, email_notifications: e.target.checked } : null
                    )}
                    colorScheme="blue"
                  />
                </FormControl>

                <Divider />

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel htmlFor="app-notifs" mb="0">
                    <VStack align="start" spacing={0}>
                      <Text>Notifications dans l'app</Text>
                      <Text fontSize="sm" color="gray.400">Afficher les notifications dans l'application</Text>
                    </VStack>
                  </FormLabel>
                  <Switch
                    id="app-notifs"
                    isChecked={preferences.app_notifications}
                    onChange={(e) => setPreferences(prev => 
                      prev ? { ...prev, app_notifications: e.target.checked } : null
                    )}
                    colorScheme="blue"
                  />
                </FormControl>

                <Divider />

                <Text fontWeight="bold">Types de notifications</Text>

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel htmlFor="doc-notifs" mb="0">Documents</FormLabel>
                  <Switch
                    id="doc-notifs"
                    isChecked={preferences.document_notifications}
                    onChange={(e) => setPreferences(prev => 
                      prev ? { ...prev, document_notifications: e.target.checked } : null
                    )}
                    colorScheme="blue"
                  />
                </FormControl>

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel htmlFor="workflow-notifs" mb="0">Workflows</FormLabel>
                  <Switch
                    id="workflow-notifs"
                    isChecked={preferences.workflow_notifications}
                    onChange={(e) => setPreferences(prev => 
                      prev ? { ...prev, workflow_notifications: e.target.checked } : null
                    )}
                    colorScheme="blue"
                  />
                </FormControl>

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel htmlFor="comment-notifs" mb="0">Commentaires</FormLabel>
                  <Switch
                    id="comment-notifs"
                    isChecked={preferences.comment_notifications}
                    onChange={(e) => setPreferences(prev => 
                      prev ? { ...prev, comment_notifications: e.target.checked } : null
                    )}
                    colorScheme="blue"
                  />
                </FormControl>

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel htmlFor="share-notifs" mb="0">Partages</FormLabel>
                  <Switch
                    id="share-notifs"
                    isChecked={preferences.share_notifications}
                    onChange={(e) => setPreferences(prev => 
                      prev ? { ...prev, share_notifications: e.target.checked } : null
                    )}
                    colorScheme="blue"
                  />
                </FormControl>

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel htmlFor="mention-notifs" mb="0">Mentions</FormLabel>
                  <Switch
                    id="mention-notifs"
                    isChecked={preferences.mention_notifications}
                    onChange={(e) => setPreferences(prev => 
                      prev ? { ...prev, mention_notifications: e.target.checked } : null
                    )}
                    colorScheme="blue"
                  />
                </FormControl>

                <Divider />

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel htmlFor="weekend-notifs" mb="0">
                    <VStack align="start" spacing={0}>
                      <Text>Notifications le weekend</Text>
                      <Text fontSize="sm" color="gray.400">Recevoir des notifications le samedi et dimanche</Text>
                    </VStack>
                  </FormLabel>
                  <Switch
                    id="weekend-notifs"
                    isChecked={preferences.weekend_notifications}
                    onChange={(e) => setPreferences(prev => 
                      prev ? { ...prev, weekend_notifications: e.target.checked } : null
                    )}
                    colorScheme="blue"
                  />
                </FormControl>
              </VStack>
            )}
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onPrefsClose}>
              Annuler
            </Button>
            <Button 
              colorScheme="blue" 
              onClick={() => preferences && handleUpdatePreferences(preferences)}
            >
              Sauvegarder
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Modal de détail de notification */}
      <NotificationModal
        isOpen={isNotificationModalOpen}
        onClose={handleCloseNotificationModal}
        notification={selectedNotification}
        onNotificationUpdated={handleNotificationUpdated}
      />
    </Box>
  );
};

export default NotificationCenter; 