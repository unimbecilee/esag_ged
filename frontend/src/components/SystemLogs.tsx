import React, { useState, useEffect } from "react";
import { Box, Heading, Text, Table, Thead, Tbody, Tr, Th, Td, Badge, Flex, Spacer, Spinner, Alert, AlertIcon } from "@chakra-ui/react";
import config from '../config';

interface HistoryItem {
  id: number;
  action_type: string;
  entity_type: string;
  entity_name: string;
  description: string;
  created_at: string;
  user_name: string;
}

interface SystemLogsProps {
  filterType?: string;
}

const SystemLogs: React.FC<SystemLogsProps> = ({ filterType = "all" }) => {
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHistoryData();
  }, [filterType]);

  const fetchHistoryData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Token d\'authentification manquant');
      }

      const url = new URL(`${config.API_URL}/api/history`);
      if (filterType && filterType !== 'all') {
        url.searchParams.append('action_type', filterType);
      }
      url.searchParams.append('per_page', '50');

      const response = await fetch(url.toString(), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setHistoryData(data.items || []);
    } catch (err) {
      console.error('Erreur lors du chargement de l\'historique:', err);
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  const getActionTypeColor = (actionType: string) => {
    switch (actionType.toLowerCase()) {
      case 'create':
      case 'upload':
        return 'green';
      case 'update':
      case 'edit':
        return 'blue';
      case 'delete':
      case 'remove':
        return 'red';
      case 'share':
        return 'purple';
      case 'download':
        return 'orange';
      case 'login':
      case 'logout':
        return 'cyan';
      default:
        return 'gray';
    }
  };

  const getActionTypeLabel = (actionType: string) => {
    const labels: { [key: string]: string } = {
      'create': 'CRÉATION',
      'update': 'MODIFICATION',
      'delete': 'SUPPRESSION',
      'share': 'PARTAGE',
      'download': 'TÉLÉCHARGEMENT',
      'upload': 'UPLOAD',
      'login': 'CONNEXION',
      'logout': 'DÉCONNEXION',
      'view': 'CONSULTATION'
    };
    return labels[actionType.toLowerCase()] || actionType.toUpperCase();
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <Box textAlign="center" py={10}>
        <Spinner size="xl" color="blue.400" />
        <Text color="white" mt={4}>Chargement de l'historique...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        Erreur lors du chargement: {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Flex align="center" mb={6}>
        <Heading size="lg" color="white">
          Logs Système
        </Heading>
        <Spacer />
        <Badge colorScheme="blue" p={2} borderRadius="md">
          {historyData.length} entrées
        </Badge>
      </Flex>

      {historyData.length > 0 ? (
        <Table variant="simple" colorScheme="blue">
          <Thead>
            <Tr>
              <Th color="gray.300">Type</Th>
              <Th color="gray.300">Message</Th>
              <Th color="gray.300">Date</Th>
            </Tr>
          </Thead>
          <Tbody>
            {historyData.map(item => (
              <Tr key={item.id}>
                <Td>
                  <Badge colorScheme={getActionTypeColor(item.action_type)}>
                    {getActionTypeLabel(item.action_type)}
                  </Badge>
                </Td>
                <Td color="white">
                  {item.description || `${item.action_type} sur ${item.entity_type}: ${item.entity_name}`}
                  {item.user_name && (
                    <Text fontSize="sm" color="gray.400" mt={1}>
                      Par: {item.user_name}
                    </Text>
                  )}
                </Td>
                <Td color="gray.300">{formatDate(item.created_at)}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      ) : (
        <Text color="white">Aucune activité enregistrée.</Text>
      )}
    </Box>
  );
};

export default SystemLogs; 

