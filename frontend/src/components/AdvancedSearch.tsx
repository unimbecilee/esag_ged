import React, { useState, useEffect } from 'react';
import {
  Box,
  Flex,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Input,
  Select,
  FormControl,
  FormLabel,
  Checkbox,
  CheckboxGroup,
  RangeSlider,
  RangeSliderTrack,
  RangeSliderFilledTrack,
  RangeSliderThumb,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Icon,
  Alert,
  AlertIcon,
  Spinner,
  Wrap,
  WrapItem,
  Tag,
  TagLabel,
  TagCloseButton,
  Divider,
  Collapse,
  IconButton,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
} from '@chakra-ui/react';
import {
  FiSearch,
  FiFilter,
  FiX,
  FiDownload,
  FiShare2,
  FiEye,
  FiChevronDown,
  FiChevronUp,
  FiCalendar,
  FiFileText,
  FiTag as FiTagIcon
} from 'react-icons/fi';
import { asElementType } from '../utils/iconUtils';
import config from '../config';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import ActionMenu from './ActionMenu';
import DocumentPreview from './Document/DocumentPreview';
import DocumentOCR from './Document/DocumentOCR';

interface SearchFilters {
  query: string;
  tags: number[];
  tagOperator: 'AND' | 'OR';
  dateFrom: string;
  dateTo: string;
  fileTypes: string[];
  categories: string[];
  minSize: number;
  maxSize: number;
  owner: string;
}

interface SearchResult {
  id: number;
  titre: string;
  categorie: string;
  mime_type: string;
  taille: number;
  date_ajout: string;
  derniere_modification: string;
  description: string;
  proprietaire_nom: string;
  proprietaire_prenom: string;
  tags: Array<{
    id: number;
    nom: string;
    couleur: string;
  }>;
}

interface AvailableTag {
  id: number;
  nom: string;
  couleur: string;
  usage_count: number;
}

