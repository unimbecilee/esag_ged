import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Select,
  useToast,
  VStack,
  Text,
  Box,
} from '@chakra-ui/react';
import { API_URL } from '../config';
import { useAsyncOperation } from '../hooks/useAsyncOperation';

interface User {
  id: number;
  nom: string;
  prenom: string;
  username: string;
  email: string;
}

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentId?: number | null;
  onShareSuccess?: () => void;
}

const ShareModal: React.FC<ShareModalProps> = ({
  isOpen,
  onClose,
  documentId = null,
  onShareSuccess,
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [permissions, setPermissions] = useState('lecture');
  const [loading, setLoading] = useState(false);
  const toast = useToast();
  const { executeOperation } = useAsyncOperation();

  useEffect(() => {
    if (isOpen) {
      fetchUsers();
      setSelectedUser(''); // Réinitialiser la sélection à chaque ouverture
    }
  }, [isOpen]);

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_URL}/users/sharing`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        throw new Error('Erreur lors de la récupération des utilisateurs');
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de récupérer la liste des utilisateurs',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleShare = async () => {
    if (!documentId) {
      toast({
        title: 'Erreur',
        description: 'Aucun document sélectionné',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    if (!selectedUser) {
      toast({
        title: 'Erreur',
        description: 'Veuillez sélectionner un utilisateur',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setLoading(true);
    try {
      const success = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }
          
          const response = await fetch(`${API_URL}/documents/share`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              document_id: documentId,
              utilisateur_id: parseInt(selectedUser),
              permissions: permissions,
            }),
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.message || 'Erreur lors du partage');
          }
          
          return true;
        },
        {
          loadingMessage: "Partage en cours...",
          successMessage: "Document partagé avec succès",
          errorMessage: "Impossible de partager le document"
        }
      );
      
      if (success) {
        onShareSuccess?.();
        onClose();
        setSelectedUser('');
      }
    } catch (error) {
      // L'erreur est déjà gérée par executeOperation
      console.error("Erreur de partage:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent bg="#20243a">
        <ModalHeader color="white">Partager le document</ModalHeader>
        <ModalCloseButton color="white" />
        <ModalBody>
          <VStack spacing={4}>
            {users.length === 0 ? (
              <Box p={4} bg="#232946" borderRadius="md" width="full">
                <Text color="white" textAlign="center">
                  Chargement des utilisateurs...
                </Text>
              </Box>
            ) : (
              <>
                <FormControl>
                  <FormLabel color="white">Utilisateur</FormLabel>
                  <Select
                    value={selectedUser}
                    onChange={(e) => setSelectedUser(e.target.value)}
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                    _hover={{ borderColor: "#3a8bfd" }}
                    _focus={{
                      borderColor: "#3a8bfd",
                      boxShadow: "0 0 0 1.5px #3a8bfd",
                    }}
                  >
                    <option value="">Sélectionner un utilisateur</option>
                    {users.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.prenom || user.username} {user.nom || user.email}
                      </option>
                    ))}
                  </Select>
                </FormControl>
                <FormControl>
                  <FormLabel color="white">Permissions</FormLabel>
                  <Select
                    value={permissions}
                    onChange={(e) => setPermissions(e.target.value)}
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                    _hover={{ borderColor: "#3a8bfd" }}
                    _focus={{
                      borderColor: "#3a8bfd",
                      boxShadow: "0 0 0 1.5px #3a8bfd",
                    }}
                  >
                    <option value="lecture">Lecture seule</option>
                    <option value="edition">Édition</option>
                    <option value="admin">Administration</option>
                  </Select>
                </FormControl>
              </>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button
            variant="ghost"
            mr={3}
            onClick={onClose}
            color="white"
            _hover={{ bg: "#232946" }}
          >
            Annuler
          </Button>
          <Button
            colorScheme="blue"
            onClick={handleShare}
            isLoading={loading}
            isDisabled={users.length === 0 || !selectedUser}
          >
            Partager
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default ShareModal; 