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
  VStack,
  HStack,
  Box,
  Text,
  Icon,
  useToast,
  Input,
  InputGroup,
  InputLeftElement,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Flex,
  Badge,
  Card,
  CardBody,
  Alert,
  AlertIcon,
  AlertDescription,
  Spinner,
  Center
} from '@chakra-ui/react';
import {
  FiFolder,
  FiSearch,
  FiHome,
  FiChevronRight,
  FiMove,
  FiFile,
  FiCheck
} from 'react-icons/fi';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';
import { asElementType } from '../utils/iconUtils';

const API_URL = config.API_URL;

interface DocumentMoveModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  documentIds: number[];
  documentTitles: string[];
}

interface Folder {
  id: number;
  titre: string;
  parent_id: number | null;
  date_creation: string;
  documents_count: number;
  sous_dossiers_count: number;
}

interface BreadcrumbItem {
  id: number;
  titre: string;
}

const DocumentMoveModal: React.FC<DocumentMoveModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  documentIds,
  documentTitles
}) => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  
  const [folders, setFolders] = useState<Folder[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);
  const [breadcrumb, setBreadcrumb] = useState<BreadcrumbItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isMoving, setIsMoving] = useState(false);

  // Charger les dossiers au niveau courant
  const loadFolders = async (folderId: number | null = null) => {
    setIsLoading(true);
    try {
      console.log(`Chargement des dossiers pour folderId=${folderId}`);
      const token = localStorage.getItem('token');
      const url = folderId 
        ? `${API_URL}/folders/${folderId}/children`
        : `${API_URL}/folders/`;
      
      console.log(`URL de l'API: ${url}`);
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      console.log(`Statut de la réponse: ${response.status}`);
      
      // Vérifier le type de contenu
      const contentType = response.headers.get("content-type");
      console.log(`Type de contenu: ${contentType}`);
      
      if (response.ok) {
        if (contentType && contentType.includes("application/json")) {
          const data = await response.json();
          console.log('Données reçues:', data);
          
          // Vérifier si data.data existe (format de réponse pour /children) ou utiliser data directement
          const folderData = data.data || data;
          console.log(`Nombre de dossiers trouvés: ${folderData.length}`);
          
          setFolders(folderData);
        } else {
          const text = await response.text();
          console.error('Réponse non-JSON reçue:', text.substring(0, 100));
          toast({
            title: 'Erreur',
            description: 'Format de réponse incorrect',
            status: 'error',
            duration: 3000,
            isClosable: true
          });
        }
      } else {
        try {
          const contentType = response.headers.get("content-type");
          if (contentType && contentType.includes("application/json")) {
            const errorData = await response.json();
            console.error('Erreur lors du chargement des dossiers:', errorData);
            toast({
              title: 'Erreur',
              description: errorData.message || 'Impossible de charger les dossiers',
              status: 'error',
              duration: 3000,
              isClosable: true
            });
          } else {
            const errorText = await response.text();
            console.error('Erreur lors du chargement des dossiers (texte):', errorText.substring(0, 100));
            toast({
              title: 'Erreur',
              description: 'Impossible de charger les dossiers',
              status: 'error',
              duration: 3000,
              isClosable: true
            });
          }
        } catch (parseError) {
          console.error('Erreur lors du parsing de la réponse:', parseError);
        }
      }
    } catch (error) {
      console.error('Erreur chargement dossiers:', error);
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les dossiers',
        status: 'error',
        duration: 3000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Construire le fil d'Ariane
  const buildBreadcrumb = async (folderId: number | null) => {
    if (!folderId) {
      setBreadcrumb([]);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/folders/${folderId}/breadcrumb`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Breadcrumb reçu:', data);
        setBreadcrumb(data.breadcrumb || []);
      }
    } catch (error) {
      console.error('Erreur breadcrumb:', error);
    }
  };

  // Navigation vers un dossier
  const navigateToFolder = async (folderId: number | null) => {
    console.log(`Navigation vers le dossier: ${folderId}`);
    setCurrentFolderId(folderId);
    await Promise.all([
      loadFolders(folderId),
      buildBreadcrumb(folderId)
    ]);
  };

  // Initialisation
  useEffect(() => {
    if (isOpen) {
      console.log('Modal ouvert, chargement des dossiers racine');
      navigateToFolder(null);
      setSelectedFolderId(null);
      setSearchQuery('');
    }
  }, [isOpen]);

  // Filtrage des dossiers par recherche
  const filteredFolders = folders.filter(folder =>
    folder.titre.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Déplacer les documents
  const handleMoveDocuments = async () => {
    if (documentIds.length === 0) return;

    setIsMoving(true);
    try {
      if (documentIds.length === 1) {
        // Déplacement simple
        await executeOperation(
          async () => {
            const token = localStorage.getItem('token');
            console.log(`Déplacement du document ${documentIds[0]} vers le dossier ${selectedFolderId}`);
            const response = await fetch(`${API_URL}/documents/${documentIds[0]}/move`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                target_folder_id: selectedFolderId
              })
            });

            console.log(`Statut de la réponse de déplacement: ${response.status}`);
            const contentType = response.headers.get("content-type");
            console.log(`Type de contenu de la réponse: ${contentType}`);

            if (!response.ok) {
              try {
                if (contentType && contentType.includes("application/json")) {
                  const error = await response.json();
                  console.error('Erreur JSON:', error);
                  throw new Error(error.message || 'Erreur lors du déplacement');
                } else {
                  const errorText = await response.text();
                  console.error('Erreur texte:', errorText.substring(0, 200));
                  throw new Error(`Erreur lors du déplacement: ${errorText.substring(0, 100)}...`);
                }
              } catch (parseError) {
                console.error('Erreur lors du parsing de la réponse d\'erreur:', parseError);
                throw new Error('Erreur lors du déplacement: impossible de lire la réponse');
              }
            }

            try {
              return await response.json();
            } catch (jsonError) {
              console.error('Erreur lors du parsing de la réponse JSON:', jsonError);
              const text = await response.text();
              console.log('Réponse texte:', text.substring(0, 200));
              return { success: true, message: 'Opération réussie' };
            }
          },
          {
            loadingMessage: 'Déplacement en cours...',
            successMessage: `Document "${documentTitles[0]}" déplacé avec succès`,
            errorMessage: 'Erreur lors du déplacement'
          }
        );
      } else {
        // Déplacement en lot
        await executeOperation(
          async () => {
            const token = localStorage.getItem('token');
            console.log(`Déplacement en lot de ${documentIds.length} documents vers le dossier ${selectedFolderId}`);
            const response = await fetch(`${API_URL}/documents/bulk-move`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                document_ids: documentIds,
                target_folder_id: selectedFolderId
              })
            });

            console.log(`Statut de la réponse de déplacement en lot: ${response.status}`);
            const contentType = response.headers.get("content-type");
            console.log(`Type de contenu de la réponse en lot: ${contentType}`);

            if (!response.ok) {
              try {
                if (contentType && contentType.includes("application/json")) {
                  const error = await response.json();
                  console.error('Erreur JSON en lot:', error);
                  throw new Error(error.message || 'Erreur lors du déplacement');
                } else {
                  const errorText = await response.text();
                  console.error('Erreur texte en lot:', errorText.substring(0, 200));
                  throw new Error(`Erreur lors du déplacement: ${errorText.substring(0, 100)}...`);
                }
              } catch (parseError) {
                console.error('Erreur lors du parsing de la réponse d\'erreur en lot:', parseError);
                throw new Error('Erreur lors du déplacement: impossible de lire la réponse');
              }
            }

            try {
              return await response.json();
            } catch (jsonError) {
              console.error('Erreur lors du parsing de la réponse JSON en lot:', jsonError);
              const text = await response.text();
              console.log('Réponse texte en lot:', text.substring(0, 200));
              return { success: true, message: 'Opération réussie' };
            }
          },
          {
            loadingMessage: 'Déplacement en cours...',
            successMessage: `${documentIds.length} document(s) déplacé(s) avec succès`,
            errorMessage: 'Erreur lors du déplacement'
          }
        );
      }

      onSuccess();
      onClose();
    } catch (error) {
      console.error('Erreur déplacement:', error);
    } finally {
      setIsMoving(false);
    }
  };

  const getFolderDestinationText = () => {
    if (selectedFolderId === null) {
      return "Racine (aucun dossier)";
    }
    
    const selectedFolder = folders.find(f => f.id === selectedFolderId);
    return selectedFolder ? selectedFolder.titre : "Dossier sélectionné";
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent bg="#20243a" color="white">
        <ModalHeader>
          <HStack>
            <Icon as={asElementType(FiMove)} color="#3a8bfd" />
            <Text>Déplacer les documents</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <VStack spacing={4} align="stretch">
            {/* Informations sur les documents à déplacer */}
            <Alert status="info" bg="#232946" borderColor="#3a8bfd">
              <AlertIcon color="#3a8bfd" />
              <AlertDescription>
                {documentIds.length === 1 
                  ? `Déplacement du document : "${documentTitles[0]}"`
                  : `Déplacement de ${documentIds.length} documents sélectionnés`
                }
              </AlertDescription>
            </Alert>

            {/* Barre de recherche */}
            <InputGroup>
              <InputLeftElement>
                <Icon as={asElementType(FiSearch)} color="gray.400" />
              </InputLeftElement>
              <Input
                placeholder="Rechercher un dossier..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                bg="#232946"
                borderColor="#232946"
                _focus={{ borderColor: "#3a8bfd", boxShadow: "0 0 0 1.5px #3a8bfd" }}
              />
            </InputGroup>

            {/* Fil d'Ariane */}
            <Box>
              <Breadcrumb 
                spacing="8px" 
                separator={<Icon as={asElementType(FiChevronRight)} color="gray.400" />}
              >
                <BreadcrumbItem>
                  <BreadcrumbLink
                    onClick={() => navigateToFolder(null)}
                    color={currentFolderId === null ? "#3a8bfd" : "gray.400"}
                    _hover={{ color: "#3a8bfd" }}
                  >
                    <HStack spacing={1}>
                      <Icon as={asElementType(FiHome)} />
                      <Text>Racine</Text>
                    </HStack>
                  </BreadcrumbLink>
                </BreadcrumbItem>
                
                {breadcrumb.map((item, index) => (
                  <BreadcrumbItem key={item.id}>
                    <BreadcrumbLink
                      onClick={() => navigateToFolder(item.id)}
                      color={index === breadcrumb.length - 1 ? "#3a8bfd" : "gray.400"}
                      _hover={{ color: "#3a8bfd" }}
                    >
                      {item.titre}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                ))}
              </Breadcrumb>
            </Box>

            {/* Option "Racine" */}
            <Card
              bg={selectedFolderId === null ? "#3a8bfd" : "#232946"}
              borderColor={selectedFolderId === null ? "#3a8bfd" : "#232946"}
              cursor="pointer"
              onClick={() => setSelectedFolderId(null)}
              _hover={{ borderColor: "#3a8bfd" }}
              transition="all 0.2s"
            >
              <CardBody py={3}>
                <HStack justify="space-between">
                  <HStack>
                    <Icon as={asElementType(FiHome)} color="#3a8bfd" />
                    <Text fontWeight="medium">Racine (aucun dossier)</Text>
                  </HStack>
                  {selectedFolderId === null && (
                    <Icon as={asElementType(FiCheck)} color="white" />
                  )}
                </HStack>
              </CardBody>
            </Card>

            {/* Liste des dossiers */}
            <Box maxH="300px" overflowY="auto">
              {isLoading ? (
                <Center py={8}>
                  <Spinner color="#3a8bfd" />
                </Center>
              ) : filteredFolders.length === 0 ? (
                <Text color="gray.400" textAlign="center" py={4}>
                  {searchQuery ? 'Aucun dossier trouvé' : 'Aucun sous-dossier'}
                </Text>
              ) : (
                <VStack spacing={2} align="stretch">
                  {filteredFolders.map((folder) => (
                    <Card
                      key={folder.id}
                      bg={selectedFolderId === folder.id ? "#3a8bfd" : "#232946"}
                      borderColor={selectedFolderId === folder.id ? "#3a8bfd" : "#232946"}
                      cursor="pointer"
                      _hover={{ borderColor: "#3a8bfd" }}
                      transition="all 0.2s"
                    >
                      <CardBody py={3}>
                        <HStack justify="space-between">
                          <HStack
                            onClick={() => setSelectedFolderId(folder.id)}
                            flex={1}
                          >
                            <Icon as={asElementType(FiFolder)} color="#3a8bfd" />
                            <VStack align="start" spacing={0} flex={1}>
                              <Text fontWeight="medium" noOfLines={1}>
                                {folder.titre}
                              </Text>
                              <HStack spacing={2}>
                                <Badge size="sm" colorScheme="blue">
                                  {folder.documents_count} doc(s)
                                </Badge>
                                <Badge size="sm" colorScheme="gray">
                                  {folder.sous_dossiers_count} sous-dossier(s)
                                </Badge>
                              </HStack>
                            </VStack>
                          </HStack>
                          
                          <HStack spacing={2}>
                            {selectedFolderId === folder.id && (
                              <Icon as={asElementType(FiCheck)} color="white" />
                            )}
                            {folder.sous_dossiers_count > 0 && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => navigateToFolder(folder.id)}
                                _hover={{ bg: "rgba(255,255,255,0.1)" }}
                              >
                                <Icon as={asElementType(FiChevronRight)} />
                              </Button>
                            )}
                          </HStack>
                        </HStack>
                      </CardBody>
                    </Card>
                  ))}
                </VStack>
              )}
            </Box>

            {/* Destination sélectionnée */}
            <Alert status="success" bg="#232946" borderColor="#28a745">
              <AlertIcon color="#28a745" />
              <AlertDescription>
                <Text>
                  <strong>Destination :</strong> {getFolderDestinationText()}
                </Text>
              </AlertDescription>
            </Alert>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <HStack spacing={3}>
            <Button variant="ghost" onClick={onClose} isDisabled={isMoving}>
              Annuler
            </Button>
            {/* Bouton Déplacer désactivé temporairement
            <Button
              colorScheme="blue"
              onClick={handleMoveDocuments}
              isLoading={isMoving}
              loadingText="Déplacement..."
              leftIcon={<Icon as={asElementType(FiMove)} />}
            >
              Déplacer {documentIds.length > 1 ? `(${documentIds.length})` : ''}
            </Button>
            */}
            <Button
              colorScheme="gray"
              disabled
              leftIcon={<Icon as={asElementType(FiMove)} />}
            >
              Fonctionnalité temporairement indisponible
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default DocumentMoveModal; 