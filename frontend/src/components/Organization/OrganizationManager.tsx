import React, { useState, useEffect, forwardRef } from 'react';
import {
  Box,
  Flex,
  Heading,
  Button,
  useDisclosure,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Icon,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useToast,
  Badge,
  Text,
  VStack,
  IconButton,
  createIcon
} from '@chakra-ui/react';
import { FiPlus, FiMoreVertical, FiEdit2, FiTrash2, FiUsers, FiMail, FiPhone, FiMapPin } from 'react-icons/fi';
import CreateOrganizationModal from './CreateOrganizationModal';
import EditOrganizationModal from './EditOrganizationModal';
import DeleteConfirmationModal from '../common/DeleteConfirmationModal';
import AddMemberModal from './AddMemberModal';
import AddDocumentModal from './AddDocumentModal';

// Créer des composants d'icônes personnalisés
const PlusIcon = (props: any) => <Icon as={FiPlus} {...props} />;
const MailIcon = (props: any) => <Icon as={FiMail} {...props} />;
const PhoneIcon = (props: any) => <Icon as={FiPhone} {...props} />;
const MapPinIcon = (props: any) => <Icon as={FiMapPin} {...props} />;
const UsersIcon = (props: any) => <Icon as={FiUsers} {...props} />;
const MoreVerticalIcon = (props: any) => <Icon as={FiMoreVertical} {...props} />;
const EditIcon = (props: any) => <Icon as={FiEdit2} {...props} />;
const TrashIcon = (props: any) => <Icon as={FiTrash2} {...props} />;

interface OrganizationMember {
  id: number;
  nom: string;
  prenom: string;
  email: string;
  role: 'ADMIN' | 'MEMBRE';
  date_ajout: string;
}

interface OrganizationDocument {
  id: number;
  nom: string;
  type: string;
  date_ajout: string;
  ajoute_par: string;
}

interface Organization {
  id: number;
  nom: string;
  description: string;
  adresse: string;
  email_contact: string;
  telephone_contact: string;
  date_creation: string;
  nombre_membres: number;
  statut: 'ACTIVE' | 'INACTIVE';
  membres?: OrganizationMember[];
  documents?: OrganizationDocument[];
  workflows?: {
    id: number;
    nom: string;
    description: string;
    etapes: Array<{
      id: number;
      nom: string;
      ordre: number;
      responsables: string[];
    }>;
  }[];
}

