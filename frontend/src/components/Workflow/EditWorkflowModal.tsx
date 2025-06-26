import React, { useState, useEffect } from 'react';
import {
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalFooter, ModalCloseButton,
  VStack, HStack, Text, Button, Box, Badge, IconButton, useToast,
  Menu, MenuButton, MenuList, MenuItem, Alert, AlertIcon, Divider
} from '@chakra-ui/react';
import { FiUser, FiUsers, FiBriefcase } from 'react-icons/fi';
import { ChevronDownIcon, DeleteIcon } from '@chakra-ui/icons';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';
import { checkAuthToken } from '../../utils/errorHandling';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

interface User {
  id: number;
  nom: string;
  prenom: string;
  email: string;
}

interface Organization {
  id: number;
  nom: string;
}

interface Role {
  id: number;
  nom: string;
}

interface Approbateur {
  type: 'utilisateur' | 'role' | 'organisation';
  id: number;
  nom: string;
  prenom?: string;
}

interface WorkflowEtape {
  id: number;
  nom: string;
  description: string;
  ordre: number;
  type_approbation: 'SIMPLE' | 'MULTIPLE' | 'PARALLELE';
  delai_max?: number;
  approbateurs?: Approbateur[];
}

interface WorkflowDetails {
  id: number;
  nom: string;
  description: string;
  etapes?: WorkflowEtape[];
}

interface EditWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowId: number | null;
  onWorkflowUpdated: () => void;
}

const IconWrapper: React.FC<{ icon: any; color?: string }> = ({ icon: IconComponent, color }) => (
  <IconComponent size={16} color={color || '#3a8bfd'} />
);

