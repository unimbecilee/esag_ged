import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Input,
  Button,
  useToast,
  Switch,
  Text,
  Divider,
  Select,
  Alert,
  AlertIcon,
  Badge,
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
  IconButton,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Textarea,
  Spinner,
  Card,
  CardBody,
  CardHeader,
  Flex,
  Icon,
  useDisclosure,
} from '@chakra-ui/react';
import {
  FiMail,
  FiSettings,
  FiCheck,
  FiX,
  FiSend,
  FiRefreshCw,
  FiEye,
  FiEdit,
  FiTrash2,
  FiPlus,
} from 'react-icons/fi';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import { checkAuthToken } from '../utils/errorHandling';
import { API_URL } from '../config';
import { asElementType } from '../utils/iconUtils';

interface EmailConfig {
  mail_server: string;
  mail_port: number;
  mail_use_tls: boolean;
  mail_use_ssl: boolean;
  mail_username: string;
  mail_password: string;
  mail_default_sender: string;
  mail_max_emails: number;
  is_configured: boolean;
  providers: Record<string, any>;
}

interface EmailTemplate {
  id: number;
  name: string;
  subject: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface EmailLog {
  id: number;
  recipients: string;
  subject: string;
  sender: string;
  sent_at: string;
  status: string;
}

const EmailSettings: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();
  const { isOpen: isTestModalOpen, onOpen: onTestModalOpen, onClose: onTestModalClose } = useDisclosure();
  
  // États pour la configuration
  const [config, setConfig] = useState<EmailConfig>({
    mail_server: '',
    mail_port: 587,
    mail_use_tls: true,
    mail_use_ssl: false,
    mail_username: '',
    mail_password: '',
    mail_default_sender: '',
    mail_max_emails: 50,
    is_configured: false,
    providers: {}
  });
  
  const [selectedProvider, setSelectedProvider] = useState('custom');
  const [testEmail, setTestEmail] = useState('');
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [isSendingTest, setIsSendingTest] = useState(false);
  
  // États pour les templates et logs
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [logs, setLogs] = useState<EmailLog[]>([]);
  const [logsPage, setLogsPage] = useState(1);
  const [logsTotalPages, setLogsTotalPages] = useState(0);

  useEffect(() => {
    loadEmailConfig();
    loadEmailTemplates();
    loadEmailLogs();
  }, []);

  const loadEmailConfig = async () => {
    const result = await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/email/config`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la récupération de la configuration');
        }

        return await response.json();
      },
      {
        loadingMessage: "Chargement de la configuration email...",
        errorMessage: "Impossible de charger la configuration email"
      }
    );

    if (result) {
      setConfig(result);
      // Détecter le fournisseur actuel
      const currentProvider = Object.keys(result.providers || {}).find(
        provider => result.providers[provider].MAIL_SERVER === result.mail_server
      );
      if (currentProvider) {
        setSelectedProvider(currentProvider);
      }
    }
  };

  const loadEmailTemplates = async () => {
    const result = await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/email/templates`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la récupération des templates');
        }