const OrganizationManager: React.FC = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const toast = useToast();

  const {
    isOpen: isCreateOpen,
    onOpen: onCreateOpen,
    onClose: onCreateClose
  } = useDisclosure();

  const {
    isOpen: isEditOpen,
    onOpen: onEditOpen,
    onClose: onEditClose
  } = useDisclosure();

  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose
  } = useDisclosure();

  const {
    isOpen: isAddMemberOpen,
    onOpen: onAddMemberOpen,
    onClose: onAddMemberClose
  } = useDisclosure();

  const {
    isOpen: isAddDocumentOpen,
    onOpen: onAddDocumentOpen,
    onClose: onAddDocumentClose
  } = useDisclosure();

  const [selectedTab, setSelectedTab] = useState<'info' | 'membres' | 'documents' | 'workflows'>('info');
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [documents, setDocuments] = useState<OrganizationDocument[]>([]);

  const fetchOrganizations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/organizations', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la récupération des organisations');
      }

      const data = await response.json();
      setOrganizations(data);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les organisations',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchOrganizationDetails = async (orgId: number) => {
    try {
      const token = localStorage.getItem('token');
      
      // Récupérer les membres
      const membersResponse = await fetch(`http://localhost:5000/api/organizations/${orgId}/members`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (membersResponse.ok) {
        const membersData = await membersResponse.json();
        setMembers(membersData);
      }

      // Récupérer les documents
      const documentsResponse = await fetch(`http://localhost:5000/api/organizations/${orgId}/documents`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (documentsResponse.ok) {
        const documentsData = await documentsResponse.json();
        setDocuments(documentsData);
      }

    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les détails de l\'organisation',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const handleDelete = async () => {
    if (!selectedOrg) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/organizations/${selectedOrg.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la suppression');
      }

      toast({
        title: 'Succès',
        description: 'Organisation supprimée avec succès',
        status: 'success',
        duration: 5000,
        isClosable: true
      });

      fetchOrganizations();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de supprimer l\'organisation',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    } finally {
      onDeleteClose();
    }
  };

  const handleRemoveMember = async (memberId: number) => {
    if (!selectedOrg) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/organizations/${selectedOrg.id}/members/${memberId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la suppression du membre');
      }

      toast({
        title: 'Succès',
        description: 'Membre retiré avec succès',
        status: 'success',
        duration: 5000,
        isClosable: true
      });

      fetchOrganizationDetails(selectedOrg.id);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de retirer le membre',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  };

  const handleViewDocument = async (documentId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/documents/${documentId}/view`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'ouverture du document');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible d\'ouvrir le document',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  };

  const handleRemoveDocument = async (documentId: number) => {
    if (!selectedOrg) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/organizations/${selectedOrg.id}/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la suppression du document');
      }

      toast({
        title: 'Succès',
        description: 'Document retiré avec succès',
        status: 'success',
        duration: 5000,
        isClosable: true
      });

      fetchOrganizationDetails(selectedOrg.id);
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de retirer le document',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  };

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">Gestion des Organisations</Heading>
        <Button
          leftIcon={<PlusIcon boxSize={5} />}
          colorScheme="blue"
          onClick={onCreateOpen}
        >
          Nouvelle Organisation
        </Button>
      </Flex>

      {selectedOrg ? (
        <Box>
          <Flex mb={4}>
            <Button
              variant={selectedTab === 'info' ? 'solid' : 'ghost'}
              onClick={() => setSelectedTab('info')}
              mr={2}
            >
              Informations
            </Button>
            <Button
              variant={selectedTab === 'membres' ? 'solid' : 'ghost'}
              onClick={() => setSelectedTab('membres')}
              mr={2}
            >
              Membres
            </Button>
            <Button
              variant={selectedTab === 'documents' ? 'solid' : 'ghost'}
              onClick={() => setSelectedTab('documents')}
              mr={2}
            >
              Documents
            </Button>
            <Button
              variant={selectedTab === 'workflows' ? 'solid' : 'ghost'}
              onClick={() => setSelectedTab('workflows')}
            >
              Workflows
            </Button>
          </Flex>

          {selectedTab === 'info' && (
            <Box bg="#20243a" borderRadius="lg" p={6}>
              <VStack align="stretch" spacing={4}>
                <Text><strong>Nom:</strong> {selectedOrg.nom}</Text>
                <Text><strong>Description:</strong> {selectedOrg.description}</Text>
                <Text><strong>Adresse:</strong> {selectedOrg.adresse}</Text>
                <Text><strong>Email:</strong> {selectedOrg.email_contact}</Text>
                <Text><strong>Téléphone:</strong> {selectedOrg.telephone_contact}</Text>
                <Text><strong>Date de création:</strong> {new Date(selectedOrg.date_creation).toLocaleDateString()}</Text>
                <Text><strong>Nombre de membres:</strong> {selectedOrg.nombre_membres}</Text>
                <Badge colorScheme={selectedOrg.statut === 'ACTIVE' ? 'green' : 'red'}>
                  {selectedOrg.statut}
                </Badge>
              </VStack>
            </Box>
          )}

          {selectedTab === 'membres' && (
            <Box bg="#20243a" borderRadius="lg" overflow="hidden">
              <Flex justify="flex-end" p={4}>
                <Button
                  leftIcon={<PlusIcon boxSize={4} />}
                  colorScheme="blue"
                  size="sm"
                  onClick={onAddMemberOpen}
                >
                  Ajouter un membre
                </Button>
              </Flex>
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th color="gray.400">Nom</Th>
                    <Th color="gray.400">Email</Th>
                    <Th color="gray.400">Rôle</Th>
                    <Th color="gray.400">Date d'ajout</Th>
                    <Th color="gray.400">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {members.map((member) => (
                    <Tr key={member.id}>
                      <Td>{`${member.prenom} ${member.nom}`}</Td>
                      <Td>{member.email}</Td>
                      <Td>
                        <Badge colorScheme={member.role === 'ADMIN' ? 'purple' : 'blue'}>
                          {member.role}
                        </Badge>
                      </Td>
                      <Td>{new Date(member.date_ajout).toLocaleDateString()}</Td>
                      <Td>
                        <Button
                          size="sm"
                          colorScheme="red"
                          variant="ghost"
                          leftIcon={<TrashIcon boxSize={4} />}
                          onClick={() => handleRemoveMember(member.id)}
                        >
                          Retirer
                        </Button>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          )}

          {selectedTab === 'documents' && (
            <Box bg="#20243a" borderRadius="lg" overflow="hidden">
              <Flex justify="flex-end" p={4}>
                <Button
                  leftIcon={<PlusIcon boxSize={4} />}
                  colorScheme="blue"
                  size="sm"
                  onClick={onAddDocumentOpen}
                >
                  Ajouter un document
                </Button>
              </Flex>
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th color="gray.400">Nom</Th>
                    <Th color="gray.400">Type</Th>
                    <Th color="gray.400">Ajouté par</Th>
                    <Th color="gray.400">Date d'ajout</Th>
                    <Th color="gray.400">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {documents.map((doc) => (
                    <Tr key={doc.id}>
                      <Td>{doc.nom}</Td>
                      <Td>{doc.type}</Td>
                      <Td>{doc.ajoute_par}</Td>
                      <Td>{new Date(doc.date_ajout).toLocaleDateString()}</Td>
                      <Td>
                        <Button
                          size="sm"
                          colorScheme="blue"
                          variant="ghost"
                          mr={2}
                          onClick={() => handleViewDocument(doc.id)}
                        >
                          Voir
                        </Button>
                        <Button
                          size="sm"
                          colorScheme="red"
                          variant="ghost"
                          leftIcon={<TrashIcon boxSize={4} />}
                          onClick={() => handleRemoveDocument(doc.id)}
                        >
                          Retirer
                        </Button>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          )}

          {selectedTab === 'workflows' && (
            <Box bg="#20243a" borderRadius="lg" p={6}>
              {selectedOrg.workflows?.map((workflow) => (
                <Box key={workflow.id} p={4} borderWidth="1px" borderRadius="md" mb={4}>
                  <Heading size="md" mb={2}>{workflow.nom}</Heading>
                  <Text mb={4}>{workflow.description}</Text>
                  <VStack align="stretch" spacing={2}>
                    {workflow.etapes.map((etape) => (
                      <Box key={etape.id} p={2} bg="whiteAlpha.100" borderRadius="md">
                        <Text fontWeight="bold">{etape.nom}</Text>
                        <Text fontSize="sm">Ordre: {etape.ordre}</Text>
                        <Text fontSize="sm">Responsables: {etape.responsables.join(', ')}</Text>
                      </Box>
                    ))}
                  </VStack>
                </Box>
              ))}
            </Box>
          )}
        </Box>
      ) : (
        <Box bg="#20243a" borderRadius="lg" overflow="hidden">
          <Table variant="simple" w="100%">
            <Thead>
              <Tr>
                <Th color="gray.400">Nom</Th>
                <Th color="gray.400">Description</Th>
                <Th color="gray.400">Contact</Th>
                <Th color="gray.400">Membres</Th>
                <Th color="gray.400">Statut</Th>
                <Th color="gray.400">Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {organizations.map((org) => (
                <Tr key={org.id}>
                  <Td>{org.nom}</Td>
                  <Td>
                    <Box maxW="300px" isTruncated>
                      {org.description || '-'}
                    </Box>
                  </Td>
                  <Td>
                    <VStack align="start" spacing={1}>
                      {org.email_contact && (
                        <Text fontSize="sm" display="flex" alignItems="center" gap={2}>
                          <MailIcon boxSize={4} />
                          {org.email_contact}
                        </Text>
                      )}
                      {org.telephone_contact && (
                        <Text fontSize="sm" display="flex" alignItems="center" gap={2}>
                          <PhoneIcon boxSize={4} />
                          {org.telephone_contact}
                        </Text>
                      )}
                      {org.adresse && (
                        <Text fontSize="sm" display="flex" alignItems="center" gap={2}>
                          <MapPinIcon boxSize={4} />
                          {org.adresse}
                        </Text>
                      )}
                      {!org.email_contact && !org.telephone_contact && !org.adresse && '-'}
                    </VStack>
                  </Td>
                  <Td>
                    <Text display="flex" alignItems="center" gap={2}>
                      <UsersIcon boxSize={4} />
                      {org.nombre_membres}
                    </Text>
                  </Td>
                  <Td>
                    <Badge
                      colorScheme={org.statut === 'ACTIVE' ? 'green' : 'red'}
                      px={2}
                      py={1}
                      borderRadius="full"
                    >
                      {org.statut === 'ACTIVE' ? 'Active' : 'Inactive'}
                    </Badge>
                  </Td>
                  <Td>
                    <Menu>
                      <MenuButton
                        as={IconButton}
                        aria-label="Actions"
                        icon={<MoreVerticalIcon boxSize={4} />}
                        variant="ghost"
                        size="sm"
                      />
                      <MenuList bg="#2a2f4a" borderColor="#363b5a">
                        <MenuItem
                          icon={<EditIcon boxSize={4} />}
                          onClick={() => {
                            setSelectedOrg(org);
                            onEditOpen();
                          }}
                          _hover={{ bg: '#363b5a' }}
                        >
                          Modifier
                        </MenuItem>
                        <MenuItem
                          icon={<TrashIcon boxSize={4} />}
                          onClick={() => {
                            setSelectedOrg(org);
                            onDeleteOpen();
                          }}
                          _hover={{ bg: '#363b5a' }}
                          color="red.300"
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

      <CreateOrganizationModal
        isOpen={isCreateOpen}
        onClose={onCreateClose}
        onSuccess={() => {
          fetchOrganizations();
          onCreateClose();
        }}
      />

      {selectedOrg && (
        <>
          <EditOrganizationModal
            isOpen={isEditOpen}
            onClose={onEditClose}
            organization={selectedOrg}
            onSuccess={() => {
              fetchOrganizations();
              onEditClose();
            }}
          />

          <AddMemberModal
            isOpen={isAddMemberOpen}
            onClose={onAddMemberClose}
            organizationId={selectedOrg.id}
            onSuccess={() => {
              fetchOrganizationDetails(selectedOrg.id);
              onAddMemberClose();
            }}
          />

          <AddDocumentModal
            isOpen={isAddDocumentOpen}
            onClose={onAddDocumentClose}
            organizationId={selectedOrg.id}
            onSuccess={() => {
              fetchOrganizationDetails(selectedOrg.id);
              onAddDocumentClose();
            }}
          />

          <DeleteConfirmationModal
            isOpen={isDeleteOpen}
            onClose={onDeleteClose}
            onConfirm={handleDelete}
            title="Supprimer l'organisation"
            message="Êtes-vous sûr de vouloir supprimer cette organisation ? Cette action est irréversible."
          />
        </>
      )}
    </Box>
  );
};

export default OrganizationManager; 