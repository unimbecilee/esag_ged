import React, { useState, useEffect } from "react";
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Grid,
  GridItem,
  Card,
  CardBody,
  CardHeader,
  Button,
  Select,
  Checkbox,
  Progress,
  useToast,
  Flex,
  Icon,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Input,
  InputGroup,
  InputLeftElement,
  Textarea,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  Switch,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Spinner,
  Divider,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Tooltip,
} from "@chakra-ui/react";
import {
  FiFolder,
  FiFileText,
  FiTag,
  FiArchive,
  FiEye,
  FiDownload,
  FiShare2,
  FiSettings,
  FiPlay,
  FiPause,
  FiStopCircle,
  FiCheck,
  FiX,
  FiImage,
  FiVideo,
  FiFile,
  FiUpload,
  FiSearch,
  FiFilter,
  FiLayers,
  FiTrendingUp,
  FiClock,
  FiAlertCircle,
  FiBarChart2,
  FiRefreshCw,
  FiChevronDown,
  FiChevronUp,
} from "react-icons/fi";
import { ElementType } from "react";
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';

interface BatchOperation {
  id: string;
  name: string;
  type: 'tag' | 'move' | 'archive' | 'delete' | 'ocr' | 'convert' | 'metadata';
  status: 'pending' | 'running' | 'paused' | 'completed' | 'error';
  progress: number;
  totalDocuments: number;
  processedDocuments: number;
  failedDocuments: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  parameters: any;
  results?: {
    success: number;
    failed: number;
    errors: string[];
  };
}

interface Document {
  id: number;
  titre: string;
  type_document: string;
  taille_formatee: string;
  date_creation: string;
  selected: boolean;
}

