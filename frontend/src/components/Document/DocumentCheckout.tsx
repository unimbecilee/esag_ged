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
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Alert,
  AlertIcon,
  Box,
} from '@chakra-ui/react';
import { 
  FiLock, 
  FiUnlock, 
  FiClock, 
  FiUser,
  FiAlertTriangle
} from 'react-icons/fi';
import { asElementType } from '../../utils/iconUtils';
import config from '../../config';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';

interface CheckoutStatus {
  is_checked_out: boolean;
  checkout?: {
    id: number;
    checked_out_by: number;
    checked_out_at: string;
    expiration: string;
    is_current_user: boolean;
    is_expired: boolean;
    user_nom: string;
    user_prenom: string;
  };
}

interface DocumentCheckoutProps {
  documentId: number;
  onStatusChange?: () => void;
}

const DocumentCheckout: React.FC<DocumentCheckoutProps> = ({
  documentId,
  onStatusChange
}) => {
  const [checkoutStatus, setCheckoutStatus] = useState<CheckoutStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [duration, setDuration] = useState(24);
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

  const fetchCheckoutStatus = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/documents/${documentId}/checkout/status`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setCheckoutStatus(data);
      } else {
        throw new Error('Erreur lors de la vérification du statut');
      }
    } catch (error) {
      console.error('Erreur checkout status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckout = async () => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/documents/${documentId}/checkout`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ duration_hours: duration })
        }
      );

      if (response.ok) {
        setShowCheckoutModal(false);
        fetchCheckoutStatus();
        onStatusChange && onStatusChange();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de la réservation');
      }
    }, {
      loadingMessage: 'Réservation en cours...',
      successMessage: 'Document réservé avec succès',
      errorMessage: 'Erreur lors de la réservation'
    });
  };

  const handleCheckin = async () => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/documents/${documentId}/checkin`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        fetchCheckoutStatus();
        onStatusChange && onStatusChange();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de la libération');
      }
    }, {
      loadingMessage: 'Libération en cours...',
      successMessage: 'Document libéré avec succès',
      errorMessage: 'Erreur lors de la libération'
    });
  };

  const handleForceCheckin = async () => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/documents/${documentId}/checkout/force-checkin`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        fetchCheckoutStatus();
        onStatusChange && onStatusChange();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de la libération forcée');
      }
    }, {
      loadingMessage: 'Libération forcée en cours...',
      successMessage: 'Document libéré de force avec succès',
      errorMessage: 'Erreur lors de la libération forcée'
    });
  };

  useEffect(() => {
    fetchCheckoutStatus();
  }, [documentId]);

  if (loading || !checkoutStatus) {
    return null;
  }

  const { is_checked_out, checkout } = checkoutStatus;

  if (!is_checked_out) {
    return (
      <>
        <Tooltip label="Réserver ce document pour modification exclusive">
          <Button
            leftIcon={<Icon as={asElementType(FiLock)} />}
            colorScheme="blue"
            variant="outline"
            size="sm"
            onClick={() => setShowCheckoutModal(true)}
          >
            Réserver
          </Button>
        </Tooltip>

        <Modal isOpen={showCheckoutModal} onClose={() => setShowCheckoutModal(false)}>
          <ModalOverlay />
          <ModalContent bg="#20243a" color="white">
            <ModalHeader>Réserver le document</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <Text mb={4}>
                Réserver ce document vous donnera un accès exclusif pour modification.
                Aucun autre utilisateur ne pourra le modifier pendant la durée de réservation.
              </Text>
              
              <FormControl>
                <FormLabel>Durée de réservation (heures)</FormLabel>
                <NumberInput
                  value={duration}
                  onChange={(_, value) => setDuration(value || 24)}
                  min={1}
                  max={168} // 7 jours max
                  bg="#2a3657"
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
            </ModalBody>

            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={() => setShowCheckoutModal(false)}>
                Annuler
              </Button>
              <Button colorScheme="blue" onClick={handleCheckout}>
                Réserver
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </>
    );
  }

  if (checkout) {
    const isCurrentUser = checkout.is_current_user;
    const isExpired = checkout.is_expired;

    return (
      <Flex direction="column" gap={2}>
        <Flex align="center" gap={2}>
          <Icon 
            as={asElementType(isExpired ? FiAlertTriangle : FiLock)} 
            color={isExpired ? "orange.400" : "red.400"} 
          />
          <Badge 
            colorScheme={isExpired ? "orange" : "red"}
            px={2}
            py={1}
          >
            {isExpired ? "Réservation expirée" : "Réservé"}
          </Badge>
        </Flex>

        <Box fontSize="sm" color="gray.300">
          <Flex align="center" gap={2} mb={1}>
            <Icon as={asElementType(FiUser)} />
            <Text>
              Par: {checkout.user_prenom} {checkout.user_nom}
              {isCurrentUser && " (vous)"}
            </Text>
          </Flex>
          <Flex align="center" gap={2}>
            <Icon as={asElementType(FiClock)} />
            <Text>
              Expire le: {formatDate(checkout.expiration)}
            </Text>
          </Flex>
        </Box>

        {isExpired && (
          <Alert status="warning" size="sm" bg="#2a3657" color="white">
            <AlertIcon color="orange.400" />
            Cette réservation a expiré
          </Alert>
        )}

        <Flex gap={2} mt={2}>
          {isCurrentUser && (
            <Button
              leftIcon={<Icon as={asElementType(FiUnlock)} />}
              colorScheme="green"
              variant="outline"
              size="sm"
              onClick={handleCheckin}
            >
              Libérer
            </Button>
          )}
          
          {/* TODO: Ajouter vérification des droits admin */}
          {!isCurrentUser && (
            <Tooltip label="Libération forcée (administrateur uniquement)">
              <Button
                leftIcon={<Icon as={asElementType(FiUnlock)} />}
                colorScheme="orange"
                variant="outline"
                size="sm"
                onClick={handleForceCheckin}
              >
                Libérer (Force)
              </Button>
            </Tooltip>
          )}
        </Flex>
      </Flex>
    );
  }

  return null;
};

export default DocumentCheckout; 