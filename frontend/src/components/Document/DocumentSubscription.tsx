import React, { useState, useEffect } from 'react';
import {
  Button,
  useToast,
  Icon,
  Text,
  Flex,
  Badge,
  Tooltip,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  VStack,
  Checkbox,
  CheckboxGroup,
  Alert,
  AlertIcon,
  Box,
} from '@chakra-ui/react';
import { 
  FiBell, 
  FiBellOff,
  FiSettings
} from 'react-icons/fi';
import { asElementType } from '../../utils/iconUtils';
import config from '../../config';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';

interface Subscription {
  id: number;
  document_id: number;
  user_id: number;
  notification_types: string[];
  created_at: string;
  is_active: boolean;
}

interface DocumentSubscriptionProps {
  documentId: number;
  onSubscriptionChange?: (isSubscribed: boolean) => void;
}

const DocumentSubscription: React.FC<DocumentSubscriptionProps> = ({
  documentId,
  onSubscriptionChange
}) => {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [selectedNotifications, setSelectedNotifications] = useState<string[]>(['all']);
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  const notificationOptions = [
    { value: 'all', label: 'Toutes les notifications' },
    { value: 'modification', label: 'Modifications du document' },
    { value: 'commentaire', label: 'Nouveaux commentaires' },
    { value: 'partage', label: 'Partages du document' },
    { value: 'suppression', label: 'Suppression du document' }
  ];

  const fetchSubscriptionStatus = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/documents/${documentId}/subscription`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setIsSubscribed(data.is_subscribed);
        setSubscription(data.subscription);
        if (data.subscription) {
          setSelectedNotifications(data.subscription.notification_types || ['all']);
        }
      } else {
        throw new Error('Erreur lors de la vérification de l\'abonnement');
      }
    } catch (error) {
      console.error('Erreur subscription status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async () => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/documents/${documentId}/subscribe`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ notification_types: selectedNotifications })
        }
      );

      if (response.ok) {
        setIsSubscribed(true);
        fetchSubscriptionStatus();
        onSubscriptionChange?.(true);
        setShowSettingsModal(false);
      } else {
        throw new Error('Erreur lors de l\'abonnement');
      }
    }, {
      successMessage: 'Abonnement créé avec succès',
      errorMessage: 'Erreur lors de l\'abonnement'
    });
  };

  const handleUpdateSubscription = async () => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/documents/${documentId}/subscription`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ notification_types: selectedNotifications })
        }
      );

      if (response.ok) {
        fetchSubscriptionStatus();
        setShowSettingsModal(false);
      } else {
        throw new Error('Erreur lors de la mise à jour');
      }
    }, {
      successMessage: 'Préférences mises à jour',
      errorMessage: 'Erreur lors de la mise à jour'
    });
  };

  const handleUnsubscribe = async () => {
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
        setIsSubscribed(false);
        setSubscription(null);
        onSubscriptionChange?.(false);
      } else {
        throw new Error('Erreur lors du désabonnement');
      }
    }, {
      successMessage: 'Désabonnement effectué avec succès',
      errorMessage: 'Erreur lors du désabonnement'
    });
  };

  useEffect(() => {
    fetchSubscriptionStatus();
  }, [documentId]);

  if (loading) {
    return null;
  }

  return (
    <>
      <Flex gap={2} align="center">
        {!isSubscribed ? (
          <Tooltip label="S'abonner aux notifications de ce document">
            <Button
              leftIcon={<Icon as={asElementType(FiBell)} />}
              colorScheme="blue"
              variant="outline"
              size="sm"
              onClick={() => setShowSettingsModal(true)}
            >
              S'abonner
            </Button>
          </Tooltip>
        ) : (
          <>
            <Flex align="center" gap={2}>
              <Icon as={asElementType(FiBell)} color="green.400" />
              <Badge colorScheme="green" px={2} py={1}>
                Abonné
              </Badge>
            </Flex>
            
            <Tooltip label="Modifier les préférences de notification">
              <Button
                leftIcon={<Icon as={asElementType(FiSettings)} />}
                variant="ghost"
                size="sm"
                onClick={() => setShowSettingsModal(true)}
              >
                Préférences
              </Button>
            </Tooltip>
            
            <Tooltip label="Se désabonner des notifications">
              <Button
                leftIcon={<Icon as={asElementType(FiBellOff)} />}
                colorScheme="red"
                variant="outline"
                size="sm"
                onClick={handleUnsubscribe}
              >
                Se désabonner
              </Button>
            </Tooltip>
          </>
        )}
      </Flex>

      <Modal isOpen={showSettingsModal} onClose={() => setShowSettingsModal(false)}>
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white">
          <ModalHeader>
            {isSubscribed ? 'Préférences de notification' : 'S\'abonner aux notifications'}
          </ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            <VStack align="stretch" spacing={4}>
              <Text>
                Choisissez les types de notifications que vous souhaitez recevoir pour ce document :
              </Text>
              
              <CheckboxGroup
                value={selectedNotifications}
                onChange={(values) => setSelectedNotifications(values as string[])}
              >
                <VStack align="stretch" spacing={3}>
                  {notificationOptions.map((option) => (
                    <Checkbox
                      key={option.value}
                      value={option.value}
                      colorScheme="blue"
                    >
                      <Text fontSize="sm">{option.label}</Text>
                    </Checkbox>
                  ))}
                </VStack>
              </CheckboxGroup>

              {selectedNotifications.includes('all') && selectedNotifications.length > 1 && (
                <Alert status="info" bg="#2a3657" color="white">
                  <AlertIcon color="#3a8bfd" />
                  <Text fontSize="sm">
                    "Toutes les notifications" inclut automatiquement tous les autres types.
                  </Text>
                </Alert>
              )}
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={() => setShowSettingsModal(false)}>
              Annuler
            </Button>
            <Button 
              colorScheme="blue" 
              onClick={isSubscribed ? handleUpdateSubscription : handleSubscribe}
              isDisabled={selectedNotifications.length === 0}
            >
              {isSubscribed ? 'Mettre à jour' : 'S\'abonner'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default DocumentSubscription; 