const BatchOperations: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [operations, setOperations] = useState<BatchOperation[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<Document[]>([]);
  const [availableDocuments, setAvailableDocuments] = useState<Document[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Configuration de l'opération
  const [operationType, setOperationType] = useState<string>("");
  const [operationParams, setOperationParams] = useState<any>({});
  const [operationName, setOperationName] = useState("");

  useEffect(() => {
    fetchDocuments();
    fetchOperations();
  }, []);

  const fetchDocuments = async () => {
    try {
      const result = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) throw new Error('Token non trouvé');

          const response = await fetch(`${config.API_URL}/documents?limit=100`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });

          if (!response.ok) throw new Error('Erreur lors de la récupération des documents');
          const data = await response.json();
          return data.documents || [];
        },
        {
          loadingMessage: "Chargement des documents...",
          errorMessage: "Impossible de charger les documents"
        }
      );

      if (result) {
        const documentsWithSelection = result.map((doc: any) => ({
          ...doc,
          selected: false
        }));
        setAvailableDocuments(documentsWithSelection);
      }
    } catch (err) {
      // Données de test
      setAvailableDocuments([
        { id: 1, titre: "Document 1", type_document: "PDF", taille_formatee: "2.5 MB", date_creation: "2024-01-01", selected: false },
        { id: 2, titre: "Document 2", type_document: "DOC", taille_formatee: "1.2 MB", date_creation: "2024-01-02", selected: false },
        { id: 3, titre: "Document 3", type_document: "XLS", taille_formatee: "856 KB", date_creation: "2024-01-03", selected: false },
      ]);
    }
  };

  const fetchOperations = async () => {
    try {
      const result = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) throw new Error('Token non trouvé');

          const response = await fetch(`${config.API_URL}/api/batch-operations`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });

          if (!response.ok) throw new Error('Erreur lors de la récupération des opérations');
          return await response.json();
        },
        {
          errorMessage: "Impossible de charger les opérations"
        }
      );

      if (result) {
        setOperations(result.operations || []);
      }
    } catch (err) {
      // Données de test
      setOperations([]);
    }
  };

  const toggleDocumentSelection = (documentId: number) => {
    setAvailableDocuments(prev => 
      prev.map(doc => 
        doc.id === documentId ? { ...doc, selected: !doc.selected } : doc
      )
    );
  };

  const selectAllDocuments = () => {
    const filteredDocs = getFilteredDocuments();
    const allSelected = filteredDocs.every(doc => doc.selected);
    
    setAvailableDocuments(prev => 
      prev.map(doc => {
        if (filteredDocs.find(fd => fd.id === doc.id)) {
          return { ...doc, selected: !allSelected };
        }
        return doc;
      })
    );
  };

  const getFilteredDocuments = () => {
    return availableDocuments.filter(doc =>
      doc.titre.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.type_document.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const getSelectedDocuments = () => {
    return availableDocuments.filter(doc => doc.selected);
  };

  const createBatchOperation = async () => {
    const selected = getSelectedDocuments();
    if (selected.length === 0) {
      toast({
        title: "Erreur",
        description: "Veuillez sélectionner au moins un document",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (!operationType || !operationName) {
      toast({
        title: "Erreur",
        description: "Veuillez configurer l'opération",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    const newOperation: BatchOperation = {
      id: `batch-${Date.now()}`,
      name: operationName,
      type: operationType as any,
      status: 'pending',
      progress: 0,
      totalDocuments: selected.length,
      processedDocuments: 0,
      failedDocuments: 0,
      createdAt: new Date().toISOString(),
      parameters: operationParams
    };

    setOperations(prev => [...prev, newOperation]);
    onClose();

    // Lancer l'opération
    await executeBatchOperation(newOperation, selected);
  };

  const executeBatchOperation = async (operation: BatchOperation, documents: Document[]) => {
    try {
      // Marquer comme en cours
      setOperations(prev => prev.map(op => 
        op.id === operation.id ? { ...op, status: 'running' as const, startedAt: new Date().toISOString() } : op
      ));

      await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) throw new Error('Token non trouvé');

          // Simulation de progression
          for (let i = 0; i <= 100; i += 10) {
            setOperations(prev => prev.map(op => 
              op.id === operation.id ? { 
                ...op, 
                progress: i,
                processedDocuments: Math.floor((i / 100) * operation.totalDocuments)
              } : op
            ));
            await new Promise(resolve => setTimeout(resolve, 300));
          }

          const response = await fetch(`${config.API_URL}/api/batch-operations`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
              type: operation.type,
              documentIds: documents.map(d => d.id),
              parameters: operation.parameters
            })
          });

          if (!response.ok) throw new Error('Erreur lors de l\'exécution');
          return await response.json();
        },
        {
          loadingMessage: `Exécution de l'opération: ${operation.name}`,
          successMessage: "Opération terminée avec succès",
          errorMessage: "Erreur lors de l'exécution"
        }
      );

      // Marquer comme terminé
      setOperations(prev => prev.map(op => 
        op.id === operation.id ? { 
          ...op, 
          status: 'completed' as const,
          progress: 100,
          processedDocuments: operation.totalDocuments,
          completedAt: new Date().toISOString(),
          results: {
            success: operation.totalDocuments - 1,
            failed: 1,
            errors: ['Exemple d\'erreur sur un document']
          }
        } : op
      ));

    } catch (error) {
      setOperations(prev => prev.map(op => 
        op.id === operation.id ? { 
          ...op, 
          status: 'error' as const,
          results: {
            success: 0,
            failed: operation.totalDocuments,
            errors: [error instanceof Error ? error.message : 'Erreur inconnue']
          }
        } : op
      ));
    }
  };

  const pauseOperation = (operationId: string) => {
    setOperations(prev => prev.map(op => 
      op.id === operationId ? { ...op, status: 'paused' as const } : op
    ));
  };

  const stopOperation = (operationId: string) => {
    setOperations(prev => prev.map(op => 
      op.id === operationId ? { ...op, status: 'error' as const } : op
    ));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'running': return 'blue';
      case 'paused': return 'orange';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return FiCheck;
      case 'running': return FiPlay;
      case 'paused': return FiPause;
      case 'error': return FiX;
      default: return FiClock;
    }
  };

  const getOperationTypeLabel = (type: string) => {
    switch (type) {
      case 'tag': return 'Étiquetage';
      case 'move': return 'Déplacement';
      case 'archive': return 'Archivage';
      case 'delete': return 'Suppression';
      case 'ocr': return 'OCR';
      case 'convert': return 'Conversion';
      case 'metadata': return 'Métadonnées';
      default: return type;
    }
  };

  const renderOperationConfig = () => {
    switch (operationType) {
      case 'tag':
        return (
          <FormControl>
            <FormLabel color="white">Tags à ajouter</FormLabel>
            <Input
              placeholder="Séparez les tags par des virgules"
              bg="#1c2338"
              color="white"
              borderColor="#3a445e"
              value={operationParams.tags || ''}
              onChange={(e) => setOperationParams({ ...operationParams, tags: e.target.value })}
            />
          </FormControl>
        );
      case 'move':
        return (
          <FormControl>
            <FormLabel color="white">Dossier de destination</FormLabel>
            <Select
              placeholder="Choisir un dossier"
              bg="#1c2338"
              color="white"
              borderColor="#3a445e"
              value={operationParams.folderId || ''}
              onChange={(e) => setOperationParams({ ...operationParams, folderId: e.target.value })}
            >
              <option value="1">Documents</option>
              <option value="2">Archives</option>
              <option value="3">Projets</option>
            </Select>
          </FormControl>
        );
      case 'convert':
        return (
          <FormControl>
            <FormLabel color="white">Format de conversion</FormLabel>
            <Select
              placeholder="Choisir un format"
              bg="#1c2338"
              color="white"
              borderColor="#3a445e"
              value={operationParams.targetFormat || ''}
              onChange={(e) => setOperationParams({ ...operationParams, targetFormat: e.target.value })}
            >
              <option value="pdf">PDF</option>
              <option value="docx">DOCX</option>
              <option value="jpg">JPG</option>
              <option value="png">PNG</option>
            </Select>
          </FormControl>
        );
      default:
        return null;
    }
  };

  return (
    <Box p={5}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          <Icon as={FiLayers as ElementType} mr={3} />
          Traitement par Lots
        </Heading>
        <Button
          leftIcon={<Icon as={FiPlay as ElementType} />}
          colorScheme="blue"
          onClick={onOpen}
          isDisabled={getSelectedDocuments().length === 0}
        >
          Nouvelle Opération
        </Button>
      </Flex>

      <Grid templateColumns="1fr 1fr" gap={6} mb={8}>
        {/* Sélection des documents */}
        <Card bg="#2a3657" borderColor="#3a445e">
          <CardHeader>
            <Flex justify="space-between" align="center">
              <Heading size="md" color="white">
                Sélection des Documents
              </Heading>
              <Badge colorScheme="blue">
                {getSelectedDocuments().length} sélectionné(s)
              </Badge>
            </Flex>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <HStack>
                <InputGroup>
                  <InputLeftElement>
                    <Icon as={FiFilter as ElementType} color="gray.400" />
                  </InputLeftElement>
                  <Input
                    placeholder="Rechercher des documents..."
                    bg="#1c2338"
                    color="white"
                    borderColor="#3a445e"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </InputGroup>
                <Button size="sm" onClick={selectAllDocuments}>
                  Tout sélectionner
                </Button>
              </HStack>

              <Box maxH="400px" overflowY="auto">
                <Table variant="simple" size="sm">
                  <Thead>
                    <Tr>
                      <Th color="gray.400" w="40px"></Th>
                      <Th color="gray.400">Document</Th>
                      <Th color="gray.400">Type</Th>
                      <Th color="gray.400">Taille</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {getFilteredDocuments().map((doc) => (
                      <Tr key={doc.id} _hover={{ bg: "#374269" }}>
                        <Td>
                          <Checkbox
                            isChecked={doc.selected}
                            onChange={() => toggleDocumentSelection(doc.id)}
                          />
                        </Td>
                        <Td color="white" fontSize="sm">{doc.titre}</Td>
                        <Td>
                          <Badge size="sm" colorScheme="blue">{doc.type_document}</Badge>
                        </Td>
                        <Td color="gray.400" fontSize="sm">{doc.taille_formatee}</Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
            </VStack>
          </CardBody>
        </Card>

        {/* Statistiques rapides */}
        <Card bg="#2a3657" borderColor="#3a445e">
          <CardHeader>
            <Heading size="md" color="white">
              Statistiques
            </Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4}>
              <HStack justify="space-between" w="full">
                <Text color="gray.400">Total documents:</Text>
                <Text color="white" fontWeight="bold">{availableDocuments.length}</Text>
              </HStack>
              <HStack justify="space-between" w="full">
                <Text color="gray.400">Sélectionnés:</Text>
                <Text color="blue.400" fontWeight="bold">{getSelectedDocuments().length}</Text>
              </HStack>
              <HStack justify="space-between" w="full">
                <Text color="gray.400">Opérations actives:</Text>
                <Text color="orange.400" fontWeight="bold">
                  {operations.filter(op => op.status === 'running' || op.status === 'paused').length}
                </Text>
              </HStack>
              <HStack justify="space-between" w="full">
                <Text color="gray.400">Terminées:</Text>
                <Text color="green.400" fontWeight="bold">
                  {operations.filter(op => op.status === 'completed').length}
                </Text>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </Grid>

      {/* Historique des opérations */}
      <Card bg="#2a3657" borderColor="#3a445e">
        <CardHeader>
          <Heading size="md" color="white">
            Historique des Opérations
          </Heading>
        </CardHeader>
        <CardBody>
          {operations.length === 0 ? (
            <Flex
              justify="center"
              align="center"
              direction="column"
              h="200px"
              color="gray.400"
            >
              <Icon as={FiLayers as ElementType} boxSize={12} mb={4} />
              <Text>Aucune opération en cours</Text>
            </Flex>
          ) : (
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th color="gray.400">Nom</Th>
                  <Th color="gray.400">Type</Th>
                  <Th color="gray.400">Statut</Th>
                  <Th color="gray.400">Progression</Th>
                  <Th color="gray.400">Documents</Th>
                  <Th color="gray.400">Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {operations.map((op) => (
                  <Tr key={op.id}>
                    <Td color="white">{op.name}</Td>
                    <Td>
                      <Badge colorScheme="purple">
                        {getOperationTypeLabel(op.type)}
                      </Badge>
                    </Td>
                    <Td>
                      <Badge colorScheme={getStatusColor(op.status)}>
                        <Icon as={getStatusIcon(op.status) as ElementType} mr={1} />
                        {op.status}
                      </Badge>
                    </Td>
                    <Td>
                      <Box w="100px">
                        <Progress value={op.progress} colorScheme={getStatusColor(op.status)} size="sm" />
                        <Text fontSize="xs" color="gray.400" mt={1}>
                          {op.processedDocuments}/{op.totalDocuments}
                        </Text>
                      </Box>
                    </Td>
                    <Td color="white">{op.totalDocuments}</Td>
                    <Td>
                      <HStack spacing={1}>
                        {op.status === 'running' && (
                          <>
                            <Button
                              size="xs"
                              leftIcon={<Icon as={FiPause as ElementType} />}
                              onClick={() => pauseOperation(op.id)}
                            >
                              Pause
                            </Button>
                            <Button
                              size="xs"
                              colorScheme="red"
                              leftIcon={<Icon as={FiStopCircle as ElementType} />}
                              onClick={() => stopOperation(op.id)}
                            >
                              Arrêter
                            </Button>
                          </>
                        )}
                      </HStack>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>

      {/* Modal de configuration d'opération */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent bg="#2a3657" color="white">
          <ModalHeader>Nouvelle Opération par Lots</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Alert status="info" bg="#1c2338" borderColor="#3a445e">
                <AlertIcon color="#3a8bfd" />
                <Box>
                  <AlertTitle>Documents sélectionnés:</AlertTitle>
                  <AlertDescription>
                    {getSelectedDocuments().length} document(s) sera(ont) traité(s)
                  </AlertDescription>
                </Box>
              </Alert>

              <FormControl>
                <FormLabel color="white">Nom de l'opération</FormLabel>
                <Input
                  placeholder="Ex: Archivage documents Q1 2024"
                  bg="#1c2338"
                  color="white"
                  borderColor="#3a445e"
                  value={operationName}
                  onChange={(e) => setOperationName(e.target.value)}
                />
              </FormControl>

              <FormControl>
                <FormLabel color="white">Type d'opération</FormLabel>
                <Select
                  placeholder="Choisir une opération"
                  bg="#1c2338"
                  color="white"
                  borderColor="#3a445e"
                  value={operationType}
                  onChange={(e) => {
                    setOperationType(e.target.value);
                    setOperationParams({});
                  }}
                >
                  <option value="tag">Ajouter des tags</option>
                  {/* Option Déplacer désactivée temporairement
                  <option value="move">Déplacer vers un dossier</option>
                  */}
                  <option value="archive">Archiver</option>
                  <option value="delete">Supprimer</option>
                  <option value="ocr">Extraction OCR</option>
                  <option value="convert">Conversion de format</option>
                  <option value="metadata">Mise à jour métadonnées</option>
                </Select>
              </FormControl>

              {renderOperationConfig()}
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Annuler
            </Button>
            <Button 
              colorScheme="blue" 
              onClick={createBatchOperation}
              isDisabled={!operationType || !operationName}
            >
              Lancer l'opération
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default BatchOperations; 


