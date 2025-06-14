import React, { useState, useEffect, ElementType } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Text,
  Center,
  Icon,
  VStack,
  HStack,
  Button,
  Select,
  Box,
  Progress,
  Textarea,
  useToast,
  Badge,
  IconButton,
  Tooltip
} from '@chakra-ui/react';
import { FiType, FiCopy } from 'react-icons/fi';
import { SearchIcon } from '@chakra-ui/icons';
import config from '../config';

interface DocumentOCRProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number | null;
  documentTitle: string;
}

interface OCRResult {
  text: string;
  confidence: number;
  language: string;
  processed_at: string;
  page_count: number;
  pages: Array<{
    page_number: number;
    text: string;
    confidence: number;
    word_count: number;
  }>;
}

const DocumentOCR: React.FC<DocumentOCRProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle
}) => {
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState('fra');
  const [copied, setCopied] = useState(false);
  const toast = useToast();

  const languages = [
    { code: 'fra', name: 'Français' },
    { code: 'eng', name: 'Anglais' },
    { code: 'spa', name: 'Espagnol' },
    { code: 'deu', name: 'Allemand' },
    { code: 'ita', name: 'Italien' }
  ];

  const performOCR = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/documents/${documentId}/ocr`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            language: selectedLanguage
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Erreur lors de l\'OCR');
      }

      setOcrResult(data.result);

      toast({
        title: 'OCR terminé',
        description: `Texte extrait avec ${Math.round(data.result.confidence)}% de confiance`,
        status: 'success',
        duration: 5000,
      });

    } catch (error) {
      console.error('Erreur OCR:', error);
      setError(error instanceof Error ? error.message : 'Erreur lors de l\'OCR');
      toast({
        title: 'Erreur OCR',
        description: error instanceof Error ? error.message : 'Erreur inconnue',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (!ocrResult) return;

    try {
      await navigator.clipboard.writeText(ocrResult.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      
      toast({
        title: 'Texte copié',
        status: 'success',
        duration: 2000,
      });
    } catch (error) {
      toast({
        title: 'Erreur de copie',
        status: 'error',
        duration: 2000,
      });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl">
      <ModalOverlay />
      <ModalContent bg="#2a3657" color="white">
        <ModalHeader>
          <HStack>
            <Icon as={FiType as ElementType} />
            <Text>Extraction OCR - {documentTitle}</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack spacing={6} align="stretch">
            {/* Configuration */}
            <Box w="100%" bg="#1a202c" p={4} borderRadius="md">
              <HStack w="100%" justify="space-between">
                <VStack align="start" spacing={2}>
                  <Text fontWeight="bold">Configuration</Text>
                  <HStack>
                    <Text fontSize="sm">Langue:</Text>
                    <Select
                      value={selectedLanguage}
                      onChange={(e) => setSelectedLanguage(e.target.value)}
                      size="sm"
                      w="200px"
                      bg="#20243a"
                      borderColor="#4A5568"
                      isDisabled={loading}
                    >
                      {languages.map(lang => (
                        <option key={lang.code} value={lang.code} style={{background: '#20243a'}}>
                          {lang.name}
                        </option>
                      ))}
                    </Select>
                  </HStack>
                </VStack>

                <Button
                  leftIcon={<SearchIcon />}
                  colorScheme="blue"
                  onClick={performOCR}
                  isLoading={loading}
                  loadingText="Extraction..."
                  size="md"
                >
                  Lancer l'OCR
                </Button>
              </HStack>

              {loading && (
                <Box w="100%" mt={4}>
                  <Text fontSize="sm" mb={2}>Extraction du texte en cours...</Text>
                  <Progress isIndeterminate colorScheme="blue" size="sm" />
                </Box>
              )}
            </Box>

            {/* Erreur */}
            {error && (
              <Box bg="red.600" p={4} borderRadius="md">
                <Text fontWeight="bold">Erreur</Text>
                <Text fontSize="sm">{error}</Text>
              </Box>
            )}

            {/* Résultats OCR */}
            {ocrResult && (
              <Box w="100%">
                <VStack spacing={4} align="stretch">
                  {/* Stats */}
                  <HStack justify="space-between" bg="#1a202c" p={3} borderRadius="md">
                    <VStack align="start" spacing={1}>
                      <Text fontSize="sm" color="gray.300">Confiance</Text>
                      <Badge colorScheme={ocrResult.confidence > 80 ? 'green' : 'yellow'}>
                        {Math.round(ocrResult.confidence)}%
                      </Badge>
                    </VStack>
                    <VStack align="start" spacing={1}>
                      <Text fontSize="sm" color="gray.300">Mots extraits</Text>
                      <Text fontWeight="bold">{ocrResult.text.split(' ').length}</Text>
                    </VStack>
                    <VStack align="end" spacing={1}>
                      <Text fontSize="sm" color="gray.300">Langue</Text>
                      <Badge colorScheme="blue">{ocrResult.language}</Badge>
                    </VStack>
                  </HStack>

                  {/* Texte */}
                  <Box>
                    <HStack justify="space-between" mb={2}>
                      <Text fontWeight="bold">Texte extrait</Text>
                      <Tooltip label={copied ? "Copié !" : "Copier le texte"}>
                        <IconButton
                          aria-label="Copier le texte"
                          icon={<Icon as={FiCopy as ElementType} />}
                          size="sm"
                          colorScheme={copied ? "green" : "gray"}
                          onClick={copyToClipboard}
                        />
                      </Tooltip>
                    </HStack>
                    <Textarea
                      value={ocrResult.text}
                      readOnly
                      minH="300px"
                      bg="#1a202c"
                      borderColor="#4A5568"
                      fontSize="sm"
                    />
                  </Box>
                </VStack>
              </Box>
            )}

            {/* Message par défaut */}
            {!ocrResult && !loading && !error && (
              <Center py={10}>
                <VStack spacing={4}>
                  <Icon as={FiType as ElementType} boxSize={16} color="gray.400" />
                  <Text color="gray.400" textAlign="center">
                    Cliquez sur "Lancer l'OCR" pour extraire le texte du document
                  </Text>
                  <Text fontSize="sm" color="gray.500" textAlign="center">
                    Fonctionne avec les PDF et les images
                  </Text>
                </VStack>
              </Center>
            )}
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default DocumentOCR; 