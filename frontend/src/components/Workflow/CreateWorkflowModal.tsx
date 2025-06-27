import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  Input,
  Textarea,
  FormControl,
  FormLabel,
  FormErrorMessage,
  Select,
  Box,
  Text,
  IconButton,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Badge,
  Divider,
  Alert,
  AlertIcon,
  useToast,
  Grid,
  GridItem,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Checkbox,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Switch,
  FormHelperText,
  Icon
} from '@chakra-ui/react';
import { AddIcon, DeleteIcon, DragHandleIcon, ChevronDownIcon } from '@chakra-ui/icons';
import { FiUsers, FiUser, FiBriefcase } from 'react-icons/fi';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import { checkAuthToken } from '../../utils/errorHandling';
import { API_URL } from '../../config';

// Helper component pour les icônes
const IconWrapper: React.FC<{ icon: any; color?: string }> = ({ icon: IconComponent, color }) => (
  <Icon as={IconComponent} color={color} />
);

interface User {
  id: number;
  nom: string;
  prenom: string;
  email: string;
  role: string;
}

interface Role {
  id: number;
  nom: string;
  description: string;
}

interface Organization {
  id: number;
  nom: string;
  description: string;
}

interface Approbateur {
  type: 'utilisateur' | 'role' | 'organisation';
  id: number;
  nom: string;
  prenom?: string;
}

interface WorkflowStep {
  nom: string;
  description: string;
  type_approbation: 'SIMPLE' | 'MULTIPLE' | 'PARALLELE';
  delai_max?: number;
  approbateurs: Approbateur[];
}

interface CreateWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onWorkflowCreated: () => void;
}

