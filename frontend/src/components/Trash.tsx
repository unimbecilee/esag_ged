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
  ButtonGroup,
} from "@chakra-ui/react";
import { SearchIcon, DeleteIcon, RepeatIcon } from "@chakra-ui/icons";
import { format } from "date-fns";
import { fr } from "date-fns/locale";
import config from "../config";
import RequireRole from './RequireRole';

interface TrashItem {
  id: number;
  item_id: number;
  item_type: string;
  title: string;
  description?: string;
  size: number;
  size_bytes: number;
  deleted_at: string;
  deleted_by: number;
  deleted_by_name: string;
  days_until_deletion: number;
}

interface TrashStats {
  total_items: number;
  pending_deletion: number;
  restored_items: number;
  permanently_deleted: number;
  total_size_formatted: string;
}

const Trash: React.FC = () => {
  const [items, setItems] = useState<TrashItem[]>([]);
  const [stats, setStats] = useState<TrashStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [error, setError] = useState<string | null>(null);

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

    try {
      const token = getAuthToken();
      console.log("🔍 [DEBUG] Token récupéré:", token ? "Présent" : "Manquant");
      
      if (!token) {
        throw new Error("Token d'authentification manquant");
      }

      console.log("🔍 [DEBUG] Appel API trash avec token:", token.substring(0, 20) + "...");

      const response = await fetch(`${config.API_URL}/api/trash`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        mode: "cors",
      });

      console.log("🔍 [DEBUG] Réponse API:", {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("🔍 [DEBUG] Erreur API:", errorText);
        throw new Error(`Erreur ${response.status}: ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      console.log("🔍 [DEBUG] Données reçues:", data);

      // Gérer différents formats de réponse
      if (Array.isArray(data)) {
        console.log("🔍 [DEBUG] Format: tableau");
        setItems(data);
        console.log("🔍 [DEBUG] Items définis (array):", data.length);
      } else if (data.items && Array.isArray(data.items)) {
        console.log("🔍 [DEBUG] Format: objet avec tableau items");
        setItems(data.items);
        console.log("🔍 [DEBUG] Items définis (object):", data.items.length);
      } else {
        console.log("🔍 [DEBUG] Format: inconnu", data);
        setItems([]);
        console.log("🔍 [DEBUG] Aucun item trouvé");
      }
    } catch (error) {
      console.error("🔍 [DEBUG] Erreur complète:", error);
      setError("Impossible de charger les éléments de la corbeille");
      
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

      const response = await fetch(`${config.API_URL}/api/trash/stats`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        mode: "cors",
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
        console.log("Stats chargées:", data);
      }
    } catch (error) {
      console.error("Erreur stats:", error);
    }
  };

  const restoreItem = async (itemId: number) => {
    try {
      const token = getAuthToken();
      if (!token) throw new Error("Token manquant");

      const response = await fetch(`${config.API_URL}/api/trash/${itemId}/restore`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        mode: "cors",
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
      console.error("Erreur restauration:", error);
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

      const response = await fetch(`${config.API_URL}/api/trash/${itemId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        mode: "cors",
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
      console.error("Erreur suppression:", error);
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

  useEffect(() => {
    console.log("Chargement initial de la corbeille");
    fetchTrashItems();
    fetchStats();
  }, []);

  const filteredItems = items.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (item.description && item.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = filterType === "all" || item.item_type === filterType;
    return matchesSearch && matchesType;
  });

  if (loading) {
    return (
      <Container maxW="7xl" py={8}>
        <VStack spacing={6}>
          <Spinner size="xl" color="blue.500" />
          <Text color="white">Chargement de la corbeille...</Text>
        </VStack>
      </Container>
    );
  }

  return (
    <RequireRole roles={["admin", "archiviste"]}>
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* En-tête */}
        <Flex justify="space-between" align="center">
          <VStack align="start" spacing={1}>
            <Heading size="lg" color="white">
              🗑️ Corbeille
            </Heading>
            <Text color="gray.300">
              Gérez les éléments supprimés de votre système
            </Text>
          </VStack>
          <HStack spacing={2}>
            <IconButton
              aria-label="Actualiser"
              icon={<RepeatIcon />}
              onClick={fetchTrashItems}
              variant="outline"
              borderColor="gray.600"
              color="white"
              _hover={{ bg: "gray.700" }}
            />
          </HStack>
        </Flex>

        {/* Filtres et recherche */}
        <Card bg="gray.700">
          <CardBody>
            <Flex direction={{ base: "column", md: "row" }} gap={4}>
              <InputGroup flex={2}>
                <InputLeftElement>
                  <SearchIcon color="gray.400" />
                </InputLeftElement>
                <Input
                  placeholder="Rechercher dans la corbeille..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  bg="gray.800"
                  borderColor="gray.600"
                  color="white"
                  _placeholder={{ color: "gray.400" }}
                />
              </InputGroup>
              <Select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                maxW="200px"
                bg="gray.800"
                borderColor="gray.600"
                color="white"
              >
                <option value="all">Tous les types</option>
                <option value="document">Documents</option>
                <option value="folder">Dossiers</option>
              </Select>
            </Flex>
          </CardBody>
        </Card>

        {/* Message d'erreur */}
        {error && (
          <Alert status="error">
            <AlertIcon />
            <AlertTitle>Erreur!</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Liste des éléments */}
        {filteredItems.length === 0 ? (
          <Card bg="gray.700">
            <CardBody>
              <VStack spacing={4} py={8}>
                <DeleteIcon boxSize={12} color="gray.400" />
                <Text fontSize="lg" color="gray.300">
                  {items.length === 0 ? "La corbeille est vide" : "Aucun élément trouvé"}
                </Text>
                <Text color="gray.400" textAlign="center">
                  {items.length === 0 
                    ? "Les éléments supprimés apparaîtront ici."
                    : "Essayez de modifier vos critères de recherche."
                  }
                </Text>
                {items.length === 0 && (
                  <Text fontSize="sm" color="orange.300">
                    Nombre d'éléments chargés: {items.length}
                  </Text>
                )}
              </VStack>
            </CardBody>
          </Card>
        ) : (
          <Card bg="gray.700">
            <CardBody p={0}>
              <TableContainer>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th color="gray.300">Élément</Th>
                      <Th color="gray.300">Type</Th>
                      <Th color="gray.300">Taille</Th>
                      <Th color="gray.300">Supprimé par</Th>
                      <Th color="gray.300">Supprimé le</Th>
                      <Th color="gray.300">Expiration</Th>
                      <Th color="gray.300">Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {filteredItems.map((item) => (
                      <Tr key={item.id} _hover={{ bg: "gray.600" }}>
                        <Td>
                          <VStack align="start" spacing={0}>
                            <Text fontWeight="medium" noOfLines={1} color="white">
                              {item.title}
                            </Text>
                            {item.description && (
                              <Text fontSize="sm" color="gray.400" noOfLines={1}>
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
                          <Text fontSize="sm" color="gray.300">
                            {formatFileSize(item.size_bytes || item.size || 0)}
                          </Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm" color="gray.300">{item.deleted_by_name}</Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm" color="gray.300">
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
    </RequireRole>
  );
};

export default Trash; 