const EditWorkflowModal: React.FC<EditWorkflowModalProps> = ({
  isOpen,
  onClose,
  workflowId,
  onWorkflowUpdated
}) => {
  const [workflow, setWorkflow] = useState<WorkflowDetails | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  useEffect(() => {
    if (isOpen && workflowId) {
      loadWorkflowData();
      loadUsersAndOrganizations();
    }
  }, [isOpen, workflowId]);

  const loadWorkflowData = async () => {
    if (!workflowId) return;
    
    setIsLoading(true);
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        // Charger les détails du workflow
        const workflowResponse = await fetch(`${API_URL}/workflows/${workflowId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!workflowResponse.ok) {
          throw new Error('Impossible de charger le workflow');
        }
        
        const workflowData = await workflowResponse.json();
        
        // Charger les étapes avec leurs approbateurs
        const etapesResponse = await fetch(`${API_URL}/workflows/${workflowId}/etapes`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!etapesResponse.ok) {
          throw new Error('Impossible de charger les étapes');
        }
        
        const etapesData = await etapesResponse.json();
        
        setWorkflow({
          ...workflowData,
          etapes: etapesData
        });
      },
      {
        loadingMessage: "Chargement du workflow...",
        errorMessage: "Impossible de charger le workflow"
      }
    );
    setIsLoading(false);
  };

  const loadUsersAndOrganizations = async () => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        // Charger les utilisateurs
        const usersResponse = await fetch(`${API_URL}/users/for-approval`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (usersResponse.ok) {
          setUsers(await usersResponse.json());
        }

        // Charger les organisations
        const orgsResponse = await fetch(`${API_URL}/organizations`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (orgsResponse.ok) {
          setOrganizations(await orgsResponse.json());
        }

        // Charger les rôles
        const rolesResponse = await fetch(`${API_URL}/sharing/roles`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (rolesResponse.ok) {
          setRoles(await rolesResponse.json());
        }
      },
      {
        errorMessage: "Impossible de charger les données"
      }
    );
  };

  const updateEtapeApprobateurs = (etapeId: number, approbateurs: Approbateur[]) => {
    if (!workflow || !workflow.etapes) return;
    
    const updatedEtapes = workflow.etapes.map(etape => 
      etape.id === etapeId 
        ? { ...etape, approbateurs }
        : etape
    );
    
    setWorkflow({ ...workflow, etapes: updatedEtapes });
  };

  const addApprobateur = (etapeId: number, approbateur: Approbateur) => {
    if (!workflow) return;
    
    const etape = workflow.etapes?.find(e => e.id === etapeId);
    if (!etape) return;
    
    // Initialiser approbateurs si undefined
    const currentApprobateurs = etape.approbateurs || [];
    
    // Vérifier si l'approbateur n'est pas déjà ajouté
    const isAlreadyAdded = currentApprobateurs.some(
      a => a.type === approbateur.type && a.id === approbateur.id
    );
    
    if (!isAlreadyAdded) {
      const newApprobateurs = [...currentApprobateurs, approbateur];
      updateEtapeApprobateurs(etapeId, newApprobateurs);
    }
  };

  const removeApprobateur = (etapeId: number, approvateurIndex: number) => {
    if (!workflow) return;
    
    const etape = workflow.etapes?.find(e => e.id === etapeId);
    if (!etape || !etape.approbateurs) return;
    
    const newApprobateurs = etape.approbateurs.filter((_, index) => index !== approvateurIndex);
    updateEtapeApprobateurs(etapeId, newApprobateurs);
  };

  const handleSaveChanges = async () => {
    if (!workflow) return;
    
    setIsLoading(true);
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        
        toast({
          title: 'Succès',
          description: 'Les approbateurs ont été mis à jour avec succès',
          status: 'success',
          duration: 5000,
          isClosable: true
        });
        
        onWorkflowUpdated();
        handleClose();
      },
      {
        loadingMessage: "Sauvegarde en cours...",
        errorMessage: "Impossible de sauvegarder les modifications"
      }
    );
    setIsLoading(false);
  };

  const handleClose = () => {
    setWorkflow(null);
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
      case 'SIMPLE': return 'Simple';
      case 'MULTIPLE': return 'Multiple';
      case 'PARALLELE': return 'Parallèle';
      default: return type;
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="4xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent bg="#232946" color="white" maxH="90vh">
        <ModalHeader>Modifier le workflow: {workflow?.nom}</ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          {isLoading ? (
            <Box textAlign="center" py={6}>
              <Text>Chargement...</Text>
            </Box>
          ) : workflow ? (
            <VStack spacing={6} align="stretch">
              <Alert status="info" bg="#20243a" borderColor="#3a8bfd">
                <AlertIcon />
                Vous pouvez modifier les approbateurs de chaque étape du workflow.
              </Alert>
              
              {workflow.etapes?.map((etape, index) => (
                <Box key={etape.id} bg="#20243a" p={4} borderRadius="md" border="1px solid #3a8bfd">
                  <VStack align="stretch" spacing={4}>
                    <HStack justify="space-between">
                      <HStack>
                        <Badge colorScheme="blue">Étape {etape.ordre}</Badge>
                        <Text fontWeight="bold">{etape.nom}</Text>
                      </HStack>
                      <Badge colorScheme="purple">
                        {getTypeApproLabel(etape.type_approbation)}
                      </Badge>
                    </HStack>
                    
                    {etape.description && (
                      <Text fontSize="sm" color="gray.300">{etape.description}</Text>
                    )}
                    
                    <Divider />
                    
                    <Box>
                      <HStack justify="space-between" align="center" mb={3}>
                        <Text fontSize="sm" fontWeight="semibold">
                          Approbateurs ({etape.approbateurs?.length || 0})
                        </Text>
                        <Menu>
                          <MenuButton as={Button} size="xs" rightIcon={<ChevronDownIcon />}>
                            Ajouter
                          </MenuButton>
                          <MenuList bg="#232946" border="1px solid #3a8bfd">
                            {users.map(user => (
                              <MenuItem
                                key={`user-${user.id}`}
                                bg="#232946"
                                _hover={{ bg: "#20243a" }}
                                onClick={() => addApprobateur(etape.id, {
                                  type: 'utilisateur',
                                  id: user.id,
                                  nom: user.nom,
                                  prenom: user.prenom
                                })}
                              >
                                <HStack>
                                  <IconWrapper icon={FiUser} />
                                  <Text>{user.prenom} {user.nom}</Text>
                                </HStack>
                              </MenuItem>
                            ))}
                            {roles.map(role => (
                              <MenuItem
                                key={`role-${role.id}`}
                                bg="#232946"
                                _hover={{ bg: "#20243a" }}
                                onClick={() => addApprobateur(etape.id, {
                                  type: 'role',
                                  id: role.id,
                                  nom: role.nom
                                })}
                              >
                                <HStack>
                                  <IconWrapper icon={FiUsers} />
                                  <Text>{role.nom}</Text>
                                </HStack>
                              </MenuItem>
                            ))}
                            {organizations.map(org => (
                              <MenuItem
                                key={`org-${org.id}`}
                                bg="#232946"
                                _hover={{ bg: "#20243a" }}
                                onClick={() => addApprobateur(etape.id, {
                                  type: 'organisation',
                                  id: org.id,
                                  nom: org.nom
                                })}
                              >
                                <HStack>
                                  <IconWrapper icon={FiBriefcase} />
                                  <Text>{org.nom}</Text>
                                </HStack>
                              </MenuItem>
                            ))}
                          </MenuList>
                        </Menu>
                      </HStack>

                      <VStack spacing={2} align="stretch">
                        {etape.approbateurs?.map((approbateur, appIndex) => (
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
                              onClick={() => removeApprobateur(etape.id, appIndex)}
                              aria-label="Supprimer l'approbateur"
                            />
                          </HStack>
                        ))}
                        
                        {(!etape.approbateurs || etape.approbateurs.length === 0) && (
                          <Text fontSize="sm" color="gray.400" textAlign="center" py={2}>
                            Aucun approbateur défini
                          </Text>
                        )}
                      </VStack>
                    </Box>
                  </VStack>
                </Box>
              ))}
            </VStack>
          ) : (
            <Box textAlign="center" py={6}>
              <Text color="gray.400">Aucun workflow sélectionné</Text>
            </Box>
          )}
        </ModalBody>
        
        <ModalFooter>
          <HStack spacing={3}>
            <Button variant="ghost" onClick={handleClose}>
              Annuler
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSaveChanges}
              isLoading={isLoading}
              isDisabled={!workflow}
            >
              Sauvegarder les modifications
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default EditWorkflowModal; 