import React, { useState, useEffect } from "react";
import {
  Box,
  Heading,
  VStack,
  Text,
  Button,
  useToast,
  Flex,
  Icon,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  FormControl,
  FormLabel,
  Select,
  Input,
  Textarea,
  Switch,
  FormHelperText,
  InputGroup,
  InputLeftElement,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  IconButton,
} from "@chakra-ui/react";
import { FiUsers, FiPlus, FiTrash2, FiEdit2, FiMail, FiPhone, FiMapPin } from "react-icons/fi";
import { ElementType } from "react";

// Composants d'icônes personnalisés
const MailIcon = (props: any) => <Icon as={FiMail as ElementType} {...props} />;
const PhoneIcon = (props: any) => <Icon as={FiPhone as ElementType} {...props} />;
const MapPinIcon = (props: any) => <Icon as={FiMapPin as ElementType} {...props} />;
const PlusIcon = (props: any) => <Icon as={FiPlus as ElementType} {...props} />;

interface Organization {
  id: number;
  nom: string;
  description: string;
  adresse: string;
  email_contact: string;
  telephone_contact: string;
  statut: 'ACTIVE' | 'INACTIVE';
  date_creation: string;
}

interface User {
  id: number;
  nom: string;
  prenom: string;
  email: string;
}

interface WorkflowStep {
  nom: string;
  description: string;
  ordre: number;
  responsables: string[];
}

