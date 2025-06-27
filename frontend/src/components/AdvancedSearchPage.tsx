import React, { useState, useEffect } from "react";
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Grid,
  GridItem,
  Input,
  Select,
  Button,
  Checkbox,
  RangeSlider,
  RangeSliderTrack,
  RangeSliderFilledTrack,
  RangeSliderThumb,
  FormControl,
  FormLabel,
  Badge,
  useToast,
  Flex,
  Icon,
  Card,
  CardBody,
  Divider,
  Switch,
  Textarea,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  useDisclosure,
} from "@chakra-ui/react";
import {
  FiSearch,
  FiFilter,
  FiCalendar,
  FiFileText,
  FiUser,
  FiTag,
  FiSettings,
  FiSave,
  FiRefreshCw
} from "react-icons/fi";
import { ElementType } from "react";
import ActionMenu from "./ActionMenu";
import DocumentPreview from "./Document/DocumentPreview";
import DocumentOCR from "./Document/DocumentOCR";
import DocumentList from "./DocumentList";
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';

interface AdvancedSearchFilters {
  query: string;
  contentSearch: string;
  documentTypes: string[];
  dateRange: {
    start: string;
    end: string;
  };
  sizeRange: {
    min: number;
    max: number;
  };
  owners: string[];
  tags: string[];
  status: string[];
  hasAttachments: boolean;
  isShared: boolean;
  isFavorite: boolean;
  language: string;
  customProperties: { [key: string]: string };
}

interface SearchResult {
  id: number;
  titre: string;
  type_document: string;
  taille_formatee: string;
  date_creation: string;
  proprietaire_nom: string;
  proprietaire_prenom: string;
  statut: string;
  relevance_score: number;
  matched_content?: string;
  highlight_snippets?: string[];
}