const AdvancedSearch: React.FC = () => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    tags: [],
    tagOperator: 'AND',
    dateFrom: '',
    dateTo: '',
    fileTypes: [],
    categories: [],
    minSize: 0,
    maxSize: 100, // MB
    owner: ''
  });

  const [results, setResults] = useState<SearchResult[]>([]);
  const [availableTags, setAvailableTags] = useState<AvailableTag[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isOCROpen, onOpen: onOCROpen, onClose: onOCRClose } = useDisclosure();
  const [previewDocument, setPreviewDocument] = useState<SearchResult | null>(null);
  const [previewDocumentId, setPreviewDocumentId] = useState<number | null>(null);
  const [previewDocumentTitle, setPreviewDocumentTitle] = useState<string>("");
  const [ocrDocumentId, setOCRDocumentId] = useState<number | null>(null);
  const [ocrDocumentTitle, setOCRDocumentTitle] = useState<string>("");

  const fileTypeOptions = [
    { value: 'application/pdf', label: 'PDF' },
    { value: 'application/msword', label: 'Word' },
    { value: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', label: 'Word (DOCX)' },
    { value: 'application/vnd.ms-excel', label: 'Excel' },
    { value: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', label: 'Excel (XLSX)' },
    { value: 'image/jpeg', label: 'JPEG' },
    { value: 'image/png', label: 'PNG' },
    { value: 'text/plain', label: 'Texte' }
  ];

  const categoryOptions = [
    'Contrat',
    'Facture',
    'Rapport',
    'Présentation',
    'Manuel',
    'Procédure',
    'Formulaire',
    'Autre'
  ];

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR');
  };

  const fetchAvailableTags = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/tags`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableTags(data.tags || []);
      }
    } catch (error) {
      console.error('Erreur tags:', error);
    }
  };

  const performSearch = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      
      // Construire les paramètres de recherche
      const searchParams = new URLSearchParams();
      
      if (filters.query) searchParams.append('q', filters.query);
      if (filters.dateFrom) searchParams.append('date_from', filters.dateFrom);
      if (filters.dateTo) searchParams.append('date_to', filters.dateTo);
      if (filters.fileTypes.length > 0) searchParams.append('file_types', filters.fileTypes.join(','));
      if (filters.categories.length > 0) searchParams.append('categories', filters.categories.join(','));
      if (filters.minSize > 0) searchParams.append('min_size', (filters.minSize * 1024 * 1024).toString());
      if (filters.maxSize < 100) searchParams.append('max_size', (filters.maxSize * 1024 * 1024).toString());
      if (filters.owner) searchParams.append('owner', filters.owner);

      let searchUrl = `${config.API_URL}/search?${searchParams.toString()}`;
      
      // Si on a des tags, utiliser l'endpoint de recherche par tags
      if (filters.tags.length > 0) {
        const response = await fetch(`${config.API_URL}/documents/search-by-tags`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            tag_ids: filters.tags,
            operator: filters.tagOperator
          })
        });

        if (response.ok) {
          const data = await response.json();
          setResults(data.documents || []);
          setTotalResults(data.total || 0);
        } else {
          throw new Error('Erreur lors de la recherche par tags');
        }
      } else {
        // Recherche classique
        const response = await fetch(searchUrl, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          setResults(data.documents || []);
          setTotalResults(data.total || 0);
        } else {
          throw new Error('Erreur lors de la recherche');
        }
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Erreur lors de la recherche',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTagAdd = (tagId: number) => {
    if (!filters.tags.includes(tagId)) {
      setFilters(prev => ({
        ...prev,
        tags: [...prev.tags, tagId]
      }));
    }
  };

  const handleTagRemove = (tagId: number) => {
    setFilters(prev => ({
      ...prev,
      tags: prev.tags.filter(id => id !== tagId)
    }));
  };

  const clearFilters = () => {
    setFilters({
      query: '',
      tags: [],
      tagOperator: 'AND',
      dateFrom: '',
      dateTo: '',
      fileTypes: [],
      categories: [],
      minSize: 0,
      maxSize: 100,
      owner: ''
    });
    setResults([]);
    setTotalResults(0);
  };

  const handleShowPreview = (documentId: number, title?: string) => {
    setPreviewDocumentId(documentId);
    setPreviewDocumentTitle(title || `Document ${documentId}`);
    onPreviewOpen();
  };

  const handleShowOCR = (documentId: number, title?: string) => {
    setOCRDocumentId(documentId);
    setOCRDocumentTitle(title || `Document ${documentId}`);
    onOCROpen();
  };

  const handleEdit = (documentId: number) => {
    toast({
      title: "Modification",
      description: "La modification sera disponible prochainement",
      status: "info",
      duration: 3000,
      isClosable: true,
    });
  };

  const handleShare = (documentId: number) => {
    toast({
      title: "Partage",
      description: "Le partage sera disponible prochainement",
      status: "info",
      duration: 3000,
      isClosable: true,
    });
  };

  const handleDelete = (documentId: number) => {
    toast({
      title: "Suppression",
      description: "La suppression sera disponible prochainement",
      status: "info",
      duration: 3000,
      isClosable: true,
    });
  };

  const handleDownload = async (documentId: number) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `document_${documentId}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        throw new Error('Erreur lors du téléchargement');
      }
    }, {
      loadingMessage: 'Téléchargement en cours...',
      successMessage: 'Document téléchargé avec succès',
      errorMessage: 'Erreur lors du téléchargement'
    });
  };

  useEffect(() => {
    fetchAvailableTags();
  }, []);

  return (
    <Box p={6} bg="#181c2f" minH="100vh" color="white">
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          <Flex align="center" gap={3}>
            <Icon as={asElementType(FiSearch)} color="#3a8bfd" />
            Recherche avancée
          </Flex>
        </Heading>
        
        <Button
          leftIcon={<Icon as={asElementType(FiFilter)} />}
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
        >
          {showFilters ? 'Masquer' : 'Afficher'} les filtres
        </Button>
      </Flex>

      {/* Barre de recherche principale */}
      <Box mb={6} p={4} bg="#20243a" borderRadius="md">
        <HStack spacing={4}>
          <Input
            placeholder="Rechercher dans les documents..."
            value={filters.query}
            onChange={(e) => setFilters(prev => ({ ...prev, query: e.target.value }))}
            bg="#2a3657"
            borderColor="#3a445e"
            size="lg"
          />
          <Button
            leftIcon={<Icon as={asElementType(FiSearch)} />}
            colorScheme="blue"
            size="lg"
            onClick={performSearch}
            isLoading={loading}
          >
            Rechercher
          </Button>
          <Button
            leftIcon={<Icon as={asElementType(FiX)} />}
            variant="outline"
            size="lg"
            onClick={clearFilters}
          >
            Effacer
          </Button>
        </HStack>
      </Box>

      {/* Filtres avancés */}
      <Collapse in={showFilters} animateOpacity>
        <Box mb={6} p={6} bg="#20243a" borderRadius="md">
          <VStack align="stretch" spacing={6}>
            {/* Tags */}
            <Box>
              <FormLabel mb={3}>
                <Flex align="center" gap={2}>
                  <Icon as={asElementType(FiTagIcon)} />
                  Tags
                </Flex>
              </FormLabel>
              
              {/* Tags sélectionnés */}
              {filters.tags.length > 0 && (
                <Box mb={3}>
                  <Text fontSize="sm" mb={2}>Tags sélectionnés:</Text>
                  <Wrap spacing={2}>
                    {filters.tags.map(tagId => {
                      const tag = availableTags.find(t => t.id === tagId);
                      return tag ? (
                        <WrapItem key={tagId}>
                          <Tag bg={tag.couleur} color="white">
                            <TagLabel>{tag.nom}</TagLabel>
                            <TagCloseButton onClick={() => handleTagRemove(tagId)} />
                          </Tag>
                        </WrapItem>
                      ) : null;
                    })}
                  </Wrap>
                  
                  <HStack mt={2}>
                    <Text fontSize="sm">Opérateur:</Text>
                    <Select
                      value={filters.tagOperator}
                      onChange={(e) => setFilters(prev => ({ ...prev, tagOperator: e.target.value as 'AND' | 'OR' }))}
                      size="sm"
                      w="100px"
                      bg="#2a3657"
                    >
                      <option value="AND">ET (tous)</option>
                      <option value="OR">OU (au moins un)</option>
                    </Select>
                  </HStack>
                </Box>
              )}
              
              {/* Tags disponibles */}
              <Box>
                <Text fontSize="sm" mb={2}>Tags disponibles:</Text>
                <Wrap spacing={2} maxH="150px" overflowY="auto">
                  {availableTags.map(tag => (
                    <WrapItem key={tag.id}>
                      <Tag
                        bg={tag.couleur}
                        color="white"
                        cursor="pointer"
                        opacity={filters.tags.includes(tag.id) ? 0.5 : 1}
                        onClick={() => handleTagAdd(tag.id)}
                        _hover={{ opacity: 0.8 }}
                      >
                        <TagLabel>{tag.nom} ({tag.usage_count})</TagLabel>
                      </Tag>
                    </WrapItem>
                  ))}
                </Wrap>
              </Box>
            </Box>

            <Divider />

            {/* Dates */}
            <HStack spacing={4}>
              <FormControl>
                <FormLabel>Date de début</FormLabel>
                <Input
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters(prev => ({ ...prev, dateFrom: e.target.value }))}
                  bg="#2a3657"
                  borderColor="#3a445e"
                />
              </FormControl>
              <FormControl>
                <FormLabel>Date de fin</FormLabel>
                <Input
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => setFilters(prev => ({ ...prev, dateTo: e.target.value }))}
                  bg="#2a3657"
                  borderColor="#3a445e"
                />
              </FormControl>
            </HStack>

            <Divider />

            {/* Types de fichiers */}
            <FormControl>
              <FormLabel>Types de fichiers</FormLabel>
              <CheckboxGroup
                value={filters.fileTypes}
                onChange={(values) => setFilters(prev => ({ ...prev, fileTypes: values as string[] }))}
              >
                <Wrap spacing={4}>
                  {fileTypeOptions.map(option => (
                    <WrapItem key={option.value}>
                      <Checkbox value={option.value} colorScheme="blue">
                        {option.label}
                      </Checkbox>
                    </WrapItem>
                  ))}
                </Wrap>
              </CheckboxGroup>
            </FormControl>

            <Divider />

            {/* Catégories */}
            <FormControl>
              <FormLabel>Catégories</FormLabel>
              <CheckboxGroup
                value={filters.categories}
                onChange={(values) => setFilters(prev => ({ ...prev, categories: values as string[] }))}
              >
                <Wrap spacing={4}>
                  {categoryOptions.map(category => (
                    <WrapItem key={category}>
                      <Checkbox value={category} colorScheme="blue">
                        {category}
                      </Checkbox>
                    </WrapItem>
                  ))}
                </Wrap>
              </CheckboxGroup>
            </FormControl>

            <Divider />

            {/* Taille des fichiers */}
            <FormControl>
              <FormLabel>Taille des fichiers (MB): {filters.minSize} - {filters.maxSize}</FormLabel>
              <RangeSlider
                value={[filters.minSize, filters.maxSize]}
                onChange={(values) => setFilters(prev => ({ ...prev, minSize: values[0], maxSize: values[1] }))}
                min={0}
                max={100}
                step={1}
                colorScheme="blue"
              >
                <RangeSliderTrack>
                  <RangeSliderFilledTrack />
                </RangeSliderTrack>
                <RangeSliderThumb index={0} />
                <RangeSliderThumb index={1} />
              </RangeSlider>
            </FormControl>
          </VStack>
        </Box>
      </Collapse>

      {/* Résultats */}
      <Box>
        {totalResults > 0 && (
          <Text mb={4} color="gray.300">
            {totalResults} résultat{totalResults > 1 ? 's' : ''} trouvé{totalResults > 1 ? 's' : ''}
          </Text>
        )}

        {loading ? (
          <Flex justify="center" py={8}>
            <Spinner color="#3a8bfd" size="xl" />
          </Flex>
        ) : results.length === 0 && totalResults === 0 ? (
          <Alert status="info" bg="#2a3657" color="white">
            <AlertIcon color="#3a8bfd" />
            Aucun résultat trouvé. Essayez de modifier vos critères de recherche.
          </Alert>
        ) : (
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">Document</Th>
                <Th color="white">Catégorie</Th>
                <Th color="white">Taille</Th>
                <Th color="white">Propriétaire</Th>
                <Th color="white">Date</Th>
                <Th color="white">Tags</Th>
                <Th color="white">Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {results.map((doc) => (
                <Tr key={doc.id}>
                  <Td>
                    <VStack align="start" spacing={1}>
                      <Text fontWeight="bold">{doc.titre}</Text>
                      {doc.description && (
                        <Text fontSize="sm" color="gray.400" noOfLines={2}>
                          {doc.description}
                        </Text>
                      )}
                    </VStack>
                  </Td>
                  <Td>
                    <Badge colorScheme="blue">{doc.categorie}</Badge>
                  </Td>
                  <Td>{formatFileSize(doc.taille)}</Td>
                  <Td>
                    <Text fontSize="sm">
                      {doc.proprietaire_prenom} {doc.proprietaire_nom}
                    </Text>
                  </Td>
                  <Td>
                    <Text fontSize="sm">{formatDate(doc.derniere_modification)}</Text>
                  </Td>
                  <Td>
                    <Wrap spacing={1}>
                      {doc.tags?.map(tag => (
                        <WrapItem key={tag.id}>
                          <Tag size="sm" bg={tag.couleur} color="white">
                            {tag.nom}
                          </Tag>
                        </WrapItem>
                      ))}
                    </Wrap>
                  </Td>
                  <Td>
                    <ActionMenu
                      documentId={doc.id}
                      documentTitle={doc.titre}
                      onDownload={handleDownload}
                      onShare={handleShare}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                      onShowPreview={handleShowPreview}
                      onShowOCR={handleShowOCR}
                    />
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </Box>

      {/* Document Preview Modal */}
      {previewDocumentId && (
        <DocumentPreview
          isOpen={isPreviewOpen}
          onClose={onPreviewClose}
          documentId={previewDocumentId}
          documentTitle={previewDocumentTitle}
        />
      )}

      {/* Document OCR Modal */}
      {ocrDocumentId && (
        <DocumentOCR
          isOpen={isOCROpen}
          onClose={onOCRClose}
          documentId={ocrDocumentId}
          documentTitle={ocrDocumentTitle}
        />
      )}
    </Box>
  );
};

export default AdvancedSearch; 