const CreateWorkflowModal: React.FC<CreateWorkflowModalProps> = ({
  isOpen,
  onClose,
  onWorkflowCreated
}) => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  // États du formulaire
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [steps, setSteps] = useState<WorkflowStep[]>([]);

  // Données pour les sélecteurs
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  
  // États pour les modals de sélection
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [organizationModalOpen, setOrganizationModalOpen] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(-1);

  // États de validation
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Charger les données nécessaires
  useEffect(() => {
    if (isOpen) {
      loadInitialData();
    }
  }, [isOpen]);

  const loadInitialData = async () => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        // Charger les utilisateurs
        const usersResponse = await fetch(`${API_URL}/api/users/for-approval`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (usersResponse.ok) {
          setUsers(await usersResponse.json());
        }

        // Charger les organisations
        const orgsResponse = await fetch(`${API_URL}/api/organizations`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (orgsResponse.ok) {
          setOrganizations(await orgsResponse.json());
        }
      },
      {
        loadingMessage: "Chargement des données...",
        errorMessage: "Impossible de charger les données"
      }
    );
  };

  const addStep = () => {
    const newStep: WorkflowStep = {
      nom: '',
      description: '',
      type_approbation: 'SIMPLE',
      delai_max: undefined,
      approbateurs: []
    };
    setSteps([...steps, newStep]);
  };

  const removeStep = (index: number) => {
    const newSteps = steps.filter((_, i) => i !== index);
    setSteps(newSteps);
  };

  const updateStep = (index: number, field: keyof WorkflowStep, value: any) => {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setSteps(newSteps);
  };

  const addApprobateur = (stepIndex: number, approbateur: Approbateur) => {
    const newSteps = [...steps];
    const currentApprobateurs = newSteps[stepIndex].approbateurs;
    
    // Vérifier si l'approbateur n'est pas déjà ajouté
    const isAlreadyAdded = currentApprobateurs.some(
      a => a.type === approbateur.type && a.id === approbateur.id
    );
    
    if (!isAlreadyAdded) {
      newSteps[stepIndex].approbateurs.push(approbateur);
      setSteps(newSteps);
    }
  };

  const removeApprobateur = (stepIndex: number, approvateurIndex: number) => {
    const newSteps = [...steps];
    newSteps[stepIndex].approbateurs.splice(approvateurIndex, 1);
    setSteps(newSteps);
  };

  const openUserModal = (stepIndex: number) => {
    setCurrentStepIndex(stepIndex);
    setUserModalOpen(true);
  };

  const openOrganizationModal = (stepIndex: number) => {
    setCurrentStepIndex(stepIndex);
    setOrganizationModalOpen(true);
  };

  const handleUserSelect = (user: User) => {
    if (currentStepIndex >= 0) {
      const approbateur: Approbateur = {
        type: 'utilisateur',
        id: user.id,
        nom: user.nom,
        prenom: user.prenom
      };
      addApprobateur(currentStepIndex, approbateur);
    }
    setUserModalOpen(false);
    setCurrentStepIndex(-1);
  };

  const handleOrganizationSelect = (org: Organization) => {
    if (currentStepIndex >= 0) {
      const approbateur: Approbateur = {
        type: 'organisation',
        id: org.id,
        nom: org.nom
      };
      addApprobateur(currentStepIndex, approbateur);
    }
    setOrganizationModalOpen(false);
    setCurrentStepIndex(-1);
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!workflowName.trim()) {
      newErrors.workflowName = 'Le nom du workflow est requis';
    }

    steps.forEach((step, index) => {
      if (!step.nom.trim()) {
        newErrors[`step_${index}_nom`] = 'Le nom de l\'étape est requis';
      }
      if (step.approbateurs.length === 0) {
        newErrors[`step_${index}_approbateurs`] = 'Au moins un approbateur est requis';
      }
    });

    if (steps.length === 0) {
      newErrors.steps = 'Au moins une étape est requise';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        const workflowData = {
          nom: workflowName,
          description: workflowDescription,
          etapes: steps.map(step => ({
            nom: step.nom,
            description: step.description,
            type_approbation: step.type_approbation,
            delai_max: step.delai_max,
            approbateurs: step.approbateurs.map(app => ({
              utilisateur_id: app.type === 'utilisateur' ? app.id : undefined,
              role_id: app.type === 'role' ? app.id : undefined,
              organisation_id: app.type === 'organisation' ? app.id : undefined
            }))
          }))
        };

        const response = await fetch(`${API_URL}/api/workflows`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(workflowData)
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Erreur lors de la création');
        }

        toast({
          title: 'Succès',
          description: 'Workflow créé avec succès',
          status: 'success',
          duration: 5000,
          isClosable: true
        });

        handleClose();
        onWorkflowCreated();
      },
      {
        loadingMessage: "Création du workflow...",
        errorMessage: "Impossible de créer le workflow"
      }
    );
  };

  const handleClose = () => {
    setWorkflowName('');
    setWorkflowDescription('');
    setSteps([]);
    setErrors({});
    onClose();
  };

  const getApprovateurIcon = (type: string) => {
    switch (type) {
      case 'utilisateur': return FiUser;
      case 'role': return FiUsers;
      case 'organisation': return FiBriefcase;
      default: return FiUser;
    }
  };

  const getTypeApproLabel = (type: string) => {
    switch (type) {
      case 'SIMPLE': return 'Simple (un approbateur suffit)';
      case 'MULTIPLE': return 'Multiple (tous doivent approuver)';
      case 'PARALLELE': return 'Parallèle (majorité requise)';
      default: return type;
    }
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={handleClose} size="4xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent bg="#232946" color="white" maxH="90vh">
        <ModalHeader>Créer un nouveau workflow</ModalHeader>
        <ModalCloseButton />
        
        <ModalBody pb={6}>
          <VStack spacing={6} align="stretch">
            {/* Informations générales */}
            <Box>
              <Text fontSize="lg" fontWeight="bold" mb={4}>Informations générales</Text>
              
              <VStack spacing={4}>
                <FormControl isInvalid={!!errors.workflowName}>
                  <FormLabel>Nom du workflow *</FormLabel>
                  <Input
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                    placeholder="Ex: Validation documents comptables"
                    bg="#20243a"
                  />
                  <FormErrorMessage>{errors.workflowName}</FormErrorMessage>
                </FormControl>

                <FormControl>
                  <FormLabel>Description</FormLabel>
                  <Textarea
                    value={workflowDescription}
                    onChange={(e) => setWorkflowDescription(e.target.value)}
                    placeholder="Description du processus de validation..."
                    bg="#20243a"
                    rows={3}
                  />
                </FormControl>
              </VStack>
            </Box>

            <Divider />

            {/* Étapes du workflow */}
            <Box>
              <HStack justify="space-between" align="center" mb={4}>
                <Text fontSize="lg" fontWeight="bold">
                  Étapes du workflow ({steps.length})
                </Text>
                <Button leftIcon={<AddIcon />} onClick={addStep} colorScheme="blue" size="sm">
                  Ajouter une étape
                </Button>
              </HStack>

              {errors.steps && (
                <Alert status="error" mb={4}>
                  <AlertIcon />
                  {errors.steps}
                </Alert>
              )}

              <VStack spacing={4}>
                {steps.map((step, stepIndex) => (
                  <Box key={stepIndex} w="100%" bg="#20243a" p={4} borderRadius="md" border="1px solid #3a8bfd">
                    <HStack justify="space-between" align="flex-start" mb={4}>
                      <HStack>
                        <DragHandleIcon color="gray.400" />
                        <Badge colorScheme="blue" size="sm">Étape {stepIndex + 1}</Badge>
                      </HStack>
                      <IconButton
                        icon={<DeleteIcon />}
                        size="sm"
                        colorScheme="red"
                        variant="ghost"
                        onClick={() => removeStep(stepIndex)}
                        aria-label="Supprimer l'étape"
                      />
                    </HStack>

                    <Grid templateColumns="1fr 1fr" gap={4} mb={4}>
                      <GridItem>
                        <FormControl isInvalid={!!errors[`step_${stepIndex}_nom`]}>
                          <FormLabel fontSize="sm">Nom de l'étape *</FormLabel>
                          <Input
                            value={step.nom}
                            onChange={(e) => updateStep(stepIndex, 'nom', e.target.value)}
                            placeholder="Ex: Validation comptable"
                            size="sm"
                            bg="#232946"
                          />
                          <FormErrorMessage>{errors[`step_${stepIndex}_nom`]}</FormErrorMessage>
                        </FormControl>
                      </GridItem>
                      
                      <GridItem>
                        <FormControl>
                          <FormLabel fontSize="sm">Délai maximum (heures)</FormLabel>
                          <NumberInput
                            value={step.delai_max || ''}
                            onChange={(_, value) => updateStep(stepIndex, 'delai_max', value || undefined)}
                            min={1}
                            size="sm"
                          >
                            <NumberInputField bg="#232946" placeholder="Optionnel" />
                            <NumberInputStepper>
                              <NumberIncrementStepper />
                              <NumberDecrementStepper />
                            </NumberInputStepper>
                          </NumberInput>
                        </FormControl>
                      </GridItem>
                    </Grid>

                    <FormControl mb={4}>
                      <FormLabel fontSize="sm">Description</FormLabel>
                      <Textarea
                        value={step.description}
                        onChange={(e) => updateStep(stepIndex, 'description', e.target.value)}
                        placeholder="Description de l'étape..."
                        size="sm"
                        rows={2}
                        bg="#232946"
                      />
                    </FormControl>

                    <Grid templateColumns="1fr 1fr" gap={4} mb={4}>
                      <GridItem>
                        <FormControl>
                          <FormLabel fontSize="sm">Type d'approbation</FormLabel>
                          <Select
                            value={step.type_approbation}
                            onChange={(e) => updateStep(stepIndex, 'type_approbation', e.target.value)}
                            size="sm"
                            bg="#232946"
                          >
                            <option value="SIMPLE">Simple</option>
                            <option value="MULTIPLE">Multiple</option>
                            <option value="PARALLELE">Parallèle</option>
                          </Select>
                          <FormHelperText fontSize="xs">
                            {getTypeApproLabel(step.type_approbation)}
                          </FormHelperText>
                        </FormControl>
                      </GridItem>
                    </Grid>

                    {/* Approbateurs */}
                    <Box>
                      <HStack justify="space-between" align="center" mb={3}>
                        <Text fontSize="sm" fontWeight="semibold">
                          Approbateurs ({step.approbateurs.length})
                        </Text>
                        <Menu>
                          <MenuButton as={Button} size="xs" rightIcon={<ChevronDownIcon />}>
                            Ajouter
                          </MenuButton>
                          <MenuList bg="#232946" border="1px solid #3a8bfd">
                            <MenuItem
                              bg="#232946"
                              _hover={{ bg: "#20243a" }}
                              onClick={() => openUserModal(stepIndex)}
                            >
                              <HStack>
                                <IconWrapper icon={FiUser} />
                                <Text>Utilisateur</Text>
                              </HStack>
                            </MenuItem>
                            <MenuItem
                              bg="#232946"
                              _hover={{ bg: "#20243a" }}
                              onClick={() => openOrganizationModal(stepIndex)}
                            >
                              <HStack>
                                <IconWrapper icon={FiBriefcase} />
                                <Text>Organisation</Text>
                              </HStack>
                            </MenuItem>
                          </MenuList>
                        </Menu>
                      </HStack>

                      {errors[`step_${stepIndex}_approbateurs`] && (
                        <Alert status="error" size="sm" mb={3}>
                          <AlertIcon />
                          {errors[`step_${stepIndex}_approbateurs`]}
                        </Alert>
                      )}

                      <VStack spacing={2} align="stretch">
                        {step.approbateurs.map((approbateur, appIndex) => (
                          <HStack
                            key={appIndex}
                            justify="space-between"
                            p={2}
                            bg="#232946"
                            borderRadius="md"
                            border="1px solid #444"
                          >
                            <HStack>
                              <IconWrapper icon={getApprovateurIcon(approbateur.type)} />
                              <Text fontSize="sm">
                                {approbateur.nom} {approbateur.prenom || ''}
                              </Text>
                              <Badge size="xs" colorScheme="gray">
                                {approbateur.type}
                              </Badge>
                            </HStack>
                            <IconButton
                              icon={<DeleteIcon />}
                              size="xs"
                              colorScheme="red"
                              variant="ghost"
                              onClick={() => removeApprobateur(stepIndex, appIndex)}
                              aria-label="Supprimer l'approbateur"
                            />
                          </HStack>
                        ))}
                        
                        {step.approbateurs.length === 0 && (
                          <Text fontSize="sm" color="gray.400" textAlign="center" py={2}>
                            Aucun approbateur défini
                          </Text>
                        )}
                      </VStack>
                    </Box>
                  </Box>
                ))}

                {steps.length === 0 && (
                  <Box textAlign="center" py={8}>
                    <Text color="gray.400" mb={4}>
                      Aucune étape définie. Cliquez sur "Ajouter une étape" pour commencer.
                    </Text>
                  </Box>
                )}
              </VStack>
            </Box>

            {/* Boutons d'action */}
            <HStack justify="flex-end" pt={4}>
              <Button variant="ghost" onClick={handleClose}>
                Annuler
              </Button>
              <Button
                colorScheme="blue"
                onClick={handleSubmit}
                isDisabled={steps.length === 0 || !workflowName.trim()}
              >
                Créer le workflow
              </Button>
            </HStack>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>

    {/* Modal de sélection d'utilisateurs */}
    <Modal isOpen={userModalOpen} onClose={() => setUserModalOpen(false)} size="md">
      <ModalOverlay />
      <ModalContent bg="#232946" color="white">
        <ModalHeader>Sélectionner un utilisateur</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={2} align="stretch" maxH="400px" overflowY="auto">
            {users.map((user) => (
              <Box
                key={user.id}
                p={3}
                bg="#20243a"
                borderRadius="md"
                cursor="pointer"
                _hover={{ bg: "#1a1f36" }}
                onClick={() => handleUserSelect(user)}
              >
                <HStack>
                  <IconWrapper icon={FiUser} />
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="semibold">{user.prenom} {user.nom}</Text>
                    <Text fontSize="sm" color="gray.400">{user.email}</Text>
                    <Badge size="sm" colorScheme="blue">{user.role}</Badge>
                  </VStack>
                </HStack>
              </Box>
            ))}
            {users.length === 0 && (
              <Text textAlign="center" color="gray.400" py={4}>
                Aucun utilisateur disponible
              </Text>
            )}
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>

    {/* Modal de sélection d'organisations */}
    <Modal isOpen={organizationModalOpen} onClose={() => setOrganizationModalOpen(false)} size="md">
      <ModalOverlay />
      <ModalContent bg="#232946" color="white">
        <ModalHeader>Sélectionner une organisation</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={2} align="stretch" maxH="400px" overflowY="auto">
            {organizations.map((org) => (
              <Box
                key={org.id}
                p={3}
                bg="#20243a"
                borderRadius="md"
                cursor="pointer"
                _hover={{ bg: "#1a1f36" }}
                onClick={() => handleOrganizationSelect(org)}
              >
                <HStack>
                  <IconWrapper icon={FiBriefcase} />
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="semibold">{org.nom}</Text>
                    <Text fontSize="sm" color="gray.400">{org.description}</Text>
                  </VStack>
                </HStack>
              </Box>
            ))}
            {organizations.length === 0 && (
              <Text textAlign="center" color="gray.400" py={4}>
                Aucune organisation disponible
              </Text>
            )}
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
    </>
  );
};

export default CreateWorkflowModal; 



