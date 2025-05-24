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
} from "@chakra-ui/react";
import { FiSearch, FiUser, FiEdit2, FiTrash2, FiGitBranch, FiPlus, FiMoreVertical } from "react-icons/fi";
import { ElementType } from "react";
import config from "../config";

const API_URL = config.API_URL;

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: 'admin' | 'user';
  date_creation: string;
  categorie?: string;
  numero_tel?: string;
}

const Users: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [newUser, setNewUser] = useState<{
    email: string;
    nom: string;
    prenom: string;
    role: 'admin' | 'user';
    categorie: string;
    numero_tel: string;
  }>({
    email: "",
    nom: "",
    prenom: "",
    role: "user",
    categorie: "",
    numero_tel: "",
  });
  const [editUser, setEditUser] = useState<{
    email: string;
    nom: string;
    prenom: string;
    role: 'admin' | 'user';
    categorie: string;
    numero_tel: string;
  }>({
    email: "",
    nom: "",
    prenom: "",
    role: "user",
    categorie: "",
    numero_tel: "",
  });
  const [generatedPassword, setGeneratedPassword] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem("token");
      console.log("État de la connexion :", {
        token: token ? "Présent" : "Absent",
        tokenValue: token
      });

      if (!token) {
        toast({
          title: "Erreur d'authentification",
          description: "Vous devez être connecté pour accéder à cette page",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
        return;
      }

      // Vérifier si le token est valide
      try {
        const checkResponse = await fetch(`${API_URL}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!checkResponse.ok) {
          console.error("Token invalide ou expiré");
          localStorage.removeItem("token");
          toast({
            title: "Session expirée",
            description: "Veuillez vous reconnecter",
            status: "error",
            duration: 5000,
            isClosable: true,
          });
          return;
        }
      } catch (error) {
        console.error("Erreur lors de la vérification du token:", error);
      }

      console.log("Tentative de récupération des utilisateurs...");
      const response = await fetch(`${API_URL}/users`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      console.log("Réponse du serveur:", {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Données reçues:", data);
        setUsers(data);
      } else if (response.status === 403) {
        const errorData = await response.json();
        console.error("Erreur 403:", errorData);
        toast({
          title: "Accès refusé",
          description: errorData.message || "Vous n'avez pas les droits d'administration nécessaires",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error("Erreur détaillée:", errorData);
        throw new Error(errorData.message || "Erreur lors de la récupération des utilisateurs");
      }
    } catch (error) {
      console.error("Erreur complète:", error);
      toast({
        title: "Erreur",
        description: error instanceof Error ? error.message : "Impossible de charger les utilisateurs",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    try {
      const response = await fetch(`${API_URL}/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(newUser),
      });

      if (response.ok) {
        const data = await response.json();
        setGeneratedPassword(data.password);
        toast({
          title: "Succès",
          description: "Utilisateur créé avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        setNewUser({
          email: "",
          nom: "",
          prenom: "",
          role: "user",
          categorie: "",
          numero_tel: "",
        });
        fetchUsers();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || "Erreur lors de la création de l'utilisateur");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: error instanceof Error ? error.message : "Impossible de créer l'utilisateur",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleEdit = (userId: number) => {
    const user = users.find(u => u.id === userId);
    if (user) {
      setSelectedUser(user);
      setEditUser({
        email: user.email,
        nom: user.nom,
        prenom: user.prenom,
        role: user.role,
        categorie: user.categorie || "",
        numero_tel: user.numero_tel || "",
      });
      setIsEditModalOpen(true);
    }
  };

  const handleUpdateUser = async () => {
    try {
      const response = await fetch(`${API_URL}/users/${selectedUser?.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(editUser),
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Utilisateur modifié avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        setIsEditModalOpen(false);
        setSelectedUser(null);
        setEditUser({
          email: "",
          nom: "",
          prenom: "",
          role: "user",
          categorie: "",
          numero_tel: "",
        });
        fetchUsers();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || "Erreur lors de la modification");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: error instanceof Error ? error.message : "Impossible de modifier l'utilisateur",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleDelete = async (userId: number) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer cet utilisateur ?")) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/users/${userId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Utilisateur supprimé avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        fetchUsers();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || "Erreur lors de la suppression");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: error instanceof Error ? error.message : "Impossible de supprimer l'utilisateur",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleWorkflow = (userId: number) => {
    // Implémenter la logique de gestion des workflows
    toast({
      title: "Info",
      description: "Fonctionnalité de gestion des workflows à implémenter",
      status: "info",
      duration: 5000,
      isClosable: true,
    });
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.prenom.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = filterRole === "" || user.role.toLowerCase() === filterRole.toLowerCase();
    return matchesSearch && matchesRole;
  });

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading color="white">Gestion des Utilisateurs</Heading>
        <Button
          leftIcon={<Icon as={FiPlus as ElementType} />}
          colorScheme="blue"
          onClick={() => setIsModalOpen(true)}
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
          <option value="admin">Administrateur</option>
          <option value="user">Utilisateur</option>
        </Select>
      </Flex>

      {loading ? (
        <Text color="white" textAlign="center">
          Chargement...
        </Text>
      ) : filteredUsers.length === 0 ? (
        <Box
          bg="#20243a"
          borderRadius="lg"
          p={6}
          textAlign="center"
          color="white"
        >
          <Icon
            as={FiUser as ElementType}
            boxSize={8}
            color="gray.400"
            mb={2}
          />
          <Text>Aucun utilisateur trouvé</Text>
        </Box>
      ) : (
        <Box overflowX="auto">
          <Table size={{ base: "sm", md: "md" }}>
            <Thead>
              <Tr>
                <Th>UTILISATEUR</Th>
                <Th>EMAIL</Th>
                <Th display={{ base: "none", md: "table-cell" }}>RÔLE</Th>
                <Th display={{ base: "none", md: "table-cell" }}>CATÉGORIE</Th>
                <Th display={{ base: "none", md: "table-cell" }}>TÉLÉPHONE</Th>
                <Th>DATE DE CRÉATION</Th>
                <Th>ACTIONS</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredUsers.map((user) => (
                <Tr key={user.id}>
                  <Td>
                    <Flex align="center">
                      <Icon
                        as={FiUser as ElementType}
                        color="#3a8bfd"
                        mr={2}
                      />
                      <Text color="white">
                        {user.prenom} {user.nom}
                      </Text>
                    </Flex>
                  </Td>
                  <Td color="white">{user.email}</Td>
                  <Td>
                    <Badge
                      colorScheme={user.role.toLowerCase() === "admin" ? "red" : "blue"}
                    >
                      {user.role.toLowerCase() === "admin" ? "Administrateur" : "Utilisateur"}
                    </Badge>
                  </Td>
                  <Td color="white">{user.categorie || "-"}</Td>
                  <Td color="white">{user.numero_tel || "-"}</Td>
                  <Td color="white">{formatDate(user.date_creation)}</Td>
                  <Td>
                    <Menu>
                      <MenuButton
                        as={Button}
                        size="md"
                        variant="ghost"
                        colorScheme="blue"
                        aria-label="Options"
                        p={2}
                        minW="40px"
                        h="40px"
                        borderRadius="md"
                        _hover={{ bg: "#2d3250" }}
                      >
                        <Icon as={FiMoreVertical as ElementType} boxSize={5} color="#3a8bfd" />
                      </MenuButton>
                      <MenuList bg="#232946" borderColor="#20243a">
                        <MenuItem 
                          icon={<Icon as={FiEdit2 as ElementType} color="blue.400" />} 
                          onClick={() => handleEdit(user.id)}
                          _hover={{ bg: "#2d3250" }}
                          _focus={{ bg: "#2d3250" }}
                        >
                          Modifier
                        </MenuItem>
                        <MenuItem 
                          icon={<Icon as={FiGitBranch as ElementType} color="green.400" />} 
                          onClick={() => handleWorkflow(user.id)}
                          _hover={{ bg: "#2d3250" }}
                          _focus={{ bg: "#2d3250" }}
                        >
                          Workflow
                        </MenuItem>
                        <MenuItem 
                          icon={<Icon as={FiTrash2 as ElementType} color="red.400" />} 
                          onClick={() => handleDelete(user.id)}
                          _hover={{ bg: "#2d3250" }}
                          _focus={{ bg: "#2d3250" }}
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
        </Box>
      )}

      <Modal isOpen={isModalOpen} onClose={() => {
        setIsModalOpen(false);
        setGeneratedPassword(null);
      }} size="xl">
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white">
          <ModalHeader>Nouvel Utilisateur</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  value={newUser.email}
                  onChange={(e) =>
                    setNewUser({ ...newUser, email: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Nom</FormLabel>
                <Input
                  value={newUser.nom}
                  onChange={(e) =>
                    setNewUser({ ...newUser, nom: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Prénom</FormLabel>
                <Input
                  value={newUser.prenom}
                  onChange={(e) =>
                    setNewUser({ ...newUser, prenom: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Catégorie</FormLabel>
                <Input
                  value={newUser.categorie}
                  onChange={(e) =>
                    setNewUser({ ...newUser, categorie: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Numéro de téléphone</FormLabel>
                <Input
                  value={newUser.numero_tel}
                  onChange={(e) =>
                    setNewUser({ ...newUser, numero_tel: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Rôle</FormLabel>
                <Select
                  value={newUser.role}
                  onChange={(e) =>
                    setNewUser({ ...newUser, role: e.target.value as 'admin' | 'user' })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                >
                  <option value="user">Utilisateur</option>
                  <option value="admin">Administrateur</option>
                </Select>
              </FormControl>
              {generatedPassword && (
                <Box
                  p={4}
                  bg="#232946"
                  borderRadius="md"
                  width="full"
                  textAlign="center"
                >
                  <Text fontWeight="bold" mb={2}>Mot de passe généré :</Text>
                  <Text color="#3a8bfd" fontSize="lg">{generatedPassword}</Text>
                  <Text fontSize="sm" color="gray.400" mt={2}>
                    Veuillez noter ce mot de passe, il ne sera plus affiché ultérieurement.
                  </Text>
                </Box>
              )}
              <Button
                colorScheme="blue"
                width="full"
                onClick={handleCreateUser}
                mt={4}
              >
                Créer l'utilisateur
              </Button>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>

      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} size="xl">
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white">
          <ModalHeader>Modifier l'utilisateur</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  value={editUser.email}
                  onChange={(e) =>
                    setEditUser({ ...editUser, email: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Nom</FormLabel>
                <Input
                  value={editUser.nom}
                  onChange={(e) =>
                    setEditUser({ ...editUser, nom: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Prénom</FormLabel>
                <Input
                  value={editUser.prenom}
                  onChange={(e) =>
                    setEditUser({ ...editUser, prenom: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Catégorie</FormLabel>
                <Input
                  value={editUser.categorie}
                  onChange={(e) =>
                    setEditUser({ ...editUser, categorie: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Numéro de téléphone</FormLabel>
                <Input
                  value={editUser.numero_tel}
                  onChange={(e) =>
                    setEditUser({ ...editUser, numero_tel: e.target.value })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl isRequired>
                <FormLabel>Rôle</FormLabel>
                <Select
                  value={editUser.role}
                  onChange={(e) =>
                    setEditUser({ ...editUser, role: e.target.value as 'admin' | 'user' })
                  }
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                >
                  <option value="user">Utilisateur</option>
                  <option value="admin">Administrateur</option>
                </Select>
              </FormControl>
              <Button
                colorScheme="blue"
                width="full"
                onClick={handleUpdateUser}
                mt={4}
              >
                Mettre à jour l'utilisateur
              </Button>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Users; 