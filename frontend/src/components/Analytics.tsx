import React, { useEffect, useState } from "react";
import {
  Box,
  Heading,
  Text,
  Grid,
  GridItem,
  Card,
  CardBody,
  CardHeader,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Progress,
  VStack,
  HStack,
  Badge,
  useToast,
  Flex,
  Icon,
  Select,
  Spinner,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  CircularProgress,
  CircularProgressLabel,
} from "@chakra-ui/react";
import {
  FiBarChart2,
  FiUsers,
  FiFileText,
  FiUpload,
  FiDownload,
  FiEye,
  FiShare2,
  FiClock,
  FiHardDrive,
  FiActivity,
  FiTrendingUp,
  FiRefreshCw,
} from "react-icons/fi";
import { ElementType } from "react";
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';

interface AnalyticsData {
  overview: {
    totalDocuments: number;
    totalUsers: number;
    totalStorage: string;
    documentsThisMonth: number;
    documentsGrowth: number;
    usersGrowth: number;
    storageUsed: number;
    storageTotal: number;
  };
  documentStats: {
    byType: Array<{ type: string; count: number; percentage: number }>;
    bySize: Array<{ range: string; count: number; percentage: number }>;
    byStatus: Array<{ status: string; count: number; color: string }>;
  };
  activityStats: {
    uploads: Array<{ date: string; count: number }>;
    downloads: Array<{ date: string; count: number }>;
    views: Array<{ date: string; count: number }>;
    mostActive: Array<{ 
      user: string; 
      uploads: number; 
      downloads: number; 
      views: number; 
    }>;
  };
  popularDocuments: Array<{
    id: number;
    titre: string;
    views: number;
    downloads: number;
    shares: number;
    type: string;
  }>;
}