const Organization: React.FC = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedOrganization, setSelectedOrganization] = useState<Organization | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const toast = useToast();

  // États pour le formulaire
  const [nom, setNom] = useState('');
  const [description, setDescription] = useState('');
  const [adresse, setAdresse] = useState('');
  const [emailContact, setEmailContact] = useState('');
  const [telephoneContact, setTelephoneContact] = useState('');
  const [statut, setStatut] = useState<'ACTIVE' | 'INACTIVE'>('ACTIVE');

  // États pour les membres
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [selectedMembers, setSelectedMembers] = useState<Array<{
    id: number;
    nom: string;
    prenom: string;
    email: string;
    role: 'ADMIN' | 'MEMBRE';
  }>>([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedRole, setSelectedRole] = useState<'ADMIN' | 'MEMBRE'>('MEMBRE');

  // États pour le workflow
  const [workflowNom, setWorkflowNom] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([]);
  const [currentStep, setCurrentStep] = useState<WorkflowStep>({
    nom: '',
    description: '',
    ordre: 1,
    responsables: []
  });

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/organizations", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setOrganizations(data);
      } else {
        throw new Error("Erreur lors de la récupération des organisations");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les organisations",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrganization = () => {
    setSelectedOrganization(null);
    setIsModalOpen(true);
  };

  const handleEditOrganization = (organization: Organization) => {
    setSelectedOrganization(organization);
    setIsModalOpen(true);
  };

  const handleDeleteOrganization = async (organizationId: number) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer cette organisation ?")) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:5000/api/organizations/${organizationId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Organisation supprimée avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        fetchOrganizations();
      } else {
        throw new Error("Erreur lors de la suppression");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer l'organisation",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleNext = () => {
    if (currentTab === 0 && !nom) {
      toast({
        title: "Erreur",
        description: "Le nom de l'organisation est requis",
        status: "error",
        duration: 3000,
        isClosable: true
      });
      return;
    }
    setCurrentTab(currentTab + 1);
  };

  const handleBack = () => {
    setCurrentTab(currentTab - 1);
  };

  // Chargement des utilisateurs disponibles
  useEffect(() => {
    if (isModalOpen) {
      fetchUsers();
    }
  }, [isModalOpen]);

  const fetchUsers = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/users", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setAvailableUsers(data);
      } else {
        throw new Error("Erreur lors de la récupération des utilisateurs");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger la liste des utilisateurs",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleAddMember = () => {
    if (!selectedUser) return;

    const user = availableUsers.find(u => u.id === parseInt(selectedUser));
    if (!user) return;

    if (selectedMembers.some(m => m.id === user.id)) {
      toast({
        title: "Erreur",
        description: "Cet utilisateur est déjà membre",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setSelectedMembers([...selectedMembers, {
      ...user,
      role: selectedRole
    }]);
    setSelectedUser('');
  };

  const handleRemoveMember = (userId: number) => {
    setSelectedMembers(selectedMembers.filter(m => m.id !== userId));
  };

  const handleAddWorkflowStep = () => {
    if (!currentStep.nom) {
      toast({
        title: "Erreur",
        description: "Le nom de l'étape est requis",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setWorkflowSteps([...workflowSteps, {
      ...currentStep,
      ordre: workflowSteps.length + 1
    }]);

    setCurrentStep({
      nom: '',
      description: '',
      ordre: workflowSteps.length + 2,
      responsables: []
    });
  };

  const handleRemoveWorkflowStep = (index: number) => {
    const newSteps = workflowSteps.filter((_, i) => i !== index)
      .map((step, i) => ({ ...step, ordre: i + 1 }));
    setWorkflowSteps(newSteps);
  };

  const handleSubmit = async () => {
    if (!nom) {
      toast({
        title: "Erreur",
        description: "Le nom de l'organisation est requis",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/api/organizations", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nom,
          description,
          adresse,
          email_contact: emailContact,
          telephone_contact: telephoneContact,
          statut,
          membres: selectedMembers.map(member => ({
            user_id: member.id,
            role: member.role
          })),
          workflow: workflowSteps.length > 0 ? {
            nom: workflowNom,
            description: workflowDescription,
            etapes: workflowSteps
          } : null
        }),
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Organisation créée avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        setIsModalOpen(false);
        fetchOrganizations();
        // Réinitialiser le formulaire
        setNom('');
        setDescription('');
        setAdresse('');
        setEmailContact('');
        setTelephoneContact('');
        setStatut('ACTIVE');
        setSelectedMembers([]);
        setWorkflowNom('');
        setWorkflowDescription('');
        setWorkflowSteps([]);
        setCurrentTab(0);
      } else {
        throw new Error("Erreur lors de la création");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de créer l'organisation",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading color="white" size="lg">
          Structure Organisationnelle
        </Heading>
        <Button
          leftIcon={<PlusIcon />}
          colorScheme="blue"
          onClick={handleCreateOrganization}
        >
          Nouvelle Organisation
        </Button>
      </Flex>

      {loading ? (
        <Text color="white" textAlign="center">
          Chargement...
        </Text>
      ) : organizations.length === 0 ? (
        <Box
          bg="#20243a"
          borderRadius="lg"
          p={6}
          textAlign="center"
          color="white"
        >
          <Icon
            as={FiUsers as ElementType}
            boxSize={8}
            color="gray.400"
            mb={2}
          />
          <Text>Aucune organisation trouvée</Text>
        </Box>
      ) : (
        <Box bg="#20243a" borderRadius="lg" p={6} overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">Nom</Th>
                <Th color="white">Description</Th>
                <Th color="white">Contact</Th>
                <Th color="white">Statut</Th>
                <Th color="white">Date de création</Th>
                <Th color="white">Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {organizations.map((organization) => (
                <Tr key={organization.id}>
                  <Td color="white">{organization.nom}</Td>
                  <Td color="white">{organization.description}</Td>
                  <Td color="white">
                    <VStack align="start" spacing={1}>
                      <Text fontSize="sm">{organization.email_contact}</Text>
                      <Text fontSize="sm">{organization.telephone_contact}</Text>
                    </VStack>
                  </Td>
                  <Td>
                    <Badge
                      colorScheme={organization.statut === 'ACTIVE' ? 'green' : 'red'}
                    >
                      {organization.statut}
                    </Badge>
                  </Td>
                  <Td color="white">
                    {new Date(organization.date_creation).toLocaleDateString()}
                  </Td>
                  <Td>
                    <Flex>
                      <Button
                        size="sm"
                        leftIcon={<Icon as={FiEdit2 as ElementType} />}
                        colorScheme="blue"
                        variant="ghost"
                        mr={2}
                        onClick={() => handleEditOrganization(organization)}
                      >
                        Modifier
                      </Button>
                      <Button
                        size="sm"
                        leftIcon={<Icon as={FiTrash2 as ElementType} />}
                        colorScheme="red"
                        variant="ghost"
                        onClick={() => handleDeleteOrganization(organization.id)}
                      >
                        Supprimer
                      </Button>
                    </Flex>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="xl">
        <ModalOverlay />
        <ModalContent bg="#1a1f37">
          <ModalHeader color="white">
            {selectedOrganization ? "Modifier l'organisation" : "Nouvelle organisation"}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Tabs 
              index={currentTab} 
              onChange={setCurrentTab} 
              variant="enclosed"
              colorScheme="blue"
              sx={{
                '.chakra-tabs__tab-panels': {
                  bg: '#20243a',
                  borderRadius: 'md',
                  p: 4
                },
                '.chakra-tabs__tablist': {
                  borderColor: '#2a2f4a',
                  mb: 4
                },
                '.chakra-tabs__tab': {
                  color: 'gray.400',
                  _selected: {
                    color: 'white',
                    bg: '#20243a',
                    borderColor: '#2a2f4a',
                    borderBottom: 'none'
                  },
                  _hover: {
                    color: 'white',
                    bg: '#2a2f4a'
                  }
                }
              }}
            >
              <TabList>
                <Tab>Informations</Tab>
                <Tab>Membres</Tab>
                <Tab>Workflow</Tab>
              </TabList>

              <TabPanels>
                {/* Panneau Informations */}
                <TabPanel>
                  <VStack spacing={4}>
                    <FormControl isRequired>
                      <FormLabel color="white">Nom</FormLabel>
                      <Input
                        value={nom}
                        onChange={(e) => setNom(e.target.value)}
                        placeholder="Nom de l'organisation"
                        bg="#20243a"
                        color="white"
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel color="white">Description</FormLabel>
                      <Textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Description de l'organisation"
                        bg="#20243a"
                        color="white"
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel color="white">Adresse</FormLabel>
                      <InputGroup>
                        <InputLeftElement>
                          <MapPinIcon color="gray.400" />
                        </InputLeftElement>
                        <Input
                          value={adresse}
                          onChange={(e) => setAdresse(e.target.value)}
                          placeholder="Adresse"
                          bg="#20243a"
                          color="white"
                        />
                      </InputGroup>
                    </FormControl>

                    <FormControl>
                      <FormLabel color="white">Email de contact</FormLabel>
                      <InputGroup>
                        <InputLeftElement>
                          <MailIcon color="gray.400" />
                        </InputLeftElement>
                        <Input
                          value={emailContact}
                          onChange={(e) => setEmailContact(e.target.value)}
                          placeholder="Email"
                          bg="#20243a"
                          color="white"
                        />
                      </InputGroup>
                    </FormControl>

                    <FormControl>
                      <FormLabel color="white">Téléphone de contact</FormLabel>
                      <InputGroup>
                        <InputLeftElement>
                          <PhoneIcon color="gray.400" />
                        </InputLeftElement>
                        <Input
                          value={telephoneContact}
                          onChange={(e) => setTelephoneContact(e.target.value)}
                          placeholder="Téléphone"
                          bg="#20243a"
                          color="white"
                        />
                      </InputGroup>
                    </FormControl>

                    <FormControl>
                      <FormLabel color="white">Statut</FormLabel>
                      <Switch
                        isChecked={statut === 'ACTIVE'}
                        onChange={(e) => setStatut(e.target.checked ? 'ACTIVE' : 'INACTIVE')}
                      />
                      <FormHelperText color="gray.400">
                        {statut === 'ACTIVE' ? 'Organisation active' : 'Organisation inactive'}
                      </FormHelperText>
                    </FormControl>
                  </VStack>
                </TabPanel>

                {/* Panneau Membres */}
                <TabPanel>
                  <VStack spacing={4} align="stretch">
                    <Box bg="#20243a" p={4} borderRadius="md">
                      <FormControl>
                        <FormLabel color="white">Ajouter un membre</FormLabel>
                        <Flex gap={2}>
                          <Select
                            value={selectedUser}
                            onChange={(e) => setSelectedUser(e.target.value)}
                            placeholder="Sélectionner un utilisateur"
                            bg="#2a2f4a"
                            color="white"
                            flex={2}
                          >
                            {availableUsers.map((user) => (
                              <option key={user.id} value={user.id}>
                                {`${user.prenom} ${user.nom} (${user.email})`}
                              </option>
                            ))}
                          </Select>
                          <Select
                            value={selectedRole}
                            onChange={(e) => setSelectedRole(e.target.value as 'ADMIN' | 'MEMBRE')}
                            bg="#2a2f4a"
                            color="white"
                            flex={1}
                          >
                            <option value="MEMBRE">Membre</option>
                            <option value="ADMIN">Admin</option>
                          </Select>
                          <IconButton
                            aria-label="Ajouter membre"
                            icon={<PlusIcon />}
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
                          {selectedMembers.map((member) => (
                            <Tr key={member.id}>
                              <Td color="white">{`${member.prenom} ${member.nom}`}</Td>
                              <Td color="white">{member.email}</Td>
                              <Td>
                                <Badge
                                  colorScheme={member.role === 'ADMIN' ? 'purple' : 'blue'}
                                >
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
                        <Icon as={FiUsers as ElementType} boxSize={8} color="gray.400" mb={2} />
                        <Text color="white">Aucun membre ajouté</Text>
                      </Box>
                    )}
                  </VStack>
                </TabPanel>

                {/* Panneau Workflow */}
                <TabPanel>
                  <VStack spacing={4} align="stretch">
                    <FormControl>
                      <FormLabel color="white">Nom du workflow</FormLabel>
                      <Input
                        value={workflowNom}
                        onChange={(e) => setWorkflowNom(e.target.value)}
                        placeholder="Nom du workflow"
                        bg="#20243a"
                        color="white"
                      />
                    </FormControl>

                    <FormControl>
                      <FormLabel color="white">Description du workflow</FormLabel>
                      <Textarea
                        value={workflowDescription}
                        onChange={(e) => setWorkflowDescription(e.target.value)}
                        placeholder="Description du workflow"
                        bg="#20243a"
                        color="white"
                      />
                    </FormControl>

                    <Box bg="#20243a" p={4} borderRadius="md">
                      <Text color="white" mb={2}>Ajouter une étape</Text>
                      <VStack spacing={3}>
                        <FormControl>
                          <FormLabel color="white">Nom de l'étape</FormLabel>
                          <Input
                            value={currentStep.nom}
                            onChange={(e) => setCurrentStep({
                              ...currentStep,
                              nom: e.target.value
                            })}
                            placeholder="Nom de l'étape"
                            bg="#2a2f4a"
                            color="white"
                          />
                        </FormControl>

                        <FormControl>
                          <FormLabel color="white">Description de l'étape</FormLabel>
                          <Textarea
                            value={currentStep.description}
                            onChange={(e) => setCurrentStep({
                              ...currentStep,
                              description: e.target.value
                            })}
                            placeholder="Description de l'étape"
                            bg="#2a2f4a"
                            color="white"
                          />
                        </FormControl>

                        <FormControl>
                          <FormLabel color="white">Responsables</FormLabel>
                          <Select
                            value=""
                            onChange={(e) => {
                              const userId = e.target.value;
                              if (userId && !currentStep.responsables.includes(userId)) {
                                setCurrentStep({
                                  ...currentStep,
                                  responsables: [...currentStep.responsables, userId]
                                });
                              }
                            }}
                            placeholder="Sélectionner des responsables"
                            bg="#2a2f4a"
                            color="white"
                          >
                            {selectedMembers.map((member) => (
                              <option key={member.id} value={member.id}>
                                {`${member.prenom} ${member.nom}`}
                              </option>
                            ))}
                          </Select>
                        </FormControl>

                        <Button
                          leftIcon={<PlusIcon />}
                          onClick={handleAddWorkflowStep}
                          colorScheme="blue"
                          width="full"
                        >
                          Ajouter l'étape
                        </Button>
                      </VStack>
                    </Box>

                    {workflowSteps.length > 0 ? (
                      <VStack spacing={2} align="stretch">
                        {workflowSteps.map((step, index) => (
                          <Box
                            key={index}
                            p={3}
                            bg="#20243a"
                            borderRadius="md"
                            position="relative"
                          >
                            <Flex justify="space-between" align="center">
                              <VStack align="start" spacing={1}>
                                <Text color="white" fontWeight="bold">
                                  {`${index + 1}. ${step.nom}`}
                                </Text>
                                <Text color="gray.400" fontSize="sm">
                                  {step.description}
                                </Text>
                                <Text color="gray.400" fontSize="sm">
                                  Responsables: {step.responsables.length}
                                </Text>
                              </VStack>
                              <IconButton
                                aria-label="Supprimer l'étape"
                                icon={<Icon as={FiTrash2 as ElementType} />}
                                onClick={() => handleRemoveWorkflowStep(index)}
                                variant="ghost"
                                colorScheme="red"
                                size="sm"
                              />
                            </Flex>
                          </Box>
                        ))}
                      </VStack>
                    ) : (
                      <Box textAlign="center" py={4}>
                        <Text color="white">Aucune étape définie</Text>
                      </Box>
                    )}
                  </VStack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={() => setIsModalOpen(false)}>
              Annuler
            </Button>
            {currentTab > 0 && (
              <Button variant="ghost" mr={3} onClick={handleBack}>
                Précédent
              </Button>
            )}
            {currentTab < 2 ? (
              <Button colorScheme="blue" onClick={handleNext}>
                Suivant
              </Button>
            ) : (
              <Button
                colorScheme="blue"
                onClick={handleSubmit}
              >
                Créer
              </Button>
            )}
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Organization; 