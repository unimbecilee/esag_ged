import React, { useState, useRef, useCallback } from 'react';
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
  VStack,
  HStack,
  Box,
  Text,
  Icon,
  useToast,
  Divider,
  Badge,
  Alert,
  AlertIcon,
  AlertDescription,
  Progress,
  Flex,
  SimpleGrid,
  Card,
  CardBody,
  IconButton,
  Tooltip
} from '@chakra-ui/react';
import {
  FiFolder,
  FiUpload,
  FiX,
  FiFile,
  FiImage,
  FiFileText,
  FiFilePlus,
  FiTrash2
} from 'react-icons/fi';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';
import { asElementType } from '../utils/iconUtils';

const API_URL = config.API_URL;

interface CreateFolderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  parentFolderId?: number | null;
}

interface FileToUpload {
  id: string;
  file: File;
  title: string;
  description: string;
  progress: number;
  uploaded: boolean;
  error?: string;
}

const CreateFolderModal: React.FC<CreateFolderModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  parentFolderId = null
}) => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [folderName, setFolderName] = useState('');
  const [folderDescription, setFolderDescription] = useState('');
  const [filesToUpload, setFilesToUpload] = useState<FileToUpload[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [uploadMode, setUploadMode] = useState<'none' | 'files'>('none');

  const resetForm = () => {
    setFolderName('');
    setFolderDescription('');
    setFilesToUpload([]);
    setUploadMode('none');
  };

  const handleClose = () => {
    if (!isCreating) {
      resetForm();
      onClose();
    }
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

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    
    const newFiles: FileToUpload[] = files.map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      title: file.name.split('.').slice(0, -1).join('.') || file.name,
      description: '',
      progress: 0,
      uploaded: false
    }));

    setFilesToUpload(prev => [...prev, ...newFiles]);
    
    // Reset l'input pour permettre de sélectionner les mêmes fichiers
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileRemove = (fileId: string) => {
    setFilesToUpload(prev => prev.filter(f => f.id !== fileId));
  };

  const updateFileData = (fileId: string, updates: Partial<FileToUpload>) => {
    setFilesToUpload(prev => 
      prev.map(f => f.id === fileId ? { ...f, ...updates } : f)
    );
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files);
    const newFiles: FileToUpload[] = files.map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      file,
      title: file.name.split('.').slice(0, -1).join('.') || file.name,
      description: '',
      progress: 0,
      uploaded: false
    }));

    setFilesToUpload(prev => [...prev, ...newFiles]);
  }, []);

  const uploadFileToFolder = async (fileData: FileToUpload, folderId: number): Promise<boolean> => {
    try {
      const formData = new FormData();
      formData.append('file', fileData.file);
      formData.append('titre', fileData.title);
      formData.append('description', fileData.description);
      formData.append('dossier_id', folderId.toString());

      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Erreur lors de l\'upload');
      }

      return true;
    } catch (error) {
      console.error('Erreur upload fichier:', error);
      updateFileData(fileData.id, { 
        error: error instanceof Error ? error.message : 'Erreur inconnue' 
      });
      return false;
    }
  };

  const handleCreateFolderWithFiles = async () => {
    if (!folderName.trim()) {
      toast({
        title: 'Erreur',
        description: 'Le nom du dossier est requis',
        status: 'error',
        duration: 3000,
        isClosable: true
      });
      return;
    }

    setIsCreating(true);

    try {
      // 1. Créer le dossier
      const folderId = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          const response = await fetch(`${API_URL}/api/folders/`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              titre: folderName,
              description: folderDescription,
              parent_id: parentFolderId
            })
          });

          if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Erreur lors de la création du dossier');
          }

          const data = await response.json();
          return data.data.folder_id;
        },
        {
          loadingMessage: 'Création du dossier...',
          successMessage: 'Dossier créé avec succès',
          errorMessage: 'Impossible de créer le dossier'
        }
      );

      // 2. Uploader les fichiers s'il y en a
      if (filesToUpload.length > 0 && folderId) {
        let uploadedCount = 0;
        
        for (let i = 0; i < filesToUpload.length; i++) {
          const fileData = filesToUpload[i];
          updateFileData(fileData.id, { progress: 0 });
          
          // Simuler le progrès
          const progressInterval = setInterval(() => {
            updateFileData(fileData.id, { 
              progress: Math.min(fileData.progress + 10, 90) 
            });
          }, 100);

          const success = await uploadFileToFolder(fileData, folderId);
          
          clearInterval(progressInterval);
          
          if (success) {
            updateFileData(fileData.id, { progress: 100, uploaded: true });
            uploadedCount++;
          } else {
            updateFileData(fileData.id, { progress: 0 });
          }
        }

        if (uploadedCount > 0) {
          toast({
            title: 'Succès',
            description: `Dossier créé avec ${uploadedCount} fichier(s) uploadé(s)`,
            status: 'success',
            duration: 5000,
            isClosable: true
          });
        }
      }

      // 3. Fermer la modal et rafraîchir
      onSuccess();
      handleClose();

    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <>
      <Modal isOpen={isOpen} onClose={handleClose} size="xl">
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white" maxW="800px">
          <ModalHeader>
            <HStack>
              <Icon as={asElementType(FiFolder)} color="#3a8bfd" />
              <Text>Créer un nouveau dossier</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton isDisabled={isCreating} />
          
          <ModalBody>
            <VStack spacing={6} align="stretch">
              {/* Informations du dossier */}
              <Box>
                <FormControl isRequired>
                  <FormLabel>Nom du dossier</FormLabel>
                  <Input
                    value={folderName}
                    onChange={(e) => setFolderName(e.target.value)}
                    placeholder="Nom du dossier..."
                    bg="#232946"
                    borderColor="#232946"
                    _focus={{ borderColor: "#3a8bfd", boxShadow: "0 0 0 1.5px #3a8bfd" }}
                    isDisabled={isCreating}
                  />
                </FormControl>

                <FormControl mt={4}>
                  <FormLabel>Description (optionnel)</FormLabel>
                  <Textarea
                    value={folderDescription}
                    onChange={(e) => setFolderDescription(e.target.value)}
                    placeholder="Description du dossier..."
                    bg="#232946"
                    borderColor="#232946"
                    _focus={{ borderColor: "#3a8bfd", boxShadow: "0 0 0 1.5px #3a8bfd" }}
                    isDisabled={isCreating}
                    rows={3}
                  />
                </FormControl>
              </Box>

              <Divider borderColor="#3a8bfd" />

              {/* Section upload de fichiers */}
              <Box>
                <HStack justify="space-between" mb={4}>
                  <Text fontWeight="bold" fontSize="lg">
                    Fichiers à ajouter (optionnel)
                  </Text>
                  <HStack>
                    {uploadMode === 'none' ? (
                      <Button
                        size="sm"
                        leftIcon={<Icon as={asElementType(FiFilePlus)} />}
                        colorScheme="blue"
                        variant="outline"
                        onClick={() => setUploadMode('files')}
                        isDisabled={isCreating}
                      >
                        Ajouter des fichiers
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        leftIcon={<Icon as={asElementType(FiX)} />}
                        variant="ghost"
                        onClick={() => {
                          setUploadMode('none');
                          setFilesToUpload([]);
                        }}
                        isDisabled={isCreating}
                      >
                        Annuler
                      </Button>
                    )}
                  </HStack>
                </HStack>

                {uploadMode === 'files' && (
                  <VStack spacing={4} align="stretch">
                    {/* Zone de drop */}
                    <Box
                      border="2px dashed #3a8bfd"
                      borderRadius="lg"
                      p={8}
                      textAlign="center"
                      cursor="pointer"
                      _hover={{ bg: "#232946" }}
                      onClick={() => fileInputRef.current?.click()}
                      onDragOver={handleDragOver}
                      onDragEnter={handleDragEnter}
                      onDrop={handleDrop}
                    >
                      <VStack spacing={3}>
                        <Icon as={asElementType(FiUpload)} boxSize={8} color="#3a8bfd" />
                        <Text fontWeight="medium">
                          Cliquez ou glissez-déposez vos fichiers ici
                        </Text>
                        <Text fontSize="sm" color="gray.400">
                          Formats supportés : PDF, DOC, DOCX, JPG, PNG, etc.
                        </Text>
                      </VStack>
                    </Box>

                    {/* Liste des fichiers */}
                    {filesToUpload.length > 0 && (
                      <Box>
                        <Text fontWeight="medium" mb={3}>
                          Fichiers sélectionnés ({filesToUpload.length})
                        </Text>
                        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
                          {filesToUpload.map((fileData) => (
                            <Card key={fileData.id} bg="#232946" size="sm">
                              <CardBody>
                                <VStack spacing={2} align="stretch">
                                  <HStack justify="space-between">
                                    <HStack spacing={2} flex={1}>
                                      <Icon 
                                        as={asElementType(getFileIcon(fileData.file.name))} 
                                        color="#3a8bfd" 
                                      />
                                      <VStack align="start" spacing={0} flex={1}>
                                        <Input
                                          value={fileData.title}
                                          onChange={(e) => updateFileData(fileData.id, { title: e.target.value })}
                                          size="sm"
                                          variant="unstyled"
                                          fontWeight="medium"
                                          isDisabled={isCreating}
                                        />
                                        <Text fontSize="xs" color="gray.400">
                                          {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
                                        </Text>
                                      </VStack>
                                    </HStack>
                                    
                                    <Tooltip label="Supprimer">
                                      <IconButton
                                        aria-label="Supprimer"
                                        icon={<Icon as={asElementType(FiTrash2)} />}
                                        size="sm"
                                        variant="ghost"
                                        colorScheme="red"
                                        onClick={() => handleFileRemove(fileData.id)}
                                        isDisabled={isCreating}
                                      />
                                    </Tooltip>
                                  </HStack>

                                  <Input
                                    value={fileData.description}
                                    onChange={(e) => updateFileData(fileData.id, { description: e.target.value })}
                                    placeholder="Description (optionnel)"
                                    size="sm"
                                    bg="#1a1f36"
                                    borderColor="#1a1f36"
                                    _focus={{ borderColor: "#3a8bfd" }}
                                    isDisabled={isCreating}
                                  />

                                  {/* Barre de progression */}
                                  {isCreating && fileData.progress > 0 && (
                                    <VStack spacing={1} align="stretch">
                                      <Progress 
                                        value={fileData.progress} 
                                        size="sm" 
                                        colorScheme={fileData.uploaded ? "green" : "blue"}
                                        borderRadius="full"
                                      />
                                      <Text fontSize="xs" color="gray.400">
                                        {fileData.uploaded ? "✓ Uploadé" : `${fileData.progress}%`}
                                      </Text>
                                    </VStack>
                                  )}

                                  {/* Erreur */}
                                  {fileData.error && (
                                    <Alert status="error" size="sm">
                                      <AlertIcon />
                                      <AlertDescription fontSize="xs">
                                        {fileData.error}
                                      </AlertDescription>
                                    </Alert>
                                  )}
                                </VStack>
                              </CardBody>
                            </Card>
                          ))}
                        </SimpleGrid>
                      </Box>
                    )}
                  </VStack>
                )}
              </Box>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <HStack spacing={3}>
              <Button 
                variant="ghost" 
                onClick={handleClose}
                isDisabled={isCreating}
              >
                Annuler
              </Button>
              <Button
                colorScheme="blue"
                onClick={handleCreateFolderWithFiles}
                isLoading={isCreating}
                loadingText="Création..."
                leftIcon={<Icon as={asElementType(FiFolder)} />}
              >
                Créer le dossier
                {filesToUpload.length > 0 && ` (${filesToUpload.length} fichier${filesToUpload.length > 1 ? 's' : ''})`}
              </Button>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Input file caché */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="*/*"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />
    </>
  );
};

export default CreateFolderModal; 



