import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Image,
  VStack,
  HStack,
  Button,
  Text,
  IconButton,
  Spinner,
  Alert,
  AlertIcon,
  Select,
  useToast,
  Badge,
  Skeleton
} from '@chakra-ui/react';
import { ChevronLeftIcon, ChevronRightIcon, DownloadIcon, ViewIcon } from '@chakra-ui/icons';
import { motion } from 'framer-motion';

const MotionBox = motion.div;

interface DocumentPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number;
  documentTitle: string;
  documentType?: string;
}

interface PreviewData {
  imageUrl?: string;
  pageCount?: number;
  currentPage?: number;
  metadata?: any;
}

const DocumentPreview: React.FC<DocumentPreviewProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  documentType
}) => {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [previewSize, setPreviewSize] = useState('medium');
  const toast = useToast();

  useEffect(() => {
    if (isOpen && documentId) {
      loadPreview();
      loadMetadata();
    }
  }, [isOpen, documentId, currentPage]);

  const loadPreview = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:5000/api/documents/${documentId}/preview?page=${currentPage}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Erreur lors du chargement de l\'aperçu');
      }

      const blob = await response.blob();
      const imageUrl = URL.createObjectURL(blob);
      
      setPreviewData(prev => ({
        imageUrl,
        currentPage,
        pageCount: prev?.pageCount || 1,
        metadata: prev?.metadata
      }));

    } catch (error) {
      console.error('Erreur preview:', error);
      setError('Impossible de charger l\'aperçu');
    } finally {
      setLoading(false);
    }
  };

  const loadMetadata = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:5000/api/documents/${documentId}/metadata`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setPreviewData(prev => ({
          imageUrl: prev?.imageUrl,
          currentPage: prev?.currentPage || 1,
          metadata: data.metadata,
          pageCount: data.metadata?.pages || 1
        }));
      }
    } catch (error) {
      console.error('Erreur métadonnées:', error);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= (previewData?.pageCount || 1)) {
      setCurrentPage(newPage);
    }
  };

  const downloadDocument = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `/api/documents/${documentId}/download`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Erreur lors du téléchargement');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = documentTitle;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: 'Téléchargement réussi',
        status: 'success',
        duration: 3000,
      });

    } catch (error) {
      console.error('Erreur téléchargement:', error);
      toast({
        title: 'Erreur de téléchargement',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const getSizeClass = () => {
    switch (previewSize) {
      case 'small': return 'max-w-md';
      case 'large': return 'max-w-4xl';
      default: return 'max-w-2xl';
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="full">
      <ModalOverlay bg="rgba(0, 0, 0, 0.8)" />
      <ModalContent 
        bg="#20243a" 
        color="white" 
        margin="20px"
        borderRadius="lg"
        maxH="90vh"
      >
        <ModalHeader borderBottom="1px solid #2D3748">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Text fontSize="lg" fontWeight="bold">
                {documentTitle}
              </Text>
              {documentType && (
                <Badge colorScheme="blue" size="sm">
                  {documentType}
                </Badge>
              )}
            </VStack>
            
            <HStack>
              <Select
                value={previewSize}
                onChange={(e) => setPreviewSize(e.target.value)}
                size="sm"
                w="120px"
                bg="#2D3748"
                borderColor="#4A5568"
              >
                <option value="small">Petit</option>
                <option value="medium">Moyen</option>
                <option value="large">Grand</option>
              </Select>
              
              <Button
                leftIcon={<DownloadIcon />}
                size="sm"
                colorScheme="blue"
                onClick={downloadDocument}
              >
                Télécharger
              </Button>
            </HStack>
          </HStack>
        </ModalHeader>

        <ModalCloseButton color="white" />

        <ModalBody p={6} overflowY="auto">
          {error ? (
            <Alert status="error" bg="#742A2A" borderRadius="md">
              <AlertIcon />
              {error}
            </Alert>
          ) : loading ? (
            <VStack spacing={4}>
              <Spinner size="xl" color="#3a8bfd" />
              <Text>Chargement de l'aperçu...</Text>
            </VStack>
          ) : previewData ? (
            <VStack spacing={4}>
              {/* Navigation des pages */}
              {(previewData.pageCount ?? 1) > 1 && (
                <HStack spacing={4} bg="#2D3748" p={3} borderRadius="md">
                  <IconButton
                    aria-label="Page précédente"
                    icon={<ChevronLeftIcon />}
                    size="sm"
                    isDisabled={currentPage <= 1}
                    onClick={() => handlePageChange(currentPage - 1)}
                    colorScheme="blue"
                  />
                  
                  <Text fontSize="sm">
                    Page {currentPage} sur {previewData.pageCount ?? 1}
                  </Text>
                  
                  <IconButton
                    aria-label="Page suivante"
                    icon={<ChevronRightIcon />}
                    size="sm"
                    isDisabled={currentPage >= (previewData.pageCount ?? 1)}
                    onClick={() => handlePageChange(currentPage + 1)}
                    colorScheme="blue"
                  />
                </HStack>
              )}

              {/* Image de prévisualisation */}
              <MotionBox
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                className={getSizeClass()}
                style={{ width: '100%' }}
              >
                {previewData.imageUrl ? (
                  <Image
                    src={previewData.imageUrl}
                    alt={`Aperçu - Page ${currentPage}`}
                    w="100%"
                    borderRadius="md"
                    border="1px solid #4A5568"
                    boxShadow="lg"
                  />
                ) : (
                  <Skeleton height="600px" borderRadius="md" />
                )}
              </MotionBox>

              {/* Métadonnées (si disponibles) */}
              {previewData.metadata && (
                <VStack 
                  align="start" 
                  bg="#2D3748" 
                  p={4} 
                  borderRadius="md" 
                  w="100%"
                  maxW="800px"
                >
                  <Text fontWeight="bold" fontSize="md" color="#3a8bfd">
                    Informations du document
                  </Text>
                  
                  <HStack spacing={8} wrap="wrap">
                    {previewData.metadata.pages && (
                      <VStack align="start" spacing={1}>
                        <Text fontSize="xs" color="gray.400">Pages</Text>
                        <Text fontSize="sm">{previewData.metadata.pages}</Text>
                      </VStack>
                    )}
                    
                    {previewData.metadata.file_size && (
                      <VStack align="start" spacing={1}>
                        <Text fontSize="xs" color="gray.400">Taille</Text>
                        <Text fontSize="sm">
                          {(previewData.metadata.file_size / 1024 / 1024).toFixed(2)} MB
                        </Text>
                      </VStack>
                    )}
                    
                    {previewData.metadata.word_count && (
                      <VStack align="start" spacing={1}>
                        <Text fontSize="xs" color="gray.400">Mots</Text>
                        <Text fontSize="sm">{previewData.metadata.word_count}</Text>
                      </VStack>
                    )}
                    
                    {previewData.metadata.language && (
                      <VStack align="start" spacing={1}>
                        <Text fontSize="xs" color="gray.400">Langue</Text>
                        <Text fontSize="sm">{previewData.metadata.language}</Text>
                      </VStack>
                    )}
                    
                    {previewData.metadata.has_images !== undefined && (
                      <VStack align="start" spacing={1}>
                        <Text fontSize="xs" color="gray.400">Images</Text>
                        <Badge 
                          colorScheme={previewData.metadata.has_images ? "green" : "gray"}
                          size="sm"
                        >
                          {previewData.metadata.has_images ? "Oui" : "Non"}
                        </Badge>
                      </VStack>
                    )}
                  </HStack>
                </VStack>
              )}
            </VStack>
          ) : (
            <VStack spacing={4}>
              <ViewIcon boxSize={12} color="gray.400" />
              <Text color="gray.400">Aucun aperçu disponible</Text>
            </VStack>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default DocumentPreview;