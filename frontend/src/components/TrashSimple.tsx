import React, { useEffect, useState } from "react";
import {
  Box,
  Heading,
  Text,
  Button,
  useToast,
  Flex,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Spinner,
  HStack,
  VStack,
  IconButton,
  Card,
  CardBody,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  useColorModeValue,
  Container,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  TableContainer,
  Checkbox,
  ButtonGroup,
  Code,
} from "@chakra-ui/react";
import { SearchIcon, DeleteIcon, RepeatIcon } from "@chakra-ui/icons";
import { format } from "date-fns";
import { fr } from "date-fns/locale";

interface TrashItem {
  id: number;
  item_id: number;
  item_type: string;
  title: string;
  description?: string;
  file_type?: string;
  size: number;
  size_bytes: number;
  deleted_at: string;
  deleted_by: number;
  deleted_by_name: string;
  days_until_deletion: number;
  expiry_date: string;
}

interface TrashStats {
  total_items: number;
  pending_deletion: number;
  restored_items: number;
  permanently_deleted: number;
  total_size_formatted: string;
}

const TrashSimple: React.FC = () => {
  const [items, setItems] = useState<TrashItem[]>([]);
  const [stats, setStats] = useState<TrashStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<string>("");

  const toast = useToast();
  const bgColor = useColorModeValue("white", "#1a202c");
  const borderColor = useColorModeValue("gray.200", "gray.600");
  const textColor = useColorModeValue("gray.800", "white");
  const mutedColor = useColorModeValue("gray.600", "gray.400");
  const cardBg = useColorModeValue("gray.50", "#2d3748");

  const getAuthToken = () => localStorage.getItem("token");

  const fetchTrashItems = async () => {
    setLoading(true);
    setError(null);
    setDebugInfo("");

    try {
      const token = getAuthToken();
      if (!token) {
        throw new Error("Token d'authentification manquant");
      }

      setDebugInfo(`Token: ${token.substring(0, 20)}...`);

      // Utiliser l'URL relative via le proxy React
      const url = "/api/trash";
      setDebugInfo(prev => prev + `\nURL: ${url}`);

      const response = await fetch(url, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      setDebugInfo(prev => prev + `\nStatus: ${response.status}`);
      setDebugInfo(prev => prev + `\nContent-Type: ${response.headers.get('Content-Type')}`);

      if (!response.ok) {
        const errorText = await response.text();
        setDebugInfo(prev => prev + `\nError: ${errorText.substring(0, 200)}`);
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('Content-Type');
      if (!contentType || !contentType.includes('application/json')) {
        const responseText = await response.text();
        setDebugInfo(prev => prev + `\nResponse (not JSON): ${responseText.substring(0, 200)}`);
        throw new Error(`Réponse non-JSON reçue: ${contentType}`);
      }

      const data = await response.json();
      setDebugInfo(prev => prev + `\nData type: ${typeof data}`);
      setDebugInfo(prev => prev + `\nData keys: ${Object.keys(data).join(', ')}`);

      console.log("Données reçues:", data);

      // Gérer différents formats de réponse
      if (Array.isArray(data)) {
        setItems(data);
        setDebugInfo(prev => prev + `\nItems (array): ${data.length}`);
      } else if (data.items && Array.isArray(data.items)) {
        setItems(data.items);
        setDebugInfo(prev => prev + `\nItems (object): ${data.items.length}`);
      } else {
        setItems([]);
        setDebugInfo(prev => prev + `\nNo items found`);
      }
    } catch (error) {
      console.error("Erreur lors de la récupération:", error);
      const errorMessage = error instanceof Error ? error.message : "Erreur inconnue";
      setError(errorMessage);
      setDebugInfo(prev => prev + `\nError: ${errorMessage}`);
      
      toast({
        title: "Erreur",
        description: "Impossible de charger les éléments de la corbeille",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = getAuthToken();
      if (!token) return;

      const response = await fetch("/api/trash/stats", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
        setDebugInfo(prev => prev + `\nStats loaded: ${JSON.stringify(data)}`);
      }
    } catch (error) {
      console.error("Erreur stats:", error);
      setDebugInfo(prev => prev + `\nStats error: ${error}`);
    }
  };

  const restoreItem = async (itemId: number) => {
    try {
      const token = getAuthToken();
      if (!token) throw new Error("Token manquant");

      const response = await fetch(`/api/trash/${itemId}/restore`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Erreur lors de la restauration");
      }

      toast({
        title: "Succès",
        description: "Élément restauré avec succès",
        status: "success",
        duration: 3000,
        isClosable: true,
      });

      fetchTrashItems();
      fetchStats();
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de restaurer l'élément",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const deleteItem = async (itemId: number) => {
    try {
      const token = getAuthToken();
      if (!token) throw new Error("Token manquant");

      const response = await fetch(`/api/trash/${itemId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Erreur lors de la suppression");
      }

      toast({
        title: "Succès",
        description: "Élément supprimé définitivement",
        status: "success",
        duration: 3000,
        isClosable: true,
      });

      fetchTrashItems();
      fetchStats();
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer l'élément",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getUrgencyColor = (daysUntilDeletion: number) => {
    if (daysUntilDeletion <= 7) return "red";
    if (daysUntilDeletion <= 14) return "orange";
    return "green";
  };

  const toggleSelectItem = (itemId: number) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
  };

  const selectAllItems = () => {
    if (selectedItems.size === items.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(items.map(item => item.id)));
    }
  };

  const filteredItems = items.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (item.description && item.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = filterType === "all" || item.item_type === filterType;
    return matchesSearch && matchesType;
  });

  useEffect(() => {
    fetchTrashItems();
    fetchStats();
  }, []);

  if (loading) {
    return (
      <Container maxW="7xl" py={8}>
        <VStack spacing={6}>
          <Spinner size="xl" color="blue.500" />
          <Text>Chargement de la corbeille...</Text>
        </VStack>
      </Container>
    );
  }

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* En-tête */}
        <Flex justify="space-between" align="center">
          <VStack align="start" spacing={1}>
            <Heading size="lg" color={textColor}>
              🗑️ Corbeille
            </Heading>
            <Text color={mutedColor}>
              Gérez les éléments supprimés de votre système
            </Text>
          </VStack>
          <HStack spacing={2}>
            <IconButton
              aria-label="Actualiser"
              icon={<RepeatIcon />}
              onClick={fetchTrashItems}
              variant="outline"
              borderColor={borderColor}
            />
          </HStack>
        </Flex>

        {/* Statistiques */}
        {stats && (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Total éléments</StatLabel>
                  <StatNumber>{stats.total_items}</StatNumber>
                  <StatHelpText>En attente: {stats.pending_deletion}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Éléments restaurés</StatLabel>
                  <StatNumber>{stats.restored_items}</StatNumber>
                  <StatHelpText>Supprimés: {stats.permanently_deleted}</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Espace utilisé</StatLabel>
                  <StatNumber>{stats.total_size_formatted}</StatNumber>
                </Stat>
              </CardBody>
            </Card>
            <Card bg={cardBg}>
              <CardBody>
                <Stat>
                  <StatLabel>Statut</StatLabel>
                  <StatNumber fontSize="sm">
                    {filteredItems.length} éléments
                  </StatNumber>
                  <StatHelpText>Affichés</StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>
        )}

        {/* Filtres et recherche */}
        <Card bg={bgColor} borderColor={borderColor}>
          <CardBody>
            <Flex direction={{ base: "column", md: "row" }} gap={4}>
              <InputGroup flex={2}>
                <InputLeftElement>
                  <SearchIcon color={mutedColor} />
                </InputLeftElement>
                <Input
                  placeholder="Rechercher dans la corbeille..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  bg={bgColor}
                  borderColor={borderColor}
                />
              </InputGroup>
              <Select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                maxW="200px"
                bg={bgColor}
                borderColor={borderColor}
              >
                <option value="all">Tous les types</option>
                <option value="document">Documents</option>
                <option value="folder">Dossiers</option>
              </Select>
            </Flex>
          </CardBody>
        </Card>

        {/* Message d'erreur utilisateur simple */}
        {error && (
          <Alert status="error">
            <AlertIcon />
            <AlertTitle>Erreur!</AlertTitle>
            <AlertDescription>Impossible de charger les éléments de la corbeille. Veuillez réessayer plus tard.</AlertDescription>
          </Alert>
        )}

        {/* Liste des éléments */}
        {filteredItems.length === 0 ? (
          <Card bg={bgColor} borderColor={borderColor}>
            <CardBody>
              <VStack spacing={4} py={8}>
                <DeleteIcon boxSize={12} color={mutedColor} />
                <Text fontSize="lg" color={mutedColor}>
                  La corbeille est vide
                </Text>
                <Text color={mutedColor} textAlign="center">
                  Les éléments supprimés apparaîtront ici.
                </Text>
              </VStack>
            </CardBody>
          </Card>
        ) : (
          <Card bg={bgColor} borderColor={borderColor}>
            <CardBody p={0}>
              <TableContainer>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Élément</Th>
                      <Th>Type</Th>
                      <Th>Taille</Th>
                      <Th>Supprimé par</Th>
                      <Th>Supprimé le</Th>
                      <Th>Expiration</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredItems.map((item) => (
                      <Tr key={item.id} _hover={{ bg: cardBg }}>
                        <Td>
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="medium" noOfLines={1}>
                              {item.title}
                            </Text>
                            {item.description && (
                              <Text fontSize="sm" color={mutedColor} noOfLines={1}>
                                {item.description}
                              </Text>
                            )}
                          </VStack>
                        </Td>
                        <Td>
                          <Badge colorScheme={item.item_type === "document" ? "blue" : "green"}>
                            {item.item_type === "document" ? "Document" : "Dossier"}
                          </Badge>
                        </Td>
                        <Td>
                          <Text fontSize="sm">
                            {formatFileSize(item.size_bytes || item.size || 0)}
                          </Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm">{item.deleted_by_name}</Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm">
                            {format(new Date(item.deleted_at), "dd/MM/yyyy HH:mm", { locale: fr })}
                          </Text>
                        </Td>
                        <Td>
                          <Badge colorScheme={getUrgencyColor(item.days_until_deletion)}>
                            {item.days_until_deletion} jours
                          </Badge>
                        </Td>
                        <Td>
                          <ButtonGroup size="sm">
                            <Button
                              leftIcon={<RepeatIcon />}
                              colorScheme="green"
                              variant="outline"
                              onClick={() => restoreItem(item.id)}
                              size="xs"
                            >
                              Restaurer
                            </Button>
                            <Button
                              leftIcon={<DeleteIcon />}
                              colorScheme="red"
                              variant="outline"
                              onClick={() => deleteItem(item.id)}
                              size="xs"
                            >
                              Supprimer
                            </Button>
                          </ButtonGroup>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </TableContainer>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Container>
  );
};

export default TrashSimple; 