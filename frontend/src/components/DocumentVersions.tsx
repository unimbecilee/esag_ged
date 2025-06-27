import React, { useState, useEffect, ElementType } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Text,
  VStack,
  HStack,
  Button,
  Box,
  Badge,
  Divider,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  Tooltip,
  Alert,
  AlertIcon,
  Spinner,
  Center,
  Icon
} from '@chakra-ui/react';
import { FiClock, FiDownload, FiRotateCcw, FiUser, FiFileText } from 'react-icons/fi';
import config from '../config';
import { useAsyncOperation } from '../hooks/useAsyncOperation';

interface DocumentVersionsProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number | null;
  documentTitle: string;
}

interface Version {
  id: number;
  version_number: number;
  fichier: string;
  taille: number;
  mime_type: string;
  commentaire: string;
  created_at: string;
  created_by: number;
  created_by_name: string;
}

const DocumentVersions: React.FC<DocumentVersionsProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle
}) => {
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(false);
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const fetchVersions = async () => {
    if (!documentId) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/api/documents/${documentId}/versions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setVersions(data.versions || []);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Erreur lors du chargement des versions');
      }
    } catch (error) {
      console.error('Erreur versions:', error);
      toast({
        title: 'Erreur',
        description: error instanceof Error ? error.message : 'Impossible de charger les versions',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadVersion = async (versionNumber: number) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/documents/${documentId}/versions/${versionNumber}/download`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Erreur lors du téléchargement');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${documentTitle}_v${versionNumber}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    }, {
      loadingMessage: 'Téléchargement en cours...',
      successMessage: 'Version téléchargée avec succès',
      errorMessage: 'Erreur lors du téléchargement'
    });
  };

  const handleRestoreVersion = async (versionNumber: number) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/documents/${documentId}/versions/restore`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ version_number: versionNumber })
        }
      );

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de la restauration');
      }

      await fetchVersions(); // Recharger les versions
    }, {
      loadingMessage: 'Restauration en cours...',
      successMessage: 'Version restaurée avec succès',
      errorMessage: 'Erreur lors de la restauration'
    });
  };

  useEffect(() => {
    if (isOpen && documentId) {
      fetchVersions();
    }
  }, [isOpen, documentId]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="6xl">
      <ModalOverlay />
      <ModalContent bg="#2a3657" color="white" maxH="90vh">
        <ModalHeader>
          <HStack>
            <Icon as={FiClock as ElementType} />
            <Text>Versions de "{documentTitle}"</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody pb={6} overflow="auto">
          {loading ? (
            <Center py={10}>
              <VStack spacing={4}>
                <Spinner size="xl" color="blue.500" />
                <Text>Chargement des versions...</Text>
              </VStack>
            </Center>
          ) : versions.length === 0 ? (
            <Alert status="info" bg="#1a202c" color="white">
              <AlertIcon color="#3a8bfd" />
              <Text>Aucune version disponible pour ce document</Text>
            </Alert>
          ) : (
            <VStack spacing={4} align="stretch">
              <Box bg="#1a202c" p={4} borderRadius="md">
                <HStack justify="space-between">
                  <Text fontWeight="bold" fontSize="lg">
                    {versions.length} version{versions.length > 1 ? 's' : ''} disponible{versions.length > 1 ? 's' : ''}
                  </Text>
                  <Badge colorScheme="blue">
                    Version courante: {Math.max(...versions.map(v => v.version_number))}
                  </Badge>
                </HStack>
              </Box>

              <Box bg="#1a202c" borderRadius="md" overflow="hidden">
                <Table variant="simple" size="sm">
                  <Thead bg="#232946">
                    <Tr>
                      <Th color="white" fontSize="xs">Version</Th>
                      <Th color="white" fontSize="xs">Taille</Th>
                      <Th color="white" fontSize="xs">Créé par</Th>
                      <Th color="white" fontSize="xs">Date</Th>
                      <Th color="white" fontSize="xs">Commentaire</Th>
                      <Th color="white" fontSize="xs">Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {versions.map((version) => {
                      const isLatest = version.version_number === Math.max(...versions.map(v => v.version_number));
                      
                      return (
                        <Tr key={version.id} bg={isLatest ? "rgba(58, 139, 253, 0.1)" : "transparent"}>
                          <Td>
                            <HStack>
                              <Badge 
                                colorScheme={isLatest ? "green" : "gray"}
                                variant={isLatest ? "solid" : "outline"}
                              >
                                v{version.version_number}
                              </Badge>
                              {isLatest && (
                                <Badge colorScheme="green" size="sm">
                                  Courante
                                </Badge>
                              )}
                            </HStack>
                          </Td>
                          <Td>
                            <Text fontSize="sm">{formatFileSize(version.taille)}</Text>
                          </Td>
                          <Td>
                            <HStack>
                              <Icon as={FiUser as ElementType} size="sm" color="gray.400" />
                              <Text fontSize="sm">{version.created_by_name || 'Inconnu'}</Text>
                            </HStack>
                          </Td>
                          <Td>
                            <Text fontSize="sm">{formatDate(version.created_at)}</Text>
                          </Td>
                          <Td>
                            <Text fontSize="sm" noOfLines={2} maxW="200px">
                              {version.commentaire || 'Aucun commentaire'}
                            </Text>
                          </Td>
                          <Td>
                            <HStack spacing={1}>
                              <Tooltip label="Télécharger cette version">
                                <IconButton
                                  aria-label="Télécharger"
                                  icon={<Icon as={FiDownload as ElementType} />}
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleDownloadVersion(version.version_number)}
                                />
                              </Tooltip>
                              
                              {!isLatest && (
                                <Tooltip label="Restaurer cette version">
                                  <IconButton
                                    aria-label="Restaurer"
                                    icon={<Icon as={FiRotateCcw as ElementType} />}
                                    size="sm"
                                    variant="ghost"
                                    colorScheme="orange"
                                    onClick={() => handleRestoreVersion(version.version_number)}
                                  />
                                </Tooltip>
                              )}
                            </HStack>
                          </Td>
                        </Tr>
                      );
                    })}
                  </Tbody>
                </Table>
              </Box>

              <Box bg="#1a202c" p={4} borderRadius="md">
                <Text fontSize="sm" color="gray.300">
                  <strong>Note:</strong> La restauration d'une version antérieure créera une nouvelle version avec le contenu sélectionné.
                  Les versions précédentes seront conservées dans l'historique.
                </Text>
              </Box>
            </VStack>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default DocumentVersions; 


