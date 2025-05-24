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
} from '@chakra-ui/react';

interface User {
  id: number;
  nom: string;
  prenom: string;
}

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number;
  onShareSuccess: () => void;
}

const ShareModal: React.FC<ShareModalProps> = ({
  isOpen,
  onClose,
  documentId,
  onShareSuccess,
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [permissions, setPermissions] = useState('lecture');
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/users', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
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
      const response = await fetch('http://localhost:5000/api/documents/share', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          document_id: documentId,
          utilisateur_id: selectedUser,
          permissions: permissions,
        }),
      });

      if (response.ok) {
        toast({
          title: 'Succès',
          description: 'Document partagé avec succès',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        onShareSuccess();
        onClose();
      } else {
        throw new Error('Erreur lors du partage');
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de partager le document',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
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
                    {user.prenom} {user.nom}
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
          >
            Partager
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default ShareModal; 