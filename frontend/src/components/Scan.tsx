import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Heading,
  VStack,
  HStack,
  Button,
  Text,
  Icon,
  useToast,
  Progress,
  Flex,
  SimpleGrid,
  Badge,
  Card,
  CardBody,
  Tooltip,
  Input,
  FormControl,
  FormLabel,
  Textarea,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Divider,
  Switch,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Slider,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Container,
  RadioGroup,
  Radio,
  Stack,
  Image,
  Spinner,
  Center
} from '@chakra-ui/react';
import { 
  FiCamera, 
  FiFile, 
  FiSettings, 
  FiSave, 
  FiImage, 
  FiFileText,
  FiDownload,
  FiTrash2,
  FiEye,
  FiUploadCloud,
  FiCheckCircle,
  FiClock,
  FiZap,
  FiRefreshCw,
  FiSmartphone,
  FiMonitor,
  FiUpload,
  FiAlertTriangle
} from 'react-icons/fi';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import { checkAuthToken } from '../utils/errorHandling';
import { API_URL } from '../config';
import { asElementType } from '../utils/iconUtils';

interface ScanSettings {
  resolution: string;
  format: string;
  mode: string;
  quality: number;
  autoEnhance: boolean;
  ocrEnabled: boolean;
}

interface ScannedDocument {
  id: string;
  filename: string;
  format: string;
  size: string;
  pages: number;
  timestamp: string;
  method: 'camera' | 'scanner';
  title: string;
  has_ocr: boolean;
  preview?: string;
}

interface DeviceCapabilities {
  device_type: 'mobile' | 'desktop';
  capabilities: {
    camera: boolean;
    scanner: boolean;
    recommended_method: 'camera' | 'scanner';
  };
  instructions: {
    camera: string;
    scanner: string;
    mobile_redirect: string;
  };
}

