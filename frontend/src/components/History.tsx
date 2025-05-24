import React, { useEffect, useState } from "react";
import {
  Box,
  Heading,
  VStack,
  Text,
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
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Button,
  Stack,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Tooltip,
} from "@chakra-ui/react";
import { FiSearch, FiClock, FiFileText, FiUser, FiDownload, FiShare2, FiTrash2, FiRefreshCw, FiFilter, FiActivity } from "react-icons/fi";
import { ElementType } from "react";

interface HistoryItem {
  id: number;
  action_type: string;
  entity_type: string;
  entity_id: number;
  entity_name: string;
  description: string;
  created_at: string;
  user_name: string;
  metadata: any;
}

interface HistoryStats {
  total_actions: number;
  actions_by_type: { [key: string]: number };
  entities_by_type: { [key: string]: number };
}

const History: React.FC = () => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<HistoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    action_type: '',
    entity_type: '',
    start_date: '',
    end_date: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const toast = useToast();

  const fetchHistory = async () => {
    try {
      const queryParams = new URLSearchParams({
        page: currentPage.toString(),
        per_page: '50',
        ...filters,
      });

      const response = await fetch(`http://localhost:5000/api/history?${queryParams}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setItems(data.items);
        setTotalPages(data.pages);
      } else {
        throw new Error('Erreur lors de la récupération de l\'historique');
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger l\'historique',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/history/stats', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Erreur lors de la récupération des statistiques:', error);
    }
  };

  useEffect(() => {
    fetchHistory();
    fetchStats();
  }, [currentPage, filters]);

  const getActionBadgeColor = (actionType: string) => {
    const colors: { [key: string]: string } = {
      CREATE: 'green',
      UPDATE: 'blue',
      DELETE: 'red',
      RESTORE: 'purple',
    };
    return colors[actionType] || 'gray';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading color="white" size="lg">
          Historique
        </Heading>
        <Button
          leftIcon={<Icon as={FiRefreshCw as ElementType} />}
          onClick={() => {
            fetchHistory();
            fetchStats();
          }}
          colorScheme="blue"
          variant="ghost"
        >
          Actualiser
        </Button>
      </Flex>

      {stats && (
        <StatGroup bg="#20243a" p={4} borderRadius="lg" mb={6}>
          <Stat>
            <StatLabel color="gray.400">Total des actions</StatLabel>
            <StatNumber color="white">{stats.total_actions}</StatNumber>
          </Stat>
          {Object.entries(stats.actions_by_type).map(([type, count]) => (
            <Stat key={type}>
              <StatLabel color="gray.400">{type}</StatLabel>
              <StatNumber color="white">{count}</StatNumber>
            </Stat>
          ))}
        </StatGroup>
      )}

      <Box bg="#20243a" p={4} borderRadius="lg" mb={6}>
        <Stack spacing={4}>
          <Heading size="sm" color="white" mb={2}>
            Filtres
          </Heading>
          <Flex gap={4} flexWrap="wrap">
            <Select
              placeholder="Type d'action"
              value={filters.action_type}
              onChange={(e) => setFilters({ ...filters, action_type: e.target.value })}
              bg="#1a1f37"
              color="white"
              width="200px"
            >
              <option value="CREATE">Création</option>
              <option value="UPDATE">Modification</option>
              <option value="DELETE">Suppression</option>
              <option value="RESTORE">Restauration</option>
            </Select>
            <Select
              placeholder="Type d'entité"
              value={filters.entity_type}
              onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}
              bg="#1a1f37"
              color="white"
              width="200px"
            >
              <option value="DOCUMENT">Document</option>
              <option value="ORGANISATION">Organisation</option>
              <option value="USER">Utilisateur</option>
            </Select>
            <Input
              type="date"
              placeholder="Date début"
              value={filters.start_date}
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              bg="#1a1f37"
              color="white"
              width="200px"
            />
            <Input
              type="date"
              placeholder="Date fin"
              value={filters.end_date}
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              bg="#1a1f37"
              color="white"
              width="200px"
            />
          </Flex>
        </Stack>
      </Box>

      {loading ? (
        <Text color="white" textAlign="center">
          Chargement...
        </Text>
      ) : items.length === 0 ? (
        <Box bg="#20243a" borderRadius="lg" p={6} textAlign="center">
          <Icon as={FiActivity as ElementType} boxSize={8} color="gray.400" mb={2} />
          <Text color="white">Aucune action trouvée</Text>
        </Box>
      ) : (
        <Box bg="#20243a" borderRadius="lg" p={4} overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">Date</Th>
                <Th color="white">Action</Th>
                <Th color="white">Entité</Th>
                <Th color="white">Description</Th>
                <Th color="white">Utilisateur</Th>
              </Tr>
            </Thead>
            <Tbody>
              {items.map((item) => (
                <Tr key={item.id}>
                  <Td color="white">{formatDate(item.created_at)}</Td>
                  <Td>
                    <Badge colorScheme={getActionBadgeColor(item.action_type)}>
                      {item.action_type}
                    </Badge>
                  </Td>
                  <Td>
                    <Tooltip label={item.entity_name}>
                      <Text color="white" isTruncated maxW="200px">
                        {item.entity_type} #{item.entity_id}
                      </Text>
                    </Tooltip>
                  </Td>
                  <Td>
                    <Text color="white" isTruncated maxW="300px">
                      {item.description}
                    </Text>
                  </Td>
                  <Td color="white">{item.user_name}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>

          {totalPages > 1 && (
            <Flex justify="center" mt={4} gap={2}>
              <Button
                onClick={() => setCurrentPage(currentPage - 1)}
                isDisabled={currentPage === 1}
                size="sm"
                variant="ghost"
                colorScheme="blue"
              >
                Précédent
              </Button>
              <Text color="white" alignSelf="center">
                Page {currentPage} sur {totalPages}
              </Text>
              <Button
                onClick={() => setCurrentPage(currentPage + 1)}
                isDisabled={currentPage === totalPages}
                size="sm"
                variant="ghost"
                colorScheme="blue"
              >
                Suivant
              </Button>
            </Flex>
          )}
        </Box>
      )}
    </Box>
  );
};

export default History; 