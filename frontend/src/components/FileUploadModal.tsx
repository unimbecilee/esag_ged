import React, { useState, useRef } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  useToast,
  Text,
  Progress,
  Select,
  Box,
  HStack,
  IconButton,
} from '@chakra-ui/react';
import { ViewIcon, DownloadIcon } from '@chakra-ui/icons';
import config from '../config';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

const FileUploadModal: React.FC<FileUploadModalProps> = ({ isOpen, onClose, onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [title, setTitle] = useState('');
  const [documentType, setDocumentType] = useState('');
  const [description, setDescription] = useState('');
  const [service, setService] = useState('GED');
  const [uploadedDocId, setUploadedDocId] = useState<number | null>(null);
  const [cloudinaryUrl, setCloudinaryUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
      // Utiliser le nom du fichier comme titre par défaut
      setTitle(event.target.files[0].name.split('.')[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !title || !documentType) {
      toast({
        title: 'Erreur',
        description: 'Veuillez remplir tous les champs requis',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('titre', title);
    formData.append('type_document', documentType);
    formData.append('description', description);
    formData.append('service', service);

    try {
      const response = await fetch(`${config.API_URL}/documents`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Une erreur est survenue lors de l\'upload');
      }

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

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent bg="#20243a" color="white">
        <ModalHeader>Upload de document</ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel>Titre du document</FormLabel>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Entrez le titre du document"
                bg="#232946"
                borderColor="#232946"
                _hover={{ borderColor: "#3a8bfd" }}
                _focus={{
                  borderColor: "#3a8bfd",
                  boxShadow: "0 0 0 1.5px #3a8bfd",
                }}
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Type de document</FormLabel>
              <Select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                placeholder="Sélectionnez le type de document"
                bg="#232946"
                borderColor="#232946"
                _hover={{ borderColor: "#3a8bfd" }}
                _focus={{
                  borderColor: "#3a8bfd",
                  boxShadow: "0 0 0 1.5px #3a8bfd",
                }}
              >
                <option value="PDF">PDF</option>
                <option value="WORD">Word</option>
                <option value="EXCEL">Excel</option>
                <option value="IMAGE">Image</option>
                <option value="AUTRE">Autre</option>
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel>Description</FormLabel>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description du document"
                bg="#232946"
                borderColor="#232946"
                _hover={{ borderColor: "#3a8bfd" }}
                _focus={{
                  borderColor: "#3a8bfd",
                  boxShadow: "0 0 0 1.5px #3a8bfd",
                }}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Service</FormLabel>
              <Input
                value={service}
                onChange={(e) => setService(e.target.value)}
                placeholder="Service"
                bg="#232946"
                borderColor="#232946"
                _hover={{ borderColor: "#3a8bfd" }}
                _focus={{
                  borderColor: "#3a8bfd",
                  boxShadow: "0 0 0 1.5px #3a8bfd",
                }}
              />
            </FormControl>

            <FormControl isRequired>
              <FormLabel>Fichier</FormLabel>
              <Input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                display="none"
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                width="full"
                colorScheme="blue"
                variant="outline"
              >
                {selectedFile ? selectedFile.name : 'Sélectionner un fichier'}
              </Button>
              {selectedFile && (
                <Text fontSize="sm" mt={2}>
                  Taille: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </Text>
              )}
            </FormControl>

            {uploading && (
              <Box width="100%">
                <Progress
                  value={uploadProgress}
                  size="sm"
                  colorScheme="blue"
                  borderRadius="full"
                />
              </Box>
            )}

            <HStack width="100%" spacing={4}>
              <Button
                colorScheme="blue"
                width="full"
                onClick={handleUpload}
                isLoading={uploading}
                loadingText="Upload en cours..."
              >
                Uploader le document
              </Button>

              {cloudinaryUrl && (
                <>
                  <IconButton
                    aria-label="Voir le document"
                    icon={<ViewIcon />}
                    colorScheme="green"
                    onClick={handleView}
                  />
                  <IconButton
                    aria-label="Télécharger le document"
                    icon={<DownloadIcon />}
                    colorScheme="blue"
                    onClick={handleDownload}
                  />
                </>
              )}
            </HStack>
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default FileUploadModal; 