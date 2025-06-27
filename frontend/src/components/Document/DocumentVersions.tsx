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
  Box,
  Text,
  Flex,
  Badge,
  IconButton,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Icon,
  Divider,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { 
  FiDownload, 
  FiRotateCcw, 
  FiMoreVertical, 
  FiEye, 
  FiClock,
  FiUser,
  FiFileText
} from 'react-icons/fi';
import { asElementType } from '../../utils/iconUtils';
import config from '../../config';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';

interface Version {
  id: number;
  version_number: number;
  fichier: string;
  taille: number;
  mime_type: string;
  commentaire: string;
  created_at: string;
  created_by: number;
  user_nom: string;
  user_prenom: string;
}

interface DocumentVersionsProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number;
  documentTitle: string;
  onVersionRestored?: () => void;
}

const DocumentVersions: React.FC<DocumentVersionsProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  onVersionRestored
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
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/versions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setVersions(data.versions || []);
      } else {
        throw new Error('Erreur lors du chargement des versions');
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les versions',
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
        `${config.API_URL}/documents/${documentId}/versions/${versionNumber}/download`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.ok) {
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
      } else {
        throw new Error('Erreur lors du téléchargement');
      }
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
        `${config.API_URL}/documents/${documentId}/versions/restore`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ version_number: versionNumber })
        }
      );

      if (response.ok) {
        fetchVersions(); // Recharger les versions
        onVersionRestored && onVersionRestored();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de la restauration');
      }
    }, {
      loadingMessage: 'Restauration en cours...',
      successMessage: 'Version restaurée avec succès',
      errorMessage: 'Erreur lors de la restauration'
    });
  };

  useEffect(() => {
    if (isOpen) {
      fetchVersions();
    }
  }, [isOpen, documentId]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="6xl">
      <ModalOverlay bg="blackAlpha.700" />
      <ModalContent bg="#20243a" color="white" maxH="90vh">
        <ModalHeader>
          <Flex align="center" gap={3}>
            <Icon as={asElementType(FiFileText)} color="#3a8bfd" />
            <Text>Versions de "{documentTitle}"</Text>
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody overflowY="auto">
          {loading ? (
            <Box textAlign="center" py={8}>
              <Text>Chargement des versions...</Text>
            </Box>
          ) : versions.length === 0 ? (
            <Alert status="info" bg="#2a3657" color="white">
              <AlertIcon color="#3a8bfd" />
              Aucune version disponible pour ce document
            </Alert>
          ) : (
            <Box>
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th color="white">Version</Th>
                    <Th color="white">Date de création</Th>
                    <Th color="white">Créé par</Th>
                    <Th color="white">Taille</Th>
                    <Th color="white">Commentaire</Th>
                    <Th color="white">Actions</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {versions.map((version, index) => (
                    <Tr key={version.id}>
                      <Td>
                        <Flex align="center" gap={2}>
                          <Badge 
                            colorScheme={index === 0 ? "green" : "blue"}
                            px={2}
                            py={1}
                          >
                            v{version.version_number}
                          </Badge>
                          {index === 0 && (
                            <Badge colorScheme="green" variant="outline" fontSize="xs">
                              Actuelle
                            </Badge>
                          )}
                        </Flex>
                      </Td>
                      <Td>
                        <Flex align="center" gap={2}>
                          <Icon as={asElementType(FiClock)} color="gray.400" />
                          <Text fontSize="sm">{formatDate(version.created_at)}</Text>
                        </Flex>
                      </Td>
                      <Td>
                        <Flex align="center" gap={2}>
                          <Icon as={asElementType(FiUser)} color="gray.400" />
                          <Text fontSize="sm">
                            {version.user_prenom} {version.user_nom}
                          </Text>
                        </Flex>
                      </Td>
                      <Td>
                        <Text fontSize="sm">{formatFileSize(version.taille)}</Text>
                      </Td>
                      <Td>
                        <Text fontSize="sm" noOfLines={2} maxW="200px">
                          {version.commentaire || 'Aucun commentaire'}
                        </Text>
                      </Td>
                      <Td>
                        <Menu>
                          <MenuButton
                            as={IconButton}
                            icon={<Icon as={asElementType(FiMoreVertical)} />}
                            variant="ghost"
                            size="sm"
                          />
                          <MenuList bg="#2a3657" borderColor="#3a445e">
                            <MenuItem
                              icon={<Icon as={asElementType(FiDownload)} />}
                              onClick={() => handleDownloadVersion(version.version_number)}
                              _hover={{ bg: "#363b5a" }}
                            >
                              Télécharger
                            </MenuItem>
                            <MenuItem
                              icon={<Icon as={asElementType(FiEye)} />}
                              onClick={() => {
                                // TODO: Prévisualiser la version
                                toast({
                                  title: 'Fonctionnalité à venir',
                                  description: 'La prévisualisation sera bientôt disponible',
                                  status: 'info',
                                  duration: 3000,
                                  isClosable: true,
                                });
                              }}
                              _hover={{ bg: "#363b5a" }}
                            >
                              Prévisualiser
                            </MenuItem>
                            {index !== 0 && (
                              <>
                                <Divider />
                                <MenuItem
                                  icon={<Icon as={asElementType(FiRotateCcw)} />}
                                  onClick={() => handleRestoreVersion(version.version_number)}
                                  _hover={{ bg: "#363b5a" }}
                                  color="orange.300"
                                >
                                  Restaurer cette version
                                </MenuItem>
                              </>
                            )}
                          </MenuList>
                        </Menu>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          )}
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" onClick={onClose}>
            Fermer
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default DocumentVersions; 

