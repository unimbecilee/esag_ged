import React, { useState, useEffect } from 'react';
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
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
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
} from '@chakra-ui/react';
import {
  FiBell,
  FiBellOff,
  FiCheck,
  FiX,
  FiMoreVertical,
  FiEye,
  FiTrash2,
  FiSettings,
  FiRefreshCw
} from 'react-icons/fi';
import { asElementType } from '../utils/iconUtils';
import config from '../config';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import NotificationModal from './NotificationModal';
import { Notification, Subscription } from '../types/notifications';

const Notifications: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  const [isNotificationModalOpen, setIsNotificationModalOpen] = useState(false);
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getNotificationTypeColor = (type: string) => {
    switch (type) {
      case 'modification': return 'blue';
      case 'commentaire': return 'green';
      case 'partage': return 'purple';
      case 'suppression': return 'red';
      default: return 'gray';
    }
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/notifications?unread_only=${showUnreadOnly}`,
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
  };

  const fetchSubscriptions = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/api/documents/my-subscriptions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSubscriptions(data.subscriptions || []);
      }
    } catch (error) {
      console.error('Erreur subscriptions:', error);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/api/notifications/unread-count`, {
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
  };

  const handleMarkAsRead = async (notificationId: number) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/notifications/${notificationId}/read`,
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
        `${config.API_URL}/api/notifications/mark-all-read`,
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

  const handleUnsubscribe = async (documentId: number) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/documents/${documentId}/unsubscribe`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        fetchSubscriptions();
      } else {
        throw new Error('Erreur lors du désabonnement');
      }
    }, {
      successMessage: 'Désabonnement effectué avec succès',
      errorMessage: 'Erreur lors du désabonnement'
    });
  };

  const handleNotificationClick = (notification: Notification) => {
    setSelectedNotification(notification);
    setIsNotificationModalOpen(true);
  };

  const handleNotificationUpdated = () => {
    fetchNotifications();
    fetchUnreadCount();
  };

  const handleCloseNotificationModal = () => {
    setIsNotificationModalOpen(false);
    setSelectedNotification(null);
  };

  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();
    fetchSubscriptions();
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [showUnreadOnly]);

  return (
    <Box p={6} bg="#181c2f" minH="100vh" color="white">
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          <Flex align="center" gap={3}>
            <Icon as={asElementType(FiBell)} color="#3a8bfd" />
            Notifications
            {unreadCount > 0 && (
              <Badge colorScheme="red" borderRadius="full" px={2}>
                {unreadCount}
              </Badge>
            )}
          </Flex>
        </Heading>
        
        <HStack spacing={3}>
          <Button
            leftIcon={<Icon as={asElementType(FiRefreshCw)} />}
            variant="outline"
            onClick={() => {
              fetchNotifications();
              fetchUnreadCount();
              fetchSubscriptions();
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
          <Tab>Mes abonnements</Tab>
        </TabList>

        <TabPanels>
          {/* Onglet Notifications */}
          <TabPanel>
            <VStack align="stretch" spacing={4}>
              <Flex justify="space-between" align="center">
                <FormControl display="flex" alignItems="center" w="auto">
                  <FormLabel htmlFor="unread-only" mb="0" fontSize="sm">
                    Afficher seulement les non lues
                  </FormLabel>
                  <Switch
                    id="unread-only"
                    isChecked={showUnreadOnly}
                    onChange={(e) => setShowUnreadOnly(e.target.checked)}
                    colorScheme="blue"
                  />
                </FormControl>
              </Flex>

              {loading ? (
                <Flex justify="center" py={8}>
                  <Spinner color="#3a8bfd" />
                </Flex>
              ) : notifications.length === 0 ? (
                <Alert status="info" bg="#2a3657" color="white">
                  <AlertIcon color="#3a8bfd" />
                  {showUnreadOnly 
                    ? "Aucune notification non lue" 
                    : "Aucune notification"
                  }
                </Alert>
              ) : (
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th color="white">Statut</Th>
                      <Th color="white">Type</Th>
                      <Th color="white">Message</Th>
                      <Th color="white">Document</Th>
                      <Th color="white">Date</Th>
                      <Th color="white">Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {notifications.map((notification) => (
                      <Tr 
                        key={notification.id}
                        bg={notification.is_read ? "transparent" : "#2a3657"}
                        onClick={() => handleNotificationClick(notification)}
                        cursor="pointer"
                        _hover={{ bg: "#363b5a" }}
                        transition="background-color 0.2s"
                      >
                        <Td>
                          {notification.is_read ? (
                            <Badge colorScheme="gray">Lu</Badge>
                          ) : (
                            <Badge colorScheme="blue">Non lu</Badge>
                          )}
                        </Td>
                        <Td>
                          <Badge colorScheme={getNotificationTypeColor(notification.type)}>
                            {notification.type}
                          </Badge>
                        </Td>
                        <Td>
                          <Text fontWeight={notification.is_read ? "normal" : "bold"}>
                            {notification.message}
                          </Text>
                        </Td>
                        <Td>
                          {notification.document_title && (
                            <Text fontSize="sm" color="gray.300">
                              {notification.document_title}
                            </Text>
                          )}
                        </Td>
                        <Td>
                          <Text fontSize="sm" color="gray.400">
                            {formatDate(notification.created_at)}
                          </Text>
                        </Td>
                        <Td>
                          <Menu>
                            <MenuButton
                              as={IconButton}
                              icon={<Icon as={asElementType(FiMoreVertical)} />}
                              variant="ghost"
                              size="sm"
                            />
                            <MenuList bg="#2a3657" borderColor="#3a445e">
                              {!notification.is_read && (
                                <MenuItem
                                  icon={<Icon as={asElementType(FiEye)} />}
                                  onClick={() => handleMarkAsRead(notification.id)}
                                  _hover={{ bg: "#363b5a" }}
                                >
                                  Marquer comme lu
                                </MenuItem>
                              )}
                              <MenuItem
                                icon={<Icon as={asElementType(FiTrash2)} />}
                                onClick={() => {
                                  // TODO: Implémenter la suppression
                                  toast({
                                    title: 'Fonctionnalité à venir',
                                    description: 'La suppression sera bientôt disponible',
                                    status: 'info',
                                    duration: 3000,
                                    isClosable: true,
                                  });
                                }}
                                _hover={{ bg: "#363b5a" }}
                                color="red.400"
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
            </VStack>
          </TabPanel>

          {/* Onglet Abonnements */}
          <TabPanel>
            {subscriptions.length === 0 ? (
              <Alert status="info" bg="#2a3657" color="white">
                <AlertIcon color="#3a8bfd" />
                Vous n'êtes abonné à aucun document
              </Alert>
            ) : (
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th color="white">Document</Th>
                    <Th color="white">Types de notifications</Th>
                    <Th color="white">Date d'abonnement</Th>
                    <Th color="white">Statut</Th>
                    <Th color="white">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {subscriptions.map((subscription) => (
                    <Tr key={subscription.id}>
                      <Td>
                        <Text fontWeight="bold">
                          {subscription.document_title}
                        </Text>
                      </Td>
                      <Td>
                        <HStack spacing={1} flexWrap="wrap">
                          {subscription.notification_types.map((type) => (
                            <Badge 
                              key={type} 
                              colorScheme={getNotificationTypeColor(type)}
                              fontSize="xs"
                            >
                              {type}
                            </Badge>
                          ))}
                        </HStack>
                      </Td>
                      <Td>
                        <Text fontSize="sm" color="gray.400">
                          {formatDate(subscription.created_at)}
                        </Text>
                      </Td>
                      <Td>
                        <Badge colorScheme={subscription.is_active ? "green" : "red"}>
                          {subscription.is_active ? "Actif" : "Inactif"}
                        </Badge>
                      </Td>
                      <Td>
                        <Menu>
                          <MenuButton
                            as={IconButton}
                            icon={<Icon as={asElementType(FiMoreVertical)} />}
                            variant="ghost"
                            size="sm"
                          />
                          <MenuList bg="#2a3657" borderColor="#3a445e">
                            <MenuItem
                              icon={<Icon as={asElementType(FiSettings)} />}
                              onClick={() => {
                                // TODO: Ouvrir modal de modification
                                toast({
                                  title: 'Fonctionnalité à venir',
                                  description: 'La modification sera bientôt disponible',
                                  status: 'info',
                                  duration: 3000,
                                  isClosable: true,
                                });
                              }}
                              _hover={{ bg: "#363b5a" }}
                            >
                              Modifier
                            </MenuItem>
                            <MenuItem
                              icon={<Icon as={asElementType(FiBellOff)} />}
                              onClick={() => handleUnsubscribe(subscription.document_id)}
                              _hover={{ bg: "#363b5a" }}
                              color="red.400"
                            >
                              Se désabonner
                            </MenuItem>
                          </MenuList>
                        </Menu>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            )}
          </TabPanel>
        </TabPanels>
      </Tabs>

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

export default Notifications; 

