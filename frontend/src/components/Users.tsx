import React, { useEffect, useState } from "react";
import {
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Heading,
  Button,
  useToast,
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  Icon,
  Badge,
  Text,
  Select,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  VStack,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  useDisclosure,
  Avatar,
  AvatarGroup,
  IconButton,
  Center,
  Spinner,
} from "@chakra-ui/react";
import { FiSearch, FiUser, FiEdit2, FiTrash2, FiMoreVertical, FiUserPlus, FiXCircle, FiCheckCircle } from "react-icons/fi";
import { ElementType } from "react";
import config from "../config";
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import { checkAuthToken } from "../utils/errorHandling";
import { useNavigate } from "react-router-dom";
import { useLoading } from "../contexts/LoadingContext";
import RequireRole from './RequireRole';
import { format } from 'date-fns';

const API_URL = config.API_URL;

interface User {
  id: number;
  nom: string;
  prenom: string;
  email: string;
  role: string;
  date_creation: string;
  derniere_connexion: string | null;
}

const initialUserState: User = {
  id: 0,
  nom: '',
  prenom: '',
  email: '',
  role: 'utilisateur',
  date_creation: new Date().toISOString(),
  derniere_connexion: null,
};

const ROLES = [
  { value: 'admin', label: 'Administrateur' },
  { value: 'chef_de_service', label: 'Chef de service' },
  { value: 'validateur', label: 'Validateur/Approbateur' },
  { value: 'utilisateur', label: 'Utilisateur standard' },
  { value: 'archiviste', label: 'Archiviste' },
];

