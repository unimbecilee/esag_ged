import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Box,
  Text,
  Badge,
  Button,
  VStack,
  HStack,
  Divider,
  Icon,
  Flex,
  Link,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  Tooltip
} from '@chakra-ui/react';
import {
  FiBell,
  FiFileText,
  FiUsers,
  FiMessageSquare,
  FiClock,
  FiSettings,
  FiExternalLink,
  FiEye,
  FiCalendar,
  FiUser,
  FiTag
} from 'react-icons/fi';
import { asElementType } from '../utils/iconUtils';
import config from '../config';
import { Notification } from '../types/notifications';

interface NotificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  notification: Notification | null;
  onNotificationUpdated?: () => void;
}

const NotificationModal: React.FC<NotificationModalProps> = ({
  isOpen,
  onClose,
  notification,
  onNotificationUpdated
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [hasMarkedAsRead, setHasMarkedAsRead] = useState(false);
  const toast = useToast();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      year: 'numeric',
      month: 'long',
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
      case 'workflow_approved':
      case 'workflow_rejected':
        return FiClock;
      case 'user_mentioned':
        return FiBell;
      case 'system_maintenance':
        return FiSettings;
      default:
        return FiBell;
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'document_uploaded':
      case 'document_updated':
        return 'blue';
      case 'document_shared':
        return 'green';
      case 'document_commented':
        return 'purple';
      case 'workflow_assigned':
        return 'orange';
      case 'workflow_approved':
        return 'green';
      case 'workflow_rejected':
        return 'red';
      case 'user_mentioned':
        return 'yellow';
      case 'system_maintenance':
        return 'gray';
      default:
        return 'blue';
    }
  };

  const getPriorityLabel = (priority: number) => {
    switch (priority) {
      case 1:
        return { label: 'Faible', color: 'gray' };
      case 2:
        return { label: 'Normale', color: 'blue' };
      case 3:
        return { label: 'Haute', color: 'orange' };
      case 4:
        return { label: 'Urgente', color: 'red' };
      default:
        return { label: 'Normale', color: 'blue' };
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'document_uploaded':
        return 'Document téléversé';
      case 'document_updated':
        return 'Document modifié';
      case 'document_shared':
        return 'Document partagé';
      case 'document_commented':
        return 'Nouveau commentaire';
      case 'workflow_assigned':
        return 'Validation assignée';
      case 'workflow_approved':
        return 'Workflow approuvé';
      case 'workflow_rejected':
        return 'Workflow rejeté';
      case 'user_mentioned':
        return 'Mention utilisateur';
      case 'system_maintenance':
        return 'Maintenance système';
      default:
        return 'Notification';
    }
  };

  const markAsReadAutomatically = async () => {
    if (!notification || notification.is_read || hasMarkedAsRead) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/notifications/${notification.id}/read`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        setHasMarkedAsRead(true);
        onNotificationUpdated?.();
        
        // Notification discrète de marquage
        toast({
          title: 'Notification marquée comme lue',
          status: 'success',
          duration: 2000,
          isClosable: true,
          position: 'bottom-right'
        });
      }
    } catch (error) {
      console.error('Erreur lors du marquage automatique:', error);
    }
  };

  const handleActionClick = async () => {
    if (!notification) return;

    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/notifications/${notification.id}/click`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const result = await response.json();
        
        // Fermer le modal
        onClose();
        
        // Mettre à jour les notifications
        onNotificationUpdated?.();
        
        // Rediriger vers l'URL appropriée
        let redirectUrl = result.redirect_url;
        
        // Si pas d'URL de redirection, construire une URL par défaut
        if (!redirectUrl) {
          if (notification.type.includes('workflow') && notification.workflow_id) {
            redirectUrl = `/workflow?tab=1`;
          } else if (notification.document_id) {
            redirectUrl = `/documents`;
          } else {
            redirectUrl = '/dashboard';
          }
        }
        
        if (redirectUrl) {
          // Navigation interne
          if (redirectUrl.startsWith('http')) {
            window.open(redirectUrl, '_blank');
          } else {
            window.location.href = redirectUrl;
          }
        }
        
        toast({
          title: 'Redirection en cours...',
          status: 'info',
          duration: 2000,
          isClosable: true
        });
        
      } else {
        throw new Error('Erreur lors de l\'action');
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible d\'effectuer l\'action',
        status: 'error',
        duration: 3000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Marquer automatiquement comme lu à l'ouverture du modal
  useEffect(() => {
    if (isOpen && notification && !notification.is_read) {
      // Délai de 2 secondes pour que l'utilisateur ait le temps de voir
      const timer = setTimeout(() => {
        markAsReadAutomatically();
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, [isOpen, notification]);

  if (!notification) {
    return null;
  }

  const IconComponent = getNotificationIcon(notification.type);
  const notificationColor = getNotificationColor(notification.type);
  const priorityInfo = getPriorityLabel(notification.priority);
  const typeLabel = getTypeLabel(notification.type);

  // Parsing des métadonnées
  let metadata = notification.metadata;
  if (typeof metadata === 'string') {
    try {
      metadata = JSON.parse(metadata);
    } catch {
      metadata = {};
    }
  }

  const isExpired = notification.expires_at && new Date(notification.expires_at) < new Date();

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay bg="blackAlpha.600" />
      <ModalContent bg="#20243a" color="white" borderRadius="lg" border="1px" borderColor="#3a445e">
        <ModalHeader pb={2}>
          <Flex align="center" gap={3}>
            <Box
              p={2}
              borderRadius="full"
              bg={`${notificationColor}.500`}
              color="white"
            >
              <Icon as={asElementType(IconComponent)} size="20px" />
            </Box>
            <VStack align="start" spacing={0} flex={1}>
              <Text fontSize="lg" fontWeight="bold" color="white">
                {notification.title}
              </Text>
              <HStack spacing={2}>
                <Badge colorScheme={notificationColor} fontSize="xs">
                  {typeLabel}
                </Badge>
                <Badge colorScheme={priorityInfo.color} fontSize="xs">
                  {priorityInfo.label}
                </Badge>
                {!notification.is_read && !hasMarkedAsRead && (
                  <Badge colorScheme="red" fontSize="xs">
                    Non lu
                  </Badge>
                )}
                {isExpired && (
                  <Badge colorScheme="gray" fontSize="xs">
                    Expirée
                  </Badge>
                )}
              </HStack>
            </VStack>
          </Flex>
        </ModalHeader>
        <ModalCloseButton />

        <ModalBody py={4}>
          <VStack align="stretch" spacing={4}>
            {/* Message principal */}
            <Box p={4} bg="#2a3657" borderRadius="md" border="1px" borderColor="#3a445e">
              <Text fontSize="md" lineHeight="1.6">
                {notification.message}
              </Text>
            </Box>

            {/* Informations détaillées */}
            <VStack align="stretch" spacing={3}>
              <Divider borderColor="#3a445e" />
              
              <HStack justify="space-between">
                <HStack>
                  <Icon as={asElementType(FiCalendar)} color="gray.400" />
                  <Text fontSize="sm" color="gray.400">Date :</Text>
                </HStack>
                <Text fontSize="sm">{formatDate(notification.created_at)}</Text>
              </HStack>

              {notification.document_title && (
                <HStack justify="space-between">
                  <HStack>
                    <Icon as={asElementType(FiFileText)} color="gray.400" />
                    <Text fontSize="sm" color="gray.400">Document :</Text>
                  </HStack>
                  <Text fontSize="sm" fontWeight="medium" color="blue.300">
                    {notification.document_title}
                  </Text>
                </HStack>
              )}

              {notification.expires_at && (
                <HStack justify="space-between">
                  <HStack>
                    <Icon as={asElementType(FiClock)} color="gray.400" />
                    <Text fontSize="sm" color="gray.400">Expire le :</Text>
                  </HStack>
                  <Text 
                    fontSize="sm" 
                    color={isExpired ? "red.300" : "orange.300"}
                    fontWeight="medium"
                  >
                    {formatDate(notification.expires_at)}
                  </Text>
                </HStack>
              )}

              {/* Métadonnées supplémentaires */}
              {metadata && Object.keys(metadata).length > 0 && (
                <>
                  <Divider borderColor="#3a445e" />
                  <Box>
                    <Text fontSize="sm" color="gray.400" mb={2}>
                      <Icon as={asElementType(FiTag)} mr={2} />
                      Informations supplémentaires :
                    </Text>
                    <Box pl={4}>
                      {Object.entries(metadata).map(([key, value]) => (
                        <HStack key={key} justify="space-between" mb={1}>
                          <Text fontSize="xs" color="gray.500" textTransform="capitalize">
                            {key.replace(/_/g, ' ')} :
                          </Text>
                          <Text fontSize="xs" color="gray.300">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </Text>
                        </HStack>
                      ))}
                    </Box>
                  </Box>
                </>
              )}
            </VStack>

            {/* Marquage automatique info */}
            {!notification.is_read && !hasMarkedAsRead && (
              <Alert status="info" bg="#2a3657" color="white" fontSize="sm">
                <AlertIcon color="#3a8bfd" />
                Cette notification sera automatiquement marquée comme lue dans quelques secondes.
              </Alert>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter pt={2}>
          <HStack spacing={3}>
            <Button
              variant="outline"
              onClick={onClose}
              size="sm"
            >
              Fermer
            </Button>
            
            {(notification.document_id || notification.workflow_id || notification.type.includes('workflow')) && (
              <Button
                colorScheme="blue"
                onClick={handleActionClick}
                isLoading={isLoading}
                loadingText="Redirection..."
                leftIcon={<Icon as={asElementType(FiExternalLink)} />}
                size="sm"
              >
                Voir les détails
              </Button>
            )}

            {!notification.is_read && !hasMarkedAsRead && (
              <Tooltip label="Marquer manuellement comme lu">
                <Button
                  colorScheme="green"
                  variant="outline"
                  onClick={markAsReadAutomatically}
                  leftIcon={<Icon as={asElementType(FiEye)} />}
                  size="sm"
                >
                  Marquer comme lu
                </Button>
              </Tooltip>
            )}
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default NotificationModal; 


