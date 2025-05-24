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
  email: string;
}

interface AddMemberModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  organizationId: number;
}

const AddMemberModal: React.FC<AddMemberModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  organizationId
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [role, setRole] = useState<'ADMIN' | 'MEMBRE'>('MEMBRE');
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    if (isOpen) {
      fetchUsers();
    }
  }, [isOpen]);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la récupération des utilisateurs');
      }

      const data = await response.json();
      setUsers(data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger la liste des utilisateurs',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  };

  const handleSubmit = async () => {
    if (!selectedUser) {
      toast({
        title: 'Erreur',
        description: 'Veuillez sélectionner un utilisateur',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
      return;
    }

    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/organizations/${organizationId}/members`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: parseInt(selectedUser),
          role: role
        })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'ajout du membre');
      }

      toast({
        title: 'Succès',
        description: 'Membre ajouté avec succès',
        status: 'success',
        duration: 5000,
        isClosable: true
      });

      onSuccess();
      onClose();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible d\'ajouter le membre',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent bg="#1a1f37">
        <ModalHeader color="white">Ajouter un membre</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <FormControl>
              <FormLabel color="white">Utilisateur</FormLabel>
              <Select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                placeholder="Sélectionner un utilisateur"
                bg="#20243a"
                color="white"
              >
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {`${user.prenom} ${user.nom} (${user.email})`}
                  </option>
                ))}
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel color="white">Rôle</FormLabel>
              <Select
                value={role}
                onChange={(e) => setRole(e.target.value as 'ADMIN' | 'MEMBRE')}
                bg="#20243a"
                color="white"
              >
                <option value="MEMBRE">Membre</option>
                <option value="ADMIN">Administrateur</option>
              </Select>
            </FormControl>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Annuler
          </Button>
          <Button
            colorScheme="blue"
            onClick={handleSubmit}
            isLoading={isLoading}
          >
            Ajouter
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default AddMemberModal; 