        return await response.json();
      },
      {
        errorMessage: "Impossible de charger les templates email"
      }
    );

    if (result) {
      setTemplates(result);
    }
  };

  const loadEmailLogs = async (page = 1) => {
    const result = await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/email/logs?page=${page}&per_page=20`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la récupération des logs');
        }

        return await response.json();
      },
      {
        errorMessage: "Impossible de charger les logs email"
      }
    );

    if (result) {
      setLogs(result.logs);
      setLogsPage(result.page);
      setLogsTotalPages(result.total_pages);
    }
  };

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    if (config.providers && config.providers[provider]) {
      const providerConfig = config.providers[provider];
      setConfig(prev => ({
        ...prev,
        mail_server: providerConfig.MAIL_SERVER || '',
        mail_port: providerConfig.MAIL_PORT || 587,
        mail_use_tls: providerConfig.MAIL_USE_TLS || true,
        mail_use_ssl: providerConfig.MAIL_USE_SSL || false,
      }));
    }
  };

  const handleSaveConfig = async () => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/email/config`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            mail_server: config.mail_server,
            mail_port: config.mail_port,
            mail_use_tls: config.mail_use_tls,
            mail_use_ssl: config.mail_use_ssl,
            mail_username: config.mail_username,
            mail_password: config.mail_password,
            mail_default_sender: config.mail_default_sender,
            mail_max_emails: config.mail_max_emails,
          })
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la sauvegarde');
        }
      },
      {
        loadingMessage: "Sauvegarde de la configuration...",
        successMessage: "Configuration email sauvegardée avec succès",
        errorMessage: "Impossible de sauvegarder la configuration"
      }
    );

    // Recharger la configuration
    await loadEmailConfig();
  };

  const handleTestConnection = async () => {
    setIsTestingConnection(true);
    try {
      const token = checkAuthToken();
      const response = await fetch(`${API_URL}/email/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const result = await response.json();

      if (result.success) {
        toast({
          title: "Test réussi",
          description: result.message,
          status: "success",
          duration: 5000,
          isClosable: true,
        });
      } else {
        toast({
          title: "Test échoué",
          description: result.message,
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur lors du test de connexion",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleSendTestEmail = async () => {
    if (!testEmail) {
      toast({
        title: "Email requis",
        description: "Veuillez saisir une adresse email pour le test",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsSendingTest(true);
    try {
      const token = checkAuthToken();
      const response = await fetch(`${API_URL}/email/send-test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: testEmail })
      });

      const result = await response.json();

      if (result.success) {
        toast({
          title: "Email envoyé",
          description: result.message,
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        onTestModalClose();
        setTestEmail('');
        // Recharger les logs
        await loadEmailLogs();
      } else {
        toast({
          title: "Échec d'envoi",
          description: result.message,
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Erreur lors de l'envoi de l'email de test",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSendingTest(false);
    }
  };

  return (
    <Box>
      <Heading color="white" mb={6}>
        <Icon as={asElementType(FiMail)} mr={3} />
        Configuration Email
      </Heading>

      <Tabs variant="enclosed" colorScheme="blue">
        <TabList>
          <Tab color="white" _selected={{ color: "blue.300", bg: "#2a3657" }}>
            <Icon as={asElementType(FiSettings)} mr={2} />
            Configuration SMTP
          </Tab>
          <Tab color="white" _selected={{ color: "blue.300", bg: "#2a3657" }}>
            <Icon as={asElementType(FiMail)} mr={2} />
            Templates
          </Tab>
          <Tab color="white" _selected={{ color: "blue.300", bg: "#2a3657" }}>
            <Icon as={asElementType(FiEye)} mr={2} />
            Logs d'envoi
          </Tab>
        </TabList>

        <TabPanels>
          {/* Configuration SMTP */}
          <TabPanel>
            <Card bg="#20243a" color="white">
              <CardHeader>
                <Flex justify="space-between" align="center">
                  <Heading size="md">Configuration SMTP</Heading>
                  <Badge colorScheme={config.is_configured ? "green" : "red"}>
                    {config.is_configured ? "Configuré" : "Non configuré"}
                  </Badge>
                </Flex>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  {/* Sélection du fournisseur */}
                  <FormControl>
                    <FormLabel>Fournisseur d'email</FormLabel>
                    <Select
                      value={selectedProvider}
                      onChange={(e) => handleProviderChange(e.target.value)}
                      bg="#2a2f4a"
                      borderColor="#363b5a"
                    >
                      {config.providers && Object.entries(config.providers).map(([key, provider]: [string, any]) => (
                        <option key={key} value={key}>
                          {provider.description}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  <Divider />

                  {/* Configuration serveur */}
                  <HStack spacing={4}>
                    <FormControl flex={3}>
                      <FormLabel>Serveur SMTP</FormLabel>
                      <Input
                        value={config.mail_server}
                        onChange={(e) => setConfig(prev => ({ ...prev, mail_server: e.target.value }))}
                        placeholder="smtp.gmail.com"
                        bg="#2a2f4a"
                        borderColor="#363b5a"
                      />
                    </FormControl>
                    <FormControl flex={1}>
                      <FormLabel>Port</FormLabel>
                      <Input
                        type="number"
                        value={config.mail_port}
                        onChange={(e) => setConfig(prev => ({ ...prev, mail_port: parseInt(e.target.value) || 587 }))}
                        bg="#2a2f4a"
                        borderColor="#363b5a"
                      />
                    </FormControl>
                  </HStack>

                  {/* Sécurité */}
                  <HStack spacing={8}>
                    <FormControl display="flex" alignItems="center">
                      <FormLabel mb={0}>Utiliser TLS</FormLabel>
                      <Switch
                        isChecked={config.mail_use_tls}
                        onChange={(e) => setConfig(prev => ({ ...prev, mail_use_tls: e.target.checked }))}
                        colorScheme="blue"
                      />
                    </FormControl>
                    <FormControl display="flex" alignItems="center">
                      <FormLabel mb={0}>Utiliser SSL</FormLabel>
                      <Switch
                        isChecked={config.mail_use_ssl}
                        onChange={(e) => setConfig(prev => ({ ...prev, mail_use_ssl: e.target.checked }))}
                        colorScheme="blue"
                      />
                    </FormControl>
                  </HStack>

                  {/* Authentification */}
                  <HStack spacing={4}>
                    <FormControl>
                      <FormLabel>Nom d'utilisateur</FormLabel>
                      <Input
                        value={config.mail_username}
                        onChange={(e) => setConfig(prev => ({ ...prev, mail_username: e.target.value }))}
                        placeholder="votre.email@gmail.com"
                        bg="#2a2f4a"
                        borderColor="#363b5a"
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel>Mot de passe</FormLabel>
                      <Input
                        type="password"
                        value={config.mail_password}
                        onChange={(e) => setConfig(prev => ({ ...prev, mail_password: e.target.value }))}
                        placeholder="Mot de passe ou mot de passe d'application"
                        bg="#2a2f4a"
                        borderColor="#363b5a"
                      />
                    </FormControl>
                  </HStack>

                  {/* Expéditeur par défaut */}
                  <FormControl>
                    <FormLabel>Expéditeur par défaut</FormLabel>
                    <Input
                      value={config.mail_default_sender}
                      onChange={(e) => setConfig(prev => ({ ...prev, mail_default_sender: e.target.value }))}
                      placeholder="noreply@esag.com"
                      bg="#2a2f4a"
                      borderColor="#363b5a"
                    />
                  </FormControl>

                  {/* Limite d'emails */}
                  <FormControl>
                    <FormLabel>Limite d'emails par connexion</FormLabel>
                    <Input
                      type="number"
                      value={config.mail_max_emails}
                      onChange={(e) => setConfig(prev => ({ ...prev, mail_max_emails: parseInt(e.target.value) || 50 }))}
                      bg="#2a2f4a"
                      borderColor="#363b5a"
                    />
                  </FormControl>

                  {/* Boutons d'action */}
                  <HStack spacing={4} pt={4}>
                    <Button
                      colorScheme="blue"
                      onClick={handleSaveConfig}
                      leftIcon={<Icon as={asElementType(FiCheck)} />}
                    >
                      Sauvegarder
                    </Button>
                    <Button
                      variant="outline"
                      colorScheme="blue"
                      onClick={handleTestConnection}
                      isLoading={isTestingConnection}
                      leftIcon={<Icon as={asElementType(FiRefreshCw)} />}
                    >
                      Tester la connexion
                    </Button>
                    <Button
                      variant="outline"
                      colorScheme="green"
                      onClick={onTestModalOpen}
                      leftIcon={<Icon as={asElementType(FiSend)} />}
                      isDisabled={!config.is_configured}
                    >
                      Envoyer un test
                    </Button>
                  </HStack>

                  {/* Aide pour Gmail */}
                  {selectedProvider === 'gmail' && (
                    <Alert status="info" bg="#2a3657" color="white">
                      <AlertIcon color="#3a8bfd" />
                      <Box>
                        <Text fontWeight="bold">Configuration Gmail</Text>
                        <Text fontSize="sm">
                          Pour Gmail, vous devez utiliser un "mot de passe d'application" au lieu de votre mot de passe habituel.
                          Activez l'authentification à 2 facteurs puis générez un mot de passe d'application dans les paramètres de sécurité.
                        </Text>
                      </Box>
                    </Alert>
                  )}
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>

          {/* Templates */}
          <TabPanel>
            <Card bg="#20243a" color="white">
              <CardHeader>
                <Flex justify="space-between" align="center">
                  <Heading size="md">Templates d'email</Heading>
                  <Button
                    size="sm"
                    colorScheme="blue"
                    leftIcon={<Icon as={asElementType(FiPlus)} />}
                  >
                    Nouveau template
                  </Button>
                </Flex>
              </CardHeader>
              <CardBody>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th color="gray.400">Nom</Th>
                      <Th color="gray.400">Sujet</Th>
                      <Th color="gray.400">Description</Th>
                      <Th color="gray.400">Statut</Th>
                      <Th color="gray.400">Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {templates.map((template) => (
                      <Tr key={template.id}>
                        <Td>{template.name}</Td>
                        <Td>{template.subject}</Td>
                        <Td>{template.description}</Td>
                        <Td>
                          <Badge colorScheme={template.is_active ? "green" : "gray"}>
                            {template.is_active ? "Actif" : "Inactif"}
                          </Badge>
                        </Td>
                        <Td>
                          <HStack spacing={2}>
                            <IconButton
                              aria-label="Voir"
                              icon={<Icon as={asElementType(FiEye)} />}
                              size="sm"
                              variant="ghost"
                              colorScheme="blue"
                            />
                            <IconButton
                              aria-label="Modifier"
                              icon={<Icon as={asElementType(FiEdit)} />}
                              size="sm"
                              variant="ghost"
                              colorScheme="yellow"
                            />
                          </HStack>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </CardBody>
            </Card>
          </TabPanel>

          {/* Logs */}
          <TabPanel>
            <Card bg="#20243a" color="white">
              <CardHeader>
                <Flex justify="space-between" align="center">
                  <Heading size="md">Logs d'envoi</Heading>
                  <Button
                    size="sm"
                    variant="outline"
                    colorScheme="blue"
                    leftIcon={<Icon as={asElementType(FiRefreshCw)} />}
                    onClick={() => loadEmailLogs()}
                  >
                    Actualiser
                  </Button>
                </Flex>
              </CardHeader>
              <CardBody>
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th color="gray.400">Date</Th>
                      <Th color="gray.400">Destinataires</Th>
                      <Th color="gray.400">Sujet</Th>
                      <Th color="gray.400">Expéditeur</Th>
                      <Th color="gray.400">Statut</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {logs.map((log) => (
                      <Tr key={log.id}>
                        <Td>{new Date(log.sent_at).toLocaleString('fr-FR')}</Td>
                        <Td>{log.recipients}</Td>
                        <Td>{log.subject}</Td>
                        <Td>{log.sender}</Td>
                        <Td>
                          <Badge colorScheme={log.status === 'sent' ? "green" : "red"}>
                            {log.status === 'sent' ? "Envoyé" : "Échec"}
                          </Badge>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>

                {/* Pagination */}
                {logsTotalPages > 1 && (
                  <Flex justify="center" mt={4}>
                    <HStack spacing={2}>
                      <Button
                        size="sm"
                        onClick={() => loadEmailLogs(logsPage - 1)}
                        isDisabled={logsPage <= 1}
                      >
                        Précédent
                      </Button>
                      <Text>
                        Page {logsPage} sur {logsTotalPages}
                      </Text>
                      <Button
                        size="sm"
                        onClick={() => loadEmailLogs(logsPage + 1)}
                        isDisabled={logsPage >= logsTotalPages}
                      >
                        Suivant
                      </Button>
                    </HStack>
                  </Flex>
                )}
              </CardBody>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* Modal de test d'email */}
      <Modal isOpen={isTestModalOpen} onClose={onTestModalClose}>
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white">
          <ModalHeader>Envoyer un email de test</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <FormControl>
              <FormLabel>Adresse email de test</FormLabel>
              <Input
                type="email"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="test@example.com"
                bg="#2a2f4a"
                borderColor="#363b5a"
              />
            </FormControl>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onTestModalClose}>
              Annuler
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSendTestEmail}
              isLoading={isSendingTest}
              leftIcon={<Icon as={asElementType(FiSend)} />}
            >
              Envoyer
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default EmailSettings; 

