import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  VStack,
  HStack,
  Button,
  Text,
  Textarea,
  Select,
  Progress,
  Alert,
  AlertIcon,
  useToast,
  Divider,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Spinner,
  Box,
  IconButton,
  Tooltip
} from '@chakra-ui/react';
import { 
  SearchIcon, 
  DownloadIcon, 
  CopyIcon, 
  RepeatIcon,
  CheckIcon
} from '@chakra-ui/icons';
import { motion } from 'framer-motion';

const MotionBox = motion.div;

interface DocumentOCRProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number;
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
  const [hasExistingOCR, setHasExistingOCR] = useState(false);
  const [selectedPage, setSelectedPage] = useState<number | 'all'>('all');
  const [copied, setCopied] = useState(false);
  const toast = useToast();

  const languages = [
    { code: 'fra', name: 'Français' },
    { code: 'eng', name: 'Anglais' },
    { code: 'spa', name: 'Espagnol' },
    { code: 'deu', name: 'Allemand' },
    { code: 'ita', name: 'Italien' },
    { code: 'por', name: 'Portugais' },
    { code: 'rus', name: 'Russe' },
    { code: 'ara', name: 'Arabe' },
    { code: 'chi_sim', name: 'Chinois (Simplifié)' },
    { code: 'jpn', name: 'Japonais' }
  ];

  useEffect(() => {
    if (isOpen && documentId) {
      checkExistingOCR();
    }
  }, [isOpen, documentId]);

  const checkExistingOCR = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `https://web-production-ae27.up.railway.app/api/documents/${documentId}/metadata`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        if (data.metadata?.ocr) {
          setOcrResult(data.metadata.ocr);
          setHasExistingOCR(true);
          setSelectedLanguage(data.metadata.ocr.language || 'fra');
        }
      }
    } catch (error) {
      console.error('Erreur vérification OCR:', error);
    }
  };

  const performOCR = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `https://web-production-ae27.up.railway.app/api/documents/${documentId}/ocr`,
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
      setHasExistingOCR(true);

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

    const textToCopy = selectedPage === 'all' 
      ? ocrResult.text 
      : ocrResult.pages.find(p => p.page_number === selectedPage)?.text || '';

    try {
      await navigator.clipboard.writeText(textToCopy);
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

  const downloadText = () => {
    if (!ocrResult) return;

    const textToDownload = selectedPage === 'all' 
      ? ocrResult.text 
      : ocrResult.pages.find(p => p.page_number === selectedPage)?.text || '';

    const blob = new Blob([textToDownload], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${documentTitle}_ocr.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    toast({
      title: 'Fichier téléchargé',
      status: 'success',
      duration: 3000,
    });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'green';
    if (confidence >= 60) return 'yellow';
    return 'red';
  };

  const getDisplayText = () => {
    if (!ocrResult) return '';
    
    if (selectedPage === 'all') {
      return ocrResult.text;
    }
    
    const page = ocrResult.pages.find(p => p.page_number === selectedPage);
    return page?.text || '';
  };

  const getCurrentConfidence = () => {
    if (!ocrResult) return 0;
    
    if (selectedPage === 'all') {
      return ocrResult.confidence;
    }
    
    const page = ocrResult.pages.find(p => p.page_number === selectedPage);
    return page?.confidence || 0;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="6xl">
      <ModalOverlay />
      <ModalContent bg="#20243a" color="white" maxH="90vh">
        <ModalHeader borderBottom="1px solid #2D3748">
          <HStack justify="space-between">
            <VStack align="start" spacing={1}>
              <Text fontSize="lg" fontWeight="bold">
                Reconnaissance OCR - {documentTitle}
              </Text>
              {hasExistingOCR && (
                <Badge colorScheme="green" size="sm">
                  OCR déjà effectué
                </Badge>
              )}
            </VStack>
          </HStack>
        </ModalHeader>

        <ModalCloseButton />

        <ModalBody p={6} overflowY="auto">
          <VStack spacing={6}>
            {/* Configuration OCR */}
            <Box w="100%" bg="#2D3748" p={4} borderRadius="md">
              <VStack spacing={4}>
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
                          <option key={lang.code} value={lang.code}>
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
                    loadingText="Analyse en cours..."
                    size="md"
                  >
                    {hasExistingOCR ? 'Refaire l\'OCR' : 'Lancer l\'OCR'}
                  </Button>
                </HStack>

                {loading && (
                  <Box w="100%">
                    <Text fontSize="sm" mb={2}>Extraction du texte en cours...</Text>
                    <Progress isIndeterminate colorScheme="blue" size="sm" />
                  </Box>
                )}
              </VStack>
            </Box>

            {/* Erreur */}
            {error && (
              <Alert status="error" bg="#742A2A" borderRadius="md">
                <AlertIcon />
                {error}
              </Alert>
            )}

            {/* Résultats OCR */}
            {ocrResult && (
              <MotionBox
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                style={{ width: '100%' }}
              >
                <VStack spacing={4} w="100%">
                  {/* Statistiques */}
                  <Box w="100%" bg="#2D3748" p={4} borderRadius="md">
                    <Text fontWeight="bold" mb={3} color="#3a8bfd">
                      Statistiques d'extraction
                    </Text>
                    
                    <StatGroup>
                      <Stat>
                        <StatLabel>Confiance globale</StatLabel>
                        <StatNumber color={getConfidenceColor(ocrResult.confidence)}>
                          {Math.round(ocrResult.confidence)}%
                        </StatNumber>
                      </Stat>
                      
                      <Stat>
                        <StatLabel>Pages analysées</StatLabel>
                        <StatNumber>{ocrResult.page_count}</StatNumber>
                      </Stat>
                      
                      <Stat>
                        <StatLabel>Mots extraits</StatLabel>
                        <StatNumber>
                          {ocrResult.text.split(/\s+/).filter(word => word.length > 0).length}
                        </StatNumber>
                      </Stat>
                      
                      <Stat>
                        <StatLabel>Langue détectée</StatLabel>
                        <StatNumber fontSize="md">
                          {languages.find(l => l.code === ocrResult.language)?.name || ocrResult.language}
                        </StatNumber>
                      </Stat>
                    </StatGroup>
                  </Box>

                  {/* Sélection de page et actions */}
                  <Box w="100%" bg="#2D3748" p={4} borderRadius="md">
                    <HStack justify="space-between" mb={4}>
                      <HStack>
                        <Text fontSize="sm">Afficher:</Text>
                        <Select
                          value={selectedPage}
                          onChange={(e) => setSelectedPage(
                            e.target.value === 'all' ? 'all' : parseInt(e.target.value)
                          )}
                          size="sm"
                          w="150px"
                          bg="#20243a"
                          borderColor="#4A5568"
                        >
                          <option value="all">Tout le texte</option>
                          {ocrResult.pages.map(page => (
                            <option key={page.page_number} value={page.page_number}>
                              Page {page.page_number}
                            </option>
                          ))}
                        </Select>
                        
                        {selectedPage !== 'all' && (
                          <Badge colorScheme={getConfidenceColor(getCurrentConfidence())}>
                            {Math.round(getCurrentConfidence())}% confiance
                          </Badge>
                        )}
                      </HStack>

                      <HStack>
                        <Tooltip label={copied ? "Copié !" : "Copier le texte"}>
                          <IconButton
                            aria-label="Copier"
                            icon={copied ? <CheckIcon /> : <CopyIcon />}
                            size="sm"
                            colorScheme={copied ? "green" : "blue"}
                            onClick={copyToClipboard}
                          />
                        </Tooltip>
                        
                        <Button
                          leftIcon={<DownloadIcon />}
                          size="sm"
                          colorScheme="green"
                          onClick={downloadText}
                        >
                          Télécharger
                        </Button>
                      </HStack>
                    </HStack>

                    {/* Zone de texte */}
                    <Textarea
                      value={getDisplayText()}
                      placeholder="Le texte extrait apparaîtra ici..."
                      minHeight="400px"
                      bg="#20243a"
                      borderColor="#4A5568"
                      _hover={{ borderColor: "#63B3ED" }}
                      _focus={{ borderColor: "#3a8bfd", boxShadow: "0 0 0 1px #3a8bfd" }}
                      readOnly
                      resize="vertical"
                      fontSize="sm"
                      fontFamily="monospace"
                    />
                  </Box>

                  {/* Détails par page */}
                  {ocrResult.pages.length > 1 && (
                    <Box w="100%" bg="#2D3748" p={4} borderRadius="md">
                      <Text fontWeight="bold" mb={3} color="#3a8bfd">
                        Détails par page
                      </Text>
                      
                      <VStack spacing={2} align="stretch">
                        {ocrResult.pages.map((page, index) => (
                          <HStack
                            key={page.page_number}
                            p={3}
                            bg="#20243a"
                            borderRadius="md"
                            justify="space-between"
                          >
                            <HStack>
                              <Text fontWeight="bold">Page {page.page_number}</Text>
                              <Badge colorScheme={getConfidenceColor(page.confidence)}>
                                {Math.round(page.confidence)}%
                              </Badge>
                            </HStack>
                            
                            <Text fontSize="sm" color="gray.400">
                              {page.word_count} mots
                            </Text>
                          </HStack>
                        ))}
                      </VStack>
                    </Box>
                  )}
                </VStack>
              </MotionBox>
            )}

            {!ocrResult && !loading && !error && (
              <VStack spacing={4} py={8}>
                <SearchIcon boxSize={12} color="gray.400" />
                <Text color="gray.400" textAlign="center">
                  Sélectionnez une langue et cliquez sur "Lancer l'OCR" pour extraire le texte de ce document
                </Text>
              </VStack>
            )}
          </VStack>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default DocumentOCR;

