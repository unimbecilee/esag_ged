import React, { useState, useEffect, ElementType } from 'react';
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
  Input,
  Textarea,
  useToast,
  VStack,
  Select,
  Flex,
  IconButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Box,
  Text,
  Icon
} from '@chakra-ui/react';
import { FiPlus, FiTrash2, FiUser } from 'react-icons/fi';

interface User {
  id: number;
  nom: string;
  prenom: string;
  email: string;
}

interface CreateOrganizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const CreateOrganizationModal: React.FC<CreateOrganizationModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [nom, setNom] = useState('');
  const [description, setDescription] = useState('');
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [selectedMembers, setSelectedMembers] = useState<Array<{ id: number; nom: string; prenom: string; email: string; role: 'ADMIN' | 'MEMBRE'; }>>([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedRole, setSelectedRole] = useState<'ADMIN' | 'MEMBRE'>('MEMBRE');
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
      if (!response.ok) throw new Error('Erreur lors de la récupération des utilisateurs');
      const data = await response.json();
      setAvailableUsers(data);
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

  const handleAddMember = () => {
    if (!selectedUser) return;
    const user = availableUsers.find(u => u.id === parseInt(selectedUser));
    if (!user) return;
    if (selectedMembers.some(m => m.id === user.id)) {
      toast({
        title: 'Erreur',
        description: 'Cet utilisateur est déjà membre',
        status: 'error',
        duration: 3000,
        isClosable: true
      });
      return;
    }
    setSelectedMembers([...selectedMembers, { ...user, role: selectedRole }]);
    setSelectedUser('');
  };

  const handleRemoveMember = (userId: number) => {
    setSelectedMembers(selectedMembers.filter(m => m.id !== userId));
  };

  const handleSubmit = async () => {
    if (!nom) {
      toast({
        title: 'Erreur',
        description: "Le nom de l'organisation est requis",
        status: 'error',
        duration: 3000,
        isClosable: true
      });
      return;
    }
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/organizations', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          nom,
          description,
          adresse: "",
          email_contact: "",
          telephone_contact: "",
          statut: "ACTIVE",
          // Ne pas envoyer les membres pour l'instant, on les ajoutera après dans une autre étape
        })
      });
      if (!response.ok) throw new Error('Erreur lors de la création de l\'organisation');
      toast({
        title: 'Succès',
        description: 'Organisation créée avec succès',
        status: 'success',
        duration: 3000,
        isClosable: true
      });
      onSuccess();
      onClose();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: "Impossible de créer l'organisation",
        status: 'error',
        duration: 3000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalOverlay />
      <ModalContent bg="#1a1f37">
        <ModalHeader color="white">Nouvelle organisation</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel color="white">Nom</FormLabel>
              <Input value={nom} onChange={e => setNom(e.target.value)} placeholder="Nom de l'organisation" bg="#20243a" color="white" />
            </FormControl>
            <FormControl>
              <FormLabel color="white">Description</FormLabel>
              <Textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Description de l'organisation" bg="#20243a" color="white" />
            </FormControl>
            <Box bg="#20243a" p={4} borderRadius="md">
              <FormControl>
                <FormLabel color="white">Ajouter un membre</FormLabel>
                <Flex gap={2}>
                  <Select
                    value={selectedUser}
                    onChange={e => setSelectedUser(e.target.value)}
                    placeholder="Sélectionner un utilisateur"
                    bg="#2a2f4a"
                    color="white"
                    flex={2}
                  >
                    {availableUsers.map(user => (
                      <option key={user.id} value={user.id}>
                        {`${user.prenom} ${user.nom} (${user.email})`}
                      </option>
                    ))}
                  </Select>
                  <Select
                    value={selectedRole}
                    onChange={e => setSelectedRole(e.target.value as 'ADMIN' | 'MEMBRE')}
                    bg="#2a2f4a"
                    color="white"
                    flex={1}
                  >
                    <option value="MEMBRE">Membre</option>
                    <option value="ADMIN">Admin</option>
                  </Select>
                  <IconButton
                    aria-label="Ajouter membre"
                    icon={<Icon as={FiPlus as ElementType} />}
                    onClick={handleAddMember}
                    colorScheme="blue"
                  />
                </Flex>
              </FormControl>
            </Box>
            {selectedMembers.length > 0 ? (
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th color="gray.400">Nom</Th>
                    <Th color="gray.400">Email</Th>
                    <Th color="gray.400">Rôle</Th>
                    <Th color="gray.400">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {selectedMembers.map(member => (
                    <Tr key={member.id}>
                      <Td color="white">{`${member.prenom} ${member.nom}`}</Td>
                      <Td color="white">{member.email}</Td>
                      <Td>
                        <Badge colorScheme={member.role === 'ADMIN' ? 'purple' : 'blue'}>
                          {member.role}
                        </Badge>
                      </Td>
                      <Td>
                        <IconButton
                          aria-label="Retirer membre"
                          icon={<Icon as={FiTrash2 as ElementType} />}
                          onClick={() => handleRemoveMember(member.id)}
                          variant="ghost"
                          colorScheme="red"
                          size="sm"
                        />
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            ) : (
              <Box textAlign="center" py={4}>
                <Icon as={FiUser as ElementType} boxSize={8} color="#718096" mb={2} />
                <Text color="white">Aucun membre ajouté</Text>
              </Box>
            )}
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose} isDisabled={isLoading}>
            Annuler
          </Button>
          <Button colorScheme="blue" onClick={handleSubmit} isLoading={isLoading}>
            Créer
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default CreateOrganizationModal; 