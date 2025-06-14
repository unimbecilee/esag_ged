import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Heading,
  Input,
  InputGroup,
  InputLeftElement,
  InputRightElement,
  Icon,
  VStack,
  Text,
  Button,
  Flex,
  Card,
  CardBody,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  useToast,
  Spinner,
  Select,
  HStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Stat,
  StatLabel,
  StatNumber,
  SimpleGrid,
  Tooltip,
  IconButton,
} from "@chakra-ui/react";
import { 
  FiSearch, 
  FiFileText, 
  FiClock, 
  FiUser, 
  FiFolder, 
  FiBriefcase, 
  FiGitBranch,
  FiTag,
  FiActivity,
  FiFilter,
  FiX
} from "react-icons/fi";
import { ElementType } from "react";
import config from "../config";

interface SearchResult {
  id: number;
  title: string;
  titre: string;
  description?: string;
  category: string;
  type_document: string;
  file_type: string;
  date_creation: string;
  size_formatted: string;
  taille_formatee: string;
  owner_firstname: string;
  owner_lastname: string;
  proprietaire_prenom: string;
  proprietaire_nom: string;
  entity_type: string;
  entity_label: string;
  highlights: string[];
  type: string;
}

interface EntityStats {
  [key: string]: {
    label: string;
    count: number;
  };
}

interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  entity_stats: EntityStats;
  message?: string;
}