const Users: React.FC = () => {
  const { isLoading, showLoading, hideLoading } = useLoading();
  const [users, setUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [newUser, setNewUser] = useState<User>(initialUserState);
  const [editingUser, setEditingUser] = useState<User>(initialUserState);
  const [replaceIfExists, setReplaceIfExists] = useState<boolean>(false);
  const toast = useToast();
  const { executeOperation } = useAsyncOperation();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const cancelRef = React.useRef<HTMLButtonElement>(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      showLoading("Chargement des utilisateurs...");
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      console.log("Tentative de récupération des utilisateurs...");
      
          const response = await fetch(`${API_URL}/api/users`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });

      console.log("Réponse API /users:", response.status);

          if (response.status === 401) {
            localStorage.removeItem('token');
            navigate('/login');
            throw new Error('Session expirée, veuillez vous reconnecter');
          }

          if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("Erreur API:", errorData);
        throw new Error(errorData.message || 'Erreur lors de la récupération des utilisateurs');
      }

      const data = await response.json();
      console.log("Utilisateurs récupérés:", data);
      
      // Mettre à jour l'état avec les utilisateurs récupérés
      setUsers(data);
      setError(null);
      
      // Masquer le chargement
      hideLoading();
      
      return data;
    } catch (err) {
      console.error("Erreur lors de la récupération des utilisateurs:", err);
      setError(err instanceof Error ? err.message : "Erreur de connexion au serveur");
      toast({
        title: "Erreur",
        description: err instanceof Error ? err.message : "Erreur de connexion au serveur",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      hideLoading();
      return null;
    }
  };

  const handleCreateUser = async () => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/users`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            ...newUser,
            replace_if_exists: replaceIfExists
          })
        });

        if (!response.ok) {
          const errorData = await response.json();
          if (errorData.message?.includes('déjà utilisé') || errorData.message?.includes('already exists')) {
            toast({
              title: "Email déjà utilisé",
              description: "Cet email est déjà associé à un compte existant. Activez l'option 'Remplacer si existe' pour écraser le compte existant.",
              status: "error",
              duration: 5000,
              isClosable: true,
            });
            throw new Error("Cet email est déjà associé à un compte existant.");
          }
          throw new Error(errorData.message || 'Erreur lors de la création de l\'utilisateur');
        }

        const data = await response.json();
        
        // Ne plus stocker le mot de passe généré
        // setGeneratedPassword(data.password);
        
        // Fermer le modal et réinitialiser le formulaire
        onCreateClose();
        setNewUser(initialUserState);
        setReplaceIfExists(false);
        
        // Actualiser la liste des utilisateurs
        await fetchUsers();
        
        // Afficher un message de succès
        toast({
          title: "Utilisateur créé",
          description: `L'utilisateur ${newUser.prenom} ${newUser.nom} a été créé avec succès. Un email contenant les instructions de connexion a été envoyé.`,
          status: "success",
          duration: 5000,
          isClosable: true,
        });
      },
      {
        loadingMessage: "Création de l'utilisateur...",
        successMessage: "Utilisateur créé avec succès",
        errorMessage: "Impossible de créer l'utilisateur"
      }
    );
  };

  const handleEdit = (userId: number) => {
    const user = users.find(u => u.id === userId);
    if (user) {
      setSelectedUser(user);
      setEditingUser(user);
      onEditOpen();
    }
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/users/${selectedUser.id}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(editingUser)
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Erreur lors de la mise à jour de l\'utilisateur');
        }

        await fetchUsers();
        onEditClose();
        setSelectedUser(null);
        setEditingUser(initialUserState);
      },
      {
        loadingMessage: "Mise à jour de l'utilisateur...",
        successMessage: "Utilisateur mis à jour avec succès",
        errorMessage: "Impossible de mettre à jour l'utilisateur"
      }
    );
  };

  const handleDelete = async (userId: number) => {
    const user = users.find(u => u.id === userId);
    if (user) {
      setSelectedUser(user);
      onDeleteOpen();
    }
  };

  const confirmDelete = async () => {
    if (!selectedUser) return;

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/users/${selectedUser.id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Erreur lors de la suppression de l\'utilisateur');
        }

        await fetchUsers();
        onDeleteClose();
        setSelectedUser(null);
      },
      {
        loadingMessage: "Suppression de l'utilisateur...",
        successMessage: "Utilisateur supprimé avec succès",
        errorMessage: "Impossible de supprimer l'utilisateur"
      }
    );
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const getRoleInfo = (role: string | undefined | null) => {
    const safeRole = (role || '').toLowerCase();
    
    // Trouver le rôle correspondant dans la liste des rôles
    const roleInfo = ROLES.find(r => r.value.toLowerCase() === safeRole);
    
    return {
      isAdmin: safeRole === 'admin',
      displayName: roleInfo?.label || (safeRole === 'admin' ? 'Administrateur' : 'Utilisateur'),
      colorScheme: 
        safeRole === 'admin' ? 'red' :
        safeRole === 'chef_de_service' ? 'purple' :
        safeRole === 'validateur' ? 'orange' :
        safeRole === 'archiviste' ? 'yellow' :
        'blue'
    };
  };

  const getFullName = (user: User) => {
    const nom = user.nom || '';
    const prenom = user.prenom || '';
    return `${prenom} ${nom}`.trim() || 'N/A';
  };

  const filteredUsers = users.filter((user) => {
    const fullName = getFullName(user).toLowerCase();
    const email = (user.email || '').toLowerCase();
    const searchLower = searchTerm.toLowerCase();
    const userRole = (user.role || '').toLowerCase();
    const filterRoleLower = filterRole.toLowerCase();
    
    const matchesSearch = fullName.includes(searchLower) || email.includes(searchLower);
    const matchesRole = filterRole === "" || userRole === filterRoleLower;
    
    return matchesSearch && matchesRole;
  });

  return (
    <RequireRole roles={["admin"]}>
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading color="white">Gestion des Utilisateurs</Heading>
        <Button
          leftIcon={<Icon as={FiUserPlus as ElementType} />}
          colorScheme="blue"
            size="md"
            fontWeight="bold"
            px={6}
            py={2}
            borderRadius="lg"
          onClick={onCreateOpen}
            boxShadow="md"
        >
          Nouvel Utilisateur
        </Button>
      </Flex>

      <Flex wrap="wrap" gap={2} direction={{ base: "column", md: "row" }} mb={4}>
        <InputGroup flex={1}>
          <InputLeftElement pointerEvents="none">
            <Icon as={FiSearch as ElementType} color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Rechercher un utilisateur..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            bg="#232946"
            color="white"
            borderColor="#232946"
            _placeholder={{ color: "gray.400" }}
            _focus={{
              borderColor: "#3a8bfd",
              boxShadow: "0 0 0 1.5px #3a8bfd",
            }}
          />
        </InputGroup>
        <Select
          value={filterRole}
          onChange={(e) => setFilterRole(e.target.value)}
          bg="#232946"
          color="white"
          borderColor="#232946"
          w="200px"
          _hover={{ borderColor: "#3a8bfd" }}
          _focus={{
            borderColor: "#3a8bfd",
            boxShadow: "0 0 0 1.5px #3a8bfd",
          }}
        >
          <option value="">Tous les rôles</option>
            {ROLES.map(role => (
              <option key={role.value} value={role.value}>{role.label}</option>
            ))}
        </Select>
      </Flex>

      {error && (
        <Box bg="#20243a" borderRadius="lg" p={6} mb={4}>
          <Text color="red.400" textAlign="center">
            {error}
          </Text>
          <Button
            mt={4}
            onClick={fetchUsers}
            colorScheme="blue"
            size="sm"
            width="full"
          >
            Réessayer
          </Button>
        </Box>
      )}

        <Table variant="simple">
            <Thead>
              <Tr>
                <Th>UTILISATEUR</Th>
                <Th>EMAIL</Th>
                <Th display={{ base: "none", md: "table-cell" }}>RÔLE</Th>
                <Th>DATE DE CRÉATION</Th>
                <Th>ACTIONS</Th>
              </Tr>
            </Thead>
            <Tbody>
            {isLoading ? (
              <Tr><Td colSpan={7}><Center py={10}><Spinner size="lg" color="blue.400" /></Center></Td></Tr>
            ) : filteredUsers.length === 0 ? (
              <Tr><Td colSpan={7}><Center py={10}><Text color="gray.400">Aucun utilisateur trouvé</Text></Center></Td></Tr>
            ) : (
              filteredUsers.map((user) => {
                const roleInfo = getRoleInfo(user.role);
                return (
                  <Tr key={user.id}>
                    <Td>
                      <Flex align="center" gap={3}>
                        <Avatar size="sm" name={`${user.prenom} ${user.nom}`} />
                        <Box>
                          <Text fontWeight="bold" color="white">{user.prenom} {user.nom}</Text>
                        </Box>
                      </Flex>
                    </Td>
                    <Td color="white">{user.email || 'N/A'}</Td>
                    <Td>
                      <Badge colorScheme={
                        user.role?.toLowerCase() === 'admin' ? 'red' :
                        user.role?.toLowerCase() === 'chef_de_service' ? 'purple' :
                        user.role?.toLowerCase() === 'validateur' ? 'orange' :
                        user.role?.toLowerCase() === 'archiviste' ? 'yellow' :
                        'blue'
                      } fontWeight="bold" px={3} py={1} borderRadius="md" fontSize="sm">
                        {ROLES.find(r => r.value.toLowerCase() === user.role?.toLowerCase())?.label || user.role}
                      </Badge>
                    </Td>
                    <Td>{user.date_creation && user.date_creation !== 'Invalid Date' ? format(new Date(user.date_creation), 'dd/MM/yyyy') : '-'}</Td>
                    <Td>
                      <Menu>
                        <MenuButton as={IconButton} icon={<Icon as={FiMoreVertical as ElementType} />} variant="ghost" colorScheme="blue" />
                        <MenuList>
                          <MenuItem icon={<Icon as={FiEdit2 as ElementType} />} onClick={() => handleEdit(user.id)}>Modifier</MenuItem>
                          <MenuItem icon={<Icon as={FiTrash2 as ElementType} />} color="red.500" onClick={() => handleDelete(user.id)}>Supprimer</MenuItem>
                        </MenuList>
                      </Menu>
                    </Td>
                  </Tr>
                );
              })
            )}
            </Tbody>
          </Table>

      {/* Modal de création d'utilisateur */}
      <Modal isOpen={isCreateOpen} onClose={onCreateClose} size="lg">
        <ModalOverlay />
        <ModalContent bg="#232946" color="white">
          <ModalHeader>Nouvel Utilisateur</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  bg="#20243a"
                  borderColor="#20243a"
                  _focus={{ borderColor: "#3a8bfd" }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Prénom</FormLabel>
                <Input
                  value={newUser.prenom}
                  onChange={(e) => setNewUser({ ...newUser, prenom: e.target.value })}
                  bg="#20243a"
                  borderColor="#20243a"
                  _focus={{ borderColor: "#3a8bfd" }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Nom</FormLabel>
                <Input
                  value={newUser.nom}
                  onChange={(e) => setNewUser({ ...newUser, nom: e.target.value })}
                  bg="#20243a"
                  borderColor="#20243a"
                  _focus={{ borderColor: "#3a8bfd" }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Rôle</FormLabel>
                <Select
                  value={newUser.role}
                    onChange={e => setNewUser({ ...newUser, role: e.target.value })}
                  bg="#20243a"
                  borderColor="#20243a"
                  _focus={{ borderColor: "#3a8bfd" }}
                >
                    {ROLES.map(role => (
                      <option key={role.value} value={role.value}>{role.label}</option>
                    ))}
                </Select>
              </FormControl>

                <FormControl display="flex" alignItems="center">
                  <FormLabel htmlFor="replace-if-exists" mb="0">
                    Remplacer si existe
                  </FormLabel>
                  <input
                    id="replace-if-exists"
                    type="checkbox"
                    checked={replaceIfExists}
                    onChange={(e) => setReplaceIfExists(e.target.checked)}
                    style={{ marginLeft: '10px' }}
                  />
              </FormControl>

              <Button
                colorScheme="blue"
                onClick={handleCreateUser}
                width="full"
                isLoading={isLoading}
              >
                Créer l'utilisateur
              </Button>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Modal d'édition d'utilisateur */}
      <Modal isOpen={isEditOpen} onClose={onEditClose} size="lg">
        <ModalOverlay />
        <ModalContent bg="#232946" color="white">
          <ModalHeader>Modifier l'utilisateur</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  value={editingUser.email}
                  onChange={(e) => setEditingUser({ ...editingUser, email: e.target.value })}
                  bg="#20243a"
                  borderColor="#20243a"
                  _focus={{ borderColor: "#3a8bfd" }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Prénom</FormLabel>
                <Input
                  value={editingUser.prenom}
                  onChange={(e) => setEditingUser({ ...editingUser, prenom: e.target.value })}
                  bg="#20243a"
                  borderColor="#20243a"
                  _focus={{ borderColor: "#3a8bfd" }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Nom</FormLabel>
                <Input
                  value={editingUser.nom}
                  onChange={(e) => setEditingUser({ ...editingUser, nom: e.target.value })}
                  bg="#20243a"
                  borderColor="#20243a"
                  _focus={{ borderColor: "#3a8bfd" }}
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Rôle</FormLabel>
                <Select
                  value={editingUser.role}
                  onChange={(e) => setEditingUser({ ...editingUser, role: e.target.value })}
                  bg="#20243a"
                  borderColor="#20243a"
                  _focus={{ borderColor: "#3a8bfd" }}
                >
                    {ROLES.map(role => (
                      <option key={role.value} value={role.value}>{role.label}</option>
                    ))}
                </Select>
              </FormControl>

              <Button
                colorScheme="blue"
                onClick={handleUpdateUser}
                width="full"
                isLoading={isLoading}
              >
                Mettre à jour
              </Button>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Dialog de confirmation de suppression */}
      <AlertDialog
        isOpen={isDeleteOpen}
        leastDestructiveRef={cancelRef}
        onClose={onDeleteClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent bg="#232946" color="white">
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Supprimer l'utilisateur
            </AlertDialogHeader>

            <AlertDialogBody>
              Êtes-vous sûr de vouloir supprimer l'utilisateur{" "}
              <strong>{selectedUser ? getFullName(selectedUser) : ""}</strong> ?
              Cette action est irréversible.
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onDeleteClose}>
                Annuler
              </Button>
              <Button
                colorScheme="red"
                onClick={confirmDelete}
                ml={3}
                isLoading={isLoading}
              >
                Supprimer
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
              </Box>
    </RequireRole>
  );
};

export default Users;
