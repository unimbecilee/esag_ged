import React, { useState } from 'react';
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
  Switch,
  FormHelperText,
  InputGroup,
  InputLeftElement,
  Icon,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Select,
  Box,
  Text,
  Flex,
  Badge,
  IconButton,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
} from '@chakra-ui/react';
import { FiMail, FiPhone, FiMapPin, FiPlus, FiTrash2, FiUser } from 'react-icons/fi';
import { ElementType } from 'react';

// Composants d'icônes personnalisés
const MailIcon = (props: any) => <Icon as={FiMail as ElementType} {...props} />;
const PhoneIcon = (props: any) => <Icon as={FiPhone as ElementType} {...props} />;
const MapPinIcon = (props: any) => <Icon as={FiMapPin as ElementType} {...props} />;
const PlusIcon = (props: any) => <Icon as={FiPlus as ElementType} {...props} />;
const TrashIcon = (props: any) => <Icon as={FiTrash2 as ElementType} {...props} />;
const UserIcon = (props: any) => <Icon as={FiUser as ElementType} {...props} />;

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

interface CreateOrganizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const CreateOrganizationModal: React.FC<CreateOrganizationModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  // État général
  const [currentTab, setCurrentTab] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  // Informations de base
  const [nom, setNom] = useState('');
  const [description, setDescription] = useState('');
  const [adresse, setAdresse] = useState('');
  const [emailContact, setEmailContact] = useState('');
  const [telephoneContact, setTelephoneContact] = useState('');
  const [statut, setStatut] = useState<'ACTIVE' | 'INACTIVE'>('ACTIVE');

  // Gestion des membres
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

  // Gestion du workflow initial
  const [workflowNom, setWorkflowNom] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([]);
  const [currentStep, setCurrentStep] = useState<WorkflowStep>({
    nom: '',
    description: '',
    ordre: 1,
    responsables: []
  });

  // Chargement des utilisateurs disponibles
  React.useEffect(() => {
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
        title: 'Erreur',
        description: 'Le nom de l\'étape est requis',
        status: 'error',
        duration: 3000,
        isClosable: true
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

  const validateBasicInfo = () => {
    if (!nom) {
      toast({
        title: 'Erreur',
        description: 'Le nom de l\'organisation est requis',
        status: 'error',
        duration: 3000,
        isClosable: true
      });
      return false;
    }
    return true;
  };

  const handleNext = () => {
    if (currentTab === 0 && !validateBasicInfo()) return;
    setCurrentTab(currentTab + 1);
  };

  const handleBack = () => {
    setCurrentTab(currentTab - 1);
  };

  const handleSubmit = async () => {
    if (!validateBasicInfo()) return;

    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      
      // Créer l'organisation
      const orgResponse = await fetch('http://localhost:5000/api/organizations', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
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
        })
      });

      if (!orgResponse.ok) {
        throw new Error('Erreur lors de la création de l\'organisation');
      }

      toast({
        title: 'Succès',
        description: 'Organisation créée avec succès',
        status: 'success',
        duration: 5000,
        isClosable: true
      });

      onSuccess();
      onClose();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de créer l\'organisation',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent bg="#1a1f37">
        <ModalHeader color="white">Créer une nouvelle organisation</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Tabs index={currentTab} onChange={setCurrentTab} variant="enclosed">
            <TabList mb={4}>
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
                                icon={<TrashIcon />}
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
                      <UserIcon boxSize={8} color="gray.400" mb={2} />
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
                              icon={<TrashIcon />}
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
          <Button variant="ghost" mr={3} onClick={onClose}>
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
              isLoading={isLoading}
            >
              Créer
            </Button>
          )}
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default CreateOrganizationModal; 