const AdvancedSearchPage: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [savedSearches, setSavedSearches] = useState<string[]>([]);
  const [searchName, setSearchName] = useState("");

  // Modales
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isOCROpen, onOpen: onOCROpen, onClose: onOCRClose } = useDisclosure();
  const [previewDocumentId, setPreviewDocumentId] = useState<number | null>(null);
  const [previewDocumentTitle, setPreviewDocumentTitle] = useState<string>("");
  const [ocrDocumentId, setOCRDocumentId] = useState<number | null>(null);
  const [ocrDocumentTitle, setOCRDocumentTitle] = useState<string>("");

  const [filters, setFilters] = useState<AdvancedSearchFilters>({
    query: "",
    contentSearch: "",
    documentTypes: [],
    dateRange: { start: "", end: "" },
    sizeRange: { min: 0, max: 100 },
    owners: [],
    tags: [],
    status: [],
    hasAttachments: false,
    isShared: false,
    isFavorite: false,
    language: "",
    customProperties: {}
  });

  const documentTypes = ["PDF", "DOC", "DOCX", "XLS", "XLSX", "PPT", "PPTX", "TXT", "JPG", "PNG"];
  const statusOptions = ["Actif", "Archivé", "Brouillon", "En révision"];
  const languages = ["Français", "Anglais", "Espagnol", "Allemand", "Italien"];

  const handleFilterChange = (key: keyof AdvancedSearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleAdvancedSearch = async () => {
    setIsLoading(true);
    try {
      const result = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const searchParams = new URLSearchParams();
          searchParams.append('documentTypes', filters.documentTypes.join(','));
          searchParams.append('owners', filters.owners.join(','));
          searchParams.append('tags', filters.tags.join(','));
          searchParams.append('status', filters.status.join(','));
          searchParams.append('startDate', filters.dateRange.start);
          searchParams.append('endDate', filters.dateRange.end);
          searchParams.append('minSize', filters.sizeRange.min.toString());
          searchParams.append('maxSize', filters.sizeRange.max.toString());
          searchParams.append('hasAttachments', filters.hasAttachments.toString());
          searchParams.append('isShared', filters.isShared.toString());
          searchParams.append('isFavorite', filters.isFavorite.toString());
          searchParams.append('searchTerm', filters.query);
          searchParams.append('contentSearch', filters.contentSearch);

          const response = await fetch(`${config.API_URL}/api/documents/search/advanced?${searchParams}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });

          if (!response.ok) {
            throw new Error('Erreur lors de la recherche avancée');
          }

          const data = await response.json();
          return data.results || [];
        },
        {
          loadingMessage: "Recherche en cours...",
          errorMessage: "Impossible d'effectuer la recherche"
        }
      );

      if (result) {
        setResults(result);
      }
    } catch (error) {
      // Pour le moment, on utilise des données de test
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const saveSearch = async () => {
    if (!searchName.trim()) {
      toast({
        title: "Erreur",
        description: "Veuillez saisir un nom pour la recherche sauvegardée",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/api/search/saved`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
              name: searchName,
              filters: filters
            })
          });

          if (!response.ok) {
            throw new Error('Erreur lors de la sauvegarde');
          }

          return true;
        },
        {
          loadingMessage: "Sauvegarde en cours...",
          successMessage: "Recherche sauvegardée avec succès",
          errorMessage: "Impossible de sauvegarder la recherche"
        }
      );

      setSearchName("");
      // Refresh saved searches list
    } catch (error) {
      // L'erreur est déjà gérée
    }
  };

  const resetFilters = () => {
    setFilters({
      query: "",
      contentSearch: "",
      documentTypes: [],
      dateRange: { start: "", end: "" },
      sizeRange: { min: 0, max: 100 },
      owners: [],
      tags: [],
      status: [],
      hasAttachments: false,
      isShared: false,
      isFavorite: false,
      language: "",
      customProperties: {}
    });
    setResults([]);
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

  const handleDownload = async (documentId: number) => {
    // Implémentation du téléchargement
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

  const handleEdit = (documentId: number) => {
    toast({
      title: "Modification",
      description: "La modification sera disponible prochainement",
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

  return (
    <Box p={5}>
      <Heading size="lg" color="white" mb={6}>
        <Icon as={FiSearch as ElementType} mr={3} />
        Recherche Avancée
      </Heading>

      <Grid templateColumns="1fr 2fr" gap={6} h="calc(100vh - 200px)">
        {/* Panneau de filtres */}
        <GridItem>
          <Card bg="#2a3657" h="full" overflowY="auto">
            <CardBody>
              <VStack spacing={4} align="stretch">
                <Box>
                  <FormLabel color="white" fontWeight="bold">
                    <Icon as={FiSearch as ElementType} mr={2} />
                    Recherche générale
                  </FormLabel>
                  <Input
                    placeholder="Rechercher dans les titres, descriptions..."
                    bg="#1c2338"
                    color="white"
                    borderColor="#3a445e"
                    value={filters.query}
                    onChange={(e) => handleFilterChange('query', e.target.value)}
                  />
                </Box>

                <Box>
                  <FormLabel color="white" fontWeight="bold">
                    <Icon as={FiFileText as ElementType} mr={2} />
                    Recherche dans le contenu
                  </FormLabel>
                  <Textarea
                    placeholder="Rechercher dans le contenu des documents..."
                    bg="#1c2338"
                    color="white"
                    borderColor="#3a445e"
                    value={filters.contentSearch}
                    onChange={(e) => handleFilterChange('contentSearch', e.target.value)}
                    rows={3}
                  />
                </Box>

                <Divider borderColor="#3a445e" />

                <Box>
                  <FormLabel color="white" fontWeight="bold">
                    <Icon as={FiFileText as ElementType} mr={2} />
                    Types de documents
                  </FormLabel>
                  <VStack align="stretch" spacing={1}>
                    {documentTypes.map(type => (
                      <Checkbox
                        key={type}
                        color="white"
                        isChecked={filters.documentTypes.includes(type)}
                        onChange={(e) => {
                          const newTypes = e.target.checked
                            ? [...filters.documentTypes, type]
                            : filters.documentTypes.filter(t => t !== type);
                          handleFilterChange('documentTypes', newTypes);
                        }}
                      >
                        {type}
                      </Checkbox>
                    ))}
                  </VStack>
                </Box>

                <Divider borderColor="#3a445e" />

                <Box>
                  <FormLabel color="white" fontWeight="bold">
                    <Icon as={FiCalendar as ElementType} mr={2} />
                    Période de création
                  </FormLabel>
                  <HStack>
                    <Input
                      type="date"
                      bg="#1c2338"
                      color="white"
                      borderColor="#3a445e"
                      value={filters.dateRange.start}
                      onChange={(e) => handleFilterChange('dateRange', { ...filters.dateRange, start: e.target.value })}
                    />
                    <Text color="white">à</Text>
                    <Input
                      type="date"
                      bg="#1c2338"
                      color="white"
                      borderColor="#3a445e"
                      value={filters.dateRange.end}
                      onChange={(e) => handleFilterChange('dateRange', { ...filters.dateRange, end: e.target.value })}
                    />
                  </HStack>
                </Box>

                <Box>
                  <FormLabel color="white" fontWeight="bold">
                    Taille des fichiers (MB)
                  </FormLabel>
                  <RangeSlider
                    min={0}
                    max={1000}
                    step={10}
                    value={[filters.sizeRange.min, filters.sizeRange.max]}
                    onChange={(val) => handleFilterChange('sizeRange', { min: val[0], max: val[1] })}
                  >
                    <RangeSliderTrack bg="#1c2338">
                      <RangeSliderFilledTrack bg="#3a8bfd" />
                    </RangeSliderTrack>
                    <RangeSliderThumb index={0} />
                    <RangeSliderThumb index={1} />
                  </RangeSlider>
                  <HStack justify="space-between" mt={2}>
                    <Text color="gray.400" fontSize="sm">{filters.sizeRange.min} MB</Text>
                    <Text color="gray.400" fontSize="sm">{filters.sizeRange.max} MB</Text>
                  </HStack>
                </Box>

                <Divider borderColor="#3a445e" />

                <Box>
                  <FormLabel color="white" fontWeight="bold">Options rapides</FormLabel>
                  <VStack align="stretch" spacing={2}>
                    <HStack justify="space-between">
                      <Text color="white">Documents partagés</Text>
                      <Switch
                        isChecked={filters.isShared}
                        onChange={(e) => handleFilterChange('isShared', e.target.checked)}
                      />
                    </HStack>
                    <HStack justify="space-between">
                      <Text color="white">Documents favoris</Text>
                      <Switch
                        isChecked={filters.isFavorite}
                        onChange={(e) => handleFilterChange('isFavorite', e.target.checked)}
                      />
                    </HStack>
                    <HStack justify="space-between">
                      <Text color="white">Avec pièces jointes</Text>
                      <Switch
                        isChecked={filters.hasAttachments}
                        onChange={(e) => handleFilterChange('hasAttachments', e.target.checked)}
                      />
                    </HStack>
                  </VStack>
                </Box>

                <Divider borderColor="#3a445e" />

                <Box>
                  <FormLabel color="white" fontWeight="bold">Langue</FormLabel>
                  <Select
                    placeholder="Toutes les langues"
                    bg="#1c2338"
                    color="white"
                    borderColor="#3a445e"
                    value={filters.language}
                    onChange={(e) => handleFilterChange('language', e.target.value)}
                  >
                    {languages.map(lang => (
                      <option key={lang} value={lang}>{lang}</option>
                    ))}
                  </Select>
                </Box>

                <Divider borderColor="#3a445e" />

                <VStack spacing={3}>
                  <HStack w="full">
                    <Input
                      placeholder="Nom de la recherche sauvegardée"
                      bg="#1c2338"
                      color="white"
                      borderColor="#3a445e"
                      value={searchName}
                      onChange={(e) => setSearchName(e.target.value)}
                      size="sm"
                    />
                    <Button
                      size="sm"
                      leftIcon={<Icon as={FiSave as ElementType} />}
                      colorScheme="green"
                      onClick={saveSearch}
                    >
                      Sauver
                    </Button>
                  </HStack>

                  <HStack w="full" spacing={2}>
                    <Button
                      leftIcon={<Icon as={FiSearch as ElementType} />}
                      colorScheme="blue"
                      onClick={handleAdvancedSearch}
                      isLoading={isLoading}
                      flex={1}
                    >
                      Rechercher
                    </Button>
                    <Button
                      leftIcon={<Icon as={FiRefreshCw as ElementType} />}
                      variant="outline"
                      onClick={resetFilters}
                    >
                      Reset
                    </Button>
                  </HStack>
                </VStack>
              </VStack>
            </CardBody>
          </Card>
        </GridItem>

        {/* Résultats de recherche */}
        <GridItem>
          <Card bg="#2a3657" h="full">
            <CardBody>
              <VStack spacing={4} align="stretch" h="full">
                <Flex justify="space-between" align="center">
                  <Text color="white" fontWeight="bold">
                    Résultats de recherche ({results.length})
                  </Text>
                  {results.length > 0 && (
                    <Badge colorScheme="blue">
                      {results.length} document{results.length > 1 ? 's' : ''} trouvé{results.length > 1 ? 's' : ''}
                    </Badge>
                  )}
                </Flex>

                {results.length > 0 ? (
                  <Box overflowY="auto" flex={1}>
                    <DocumentList
                      documents={results.map(doc => ({
                        id: doc.id,
                        titre: doc.titre,
                        type_document: doc.type_document,
                        taille_formatee: doc.taille_formatee,
                        date_creation: doc.date_creation,
                        proprietaire_nom: doc.proprietaire_nom,
                        proprietaire_prenom: doc.proprietaire_prenom,
                        statut: doc.statut
                      }))}
                      onPreview={handleShowPreview}
                      onOCR={handleShowOCR}
                      onDownload={handleDownload}
                      onShare={handleShare}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                    />
                  </Box>
                ) : (
                  <Flex
                    flex={1}
                    align="center"
                    justify="center"
                    direction="column"
                    color="gray.400"
                  >
                    <Icon as={FiSearch as ElementType} boxSize={12} mb={4} />
                    <Text>Aucun résultat trouvé</Text>
                    <Text fontSize="sm">Essayez de modifier vos critères de recherche</Text>
                  </Flex>
                )}
              </VStack>
            </CardBody>
          </Card>
        </GridItem>
      </Grid>

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

export default AdvancedSearchPage; 


