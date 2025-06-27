import React, { useState, useEffect } from 'react';
import {
  Box,
  Text,
  VStack,
  HStack,
  Badge,
  Spinner,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Input,
  Select,
  InputGroup,
  InputLeftElement,
  useToast,
  Flex,
  Button
} from '@chakra-ui/react';
import { SearchIcon, RepeatIcon } from '@chakra-ui/icons';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';

interface HistoryLogProps {
  filterType?: 'all' | 'errors' | 'user_activity';
}

interface HistoryEntry {
  id: number;
  action_type: string;
  entity_type: string;
  entity_id: number;
  entity_name?: string;
  description?: string;
  metadata?: any;
  created_at: string;
  user_name: string;
}

const HistoryLog: React.FC<HistoryLogProps> = ({ filterType = 'all' }) => {
  const { executeOperation } = useAsyncOperation();
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const toast = useToast();

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const result = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          console.log('Calling API:', `${config.API_URL}/history`);
          const response = await fetch(`${config.API_URL}/api/history`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });
          
          console.log('Response status:', response.status);
          console.log('Response headers:', response.headers);

          if (!response.ok) {
            throw new Error('Erreur lors de la récupération de l\'historique');
          }

          const data = await response.json();
          console.log('Données reçues de l\'API:', data);
          console.log('Type des données:', typeof data);
          console.log('Est-ce un tableau?', Array.isArray(data));
          
          // Gérer différents formats de réponse
          if (Array.isArray(data)) {
            console.log('Données sont un tableau direct');
            return data;
          } else if (data && typeof data === 'object') {
            // Vérifier si les données sont dans une propriété spécifique
            if (Array.isArray(data.data)) {
              console.log('Données trouvées dans data.data');
              return data.data;
            } else if (Array.isArray(data.results)) {
              console.log('Données trouvées dans data.results');
              return data.results;
            } else if (Array.isArray(data.items)) {
              console.log('Données trouvées dans data.items');
              return data.items;
            } else {
              console.log('Format de données non reconnu:', Object.keys(data));
              return [];
            }
          } else {
            console.log('Format de données inattendu');
            return [];
          }
        },
        {
          loadingMessage: "Chargement de l'historique...",
          errorMessage: "Impossible de charger l'historique"
        }
      );

      console.log('Résultat de executeOperation:', result);
      console.log('Length du résultat:', result?.length);
      
      if (result && Array.isArray(result)) {
        console.log('Setting history with', result.length, 'items');
        setHistory(result);
      } else {
        console.log('Setting history to empty array');
        setHistory([]);
      }
    } catch (err) {
      console.error('Erreur lors du chargement de l\'historique:', err);
      setHistory([]); // S'assurer que history reste un tableau même en cas d'erreur
      toast({
        title: "Erreur",
        description: err instanceof Error ? err.message : "Erreur lors du chargement de l'historique",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [filterType]);

  const formatDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return 'Date invalide';
    }
  };

  const getActionBadgeColor = (action: string) => {
    if (!action) return 'gray';
    
    const errorActions = ['ERROR', 'FAILED', 'DELETE'];
    const successActions = ['CREATE', 'UPLOAD', 'LOGIN', 'UPDATE'];
    const warningActions = ['LOGOUT', 'DOWNLOAD', 'MOVE'];

    if (errorActions.some(a => action.includes(a))) return 'red';
    if (successActions.some(a => action.includes(a))) return 'green';
    if (warningActions.some(a => action.includes(a))) return 'orange';
    return 'blue';
  };

  console.log('History state:', history);
  console.log('Search term:', searchTerm);
  console.log('Action filter:', actionFilter);
  console.log('Filter type:', filterType);

  const filteredHistory = Array.isArray(history) ? history.filter(entry => {
    if (!entry) return false;
    
    const matchesSearch = 
      entry.action_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.entity_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.description?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesAction = !actionFilter || entry.action_type?.includes(actionFilter);

    if (filterType === 'errors') {
      return matchesSearch && matchesAction && ['ERROR', 'FAILED'].some(a => entry.action_type?.includes(a));
    }
    if (filterType === 'user_activity') {
      return matchesSearch && matchesAction && ['LOGIN', 'LOGOUT', 'CREATE', 'UPDATE', 'DELETE'].some(a => entry.action_type?.includes(a));
    }

    return matchesSearch && matchesAction;
  }) : [];
  
  console.log('Filtered history length:', filteredHistory.length);
  console.log('Filtered history:', filteredHistory);

  if (isLoading) {
    return (
      <Flex justify="center" align="center" h="200px">
        <VStack>
          <Spinner color="#3a8bfd" size="lg" />
          <Text color="gray.400">Chargement de l'historique...</Text>
        </VStack>
      </Flex>
    );
  }

  return (
    <Box>
      <HStack spacing={4} mb={4}>
        <InputGroup flex={1}>
          <InputLeftElement pointerEvents="none">
            <SearchIcon color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Rechercher dans l'historique..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            bg="#232946"
            color="white"
            _placeholder={{ color: "gray.400" }}
          />
        </InputGroup>
        
        <Select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          bg="#232946"
          color="white"
          w="200px"
        >
          <option value="">Toutes les actions</option>
          <option value="LOGIN">Connexions</option>
          <option value="UPLOAD">Upload</option>
          <option value="DOWNLOAD">Téléchargements</option>
          <option value="VIEW">Consultations</option>
          <option value="CREATE">Créations</option>
          <option value="UPDATE">Modifications</option>
          <option value="DELETE">Suppressions</option>
        </Select>

        <Button
          leftIcon={<RepeatIcon />}
          onClick={loadHistory}
          colorScheme="blue"
          variant="outline"
        >
          Actualiser
        </Button>
      </HStack>

      {filteredHistory.length === 0 ? (
        <Box textAlign="center" py={8}>
          <Text color="gray.400">Aucune entrée d'historique trouvée</Text>
        </Box>
      ) : (
        <Box overflowX="auto" bg="#20243a" borderRadius="lg">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">Date</Th>
                <Th color="white">Action</Th>
                <Th color="white">Utilisateur</Th>
                <Th color="white">Document</Th>
                <Th color="white">Détails</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredHistory.map((entry) => (
                <Tr key={entry.id}>
                  <Td color="white" fontSize="sm">
                    {formatDate(entry.created_at)}
                  </Td>
                  <Td>
                    <Badge colorScheme={getActionBadgeColor(entry.action_type)}>
                      {entry.action_type || 'Action inconnue'}
                    </Badge>
                  </Td>
                  <Td color="white">
                    {entry.user_name || 'Utilisateur inconnu'}
                  </Td>
                  <Td color="gray.300" maxW="200px" isTruncated>
                    {entry.entity_name || '-'}
                  </Td>
                  <Td color="gray.300" maxW="300px" isTruncated>
                    {entry.description || '-'}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}
    </Box>
  );
};

export default HistoryLog; 