const Scan: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const { isOpen: isSettingsOpen, onOpen: onSettingsOpen, onClose: onSettingsClose } = useDisclosure();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isCameraOpen, onOpen: onCameraOpen, onClose: onCameraClose } = useDisclosure();
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [selectedPreset, setSelectedPreset] = useState('document');
  const [documentTitle, setDocumentTitle] = useState('');
  const [documentDescription, setDocumentDescription] = useState('');
  const [previewDocument, setPreviewDocument] = useState<ScannedDocument | null>(null);
  
  const [deviceCapabilities, setDeviceCapabilities] = useState<DeviceCapabilities | null>(null);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [loadingCapabilities, setLoadingCapabilities] = useState(true);
  
  const [settings, setSettings] = useState<ScanSettings>({
    resolution: '300',
    format: 'PDF',
    mode: 'COULEUR',
    quality: 85,
    autoEnhance: true,
    ocrEnabled: true
  });
  
  const [scannedDocuments, setScannedDocuments] = useState<ScannedDocument[]>([]);

  // Presets de numérisation
  const scanPresets = [
    {
      id: 'document',
      name: 'Document',
      description: 'Idéal pour textes et documents',
      icon: FiFileText,
      settings: { resolution: '300', format: 'PDF', mode: 'COULEUR', quality: 85 }
    },
    {
      id: 'photo',
      name: 'Photo',
      description: 'Haute qualité pour images',
      icon: FiImage,
      settings: { resolution: '600', format: 'JPEG', mode: 'COULEUR', quality: 95 }
    },
    {
      id: 'rapide',
      name: 'Rapide',
      description: 'Numérisation rapide',
      icon: FiZap,
      settings: { resolution: '150', format: 'PDF', mode: 'NIVEAUX_GRIS', quality: 70 }
    }
  ];

  // Détection des capacités de l'appareil au chargement
  useEffect(() => {
    detectDeviceCapabilities();
    loadScannedDocuments();
  }, []);

  const detectDeviceCapabilities = async () => {
    try {
      const token = checkAuthToken();
      const response = await fetch(`${API_URL}/scan/detect-device`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const capabilities = await response.json();
        setDeviceCapabilities(capabilities);
      }
    } catch (error) {
      console.error('Erreur détection appareil:', error);
    } finally {
      setLoadingCapabilities(false);
    }
  };

  const loadScannedDocuments = async () => {
    try {
      const token = checkAuthToken();
      const response = await fetch(`${API_URL}/scan/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setScannedDocuments(data.scanned_documents.map((doc: any) => ({
          id: doc.id,
          filename: doc.filename,
          format: doc.title?.includes('.') ? doc.title.split('.').pop()?.toUpperCase() || 'UNKNOWN' : 'PDF',
          size: doc.size,
          pages: doc.pages,
          timestamp: new Date(doc.date_scan).toLocaleString('fr-FR'),
          method: doc.method,
          title: doc.title || doc.filename,
          has_ocr: doc.has_ocr,
          preview: doc.preview
        })));
      }
    } catch (error) {
      console.error('Erreur chargement documents:', error);
    }
  };

  const applyPreset = (presetId: string) => {
    const preset = scanPresets.find(p => p.id === presetId);
    if (preset) {
      setSettings(prev => ({ ...prev, ...preset.settings }));
      setSelectedPreset(presetId);
    }
  };

  const startCameraCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: 'environment', // Caméra arrière par défaut
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      
      setCameraStream(stream);
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      
      onCameraOpen();
    } catch (error) {
      console.error('Erreur accès caméra:', error);
      alert('Impossible d\'accéder à la caméra. Vérifiez les permissions.');
    }
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        setCapturedImage(imageData);
      }
    }
  };

  const processCameraCapture = async () => {
    if (!capturedImage) return;

    setScanning(true);
    setProgress(0);
    setCurrentStep('Traitement de l\'image...');

    try {
      const result = await executeOperation(
        async () => {
          const token = checkAuthToken();
          const response = await fetch(`${API_URL}/scan/camera`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              image: capturedImage,
              settings: settings,
              title: documentTitle || `Scan mobile ${new Date().toLocaleString('fr-FR')}`,
              description: documentDescription
            })
          });

          if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erreur lors de la numérisation');
          }

          return await response.json();
        },
        {
          loadingMessage: "Numérisation en cours...",
          successMessage: "Document numérisé avec succès !",
          errorMessage: "Erreur lors de la numérisation"
        }
      );

      if (result && result.success) {
        await loadScannedDocuments();
        setDocumentTitle('');
        setDocumentDescription('');
        setCapturedImage(null);
        stopCameraStream();
        onCameraClose();
      }
    } catch (error) {
      console.error('Erreur numérisation caméra:', error);
    } finally {
      setScanning(false);
      setProgress(0);
      setCurrentStep('');
    }
  };

  const handleScannerUpload = async (file: File) => {
    setScanning(true);
    setProgress(0);
    setCurrentStep('Upload du fichier...');

    try {
      const result = await executeOperation(
        async () => {
          const token = checkAuthToken();
          const formData = new FormData();
          formData.append('file', file);
          formData.append('settings', JSON.stringify(settings));
          formData.append('title', documentTitle || `Scan ${new Date().toLocaleString('fr-FR')}`);
          formData.append('description', documentDescription || '');

          const response = await fetch(`${API_URL}/scan/scanner`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            },
            body: formData
          });

          if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Erreur lors de la numérisation');
          }

          return await response.json();
        },
        {
          loadingMessage: "Traitement du document...",
          successMessage: "Document numérisé avec succès !",
          errorMessage: "Erreur lors de la numérisation"
        }
      );

      if (result && result.success) {
        await loadScannedDocuments();
        setDocumentTitle('');
        setDocumentDescription('');
      }
    } catch (error) {
      console.error('Erreur numérisation scanner:', error);
    } finally {
      setScanning(false);
      setProgress(0);
      setCurrentStep('');
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files[0]) {
      handleScannerUpload(files[0]);
    }
  };

  const handleSaveDocument = async (doc: ScannedDocument) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/scan/${doc.id}/save-to-ged`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            title: doc.title,
            description: documentDescription
          })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Erreur lors de la sauvegarde');
        }

        await loadScannedDocuments();
      },
      {
        loadingMessage: "Sauvegarde en cours...",
        successMessage: "Document sauvegardé dans le GED !",
        errorMessage: "Impossible de sauvegarder le document"
      }
    );
  };

  const handleDeleteDocument = async (docId: string) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/scan/${docId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Erreur lors de la suppression');
        }

        await loadScannedDocuments();
      },
      {
        loadingMessage: "Suppression...",
        successMessage: "Document supprimé",
        errorMessage: "Erreur lors de la suppression"
      }
    );
  };

  const stopCameraStream = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
    }
  };

  const handlePreviewDocument = (doc: ScannedDocument) => {
    setPreviewDocument(doc);
    onPreviewOpen();
  };

  // Cleanup au démontage du composant
  useEffect(() => {
    return () => {
      stopCameraStream();
    };
  }, [cameraStream]);

  if (loadingCapabilities) {
    return (
      <Container maxW="container.xl" py={6}>
        <Center h="400px">
          <VStack spacing={4}>
            <Spinner size="xl" color="blue.500" />
            <Text color="white">Détection des capacités de l'appareil...</Text>
          </VStack>
        </Center>
      </Container>
    );
  }

  return (
    <Container maxW="container.xl" py={6}>
      <VStack spacing={6} align="stretch">
        {/* En-tête avec détection d'appareil */}
        <Flex justify="space-between" align="center">
          <Box>
            <Heading color="white" size="lg" mb={2}>
              Scanner de documents
            </Heading>
            <HStack spacing={2} mb={2}>
              <Icon 
                as={asElementType(deviceCapabilities?.device_type === 'mobile' ? FiSmartphone : FiMonitor)} 
                color="#3a8bfd" 
              />
              <Text color="gray.400">
                Appareil {deviceCapabilities?.device_type === 'mobile' ? 'mobile' : 'ordinateur'} détecté
              </Text>
            </HStack>
            <Text color="gray.400" fontSize="sm">
              Méthode recommandée : {deviceCapabilities?.capabilities.recommended_method === 'camera' ? 'Caméra' : 'Scanner'}
            </Text>
          </Box>
          <Button
            leftIcon={<Icon as={asElementType(FiSettings)} />}
            variant="outline"
            colorScheme="blue"
            onClick={onSettingsOpen}
          >
            Paramètres avancés
          </Button>
        </Flex>

        {/* Alerte pour PC sans caméra */}
        {deviceCapabilities?.device_type === 'desktop' && (
          <Alert status="info" bg="#20243a" borderColor="#3a8bfd">
            <AlertIcon color="#3a8bfd" />
            <Box>
              <AlertTitle color="white">Numérisation sur ordinateur</AlertTitle>
              <AlertDescription color="gray.400">
                Pour utiliser la caméra, connectez-vous depuis votre téléphone. 
                Sur PC, vous pouvez uploader un fichier depuis votre scanner ou dossier.
              </AlertDescription>
            </Box>
          </Alert>
        )}

        {/* Zone de numérisation principale */}
        <Card bg="#20243a" borderColor="#3a8bfd">
          <CardBody p={8}>
            <VStack spacing={6}>
              {/* Presets de numérisation */}
              <Box w="full">
                <Text color="white" fontWeight="semibold" mb={4}>
                  Choisissez un type de numérisation :
                </Text>
                <RadioGroup value={selectedPreset} onChange={setSelectedPreset}>
                  <HStack spacing={4} justify="center">
                    {scanPresets.map((preset) => (
                      <Card
                        key={preset.id}
                        bg={selectedPreset === preset.id ? "#3a8bfd" : "#232946"}
                        borderColor={selectedPreset === preset.id ? "#3a8bfd" : "#232946"}
                        cursor="pointer"
                        onClick={() => applyPreset(preset.id)}
                        _hover={{ borderColor: "#3a8bfd", transform: "translateY(-2px)" }}
                        transition="all 0.2s"
                        minW="200px"
                      >
                        <CardBody textAlign="center" p={6}>
                          <Icon 
                            as={asElementType(preset.icon)} 
                            boxSize={8} 
                            color={selectedPreset === preset.id ? "white" : "#3a8bfd"}
                            mb={3}
                          />
                          <Text 
                            color="white" 
                            fontWeight="bold" 
                            mb={2}
                          >
                            {preset.name}
                          </Text>
                          <Text 
                            color={selectedPreset === preset.id ? "gray.200" : "gray.400"}
                            fontSize="sm"
                          >
                            {preset.description}
                          </Text>
                        </CardBody>
                      </Card>
                    ))}
                  </HStack>
                </RadioGroup>
              </Box>

              <Divider borderColor="#3a8bfd" />

              {/* Informations du document */}
              <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} w="full">
                <FormControl>
                  <FormLabel color="white">Titre du document</FormLabel>
                  <Input
                    value={documentTitle}
                    onChange={(e) => setDocumentTitle(e.target.value)}
                    placeholder="Mon document important..."
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                    _focus={{ borderColor: "#3a8bfd" }}
                  />
                </FormControl>
                <FormControl>
                  <FormLabel color="white">Description (optionnel)</FormLabel>
                  <Input
                    value={documentDescription}
                    onChange={(e) => setDocumentDescription(e.target.value)}
                    placeholder="Description du document..."
                    bg="#232946"
                    color="white"
                    borderColor="#232946"
                    _focus={{ borderColor: "#3a8bfd" }}
                  />
                </FormControl>
              </SimpleGrid>

              {/* Boutons de numérisation selon l'appareil */}
              <HStack spacing={4} w="full" justify="center">
                {deviceCapabilities?.capabilities.camera && (
                  <Button
                    leftIcon={<Icon as={asElementType(FiCamera)} />}
                    colorScheme="blue"
                    size="lg"
                    onClick={startCameraCapture}
                    isDisabled={scanning}
                    px={8}
                    py={6}
                    fontSize="lg"
                    borderRadius="xl"
                  >
                    Utiliser la caméra
                  </Button>
                )}
                
                {deviceCapabilities?.capabilities.scanner && (
                  <Button
                    leftIcon={<Icon as={asElementType(FiUpload)} />}
                    colorScheme="green"
                    size="lg"
                    onClick={() => fileInputRef.current?.click()}
                    isDisabled={scanning}
                    px={8}
                    py={6}
                    fontSize="lg"
                    borderRadius="xl"
                  >
                    Uploader un fichier
                  </Button>
                )}
              </HStack>

              {/* Barre de progression */}
              {scanning && (
                <Box w="full">
                  <Flex justify="space-between" align="center" mb={2}>
                    <Text color="white" fontSize="sm">{currentStep}</Text>
                    <Text color="white" fontSize="sm">{Math.round(progress)}%</Text>
                  </Flex>
                  <Progress
                    value={progress}
                    size="lg"
                    colorScheme="blue"
                    borderRadius="full"
                    hasStripe
                    isAnimated
                  />
                </Box>
              )}

              {/* Paramètres rapides */}
              <HStack spacing={6} color="gray.400" fontSize="sm">
                <HStack>
                  <Icon as={asElementType(FiImage)} />
                  <Text>{settings.resolution} DPI</Text>
                </HStack>
                <HStack>
                  <Icon as={asElementType(FiFileText)} />
                  <Text>{settings.format}</Text>
                </HStack>
                <HStack>
                  <Icon as={asElementType(FiZap)} />
                  <Text>Qualité {settings.quality}%</Text>
                </HStack>
                {settings.ocrEnabled && (
                  <HStack>
                    <Icon as={asElementType(FiFileText)} />
                    <Text>OCR activé</Text>
                  </HStack>
                )}
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Documents numérisés */}
        {scannedDocuments.length > 0 && (
          <Box>
            <Heading color="white" size="md" mb={4}>
              Documents numérisés ({scannedDocuments.length})
            </Heading>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
              {scannedDocuments.map((doc) => (
                <Card key={doc.id} bg="#20243a" borderColor="#232946">
                  <CardBody>
                    <VStack spacing={3} align="stretch">
                      <Flex justify="space-between" align="start">
                        <HStack>
                          <Icon 
                            as={asElementType(doc.method === 'camera' ? FiCamera : FiFile)} 
                            color="#3a8bfd" 
                            boxSize={5} 
                          />
                          <Box>
                            <Text color="white" fontWeight="semibold" fontSize="sm">
                              {doc.title}
                            </Text>
                            <HStack spacing={2} mt={1}>
                              <Badge colorScheme="blue" size="sm">{doc.format}</Badge>
                              <Badge colorScheme="gray" size="sm">{doc.size}</Badge>
                              <Badge colorScheme="green" size="sm">{doc.pages}p</Badge>
                              {doc.has_ocr && <Badge colorScheme="purple" size="sm">OCR</Badge>}
                            </HStack>
                          </Box>
                        </HStack>
                        <Icon as={asElementType(FiCheckCircle)} color="green.400" />
                      </Flex>
                      
                      <Text color="gray.400" fontSize="xs">
                        <Icon as={asElementType(FiClock)} mr={1} />
                        {doc.timestamp}
                      </Text>

                      <HStack spacing={2}>
                        <Tooltip label="Aperçu">
                          <Button
                            size="sm"
                            variant="ghost"
                            colorScheme="blue"
                            onClick={() => handlePreviewDocument(doc)}
                          >
                            <Icon as={asElementType(FiEye)} />
                          </Button>
                        </Tooltip>
                        <Button
                          size="sm"
                          colorScheme="green"
                          leftIcon={<Icon as={asElementType(FiUploadCloud)} />}
                          onClick={() => handleSaveDocument(doc)}
                          flex={1}
                        >
                          Sauvegarder
                        </Button>
                        <Tooltip label="Supprimer">
                          <Button
                            size="sm"
                            variant="ghost"
                            colorScheme="red"
                            onClick={() => handleDeleteDocument(doc.id)}
                          >
                            <Icon as={asElementType(FiTrash2)} />
                          </Button>
                        </Tooltip>
                      </HStack>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </Box>
        )}
      </VStack>

      {/* Input file caché */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,.pdf"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />

      {/* Modal de capture caméra */}
      <Modal isOpen={isCameraOpen} onClose={() => { onCameraClose(); stopCameraStream(); }} size="xl">
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white">
          <ModalHeader>Capture avec la caméra</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {!capturedImage ? (
              <VStack spacing={4}>
                <video
                  ref={videoRef}
                  style={{
                    width: '100%',
                    maxHeight: '400px',
                    borderRadius: '8px',
                    backgroundColor: '#232946'
                  }}
                  playsInline
                />
                <Button
                  colorScheme="blue"
                  onClick={capturePhoto}
                  size="lg"
                  leftIcon={<Icon as={asElementType(FiCamera)} />}
                >
                  Capturer
                </Button>
              </VStack>
            ) : (
              <VStack spacing={4}>
                <img
                  src={capturedImage}
                  alt="Capture"
                  style={{
                    width: '100%',
                    maxHeight: '400px',
                    borderRadius: '8px'
                  }}
                />
                <HStack spacing={2}>
                  <Button
                    colorScheme="green"
                    onClick={processCameraCapture}
                    isLoading={scanning}
                    loadingText="Traitement..."
                  >
                    Valider et traiter
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setCapturedImage(null)}
                    isDisabled={scanning}
                  >
                    Reprendre
                  </Button>
                </HStack>
              </VStack>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>

      {/* Canvas caché pour capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Modal des paramètres avancés */}
      <Modal isOpen={isSettingsOpen} onClose={onSettingsClose} size="lg">
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white">
          <ModalHeader>Paramètres avancés</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={6} align="stretch">
              <FormControl>
                <FormLabel>Résolution (DPI)</FormLabel>
                <Slider
                  value={parseInt(settings.resolution)}
                  onChange={(val) => setSettings({...settings, resolution: val.toString()})}
                  min={150}
                  max={1200}
                  step={150}
                >
                  <SliderTrack>
                    <SliderFilledTrack bg="#3a8bfd" />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
                <HStack justify="space-between" mt={2} fontSize="sm" color="gray.400">
                  <Text>150 DPI</Text>
                  <Text fontWeight="bold" color="white">{settings.resolution} DPI</Text>
                  <Text>1200 DPI</Text>
                </HStack>
              </FormControl>

              <FormControl>
                <FormLabel>Qualité ({settings.quality}%)</FormLabel>
                <Slider
                  value={settings.quality}
                  onChange={(val) => setSettings({...settings, quality: val})}
                  min={50}
                  max={100}
                >
                  <SliderTrack>
                    <SliderFilledTrack bg="#3a8bfd" />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
              </FormControl>

              <HStack justify="space-between">
                <FormLabel mb={0}>Amélioration automatique</FormLabel>
                <Switch
                  isChecked={settings.autoEnhance}
                  onChange={(e) => setSettings({...settings, autoEnhance: e.target.checked})}
                  colorScheme="blue"
                />
              </HStack>

              <HStack justify="space-between">
                <FormLabel mb={0}>Reconnaissance de texte (OCR)</FormLabel>
                <Switch
                  isChecked={settings.ocrEnabled}
                  onChange={(e) => setSettings({...settings, ocrEnabled: e.target.checked})}
                  colorScheme="blue"
                />
              </HStack>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" onClick={onSettingsClose}>
              Appliquer
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Modal d'aperçu */}
      <Modal isOpen={isPreviewOpen} onClose={onPreviewClose} size="xl">
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white">
          <ModalHeader>Aperçu du document</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {previewDocument && (
              <VStack spacing={4}>
                <Text fontSize="lg" fontWeight="bold">{previewDocument.title}</Text>
                <Box
                  w="full"
                  h="400px"
                  bg="#232946"
                  borderRadius="md"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                >
                  <VStack>
                    <Icon 
                      as={asElementType(previewDocument.method === 'camera' ? FiCamera : FiFile)} 
                      boxSize={12} 
                      color="#3a8bfd" 
                    />
                    <Text color="gray.400">Aperçu non disponible</Text>
                    <Text color="gray.500" fontSize="sm">
                      Format: {previewDocument.format} | Pages: {previewDocument.pages} | Méthode: {previewDocument.method}
                    </Text>
                    {previewDocument.has_ocr && (
                      <Badge colorScheme="purple">Texte extrait par OCR</Badge>
                    )}
                  </VStack>
                </Box>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button colorScheme="blue" onClick={onPreviewClose}>
              Fermer
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  );
};

export default Scan;

