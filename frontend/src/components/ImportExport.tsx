import React, { useState, useRef } from "react";
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
  Input,
  Select,
  Checkbox,
  Progress,
  useToast,
  Flex,
  Icon,
  List,
  ListItem,
  ListIcon,
  Badge,
  Divider,
  Textarea,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  FormControl,
  FormLabel,
  FormHelperText,
  Switch,
} from "@chakra-ui/react";
import {
  FiUpload,
  FiDownload,
  FiFileText,
  FiFolder,
  FiCheck,
  FiX,
  FiAlertCircle,
  FiRefreshCw,
  FiSettings,
  FiArchive,
  FiDatabase,
  FiCloud,
} from "react-icons/fi";
import { ElementType } from "react";
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';

interface ImportJob {
  id: string;
  fileName: string;
  fileSize: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  documentsImported: number;
  errors: string[];
  createdAt: string;
}

interface ExportJob {
  id: string;
  name: string;
  format: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  documentsCount: number;
  downloadUrl?: string;
  createdAt: string;
}

const ImportExport: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Import state
  const [importJobs, setImportJobs] = useState<ImportJob[]>([]);
  const [importFormat, setImportFormat] = useState("zip");
  const [preserveStructure, setPreserveStructure] = useState(true);
  const [autoTag, setAutoTag] = useState(false);
  const [duplicateHandling, setDuplicateHandling] = useState("skip");

  // Export state
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [exportFormat, setExportFormat] = useState("zip");
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [includeVersions, setIncludeVersions] = useState(false);
  const [exportFilter, setExportFilter] = useState("");

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    for (const file of Array.from(files)) {
      const newJob: ImportJob = {
        id: `import-${Date.now()}-${Math.random()}`,
        fileName: file.name,
        fileSize: formatFileSize(file.size),
        status: 'pending',
        progress: 0,
        documentsImported: 0,
        errors: [],
        createdAt: new Date().toISOString(),
      };

      setImportJobs(prev => [...prev, newJob]);
      await processImport(newJob, file);
    }
  };

  const processImport = async (job: ImportJob, file: File) => {
    try {
      // Mise à jour du statut à "processing"
      setImportJobs(prev => prev.map(j => 
        j.id === job.id ? { ...j, status: 'processing' as const } : j
      ));

      await executeOperation(
        async () => {
          const formData = new FormData();
          formData.append('file', file);
          formData.append('format', importFormat);
          formData.append('preserveStructure', preserveStructure.toString());
          formData.append('autoTag', autoTag.toString());
          formData.append('duplicateHandling', duplicateHandling);

          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/documents/import`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
            body: formData,
          });

          if (!response.ok) {
            throw new Error('Erreur lors de l\'import');
          }

          // Simulation de progression
          for (let i = 0; i <= 100; i += 10) {
            setImportJobs(prev => prev.map(j => 
              j.id === job.id ? { ...j, progress: i } : j
            ));
            await new Promise(resolve => setTimeout(resolve, 200));
          }

          const result = await response.json();
          
          // Mise à jour finale
          setImportJobs(prev => prev.map(j => 
            j.id === job.id ? { 
              ...j, 
              status: 'completed' as const,
              progress: 100,
              documentsImported: result.documentsImported || 0
            } : j
          ));

          return result;
        },
        {
          loadingMessage: "Import en cours...",
          successMessage: `Import terminé: ${job.fileName}`,
          errorMessage: "Erreur lors de l'import"
        }
      );
    } catch (error) {
      setImportJobs(prev => prev.map(j => 
        j.id === job.id ? { 
          ...j, 
          status: 'error' as const,
          errors: [error instanceof Error ? error.message : 'Erreur inconnue']
        } : j
      ));
    }
  };

  const handleExport = async () => {
    const newJob: ExportJob = {
      id: `export-${Date.now()}`,
      name: `Export_${new Date().toISOString().split('T')[0]}`,
      format: exportFormat,
      status: 'pending',
      progress: 0,
      documentsCount: 0,
      createdAt: new Date().toISOString(),
    };

    setExportJobs(prev => [...prev, newJob]);

    try {
      setExportJobs(prev => prev.map(j => 
        j.id === newJob.id ? { ...j, status: 'processing' as const } : j
      ));

      await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/documents/export`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              format: exportFormat,
              includeMetadata,
              includeVersions,
              filter: exportFilter
            }),
          });

          if (!response.ok) {
            throw new Error('Erreur lors de l\'export');
          }

          // Simulation de progression
          for (let i = 0; i <= 100; i += 20) {
            setExportJobs(prev => prev.map(j => 
              j.id === newJob.id ? { ...j, progress: i } : j
            ));
            await new Promise(resolve => setTimeout(resolve, 500));
          }

          const result = await response.json();
          
          setExportJobs(prev => prev.map(j => 
            j.id === newJob.id ? { 
              ...j, 
              status: 'completed' as const,
              progress: 100,
              documentsCount: result.documentsCount || 0,
              downloadUrl: result.downloadUrl
            } : j
          ));

          return result;
        },
        {
          loadingMessage: "Export en cours...",
          successMessage: "Export terminé avec succès",
          errorMessage: "Erreur lors de l'export"
        }
      );
    } catch (error) {
      setExportJobs(prev => prev.map(j => 
        j.id === newJob.id ? { 
          ...j, 
          status: 'error' as const
        } : j
      ));
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'processing': return 'blue';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return FiCheck;
      case 'processing': return FiRefreshCw;
      case 'error': return FiX;
      default: return FiAlertCircle;
    }
  };

  return (
    <Box p={5}>
      <Heading size="lg" color="white" mb={6}>
        <Icon as={FiArchive as ElementType} mr={3} />
        Import / Export
      </Heading>

      <Tabs colorScheme="blue" variant="enclosed">
        <TabList>
          <Tab color="white" _selected={{ color: "white", bg: "#3a8bfd" }}>
            <Icon as={FiUpload as ElementType} mr={2} />
            Import
          </Tab>
          <Tab color="white" _selected={{ color: "white", bg: "#3a8bfd" }}>
            <Icon as={FiDownload as ElementType} mr={2} />
            Export
          </Tab>
        </TabList>

        <TabPanels>
          {/* Onglet Import */}
          <TabPanel px={0}>
            <Grid templateColumns="1fr 2fr" gap={6}>
              {/* Configuration Import */}
              <Card bg="#2a3657" borderColor="#3a445e">
                <CardHeader>
                  <Heading size="md" color="white">
                    <Icon as={FiSettings as ElementType} mr={2} />
                    Configuration Import
                  </Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <FormControl>
                      <FormLabel color="white">Format d'import</FormLabel>
                      <Select
                        value={importFormat}
                        onChange={(e) => setImportFormat(e.target.value)}
                        bg="#1c2338"
                        color="white"
                        borderColor="#3a445e"
                      >
                        <option value="zip">Archive ZIP</option>
                        <option value="csv">Fichier CSV</option>
                        <option value="excel">Fichier Excel</option>
                        <option value="folder">Dossier</option>
                      </Select>
                      <FormHelperText color="gray.400">
                        Format du fichier à importer
                      </FormHelperText>
                    </FormControl>

                    <FormControl>
                      <HStack justify="space-between">
                        <FormLabel color="white" mb={0}>
                          Préserver la structure
                        </FormLabel>
                        <Switch
                          isChecked={preserveStructure}
                          onChange={(e) => setPreserveStructure(e.target.checked)}
                        />
                      </HStack>
                      <FormHelperText color="gray.400">
                        Conserver l'arborescence des dossiers
                      </FormHelperText>
                    </FormControl>

                    <FormControl>
                      <HStack justify="space-between">
                        <FormLabel color="white" mb={0}>
                          Tagage automatique
                        </FormLabel>
                        <Switch
                          isChecked={autoTag}
                          onChange={(e) => setAutoTag(e.target.checked)}
                        />
                      </HStack>
                      <FormHelperText color="gray.400">
                        Générer des tags basés sur le contenu
                      </FormHelperText>
                    </FormControl>

                    <FormControl>
                      <FormLabel color="white">Gestion des doublons</FormLabel>
                      <Select
                        value={duplicateHandling}
                        onChange={(e) => setDuplicateHandling(e.target.value)}
                        bg="#1c2338"
                        color="white"
                        borderColor="#3a445e"
                      >
                        <option value="skip">Ignorer</option>
                        <option value="overwrite">Écraser</option>
                        <option value="rename">Renommer</option>
                        <option value="version">Nouvelle version</option>
                      </Select>
                    </FormControl>

                    <Divider borderColor="#3a445e" />

                    <Input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileUpload}
                      multiple
                      accept=".zip,.csv,.xlsx,.xls"
                      display="none"
                    />
                    <Button
                      leftIcon={<Icon as={FiUpload as ElementType} />}
                      colorScheme="blue"
                      onClick={() => fileInputRef.current?.click()}
                      size="lg"
                    >
                      Sélectionner les fichiers
                    </Button>

                    <Alert status="info" bg="#1c2338" borderColor="#3a445e">
                      <AlertIcon color="#3a8bfd" />
                      <Box>
                        <AlertTitle color="white">Formats supportés:</AlertTitle>
                        <AlertDescription color="gray.400">
                          ZIP, CSV, Excel, et dossiers compressés
                        </AlertDescription>
                      </Box>
                    </Alert>
                  </VStack>
                </CardBody>
              </Card>

              {/* Jobs d'import */}
              <Card bg="#2a3657" borderColor="#3a445e">
                <CardHeader>
                  <Heading size="md" color="white">
                    Historique des imports
                  </Heading>
                </CardHeader>
                <CardBody>
                  {importJobs.length === 0 ? (
                    <Flex
                      justify="center"
                      align="center"
                      direction="column"
                      h="200px"
                      color="gray.400"
                    >
                      <Icon as={FiUpload as ElementType} boxSize={12} mb={4} />
                      <Text>Aucun import en cours</Text>
                    </Flex>
                  ) : (
                    <VStack spacing={4} align="stretch">
                      {importJobs.map((job) => (
                        <Box
                          key={job.id}
                          p={4}
                          bg="#1c2338"
                          borderRadius="md"
                          borderColor="#3a445e"
                          borderWidth="1px"
                        >
                          <Flex justify="space-between" align="center" mb={2}>
                            <Text color="white" fontWeight="bold" fontSize="sm">
                              {job.fileName}
                            </Text>
                            <Badge colorScheme={getStatusColor(job.status)}>
                              <Icon as={getStatusIcon(job.status) as ElementType} mr={1} />
                              {job.status}
                            </Badge>
                          </Flex>
                          <Text color="gray.400" fontSize="xs" mb={2}>
                            {job.fileSize} • {new Date(job.createdAt).toLocaleString()}
                          </Text>
                          {job.status === 'processing' && (
                            <Progress value={job.progress} colorScheme="blue" size="sm" />
                          )}
                          {job.status === 'completed' && (
                            <Text color="green.400" fontSize="sm">
                              {job.documentsImported} documents importés
                            </Text>
                          )}
                          {job.errors.length > 0 && (
                            <Text color="red.400" fontSize="sm">
                              Erreurs: {job.errors.join(', ')}
                            </Text>
                          )}
                        </Box>
                      ))}
                    </VStack>
                  )}
                </CardBody>
              </Card>
            </Grid>
          </TabPanel>

          {/* Onglet Export */}
          <TabPanel px={0}>
            <Grid templateColumns="1fr 2fr" gap={6}>
              {/* Configuration Export */}
              <Card bg="#2a3657" borderColor="#3a445e">
                <CardHeader>
                  <Heading size="md" color="white">
                    <Icon as={FiSettings as ElementType} mr={2} />
                    Configuration Export
                  </Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <FormControl>
                      <FormLabel color="white">Format d'export</FormLabel>
                      <Select
                        value={exportFormat}
                        onChange={(e) => setExportFormat(e.target.value)}
                        bg="#1c2338"
                        color="white"
                        borderColor="#3a445e"
                      >
                        <option value="zip">Archive ZIP</option>
                        <option value="csv">Fichier CSV</option>
                        <option value="excel">Fichier Excel</option>
                        <option value="pdf">Portfolio PDF</option>
                      </Select>
                    </FormControl>

                    <FormControl>
                      <HStack justify="space-between">
                        <FormLabel color="white" mb={0}>
                          Inclure les métadonnées
                        </FormLabel>
                        <Switch
                          isChecked={includeMetadata}
                          onChange={(e) => setIncludeMetadata(e.target.checked)}
                        />
                      </HStack>
                    </FormControl>

                    <FormControl>
                      <HStack justify="space-between">
                        <FormLabel color="white" mb={0}>
                          Inclure les versions
                        </FormLabel>
                        <Switch
                          isChecked={includeVersions}
                          onChange={(e) => setIncludeVersions(e.target.checked)}
                        />
                      </HStack>
                    </FormControl>

                    <FormControl>
                      <FormLabel color="white">Filtres d'export</FormLabel>
                      <Textarea
                        value={exportFilter}
                        onChange={(e) => setExportFilter(e.target.value)}
                        placeholder="Critères de filtrage (tags, dates, etc.)"
                        bg="#1c2338"
                        color="white"
                        borderColor="#3a445e"
                        rows={3}
                      />
                      <FormHelperText color="gray.400">
                        Laissez vide pour exporter tous les documents
                      </FormHelperText>
                    </FormControl>

                    <Divider borderColor="#3a445e" />

                    <Button
                      leftIcon={<Icon as={FiDownload as ElementType} />}
                      colorScheme="green"
                      onClick={handleExport}
                      size="lg"
                    >
                      Lancer l'export
                    </Button>
                  </VStack>
                </CardBody>
              </Card>

              {/* Jobs d'export */}
              <Card bg="#2a3657" borderColor="#3a445e">
                <CardHeader>
                  <Heading size="md" color="white">
                    Historique des exports
                  </Heading>
                </CardHeader>
                <CardBody>
                  {exportJobs.length === 0 ? (
                    <Flex
                      justify="center"
                      align="center"
                      direction="column"
                      h="200px"
                      color="gray.400"
                    >
                      <Icon as={FiDownload as ElementType} boxSize={12} mb={4} />
                      <Text>Aucun export en cours</Text>
                    </Flex>
                  ) : (
                    <VStack spacing={4} align="stretch">
                      {exportJobs.map((job) => (
                        <Box
                          key={job.id}
                          p={4}
                          bg="#1c2338"
                          borderRadius="md"
                          borderColor="#3a445e"
                          borderWidth="1px"
                        >
                          <Flex justify="space-between" align="center" mb={2}>
                            <Text color="white" fontWeight="bold" fontSize="sm">
                              {job.name}
                            </Text>
                            <Badge colorScheme={getStatusColor(job.status)}>
                              <Icon as={getStatusIcon(job.status) as ElementType} mr={1} />
                              {job.status}
                            </Badge>
                          </Flex>
                          <Text color="gray.400" fontSize="xs" mb={2}>
                            Format: {job.format.toUpperCase()} • {new Date(job.createdAt).toLocaleString()}
                          </Text>
                          {job.status === 'processing' && (
                            <Progress value={job.progress} colorScheme="green" size="sm" />
                          )}
                          {job.status === 'completed' && (
                            <HStack justify="space-between">
                              <Text color="green.400" fontSize="sm">
                                {job.documentsCount} documents exportés
                              </Text>
                              {job.downloadUrl && (
                                <Button
                                  size="xs"
                                  leftIcon={<Icon as={FiDownload as ElementType} />}
                                  colorScheme="blue"
                                  onClick={() => window.open(job.downloadUrl, '_blank')}
                                >
                                  Télécharger
                                </Button>
                              )}
                            </HStack>
                          )}
                        </Box>
                      ))}
                    </VStack>
                  )}
                </CardBody>
              </Card>
            </Grid>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default ImportExport; 