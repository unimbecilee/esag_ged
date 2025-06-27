import React, { useState, useEffect } from 'react';
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Icon,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  SimpleGrid,
  Card,
  CardBody,
  Badge,
  Tooltip,
  useToast,
  useDisclosure,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Divider,
  Heading,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Center,
  Spinner
} from '@chakra-ui/react';
import {
  FiFolder,
  FiFile,
  FiFileText,
  FiImage,
  FiDownload,
  FiShare2,
  FiMoreVertical,
  FiSearch,
  FiHome,
  FiChevronRight,
  FiUpload,
  FiMove,
  FiEye,
  FiGrid,
  FiList
} from 'react-icons/fi';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';

const API_URL = config.API_URL;
import { asElementType } from '../utils/iconUtils';
import FileUploadModal from './FileUploadModal';
import CreateFolderModal from './CreateFolderModal';
import DocumentMoveModal from './DocumentMoveModal';
import ShareModal from './ShareModal';
import DocumentPreview from './Document/DocumentPreview';

interface Folder {
  id: number;
  titre: string;
  description?: string;
  parent_id: number | null;
  date_creation: string;
  documents_count: number;
  sous_dossiers_count: number;
}

interface Document {
  id: number;
  titre: string;
  type_document: string;
  date_creation: string;
  derniere_modification: string;
  taille: number;
  taille_formatee: string;
  dossier_id: number | null;
}

interface BreadcrumbItem {
  id: number;
  titre: string;
}