const SearchPage: React.FC = () => {
  const toast = useToast();
  
  const [searchTerm, setSearchTerm] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [entityStats, setEntityStats] = useState<EntityStats>({});
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [lastQuery, setLastQuery] = useState("");
  const [selectedEntityType, setSelectedEntityType] = useState("");
  const [activeTab, setActiveTab] = useState(0);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  const entityTypeOptions = [
    { value: "", label: "Tous les types", icon: FiSearch },
    { value: "document", label: "Documents", icon: FiFileText },
    { value: "user", label: "Utilisateurs", icon: FiUser },
    { value: "folder", label: "Dossiers", icon: FiFolder },
    { value: "organization", label: "Organisations", icon: FiBriefcase },
    { value: "workflow", label: "Workflows", icon: FiGitBranch },
    { value: "tag", label: "Tags", icon: FiTag },
    { value: "history", label: "Historique", icon: FiActivity },
  ];

  // Fonction de recherche optimisée
  const performSearch = useCallback(async (query: string, entityType: string = selectedEntityType) => {
    if (!query.trim()) {
      setResults([]);
      setEntityStats({});
      setHasSearched(false);
      return;
    }

    // Éviter les recherches en double
    if (query === lastQuery && entityType === selectedEntityType && !isLoading) {
      return;
    }

    setIsLoading(true);
    setHasSearched(true);
    setLastQuery(query);

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("Token non trouvé");
      }

      const searchParams = new URLSearchParams({
        q: query,
        limit: "50"
      });
      
      if (entityType) {
        searchParams.append('type', entityType);
      }

      const response = await fetch(`${config.API_URL}/search?${searchParams.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        credentials: "include"
      });

      if (!response.ok) {
        throw new Error("Erreur lors de la recherche");
      }

      const data: SearchResponse = await response.json();
      setResults(data.results || []);
      setEntityStats(data.entity_stats || {});
      
      // Ajouter à l'historique si ce n'est pas déjà présent
      if (query.length >= 3 && !searchHistory.includes(query)) {
        setSearchHistory(prev => [query, ...prev.slice(0, 4)]); // Garder les 5 dernières recherches
      }
      
      // Toast pour les recherches manuelles
      if (data.message) {
        toast({
          title: "Recherche terminée",
          description: data.message,
          status: "success",
          duration: 2000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error("Erreur de recherche:", error);
        toast({
          title: "Erreur de recherche",
          description: "Impossible d'effectuer la recherche",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      setResults([]);
      setEntityStats({});
    } finally {
      setIsLoading(false);
    }
  }, [lastQuery, selectedEntityType, isLoading, searchHistory, toast]);

  // Effectuer une recherche lorsque le terme change
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchTerm.trim().length >= 2) {
        performSearch(searchTerm);
      } else if (searchTerm.trim().length === 0) {
        setResults([]);
        setEntityStats({});
        setHasSearched(false);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm, performSearch]);

  const handleManualSearch = () => {
    if (searchTerm.trim().length > 0) {
      performSearch(searchTerm);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleManualSearch();
    }
  };

  const handleEntityTypeChange = (entityType: string) => {
    setSelectedEntityType(entityType);
    if (hasSearched && lastQuery) {
      performSearch(lastQuery, entityType);
    }
  };

  const clearSearch = () => {
    setSearchTerm("");
    setResults([]);
    setEntityStats({});
    setHasSearched(false);
    setLastQuery("");
  };

  const formatDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch (e) {
      return "Date invalide";
    }
  };

  const getTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      PDF: "red",
      DOC: "blue",
      XLS: "green",
      Image: "purple",
      TXT: "gray",
      document: "blue",
      user: "green",
      folder: "yellow",
      organization: "purple",
      workflow: "cyan",
      tag: "pink",
      history: "orange",
    };
    return colors[type] || "gray";
  };

  const getEntityIcon = (entityType: string) => {
    const icons: { [key: string]: any } = {
      document: FiFileText,
      user: FiUser,
      folder: FiFolder,
      organization: FiBriefcase,
      workflow: FiGitBranch,
      tag: FiTag,
      history: FiActivity,
    };
    return icons[entityType] || FiFileText;
  };

  const filteredResults = selectedEntityType 
    ? results.filter(result => result.entity_type === selectedEntityType)
    : results;

  return (
    <Box p={5}>
      <Heading mb={6} size="lg" color="white">
        <Icon as={FiSearch as ElementType} mr={3} />
        Recherche Globale ESAG GED
      </Heading>
      
      {/* Barre de recherche avec filtres et options */}
      <Card bg="#2a3657" mb={6}>
        <CardBody>
          <VStack spacing={4}>
            {/* Ligne principale de recherche */}
            <Flex gap={4} align="center" w="100%">
              <InputGroup flex="1">
                <InputLeftElement pointerEvents="none">
                  <Icon as={FiSearch as ElementType} color="gray.400" />
                </InputLeftElement>
                <Input
                  placeholder="Rechercher dans toute l'application..."
                  bg="#1c2338"
                  color="white"
                  borderColor="#3a445e"
                  _placeholder={{ color: "gray.400" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={handleKeyPress}
                />
                <InputRightElement width="auto" pr={2}>
                  <HStack spacing={1}>
                    {searchTerm && (
                      <Tooltip label="Effacer la recherche">
                        <IconButton
                          aria-label="Effacer"
                          icon={<Icon as={FiX as ElementType} />}
                          size="sm"
                          variant="ghost"
                          color="gray.400"
                          onClick={clearSearch}
                        />
                      </Tooltip>
                    )}
                    {isLoading && <Spinner size="sm" color="#3a8bfd" />}
                  </HStack>
                </InputRightElement>
              </InputGroup>
                <Button
                  leftIcon={<Icon as={FiSearch as ElementType} />}
                  colorScheme="blue"
                  onClick={handleManualSearch}
                  isLoading={isLoading}
                  loadingText="Recherche..."
                >
                  Rechercher
                </Button>
            </Flex>
            
            {/* Options et filtres */}
            <Flex gap={4} align="center" w="100%" wrap="wrap">
              {/* Filtre par type */}
              <HStack>
                <Icon as={FiFilter as ElementType} color="gray.400" />
                <Text color="white" fontSize="sm">Filtrer par type :</Text>
              </HStack>
              <Select
                placeholder="Tous les types"
                bg="#1c2338"
                color="white"
                borderColor="#3a445e"
                value={selectedEntityType}
                onChange={(e) => handleEntityTypeChange(e.target.value)}
                w="250px"
                size="sm"
              >
                {entityTypeOptions.slice(1).map((option) => (
                  <option key={option.value} value={option.value} style={{backgroundColor: '#1c2338'}}>
                    {option.label}
                  </option>
                ))}
              </Select>

              {/* Historique de recherche */}
              {searchHistory.length > 0 && (
                <HStack>
                  <Text color="gray.400" fontSize="sm">Récent:</Text>
                  {searchHistory.slice(0, 3).map((term, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      colorScheme="blue"
                      cursor="pointer"
                      onClick={() => setSearchTerm(term)}
                      fontSize="xs"
                    >
                      {term}
                    </Badge>
                  )                  )}
                </HStack>
              )}
            </Flex>
          </VStack>
        </CardBody>
      </Card>

      {/* Statistiques de recherche */}
      {hasSearched && Object.keys(entityStats).length > 0 && (
        <Card bg="#2a3657" mb={6}>
          <CardBody>
            <Text color="white" fontSize="lg" fontWeight="bold" mb={4}>
              Répartition des résultats pour "{lastQuery}"
            </Text>
            <SimpleGrid columns={{ base: 2, md: 4, lg: 7 }} spacing={4}>
              {Object.entries(entityStats).map(([type, stats]) => (
                <Stat key={type}>
                  <StatLabel color="gray.300" fontSize="sm">
                    <HStack>
                      <Icon as={getEntityIcon(type) as ElementType} />
                      <Text>{stats.label}</Text>
                    </HStack>
                  </StatLabel>
                  <StatNumber color="white" fontSize="lg">
                    {stats.count}
                  </StatNumber>
                </Stat>
              ))}
            </SimpleGrid>
          </CardBody>
        </Card>
      )}

      {/* Résultats de recherche */}
      {hasSearched ? (
        filteredResults.length > 0 ? (
          <VStack spacing={4} align="stretch">
            <Text color="white" fontSize="lg" fontWeight="bold">
              {filteredResults.length} résultat(s) trouvé(s)
              {selectedEntityType && ` (${entityTypeOptions.find(opt => opt.value === selectedEntityType)?.label})`}
            </Text>
            
            <Card bg="#2a3657">
              <CardBody p={0}>
                <Table variant="simple">
                  <Thead bg="#1c2338">
                    <Tr>
                      <Th color="white" borderColor="#3a445e">Élément</Th>
                      <Th color="white" borderColor="#3a445e">Type</Th>
                      <Th color="white" borderColor="#3a445e">Catégorie</Th>
                      <Th color="white" borderColor="#3a445e">Propriétaire</Th>
                      <Th color="white" borderColor="#3a445e">Date</Th>
                      <Th color="white" borderColor="#3a445e">Détails</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredResults.map((item) => (
                      <Tr key={`search-result-${item.entity_type}-${item.id}`} _hover={{ bg: "#374269" }}>
                        <Td color="white" borderColor="#3a445e">
                          <VStack align="start" spacing={1}>
                            <Flex align="center">
                              <Icon as={getEntityIcon(item.entity_type) as ElementType} mr={2} color="#3a8bfd" />
                              <Text fontWeight="bold">{item.title || item.titre}</Text>
                            </Flex>
                            {item.highlights && item.highlights.length > 0 && (
                              <VStack align="start" spacing={1}>
                                {item.highlights.map((highlight, index) => (
                                  <Text key={index} fontSize="sm" color="gray.300">
                                    {highlight}
                                  </Text>
                                ))}
                              </VStack>
                            )}
                          </VStack>
                        </Td>
                        <Td color="white" borderColor="#3a445e">
                          <Badge colorScheme={getTypeColor(item.entity_type)}>
                            {item.entity_label}
                          </Badge>
                        </Td>
                        <Td color="white" borderColor="#3a445e">
                          <Badge variant="outline" colorScheme={getTypeColor(item.file_type)}>
                            {item.category || item.type_document || item.file_type}
                          </Badge>
                        </Td>
                        <Td color="white" borderColor="#3a445e">
                          {(item.owner_firstname || item.proprietaire_prenom) && 
                           (item.owner_lastname || item.proprietaire_nom) ? 
                            `${item.owner_firstname || item.proprietaire_prenom} ${item.owner_lastname || item.proprietaire_nom}` : 
                            'Système'
                          }
                        </Td>
                        <Td color="white" borderColor="#3a445e">
                          <Flex align="center">
                            <Icon as={FiClock as ElementType} mr={1} color="gray.400" />
                            {formatDate(item.date_creation)}
                          </Flex>
                        </Td>
                        <Td color="white" borderColor="#3a445e">
                          {item.size_formatted || item.taille_formatee || item.description || '-'}
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          </VStack>
        ) : (
          <Card bg="#2a3657">
            <CardBody textAlign="center" py={8}>
              <Icon as={FiSearch as ElementType} boxSize={12} color="gray.400" mb={4} />
              <Text fontSize="lg" color="white" mb={2}>
                Aucun résultat trouvé
              </Text>
              <Text color="gray.400">
                Aucun élément ne correspond à votre recherche "{lastQuery}"
                {selectedEntityType && ` dans la catégorie ${entityTypeOptions.find(opt => opt.value === selectedEntityType)?.label}`}.
                Essayez avec d'autres termes ou changez le filtre.
              </Text>
            </CardBody>
          </Card>
        )
      ) : (
        <Card bg="#2a3657">
          <CardBody textAlign="center" py={8}>
            <Icon as={FiSearch as ElementType} boxSize={12} color="gray.400" mb={4} />
            <Text fontSize="lg" color="white" mb={2}>
              Recherche Globale ESAG GED
            </Text>
            <Text color="gray.400" mb={4}>
              Recherchez dans tous les éléments de l'application : documents, utilisateurs, dossiers, organisations, workflows, tags et historique.
            </Text>
            <SimpleGrid columns={{ base: 2, md: 4, lg: 7 }} spacing={4} mt={6}>
              {entityTypeOptions.slice(1).map((option) => (
                <Card key={option.value} bg="#1c2338" p={3} textAlign="center">
                  <Icon as={option.icon as ElementType} color="#3a8bfd" boxSize={6} mb={2} />
                  <Text color="white" fontSize="sm">{option.label}</Text>
                </Card>
              ))}
            </SimpleGrid>
          </CardBody>
        </Card>
      )}
    </Box>
  );
};

export default SearchPage;
