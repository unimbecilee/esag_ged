import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Heading,
  VStack,
  HStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Card,
  CardBody,
  CardHeader,
  Text,
  Divider,
  Badge,
  Flex,
  Avatar,
  FormControl,
  FormLabel,
  Input,
  Button,
  Switch,
  Select,
  SimpleGrid,
  Textarea,
  Progress,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useToast,
} from '@chakra-ui/react';
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import { checkAuthToken } from '../utils/errorHandling';
import { API_URL } from '../config';

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: string;
  date_creation?: string;
  derniere_connexion?: string;
}

interface UserSettings {
  email_notifications: boolean;
  app_notifications: boolean;
  digest_frequency: string;
  quiet_hours_start: string;
  quiet_hours_end: string;
  weekend_notifications: boolean;
  langue: string;
  theme: string;
  format_date: string;
  fuseau_horaire: string;
  compact_mode: boolean;
  animations: boolean;
  high_contrast: boolean;
}

interface SystemSettings {
  taille_max_fichier: number;
  retention_corbeille: number;
  max_users: number;
  maintenance_mode: boolean;
}

const SettingsSimple: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userSettings, setUserSettings] = useState<UserSettings>({
    email_notifications: true,
    app_notifications: true,
    digest_frequency: 'daily',
    quiet_hours_start: '22:00',
    quiet_hours_end: '08:00',
    weekend_notifications: false,
    langue: 'fr',
    theme: 'dark',
    format_date: 'DD/MM/YYYY',
    fuseau_horaire: 'Europe/Paris',
    compact_mode: false,
    animations: true,
    high_contrast: false,
  });
  const [systemSettings, setSystemSettings] = useState<SystemSettings>({
    taille_max_fichier: 10,
    retention_corbeille: 30,
    max_users: 100,
    maintenance_mode: false,
  });
  const [activeTab, setActiveTab] = useState(0);
  const [passwordData, setPasswordData] = useState({
    current: '',
    new: '',
    confirm: '',
  });
  const [passwordStrength, setPasswordStrength] = useState(0);
  const toast = useToast();

  // Vérifie si l'utilisateur est admin
  const isAdmin = currentUser?.role === 'ADMIN';

  useEffect(() => {
    fetchCurrentUser();
    fetchUserSettings();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const token = checkAuthToken();
      const response = await fetch(`${API_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const user = await response.json();
        setCurrentUser(user);
      }
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'utilisateur:', error);
    }
  };

  const fetchUserSettings = async () => {
    const result = await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/settings/user`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          return await response.json();
        }
        return userSettings; // Valeurs par défaut si pas de settings
      },
      {
        loadingMessage: "Chargement des paramètres...",
        errorMessage: "Impossible de charger les paramètres"
      }
    );

    if (result) {
      setUserSettings({ ...userSettings, ...result });
    }
  };

  const saveUserSettings = async () => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/settings/user`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(userSettings),
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la sauvegarde');
        }
      },
      {
        loadingMessage: "Sauvegarde...",
        successMessage: "Paramètres sauvegardés avec succès",
        errorMessage: "Impossible de sauvegarder les paramètres"
      }
    );
  };

  const saveSystemSettings = async () => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/settings/system`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(systemSettings),
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la sauvegarde');
        }
      },
      {
        loadingMessage: "Sauvegarde des paramètres système...",
        successMessage: "Paramètres système sauvegardés",
        errorMessage: "Impossible de sauvegarder les paramètres système"
      }
    );
  };

  const updateProfile = async () => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/auth/profile`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            nom: currentUser?.nom,
            prenom: currentUser?.prenom,
          }),
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la mise à jour du profil');
        }
      },
      {
        loadingMessage: "Mise à jour du profil...",
        successMessage: "Profil mis à jour avec succès",
        errorMessage: "Impossible de mettre à jour le profil"
      }
    );
  };

  const changePassword = async () => {
    if (passwordData.new !== passwordData.confirm) {
      toast({
        title: "Erreur",
        description: "Les mots de passe ne correspondent pas",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/auth/change-password`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            current_password: passwordData.current,
            new_password: passwordData.new,
          }),
        });

        if (!response.ok) {
          throw new Error('Erreur lors du changement de mot de passe');
        }

        setPasswordData({ current: '', new: '', confirm: '' });
      },
      {
        loadingMessage: "Changement du mot de passe...",
        successMessage: "Mot de passe changé avec succès",
        errorMessage: "Impossible de changer le mot de passe"
      }
    );
  };

  const calculatePasswordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (/[A-Z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 25;
    if (/[^A-Za-z0-9]/.test(password)) strength += 25;
    return strength;
  };

  const handlePasswordChange = (value: string) => {
    setPasswordData({ ...passwordData, new: value });
    setPasswordStrength(calculatePasswordStrength(value));
  };

  return (
    <Container maxW="container.lg" py={8}>
      <Box mb={8}>
        <Flex align="center" mb={4}>
                  <Avatar
            size="xl"
            name={`${currentUser?.prenom || ''} ${currentUser?.nom || ''}`}
                    bg="blue.500"
                    color="white"
            mr={6}
          />
          <Box>
            <Heading size="xl" color="white">
              {currentUser?.prenom || ''} {currentUser?.nom || ''}
            </Heading>
            <Flex align="center" mt={1}>
              <Text color="gray.400">{currentUser?.email || ''}</Text>
              <Badge ml={2} colorScheme={currentUser?.role === 'ADMIN' ? 'red' : 'blue'}>
                {currentUser?.role || ''}
                      </Badge>
            </Flex>
          </Box>
                </Flex>
        </Box>

      <Box>
        <Tabs
          variant="enclosed"
          colorScheme="blue"
          index={activeTab}
          onChange={setActiveTab}
          isLazy
        >
          <TabList bg="gray.700" borderRadius="lg" p={2}>
            <Tab color="gray.300" _selected={{ color: 'white', bg: 'blue.600' }}>
              👤 Profil
            </Tab>
            <Tab color="gray.300" _selected={{ color: 'white', bg: 'blue.600' }}>
              🔒 Sécurité
            </Tab>
            {isAdmin && (
              <Tab color="gray.300" _selected={{ color: 'white', bg: 'blue.600' }}>
                ⚙️ Système
              </Tab>
            )}
          </TabList>

          <TabPanels mt={6}>
            {/* Profil */}
            <TabPanel p={0}>
              <Card bg="gray.700">
                <CardHeader>
                  <Heading size="lg" color="white">
                    👤 Profil
                  </Heading>
                  <Text color="gray.400" fontSize="sm">
                    Informations personnelles et compte
                  </Text>
                </CardHeader>
                <Divider borderColor="gray.600" />
                <CardBody>
                  <VStack spacing={6} align="stretch">
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <FormControl>
                        <FormLabel color="gray.300">Prénom</FormLabel>
                        <Input
                          value={currentUser?.prenom || ''}
                          onChange={(e) => setCurrentUser(prev => prev ? { ...prev, prenom: e.target.value } : null)}
                          bg="gray.800"
                          color="white"
                          borderColor="gray.600"
                        />
                      </FormControl>
                      <FormControl>
                        <FormLabel color="gray.300">Nom</FormLabel>
                        <Input
                          value={currentUser?.nom || ''}
                          onChange={(e) => setCurrentUser(prev => prev ? { ...prev, nom: e.target.value } : null)}
                          bg="gray.800"
                          color="white"
                          borderColor="gray.600"
                        />
                      </FormControl>
                    </SimpleGrid>
                    
                    <FormControl>
                      <FormLabel color="gray.300">Email</FormLabel>
                      <Input
                        value={currentUser?.email || ''}
                        isReadOnly
                        bg="gray.800"
                        color="gray.400"
                        borderColor="gray.600"
                      />
                      <Text fontSize="xs" color="gray.500" mt={1}>
                        L'email ne peut pas être modifié
                      </Text>
                    </FormControl>

                    <Flex justify="flex-end">
                      <Button colorScheme="blue" onClick={updateProfile}>
                        💾 Sauvegarder le profil
                      </Button>
                    </Flex>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Sécurité */}
            <TabPanel p={0}>
              <Card bg="gray.700">
                <CardHeader>
                  <Heading size="lg" color="white">
                    🔒 Sécurité
                  </Heading>
                  <Text color="gray.400" fontSize="sm">
                    Mot de passe et options de sécurité
                  </Text>
                </CardHeader>
                <Divider borderColor="gray.600" />
                <CardBody>
                  <VStack spacing={6} align="stretch">
                    <Box>
                      <Text color="white" fontWeight="bold" mb={4}>
                        🔑 Changement de mot de passe
                      </Text>
                      <VStack spacing={4} align="stretch">
                        <FormControl>
                          <FormLabel color="gray.300">Mot de passe actuel</FormLabel>
                          <Input
                            type="password"
                            value={passwordData.current}
                            onChange={(e) => setPasswordData({ ...passwordData, current: e.target.value })}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel color="gray.300">Nouveau mot de passe</FormLabel>
                          <Input
                            type="password"
                            value={passwordData.new}
                            onChange={(e) => {
                              setPasswordData({ ...passwordData, new: e.target.value });
                              handlePasswordChange(e.target.value);
                            }}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                            <Box mt={2}>
                            <Progress value={passwordStrength} colorScheme={passwordStrength < 40 ? "red" : passwordStrength < 70 ? "yellow" : "green"} size="sm" borderRadius="md" />
                            <Text fontSize="xs" color="gray.400" mt={1}>
                              Force: {passwordStrength < 40 ? "Faible" : passwordStrength < 70 ? "Moyenne" : "Forte"}
                              </Text>
                            </Box>
                        </FormControl>
                        <FormControl>
                          <FormLabel color="gray.300">Confirmer le mot de passe</FormLabel>
                          <Input
                            type="password"
                            value={passwordData.confirm}
                            onChange={(e) => setPasswordData({ ...passwordData, confirm: e.target.value })}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                          {passwordData.new && passwordData.confirm && passwordData.new !== passwordData.confirm && (
                            <Text fontSize="sm" color="red.400" mt={1}>
                              Les mots de passe ne correspondent pas
                            </Text>
                          )}
                        </FormControl>
                        <Flex justify="flex-end">
                          <Button
                            colorScheme="blue"
                            onClick={changePassword}
                            isDisabled={!passwordData.current || !passwordData.new || !passwordData.confirm || passwordData.new !== passwordData.confirm}
                          >
                            💾 Changer le mot de passe
                          </Button>
                        </Flex>
                      </VStack>
                    </Box>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Système (Admin uniquement) */}
            {isAdmin && (
              <TabPanel p={0}>
                <Card bg="gray.700">
                  <CardHeader>
                    <Heading size="lg" color="white">
                      ⚙️ Paramètres système
                    </Heading>
                    <Text color="gray.400" fontSize="sm">
                      Configuration globale de l'application (Admin uniquement)
                    </Text>
                  </CardHeader>
                  <Divider borderColor="gray.600" />
                  <CardBody>
                    <VStack spacing={6} align="stretch">
                        <Box>
                        <Text color="white" fontWeight="bold" mb={4}>
                          📁 Gestion des fichiers
                        </Text>
                        <FormControl>
                          <FormLabel color="gray.300">Taille maximale des fichiers (MB)</FormLabel>
                          <Input
                            type="number"
                            value={systemSettings.taille_max_fichier}
                            onChange={(e) => setSystemSettings({ ...systemSettings, taille_max_fichier: Number(e.target.value) })}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>
                        <FormControl mt={4}>
                          <FormLabel color="gray.300">Durée de rétention dans la corbeille (jours)</FormLabel>
                          <Input
                            type="number"
                            value={systemSettings.retention_corbeille}
                            onChange={(e) => setSystemSettings({ ...systemSettings, retention_corbeille: Number(e.target.value) })}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>
                      </Box>

                      <Divider borderColor="gray.600" />

                      <Box>
                        <Text color="white" fontWeight="bold" mb={4}>
                          👥 Utilisateurs
                        </Text>
                        <FormControl>
                          <FormLabel color="gray.300">Nombre maximum d'utilisateurs</FormLabel>
                          <Input
                            type="number"
                            value={systemSettings.max_users}
                            onChange={(e) => setSystemSettings({ ...systemSettings, max_users: Number(e.target.value) })}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>
                      </Box>

                      <Divider borderColor="gray.600" />

                      <Box>
                        <Text color="white" fontWeight="bold" mb={4}>
                          🔧 Maintenance
                        </Text>
                      <FormControl display="flex" alignItems="center" justifyContent="space-between">
                        <VStack align="start" spacing={0}>
                          <FormLabel color="white" mb={0}>
                            Mode maintenance
                          </FormLabel>
                          <Text fontSize="sm" color="gray.400">
                              Activer le mode maintenance (seuls les admins pourront se connecter)
                          </Text>
                        </VStack>
                        <Switch
                          isChecked={systemSettings.maintenance_mode}
                          onChange={(e) => setSystemSettings({ ...systemSettings, maintenance_mode: e.target.checked })}
                            colorScheme="blue"
                        />
                      </FormControl>
                      </Box>

                      <Flex justify="flex-end">
                        <Button colorScheme="blue" onClick={saveSystemSettings}>
                          💾 Sauvegarder les paramètres système
                        </Button>
                      </Flex>
                    </VStack>
                  </CardBody>
                </Card>
              </TabPanel>
            )}
          </TabPanels>
        </Tabs>
      </Box>
    </Container>
  );
};

export default SettingsSimple; 