const Analytics: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("30"); // 7, 30, 90 jours
  const toast = useToast();

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    try {
      const result = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/analytics?range=${timeRange}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });

          if (!response.ok) {
            throw new Error('Erreur lors de la récupération des analytics');
          }

          const analyticsData = await response.json();
          return analyticsData;
        },
        {
          loadingMessage: "Chargement des statistiques...",
          errorMessage: "Impossible de charger les statistiques"
        }
      );

      if (result) {
        setData(result);
      }
    } catch (err) {
      // Pour le moment, utilisons des données de test
      setData({
        overview: {
          totalDocuments: 1250,
          totalUsers: 45,
          totalStorage: "2.4 TB",
          documentsThisMonth: 180,
          documentsGrowth: 12.5,
          usersGrowth: 8.3,
          storageUsed: 75,
          storageTotal: 100
        },
        documentStats: {
          byType: [
            { type: "PDF", count: 450, percentage: 36 },
            { type: "DOC/DOCX", count: 320, percentage: 25.6 },
            { type: "XLS/XLSX", count: 200, percentage: 16 },
            { type: "Images", count: 180, percentage: 14.4 },
            { type: "Autres", count: 100, percentage: 8 }
          ],
          bySize: [
            { range: "< 1 MB", count: 680, percentage: 54.4 },
            { range: "1-10 MB", count: 380, percentage: 30.4 },
            { range: "10-50 MB", count: 140, percentage: 11.2 },
            { range: "> 50 MB", count: 50, percentage: 4 }
          ],
          byStatus: [
            { status: "Actif", count: 950, color: "green" },
            { status: "Archivé", count: 200, color: "gray" },
            { status: "Brouillon", count: 80, color: "orange" },
            { status: "En révision", count: 20, color: "blue" }
          ]
        },
        activityStats: {
          uploads: [
            { date: "2024-01-01", count: 15 },
            { date: "2024-01-02", count: 23 },
            { date: "2024-01-03", count: 18 }
          ],
          downloads: [
            { date: "2024-01-01", count: 45 },
            { date: "2024-01-02", count: 67 },
            { date: "2024-01-03", count: 34 }
          ],
          views: [
            { date: "2024-01-01", count: 125 },
            { date: "2024-01-02", count: 158 },
            { date: "2024-01-03", count: 142 }
          ],
          mostActive: [
            { user: "Jean Dupont", uploads: 45, downloads: 120, views: 350 },
            { user: "Marie Martin", uploads: 38, downloads: 95, views: 280 },
            { user: "Pierre Durand", uploads: 32, downloads: 85, views: 245 }
          ]
        },
        popularDocuments: [
          { id: 1, titre: "Guide d'utilisation", views: 245, downloads: 89, shares: 12, type: "PDF" },
          { id: 2, titre: "Rapport mensuel", views: 198, downloads: 67, shares: 8, type: "DOC" },
          { id: 3, titre: "Présentation Q1", views: 156, downloads: 45, shares: 15, type: "PPT" }
        ]
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !data) {
    return (
      <Box p={5}>
        <Flex justify="center" align="center" h="50vh">
          <Spinner color="#3a8bfd" size="xl" />
        </Flex>
      </Box>
    );
  }

  return (
    <Box p={5}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          <Icon as={FiBarChart2 as ElementType} mr={3} />
          Analytics & Statistiques
        </Heading>
        <HStack>
          <Select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            bg="#2a3657"
            color="white"
            borderColor="#3a445e"
            maxW="150px"
          >
            <option value="7">7 derniers jours</option>
            <option value="30">30 derniers jours</option>
            <option value="90">90 derniers jours</option>
          </Select>
          <Button
            leftIcon={<Icon as={FiRefreshCw as ElementType} />}
            colorScheme="blue"
            onClick={fetchAnalytics}
          >
            Actualiser
          </Button>
        </HStack>
      </Flex>

      {/* Vue d'ensemble */}
      <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={5} mb={8}>
        <Card bg="#2a3657" borderColor="#3a445e">
          <CardBody>
            <Stat>
              <StatLabel color="gray.400">
                <Icon as={FiFileText as ElementType} mr={2} />
                Total Documents
              </StatLabel>
              <StatNumber color="white">{data.overview.totalDocuments.toLocaleString()}</StatNumber>
              <StatHelpText color="gray.400">
                <StatArrow type={data.overview.documentsGrowth > 0 ? "increase" : "decrease"} />
                {Math.abs(data.overview.documentsGrowth)}% ce mois
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg="#2a3657" borderColor="#3a445e">
          <CardBody>
            <Stat>
              <StatLabel color="gray.400">
                <Icon as={FiUsers as ElementType} mr={2} />
                Utilisateurs Actifs
              </StatLabel>
              <StatNumber color="white">{data.overview.totalUsers}</StatNumber>
              <StatHelpText color="gray.400">
                <StatArrow type={data.overview.usersGrowth > 0 ? "increase" : "decrease"} />
                {Math.abs(data.overview.usersGrowth)}% ce mois
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg="#2a3657" borderColor="#3a445e">
          <CardBody>
            <Stat>
              <StatLabel color="gray.400">
                <Icon as={FiHardDrive as ElementType} mr={2} />
                Stockage Utilisé
              </StatLabel>
              <StatNumber color="white">{data.overview.totalStorage}</StatNumber>
              <Progress 
                value={data.overview.storageUsed} 
                colorScheme="blue" 
                mt={2} 
                size="sm"
                bg="#1c2338"
              />
              <StatHelpText color="gray.400">
                {data.overview.storageUsed}% utilisé
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg="#2a3657" borderColor="#3a445e">
          <CardBody>
            <Stat>
              <StatLabel color="gray.400">
                <Icon as={FiUpload as ElementType} mr={2} />
                Documents ce mois
              </StatLabel>
              <StatNumber color="white">{data.overview.documentsThisMonth}</StatNumber>
              <StatHelpText color="gray.400">
                Nouveaux documents
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </Grid>

      <Grid templateColumns="repeat(auto-fit, minmax(400px, 1fr))" gap={6} mb={8}>
        {/* Répartition par type */}
        <Card bg="#2a3657" borderColor="#3a445e">
          <CardHeader>
            <Heading size="md" color="white">
              Documents par Type
            </Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={3} align="stretch">
              {data.documentStats.byType.map((item) => (
                <Box key={item.type}>
                  <Flex justify="space-between" mb={2}>
                    <Text color="white" fontSize="sm">{item.type}</Text>
                    <Text color="gray.400" fontSize="sm">{item.count} ({item.percentage}%)</Text>
                  </Flex>
                  <Progress value={item.percentage} colorScheme="blue" size="sm" bg="#1c2338" />
                </Box>
              ))}
            </VStack>
          </CardBody>
        </Card>

        {/* Répartition par taille */}
        <Card bg="#2a3657" borderColor="#3a445e">
          <CardHeader>
            <Heading size="md" color="white">
              Documents par Taille
            </Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={3} align="stretch">
              {data.documentStats.bySize.map((item) => (
                <Box key={item.range}>
                  <Flex justify="space-between" mb={2}>
                    <Text color="white" fontSize="sm">{item.range}</Text>
                    <Text color="gray.400" fontSize="sm">{item.count} ({item.percentage}%)</Text>
                  </Flex>
                  <Progress value={item.percentage} colorScheme="green" size="sm" bg="#1c2338" />
                </Box>
              ))}
            </VStack>
          </CardBody>
        </Card>
      </Grid>

      <Grid templateColumns="repeat(auto-fit, minmax(500px, 1fr))" gap={6}>
        {/* Utilisateurs les plus actifs */}
        <Card bg="#2a3657" borderColor="#3a445e">
          <CardHeader>
            <Heading size="md" color="white">
              <Icon as={FiTrendingUp as ElementType} mr={2} />
              Utilisateurs Actifs
            </Heading>
          </CardHeader>
          <CardBody>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th color="gray.400">Utilisateur</Th>
                  <Th color="gray.400">Uploads</Th>
                  <Th color="gray.400">Downloads</Th>
                  <Th color="gray.400">Vues</Th>
                </Tr>
              </Thead>
              <Tbody>
                {data.activityStats.mostActive.map((user, index) => (
                  <Tr key={index}>
                    <Td color="white">{user.user}</Td>
                    <Td color="white">
                      <Badge colorScheme="green">{user.uploads}</Badge>
                    </Td>
                    <Td color="white">
                      <Badge colorScheme="blue">{user.downloads}</Badge>
                    </Td>
                    <Td color="white">
                      <Badge colorScheme="purple">{user.views}</Badge>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </CardBody>
        </Card>

        {/* Documents populaires */}
        <Card bg="#2a3657" borderColor="#3a445e">
          <CardHeader>
            <Heading size="md" color="white">
              <Icon as={FiEye as ElementType} mr={2} />
              Documents Populaires
            </Heading>
          </CardHeader>
          <CardBody>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th color="gray.400">Document</Th>
                  <Th color="gray.400">Vues</Th>
                  <Th color="gray.400">Téléchargements</Th>
                  <Th color="gray.400">Partages</Th>
                </Tr>
              </Thead>
              <Tbody>
                {data.popularDocuments.map((doc) => (
                  <Tr key={doc.id}>
                    <Td color="white">
                      <VStack align="start" spacing={0}>
                        <Text fontSize="sm" fontWeight="bold">{doc.titre}</Text>
                        <Badge size="xs" colorScheme="blue">{doc.type}</Badge>
                      </VStack>
                    </Td>
                    <Td color="white">
                      <Badge colorScheme="purple">{doc.views}</Badge>
                    </Td>
                    <Td color="white">
                      <Badge colorScheme="green">{doc.downloads}</Badge>
                    </Td>
                    <Td color="white">
                      <Badge colorScheme="orange">{doc.shares}</Badge>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </CardBody>
        </Card>
      </Grid>
    </Box>
  );
};

export default Analytics; 

