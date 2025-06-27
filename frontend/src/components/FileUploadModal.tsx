import React, { useState, useRef } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  useToast,
  Text,
  Progress,
  Box,
  HStack,
  IconButton,
  Flex,
  Center,
} from '@chakra-ui/react';
import { ViewIcon, DownloadIcon, AttachmentIcon } from '@chakra-ui/icons';
import config from '../config';
import { useAsyncOperation } from '../hooks/useAsyncOperation';

// Fonction pour déterminer le type MIME à partir de l'extension du fichier
const getMimeTypeFromExtension = (filename: string): string => {
  const extension = filename.split('.').pop()?.toLowerCase() || '';
  const mimeTypes: { [key: string]: string } = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'txt': 'text/plain',
    'csv': 'text/csv',
    'html': 'text/html',
    'htm': 'text/html',
    'xml': 'application/xml',
    'zip': 'application/zip',
    'rar': 'application/x-rar-compressed',
    'tar': 'application/x-tar',
    'gz': 'application/gzip',
  };
  
  return mimeTypes[extension] || 'application/octet-stream';
};

// Fonction pour déterminer le type de document à partir de l'extension
const getDocumentType = (filename: string): string => {
  const extension = filename.split('.').pop()?.toLowerCase() || '';
  
  if (['pdf'].includes(extension)) return 'PDF';
  if (['doc', 'docx', 'rtf'].includes(extension)) return 'WORD';
  if (['xls', 'xlsx', 'csv'].includes(extension)) return 'EXCEL';
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(extension)) return 'IMAGE';
  
  return 'AUTRE';
};

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
  currentFolderId?: number | null;
}

const FileUploadModal: React.FC<FileUploadModalProps> = ({ 
  isOpen, 
  onClose, 
  onUploadSuccess,
  currentFolderId = null
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedDocId, setUploadedDocId] = useState<number | null>(null);
  const [cloudinaryUrl, setCloudinaryUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast({
        title: 'Erreur',
        description: 'Veuillez sélectionner un fichier',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setUploading(true);
    setUploadProgress(10);

    // Extraction automatique des métadonnées
    const title = selectedFile.name.split('.')[0];
    const documentType = getDocumentType(selectedFile.name);
    const mimeType = selectedFile.type || getMimeTypeFromExtension(selectedFile.name);
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('titre', title);
    formData.append('type_document', documentType);
    formData.append('description', `Document automatiquement importé le ${new Date().toLocaleString()}`);
    formData.append('service', 'GED');
    formData.append('mime_type', mimeType);
    
    // Ajouter l'ID du dossier s'il est disponible
    if (currentFolderId !== null) {
      formData.append('dossier_id', currentFolderId.toString());
    }

    setUploadProgress(30);

    try {
      const response = await fetch(`${config.API_URL}/documents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      setUploadProgress(70);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Une erreur est survenue lors de l\'upload');
      }

      setUploadProgress(100);
      setUploadedDocId(data.document_id);
      setCloudinaryUrl(data.url);

      toast({
        title: 'Succès',
        description: data.message || 'Document uploadé avec succès',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });

      onUploadSuccess();
    } catch (error) {
      console.error('Erreur d\'upload:', error);
      toast({
        title: 'Erreur',
        description: error instanceof Error ? error.message : 'Une erreur est survenue lors de l\'upload',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setUploading(false);
    }
  };

  const handleView = () => {
    if (cloudinaryUrl) {
      window.open(cloudinaryUrl, '_blank');
    } else {
      toast({
        title: 'Erreur',
        description: 'URL du document non disponible',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleDownload = () => {
    if (cloudinaryUrl) {
      window.open(cloudinaryUrl, '_blank');
    } else {
      toast({
        title: 'Erreur',
        description: 'URL du document non disponible',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalOverlay backdropFilter="blur(10px)" />
      <ModalContent bg="#20243a" color="white" borderRadius="xl" boxShadow="0 10px 30px -5px rgba(0, 0, 0, 0.3)">
        <ModalHeader fontSize="xl" fontWeight="bold" textAlign="center">Upload de document</ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack spacing={6}>
            {!selectedFile ? (
              <Center 
                h="200px" 
                w="100%" 
                borderWidth="2px" 
                borderStyle="dashed" 
                borderColor="#3a8bfd" 
                borderRadius="xl"
                bg="#232946"
                onClick={triggerFileInput}
                cursor="pointer"
                transition="all 0.3s"
                _hover={{
                  bg: "#2a325a",
                  transform: "scale(1.02)",
                }}
              >
                <VStack spacing={3}>
                  <AttachmentIcon boxSize={10} color="#3a8bfd" />
                  <Text fontWeight="medium">Cliquez pour sélectionner un fichier</Text>
                  <Text fontSize="sm" color="gray.400">ou glissez-déposez votre fichier ici</Text>
                </VStack>
                <input
                type="file"
                onChange={handleFileChange}
                ref={fileInputRef}
                  style={{ display: 'none' }}
                />
              </Center>
            ) : (
              <Box 
                w="100%" 
                p={4} 
                bg="#232946"
                borderRadius="xl"
                borderWidth="1px"
                borderColor="#3a8bfd"
              >
                <VStack align="start" spacing={2}>
                  <Text fontWeight="bold">{selectedFile.name}</Text>
                  <Text fontSize="sm">Taille: {(selectedFile.size / 1024).toFixed(2)} KB</Text>
                  <Text fontSize="sm">Type: {getDocumentType(selectedFile.name)}</Text>
                  <Flex w="100%" justify="space-between" mt={2}>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      colorScheme="red" 
                      onClick={() => setSelectedFile(null)}
                    >
                      Changer
                    </Button>
                    <Button 
                      size="sm" 
                      colorScheme="blue" 
                      onClick={handleUpload}
                      isLoading={uploading}
                      loadingText="Upload..."
                    >
                      Uploader
                    </Button>
                  </Flex>
                </VStack>
              </Box>
            )}

            {uploading && (
              <Box w="100%">
                <Text mb={1} textAlign="center">Upload en cours...</Text>
                <Progress value={uploadProgress} size="sm" colorScheme="blue" borderRadius="full" />
              </Box>
            )}

            {uploadedDocId && (
              <Box w="100%" p={4} bg="#232946" borderRadius="xl" borderWidth="1px" borderColor="green.500">
                <VStack spacing={3}>
                  <Text fontWeight="bold" color="green.400">Document uploadé avec succès!</Text>
                <HStack>
                  <IconButton
                    aria-label="Voir le document"
                    icon={<ViewIcon />}
                    onClick={handleView}
                    colorScheme="blue"
                      variant="outline"
                      size="md"
                  />
                  <IconButton
                    aria-label="Télécharger le document"
                    icon={<DownloadIcon />}
                    onClick={handleDownload}
                    colorScheme="green"
                      variant="outline"
                      size="md"
                  />
                </HStack>
                </VStack>
              </Box>
            )}

            {!selectedFile && !uploading && !uploadedDocId && (
            <Button
              colorScheme="blue"
                onClick={triggerFileInput}
              w="100%"
                size="lg"
                borderRadius="lg"
                boxShadow="0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08)"
                _hover={{
                  transform: "translateY(-1px)",
                  boxShadow: "0 7px 14px rgba(50, 50, 93, 0.1), 0 3px 6px rgba(0, 0, 0, 0.08)"
                }}
                _active={{
                  transform: "translateY(1px)"
                }}
              >
                Sélectionner un fichier
            </Button>
            )}
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default FileUploadModal; 