const FolderDocumentView: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  // États pour la navigation
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [breadcrumb, setBreadcrumb] = useState<BreadcrumbItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // États pour l'interface
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<number[]>([]);

  // États pour les modales
  const { isOpen: isUploadOpen, onOpen: onUploadOpen, onClose: onUploadClose } = useDisclosure();
  const { isOpen: isCreateFolderOpen, onOpen: onCreateFolderOpen, onClose: onCreateFolderClose } = useDisclosure();
  const { isOpen: isMoveOpen, onOpen: onMoveOpen, onClose: onMoveClose } = useDisclosure();
  const { isOpen: isShareOpen, onOpen: onShareOpen, onClose: onShareClose } = useDisclosure();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();

  // États pour les actions
  const [selectedDocument, setSelectedDocument] = useState<number | null>(null);
  const [previewDocumentId, setPreviewDocumentId] = useState<number | null>(null);
  const [previewDocumentTitle, setPreviewDocumentTitle] = useState<string>('');

  // Charger les données au changement de dossier
  useEffect(() => {
    loadFolderContent();
  }, [currentFolderId]);

  const loadFolderContent = async () => {
    setIsLoading(true);
    try {
      await Promise.all([
        loadFolders(),
        loadDocuments(),
        loadBreadcrumb()
      ]);
    } catch (error) {
      console.error('Erreur chargement contenu:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadFolders = async () => {
    try {
      const token = localStorage.getItem('token');
      const url = currentFolderId 
        ? `${API_URL}/api/folders/${currentFolderId}/children`
        : `${API_URL}/api/folders/?parent_id=`;
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setFolders(Array.isArray(data) ? data : data.data || []);
      }
    } catch (error) {
      console.error('Erreur chargement dossiers:', error);
    }
  };

  const loadDocuments = async () => {
    try {
      const token = localStorage.getItem('token');
      let url = `${API_URL}/api/documents/my`;
      if (currentFolderId !== null) {
        url += `?dossier_id=${currentFolderId}`;
      }

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      }
    } catch (error) {
      console.error('Erreur chargement documents:', error);
    }
  };

  const loadBreadcrumb = async () => {
    if (!currentFolderId) {
      setBreadcrumb([]);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/folders/${currentFolderId}/breadcrumb`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setBreadcrumb(data || []);
      }
    } catch (error) {
      console.error('Erreur breadcrumb:', error);
    }
  };

  const navigateToFolder = (folderId: number | null) => {
    setCurrentFolderId(folderId);
    setSelectedDocumentIds([]);
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
        return FiImage;
      case 'pdf':
      case 'doc':
      case 'docx':
      case 'txt':
        return FiFileText;
      default:
        return FiFile;
    }
  };

  const handleDocumentAction = (action: string, documentId: number, documentTitle?: string) => {
    setSelectedDocument(documentId);
    
    switch (action) {
      case 'preview':
        setPreviewDocumentId(documentId);
        setPreviewDocumentTitle(documentTitle || '');
        onPreviewOpen();
        break;
      case 'share':
        onShareOpen();
        break;
      case 'move':
        setSelectedDocumentIds([documentId]);
        onMoveOpen();
        break;
      case 'download':
        handleDownload(documentId);
        break;
    }
  };

  const handleDownload = async (documentId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/documents/${documentId}/download`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const doc = documents.find(d => d.id === documentId);
        a.download = doc ? doc.titre : `document-${documentId}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Erreur téléchargement:', error);
    }
  };

  const filteredFolders = folders.filter(folder =>
    folder.titre.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredDocuments = documents.filter(doc =>
    doc.titre.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box p={5} h="100vh">
      {/* En-tête */}
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          Explorateur de Documents
        </Heading>
        <HStack spacing={3}>
          <Button
            leftIcon={<Icon as={asElementType(FiUpload)} />}
            colorScheme="blue"
            onClick={onUploadOpen}
          >
            Upload
          </Button>
          <Button
            leftIcon={<Icon as={asElementType(FiFolder)} />}
            colorScheme="green"
            variant="outline"
            onClick={onCreateFolderOpen}
          >
            Nouveau dossier
          </Button>
        </HStack>
      </Flex>

      {/* Breadcrumb et contrôles */}
      <Flex justify="space-between" align="center" mb={4}>
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

        <InputGroup maxW="300px">
          <InputLeftElement>
            <Icon as={asElementType(FiSearch)} color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Rechercher..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            bg="#2a3657"
            borderColor="#3a445e"
            _focus={{ borderColor: "#3a8bfd" }}
          />
        </InputGroup>
      </Flex>

      {/* Contenu principal */}
      {isLoading ? (
        <Center h="300px">
          <Spinner size="lg" color="#3a8bfd" />
        </Center>
      ) : (
        <Box>
          {/* Dossiers */}
          {filteredFolders.length > 0 && (
            <Box mb={6}>
              <Text fontWeight="bold" mb={3} color="white" fontSize="lg">
                Dossiers ({filteredFolders.length})
              </Text>
              <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={4}>
                {filteredFolders.map((folder) => (
                  <Card
                    key={folder.id}
                    bg="#2a3657"
                    borderColor="#3a445e"
                    cursor="pointer"
                    onClick={() => navigateToFolder(folder.id)}
                    _hover={{ 
                      borderColor: "#3a8bfd", 
                      transform: "translateY(-2px)",
                      boxShadow: "0 4px 12px rgba(58, 139, 253, 0.3)"
                    }}
                    transition="all 0.2s"
                  >
                    <CardBody textAlign="center" py={4}>
                      <VStack spacing={2}>
                        <Icon as={asElementType(FiFolder)} boxSize={8} color="#3a8bfd" />
                        <Text 
                          fontWeight="medium" 
                          noOfLines={1} 
                          color="white"
                          fontSize="sm"
                        >
                          {folder.titre}
                        </Text>
                        <HStack spacing={1}>
                          <Badge size="xs" colorScheme="blue">
                            {folder.documents_count} doc(s)
                          </Badge>
                          <Badge size="xs" colorScheme="gray">
                            {folder.sous_dossiers_count} dossier(s)
                          </Badge>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            </Box>
          )}

          {/* Divider si les deux sections sont présentes */}
          {filteredFolders.length > 0 && filteredDocuments.length > 0 && (
            <Divider borderColor="#3a445e" mb={6} />
          )}

          {/* Documents */}
          {filteredDocuments.length > 0 ? (
            <Box>
              <Text fontWeight="bold" mb={3} color="white" fontSize="lg">
                Documents ({filteredDocuments.length})
              </Text>
              <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={4}>
                {filteredDocuments.map((doc) => (
                  <Card
                    key={doc.id}
                    bg="#2a3657"
                    borderColor="#3a445e"
                    _hover={{ 
                      borderColor: "#3a8bfd",
                      transform: "translateY(-2px)",
                      boxShadow: "0 4px 12px rgba(58, 139, 253, 0.3)"
                    }}
                    transition="all 0.2s"
                  >
                    <CardBody py={4}>
                      <VStack spacing={2}>
                        <Box position="relative" w="100%">
                          <Icon 
                            as={asElementType(getFileIcon(doc.titre))} 
                            boxSize={8} 
                            color="#3a8bfd" 
                          />
                          <Menu>
                            <MenuButton
                              as={IconButton}
                              icon={<Icon as={asElementType(FiMoreVertical)} />}
                              variant="ghost"
                              size="xs"
                              position="absolute"
                              top="-8px"
                              right="-8px"
                              aria-label="Options"
                            />
                            <MenuList bg="#1c2338" borderColor="#3a445e">
                              <MenuItem
                                icon={<Icon as={asElementType(FiEye)} />}
                                onClick={() => handleDocumentAction('preview', doc.id, doc.titre)}
                                _hover={{ bg: "#2d3250" }}
                              >
                                Aperçu
                              </MenuItem>
                              <MenuItem
                                icon={<Icon as={asElementType(FiDownload)} />}
                                onClick={() => handleDocumentAction('download', doc.id)}
                                _hover={{ bg: "#2d3250" }}
                              >
                                Télécharger
                              </MenuItem>
                              <MenuItem
                                icon={<Icon as={asElementType(FiShare2)} />}
                                onClick={() => handleDocumentAction('share', doc.id)}
                                _hover={{ bg: "#2d3250" }}
                              >
                                Partager
                              </MenuItem>
                              {/* Option Déplacer désactivée temporairement
                              <MenuItem
                                icon={<Icon as={asElementType(FiMove)} />}
                                onClick={() => handleDocumentAction('move', doc.id, doc.titre)}
                                _hover={{ bg: "#2d3250" }}
                              >
                                Déplacer
                              </MenuItem>
                              */}
                            </MenuList>
                          </Menu>
                        </Box>
                        
                        <Tooltip label={doc.titre} hasArrow>
                          <Text 
                            fontWeight="medium" 
                            noOfLines={2} 
                            color="white"
                            fontSize="sm"
                            textAlign="center"
                            minH="32px"
                          >
                            {doc.titre}
                          </Text>
                        </Tooltip>
                        
                        <VStack spacing={1}>
                          <Badge size="xs" colorScheme="blue">
                            {doc.type_document || 'Unknown'}
                          </Badge>
                          <Text fontSize="xs" color="gray.400">
                            {doc.taille_formatee}
                          </Text>
                        </VStack>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            </Box>
          ) : filteredFolders.length === 0 && (
            <Center h="200px">
              <VStack spacing={3}>
                <Icon as={asElementType(FiFolder)} boxSize={12} color="gray.400" />
                <Text color="gray.400" fontSize="lg">
                  Ce dossier est vide
                </Text>
                <Button
                  leftIcon={<Icon as={asElementType(FiUpload)} />}
                  colorScheme="blue"
                  variant="outline"
                  onClick={onUploadOpen}
                >
                  Ajouter des documents
                </Button>
              </VStack>
            </Center>
          )}
        </Box>
      )}

      {/* Modales */}
      <FileUploadModal
        isOpen={isUploadOpen}
        onClose={onUploadClose}
        onUploadSuccess={loadFolderContent}
        currentFolderId={currentFolderId}
      />

      <CreateFolderModal
        isOpen={isCreateFolderOpen}
        onClose={onCreateFolderClose}
        onSuccess={loadFolderContent}
        parentFolderId={currentFolderId}
      />

      <DocumentMoveModal
        isOpen={isMoveOpen}
        onClose={onMoveClose}
        onSuccess={loadFolderContent}
        documentIds={selectedDocumentIds}
        documentTitles={selectedDocumentIds.map(id => {
          const doc = documents.find(d => d.id === id);
          return doc ? doc.titre : '';
        })}
      />

      <ShareModal
        open={isShareOpen}
        onClose={onShareClose}
        documentId={selectedDocument || 0}
        documentTitle={documents.find(d => d.id === selectedDocument)?.titre || "Document"}
        onShareSuccess={loadFolderContent}
      />

      {previewDocumentId && (
        <DocumentPreview
          isOpen={isPreviewOpen}
          onClose={() => {
            onPreviewClose();
            setPreviewDocumentId(null);
          }}
          documentId={previewDocumentId}
          documentTitle={previewDocumentTitle}
        />
      )}
    </Box>
  );
};

export default FolderDocumentView; 


