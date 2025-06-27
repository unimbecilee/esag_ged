import React, { useEffect, useState } from 'react';
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Icon,
  Badge,
  Flex,
  Text,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useToast,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  VStack,
} from '@chakra-ui/react';
import { FiBriefcase, FiMoreVertical, FiEdit2, FiTrash2, FiPlus, FiUsers } from 'react-icons/fi';
import { ElementType } from 'react';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import { checkAuthToken } from '../utils/errorHandling';
import { API_URL } from '../config';
import { asElementType } from '../utils/iconUtils';
import RequireRole from './RequireRole';
import CreateOrganizationModal from './Organization/CreateOrganizationModal';

interface Organization {
  id: number;
  nom: string;
  description: string;
  adresse: string;
  email_contact: string;
  telephone_contact: string;
  nombre_employes: number;
  statut: string;
  date_creation: string;
}

const Organization: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const { isOpen: isCreateModalOpen, onOpen: onCreateModalOpen, onClose: onCreateModalClose } = useDisclosure();
  const { isOpen: isEditModalOpen, onOpen: onEditModalOpen, onClose: onEditModalClose } = useDisclosure();
  const [formData, setFormData] = useState({
    nom: '',
    description: '',
    adresse: '',
    email_contact: '',
    telephone_contact: '',
    nombre_employes: 0
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    const result = await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/organizations`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la récupération des organisations');
        }

        return await response.json();
      },
      {
        loadingMessage: "Chargement des organisations...",
        errorMessage: "Impossible de charger les organisations"
      }
    );

    if (result) {
      setOrganizations(result);
    }
  };

  const handleUpdate = async () => {
    if (!selectedOrg) return;

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/organizations/${selectedOrg.id}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(formData)
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la mise à jour');
        }

        onEditModalClose();
        await fetchOrganizations();
      },
      {
        loadingMessage: "Mise à jour de l'organisation...",
        successMessage: "Organisation mise à jour avec succès",
        errorMessage: "Impossible de mettre à jour l'organisation"
      }
    );
  };

  const handleDelete = async (orgId: number) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/organizations/${orgId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la suppression');
        }

        await fetchOrganizations();
      },
      {
        loadingMessage: "Suppression de l'organisation...",
        successMessage: "Organisation supprimée avec succès",
        errorMessage: "Impossible de supprimer l'organisation"
      }
    );
  };

  const handleEdit = (org: Organization) => {
    setSelectedOrg(org);
    setFormData({
      nom: org.nom,
      description: org.description,
      adresse: org.adresse,
      email_contact: org.email_contact,
      telephone_contact: org.telephone_contact,
      nombre_employes: org.nombre_employes
    });
    onEditModalOpen();
  };

  const handleNew = () => {
    setSelectedOrg(null);
    onCreateModalOpen();
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <RequireRole roles={["admin"]}>
      <Box>
        <Flex justify="space-between" align="center" mb={6}>
          <Heading color="white">Organisations</Heading>
          <Button
            leftIcon={<Icon as={asElementType(FiPlus)} />}
            colorScheme="blue"
            onClick={handleNew}
          >
            Nouvelle Organisation
          </Button>
        </Flex>

        <Box bg="#20243a" borderRadius="lg" p={6} overflowX="auto">
          {organizations.length === 0 ? (
            <Text color="white" textAlign="center">
              Aucune organisation trouvée
            </Text>
          ) : (
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th color="white">Organisation</Th>
                  <Th color="white">Contact</Th>
                  <Th color="white">Employés</Th>
                  <Th color="white">Statut</Th>
                  <Th color="white">Date de création</Th>
                  <Th color="white">Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {organizations.map((org) => (
                  <Tr key={org.id}>
                    <Td>
                      <Flex align="center">
                        <Icon as={asElementType(FiBriefcase)} color="#3a8bfd" mr={2} />
                        <Box>
                          <Text color="white" fontWeight="bold">{org.nom}</Text>
                          <Text color="gray.400" fontSize="sm">{org.description}</Text>
                        </Box>
                      </Flex>
                    </Td>
                    <Td>
                      <Box color="white">
                        <Text>{org.email_contact}</Text>
                        <Text color="gray.400">{org.telephone_contact}</Text>
                      </Box>
                    </Td>
                    <Td>
                      <Flex align="center">
                        <Icon as={asElementType(FiUsers)} mr={2} />
                        <Text color="white">{org.nombre_employes}</Text>
                      </Flex>
                    </Td>
                    <Td>
                      <Badge colorScheme={org.statut === 'ACTIVE' ? 'green' : 'red'}>
                        {org.statut}
                      </Badge>
                    </Td>
                    <Td color="white">{formatDate(org.date_creation)}</Td>
                    <Td>
                      <Menu>
                        <MenuButton
                          as={Button}
                          size="sm"
                          variant="ghost"
                          colorScheme="blue"
                        >
                          <Icon as={asElementType(FiMoreVertical)} />
                        </MenuButton>
                        <MenuList bg="#232946">
                          <MenuItem
                            icon={<Icon as={asElementType(FiEdit2)} />}
                            onClick={() => handleEdit(org)}
                            _hover={{ bg: "#20243a" }}
                          >
                            Modifier
                          </MenuItem>
                          <MenuItem
                            icon={<Icon as={asElementType(FiTrash2)} />}
                            onClick={() => handleDelete(org.id)}
                            _hover={{ bg: "#20243a" }}
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
        </Box>

        {/* Modal pour créer une nouvelle organisation */}
        <CreateOrganizationModal 
          isOpen={isCreateModalOpen} 
          onClose={onCreateModalClose} 
          onSuccess={fetchOrganizations} 
        />

        {/* Modal pour modifier une organisation existante */}
        <Modal isOpen={isEditModalOpen} onClose={onEditModalClose} size="xl">
          <ModalOverlay />
          <ModalContent bg="#20243a">
            <ModalHeader color="white">
              Modifier l'organisation
            </ModalHeader>
            <ModalCloseButton color="white" />
            <ModalBody>
              <VStack spacing={4}>
                <FormControl>
                  <FormLabel color="white">Nom</FormLabel>
                  <Input
                    value={formData.nom}
                    onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
                    placeholder="Nom de l'organisation"
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel color="white">Description</FormLabel>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Description de l'organisation"
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel color="white">Adresse</FormLabel>
                  <Input
                    value={formData.adresse}
                    onChange={(e) => setFormData({ ...formData, adresse: e.target.value })}
                    placeholder="Adresse"
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel color="white">Email de contact</FormLabel>
                  <Input
                    value={formData.email_contact}
                    onChange={(e) => setFormData({ ...formData, email_contact: e.target.value })}
                    placeholder="Email"
                    type="email"
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel color="white">Téléphone</FormLabel>
                  <Input
                    value={formData.telephone_contact}
                    onChange={(e) => setFormData({ ...formData, telephone_contact: e.target.value })}
                    placeholder="Téléphone"
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel color="white">Nombre d'employés</FormLabel>
                  <Input
                    value={formData.nombre_employes}
                    onChange={(e) => setFormData({ ...formData, nombre_employes: parseInt(e.target.value) || 0 })}
                    type="number"
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                  />
                </FormControl>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onEditModalClose}>
                Annuler
              </Button>
              <Button
                colorScheme="blue"
                onClick={handleUpdate}
              >
                Mettre à jour
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </Box>
    </RequireRole>
  );
};

export default Organization; 



