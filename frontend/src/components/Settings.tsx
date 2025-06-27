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
  Icon,
  Text,
  useToast,
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
} from '@chakra-ui/react';
import { 
  FiUser, 
  FiSettings, 
  FiShield, 
  FiDatabase, 
  FiMail, 
  FiSave,
  FiEye,
  FiLock,
  FiCheck,
  FiCalendar,
  FiBriefcase,
  FiClock,
  FiMonitor,
  FiSun,
  FiMoon
} from 'react-icons/fi';
import { asElementType } from '../utils/iconUtils';
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
  service?: string;
  bio?: string;
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

const Settings: React.FC = () => {
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

  useEffect(() => {
    fetchCurrentUser();
    fetchUserSettings();
    if (currentUser?.role === 'admin') {
      fetchSystemSettings();
    }
  }, [currentUser?.role]);

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

  const fetchSystemSettings = async () => {
    const result = await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/settings/system`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (response.ok) {
          return await response.json();
        }
        return systemSettings;
      },
      {
        loadingMessage: "Chargement des paramètres système...",
        errorMessage: "Impossible de charger les paramètres système"
      }
    );

    if (result) {
      setSystemSettings({ ...systemSettings, ...result });
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
            service: currentUser?.service,
            bio: currentUser?.bio,
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

  const isAdmin = currentUser?.role === 'admin';

  const tabs = [
    { id: 'profile', label: 'Profil', icon: FiUser },
    { id: 'security', label: 'Sécurité', icon: FiShield },
    ...(isAdmin ? [{ id: 'system', label: 'Système', icon: FiDatabase }] : []),
  ];

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* En-tête */}
        <Box>
          <Flex align="center" mb={2}>
            <Icon as={asElementType(FiSettings)} boxSize={8} color="blue.400" mr={4} />
            <VStack align="start" spacing={0}>
              <Heading size="xl" color="white">
                Paramètres
              </Heading>
              <Text color="gray.400" fontSize="lg">
                Gérez vos préférences et votre compte
              </Text>
            </VStack>
          </Flex>
          
          {currentUser && (
            <Card bg="gray.700" mt={6}>
              <CardBody>
                <Flex align="center">
                  <Avatar
                    size="lg"
                    name={`${currentUser.prenom} ${currentUser.nom}`}
                    bg="blue.500"
                    color="white"
                    mr={4}
                  />
                  <VStack align="start" spacing={1}>
                    <Text fontSize="xl" fontWeight="bold" color="white">
                      {currentUser.prenom} {currentUser.nom}
                    </Text>
                    <Text color="gray.300">{currentUser.email}</Text>
                    <HStack>
                      <Badge colorScheme={currentUser.role === 'admin' ? 'red' : 'blue'}>
                        {currentUser.role}
                      </Badge>
                      {currentUser.derniere_connexion && (
                        <Text fontSize="sm" color="gray.400">
                          Dernière connexion: {new Date(currentUser.derniere_connexion).toLocaleDateString('fr-FR')}
                        </Text>
                      )}
                    </HStack>
                  </VStack>
                </Flex>
              </CardBody>
            </Card>
          )}
        </Box>

        {/* Navigation par onglets */}
        <Tabs
          index={activeTab}
          onChange={setActiveTab}
          variant="enclosed"
          colorScheme="blue"
          isLazy
        >
          <TabList bg="gray.700" borderRadius="lg" p={2}>
            {tabs.map((tab, index) => (
              <Tab
                key={tab.id}
                color="gray.300"
                _selected={{
                  color: 'white',
                  bg: 'blue.600',
                  borderColor: 'blue.600',
                }}
                _hover={{
                  color: 'white',
                  bg: 'gray.600',
                }}
                borderRadius="md"
                mr={2}
              >
                <HStack spacing={2}>
                  <Icon as={asElementType(tab.icon)} />
                  <Text>{tab.label}</Text>
                </HStack>
              </Tab>
            ))}
          </TabList>

          <TabPanels mt={6}>
            {/* Profil */}
            <TabPanel p={0}>
              <Card bg="gray.700">
                <CardHeader>
                  <HStack>
                    <Icon as={asElementType(FiUser)} color="blue.400" boxSize={6} />
                    <VStack align="start" spacing={0}>
                      <Heading size="lg" color="white">
                        Profil
                      </Heading>
                      <Text color="gray.400" fontSize="sm">
                        Informations personnelles et compte
                      </Text>
                    </VStack>
                  </HStack>
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

                    <FormControl>
                      <FormLabel color="gray.300">Service</FormLabel>
                      <Select
                        value={currentUser?.service || ''}
                        onChange={(e) => setCurrentUser(prev => prev ? { ...prev, service: e.target.value } : null)}
                        bg="gray.800"
                        color="white"
                        borderColor="gray.600"
                        placeholder="Sélectionnez votre service"
                      >
                        <option value="RH" style={{ backgroundColor: '#2D3748' }}>Ressources Humaines</option>
                        <option value="IT" style={{ backgroundColor: '#2D3748' }}>Informatique</option>
                        <option value="Finance" style={{ backgroundColor: '#2D3748' }}>Finance</option>
                        <option value="Marketing" style={{ backgroundColor: '#2D3748' }}>Marketing</option>
                        <option value="Operations" style={{ backgroundColor: '#2D3748' }}>Opérations</option>
                        <option value="Legal" style={{ backgroundColor: '#2D3748' }}>Juridique</option>
                      </Select>
                    </FormControl>

                    <FormControl>
                      <FormLabel color="gray.300">Bio</FormLabel>
                      <Textarea
                        value={currentUser?.bio || ''}
                        onChange={(e) => setCurrentUser(prev => prev ? { ...prev, bio: e.target.value } : null)}
                        bg="gray.800"
                        color="white"
                        borderColor="gray.600"
                        placeholder="Décrivez-vous en quelques mots..."
                        rows={3}
                      />
                    </FormControl>

                    <Flex justify="flex-end">
                      <Button
                        leftIcon={<Icon as={asElementType(FiSave)} />}
                        colorScheme="blue"
                        onClick={updateProfile}
                      >
                        Sauvegarder le profil
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
                  <HStack>
                    <Icon as={asElementType(FiShield)} color="blue.400" boxSize={6} />
                    <VStack align="start" spacing={0}>
                      <Heading size="lg" color="white">
                        Sécurité
                      </Heading>
                      <Text color="gray.400" fontSize="sm">
                        Mot de passe et authentification
                      </Text>
                    </VStack>
                  </HStack>
                </CardHeader>
                <Divider borderColor="gray.600" />
                <CardBody>
                  <VStack spacing={6} align="stretch">
                    <Box>
                      <Heading size="md" color="white" mb={4}>
                        Changer le mot de passe
                      </Heading>
                      
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
                            onChange={(e) => handlePasswordChange(e.target.value)}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                          {passwordData.new && (
                            <Box mt={2}>
                              <Text fontSize="sm" color="gray.400" mb={1}>
                                Force du mot de passe: {passwordStrength}%
                              </Text>
                              <Progress
                                value={passwordStrength}
                                colorScheme={passwordStrength < 50 ? 'red' : passwordStrength < 75 ? 'yellow' : 'green'}
                                size="sm"
                              />
                            </Box>
                          )}
                        </FormControl>

                        <FormControl>
                          <FormLabel color="gray.300">Confirmer le nouveau mot de passe</FormLabel>
                          <Input
                            type="password"
                            value={passwordData.confirm}
                            onChange={(e) => setPasswordData({ ...passwordData, confirm: e.target.value })}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>

                        <Alert status="info" bg="blue.900" borderColor="blue.600">
                          <AlertIcon />
                          <Box>
                            <AlertTitle>Conseils de sécurité:</AlertTitle>
                            <AlertDescription>
                              Utilisez au moins 8 caractères avec des majuscules, minuscules, chiffres et symboles.
                            </AlertDescription>
                          </Box>
                        </Alert>

                        <Flex justify="flex-end">
                          <Button
                            leftIcon={<Icon as={asElementType(FiLock)} />}
                            colorScheme="blue"
                            onClick={changePassword}
                            isDisabled={!passwordData.current || !passwordData.new || !passwordData.confirm}
                          >
                            Changer le mot de passe
                          </Button>
                        </Flex>
                      </VStack>
                    </Box>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Système (Admin seulement) */}
            {isAdmin && (
              <TabPanel p={0}>
                <Card bg="gray.700">
                  <CardHeader>
                    <HStack>
                      <Icon as={asElementType(FiDatabase)} color="blue.400" boxSize={6} />
                      <VStack align="start" spacing={0}>
                        <Heading size="lg" color="white">
                          Système
                        </Heading>
                        <Text color="gray.400" fontSize="sm">
                          Configuration système (Admin uniquement)
                        </Text>
                      </VStack>
                    </HStack>
                  </CardHeader>
                  <Divider borderColor="gray.600" />
                  <CardBody>
                    <VStack spacing={6} align="stretch">
                      <Alert status="warning" bg="orange.900" borderColor="orange.600">
                        <AlertIcon />
                        <Box>
                          <AlertTitle>Attention!</AlertTitle>
                          <AlertDescription>
                            Ces paramètres affectent l'ensemble du système. Modifiez avec précaution.
                          </AlertDescription>
                        </Box>
                      </Alert>

                      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                        <FormControl>
                          <FormLabel color="gray.300">Taille max fichier (MB)</FormLabel>
                          <Input
                            type="number"
                            value={systemSettings.taille_max_fichier}
                            onChange={(e) => setSystemSettings({ ...systemSettings, taille_max_fichier: parseInt(e.target.value) || 0 })}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>

                        <FormControl>
                          <FormLabel color="gray.300">Rétention corbeille (jours)</FormLabel>
                          <Input
                            type="number"
                            value={systemSettings.retention_corbeille}
                            onChange={(e) => setSystemSettings({ ...systemSettings, retention_corbeille: parseInt(e.target.value) || 0 })}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>

                        <FormControl>
                          <FormLabel color="gray.300">Nombre max d'utilisateurs</FormLabel>
                          <Input
                            type="number"
                            value={systemSettings.max_users}
                            onChange={(e) => setSystemSettings({ ...systemSettings, max_users: parseInt(e.target.value) || 0 })}
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>
                      </SimpleGrid>

                      <FormControl display="flex" alignItems="center" justifyContent="space-between">
                        <VStack align="start" spacing={0}>
                          <FormLabel color="white" mb={0}>
                            Mode maintenance
                          </FormLabel>
                          <Text fontSize="sm" color="gray.400">
                            Activer le mode maintenance pour bloquer l'accès aux utilisateurs
                          </Text>
                        </VStack>
                        <Switch
                          isChecked={systemSettings.maintenance_mode}
                          onChange={(e) => setSystemSettings({ ...systemSettings, maintenance_mode: e.target.checked })}
                          colorScheme="red"
                        />
                      </FormControl>

                      <Flex justify="flex-end">
                        <Button
                          leftIcon={<Icon as={asElementType(FiSave)} />}
                          colorScheme="blue"
                          onClick={saveSystemSettings}
                        >
                          Sauvegarder les paramètres système
                        </Button>
                      </Flex>
                    </VStack>
                  </CardBody>
                </Card>
              </TabPanel>
            )}
          </TabPanels>
        </Tabs>
      </VStack>
    </Container>
  );
};

export default Settings; 

