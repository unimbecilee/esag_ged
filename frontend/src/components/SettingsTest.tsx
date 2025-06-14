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
  useToast,
  SimpleGrid,
} from '@chakra-ui/react';

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: string;
  date_creation?: string;
  derniere_connexion?: string;
}

const SettingsTest: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const toast = useToast();

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('/api/auth/me', {
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

  const isAdmin = currentUser?.role === 'admin';

  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* En-tête */}
        <Box>
          <Flex align="center" mb={2}>
            <VStack align="start" spacing={0}>
              <Heading size="xl" color="white">
                ⚙️ Paramètres Modernes
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
            <Tab color="gray.300" _selected={{ color: 'white', bg: 'blue.600' }}>
              👤 Profil
            </Tab>
            <Tab color="gray.300" _selected={{ color: 'white', bg: 'blue.600' }}>
              🔔 Notifications
            </Tab>
            <Tab color="gray.300" _selected={{ color: 'white', bg: 'blue.600' }}>
              🔒 Sécurité
            </Tab>
            <Tab color="gray.300" _selected={{ color: 'white', bg: 'blue.600' }}>
              🌐 Interface
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
                  <VStack spacing={4} align="stretch">
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <FormControl>
                        <FormLabel color="gray.300">Prénom</FormLabel>
                        <Input
                          value={currentUser?.prenom || ''}
                          bg="gray.800"
                          color="white"
                          borderColor="gray.600"
                        />
                      </FormControl>
                      <FormControl>
                        <FormLabel color="gray.300">Nom</FormLabel>
                        <Input
                          value={currentUser?.nom || ''}
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
                        bg="gray.800"
                        color="white"
                        borderColor="gray.600"
                      />
                    </FormControl>
                    <Button colorScheme="blue" alignSelf="flex-end">
                      Sauvegarder
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Notifications */}
            <TabPanel p={0}>
              <Card bg="gray.700">
                <CardHeader>
                  <Heading size="lg" color="white">
                    🔔 Notifications
                  </Heading>
                  <Text color="gray.400" fontSize="sm">
                    Préférences de notification
                  </Text>
                </CardHeader>
                <Divider borderColor="gray.600" />
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <FormControl display="flex" alignItems="center" justifyContent="space-between">
                      <FormLabel color="white" mb={0}>
                        Notifications par email
                      </FormLabel>
                      <Switch colorScheme="blue" />
                    </FormControl>
                    <FormControl display="flex" alignItems="center" justifyContent="space-between">
                      <FormLabel color="white" mb={0}>
                        Notifications dans l'app
                      </FormLabel>
                      <Switch colorScheme="blue" />
                    </FormControl>
                    <Button colorScheme="blue" alignSelf="flex-end">
                      Sauvegarder
                    </Button>
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
                    Mot de passe et authentification
                  </Text>
                </CardHeader>
                <Divider borderColor="gray.600" />
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <FormControl>
                      <FormLabel color="gray.300">Mot de passe actuel</FormLabel>
                      <Input
                        type="password"
                        bg="gray.800"
                        color="white"
                        borderColor="gray.600"
                      />
                    </FormControl>
                    <FormControl>
                      <FormLabel color="gray.300">Nouveau mot de passe</FormLabel>
                      <Input
                        type="password"
                        bg="gray.800"
                        color="white"
                        borderColor="gray.600"
                      />
                    </FormControl>
                    <Button colorScheme="blue" alignSelf="flex-end">
                      Changer le mot de passe
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Interface */}
            <TabPanel p={0}>
              <Card bg="gray.700">
                <CardHeader>
                  <Heading size="lg" color="white">
                    🌐 Interface
                  </Heading>
                  <Text color="gray.400" fontSize="sm">
                    Langue, thème et affichage
                  </Text>
                </CardHeader>
                <Divider borderColor="gray.600" />
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                      <FormControl>
                        <FormLabel color="gray.300">Langue</FormLabel>
                        <Select bg="gray.800" color="white" borderColor="gray.600">
                          <option value="fr" style={{ backgroundColor: '#2D3748' }}>🇫🇷 Français</option>
                          <option value="en" style={{ backgroundColor: '#2D3748' }}>🇺🇸 English</option>
                        </Select>
                      </FormControl>
                      <FormControl>
                        <FormLabel color="gray.300">Thème</FormLabel>
                        <Select bg="gray.800" color="white" borderColor="gray.600">
                          <option value="dark" style={{ backgroundColor: '#2D3748' }}>🌙 Sombre</option>
                          <option value="light" style={{ backgroundColor: '#2D3748' }}>☀️ Clair</option>
                        </Select>
                      </FormControl>
                    </SimpleGrid>
                    <Button colorScheme="blue" alignSelf="flex-end">
                      Sauvegarder
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            </TabPanel>

            {/* Système (Admin seulement) */}
            {isAdmin && (
              <TabPanel p={0}>
                <Card bg="gray.700">
                  <CardHeader>
                    <Heading size="lg" color="white">
                      ⚙️ Système
                    </Heading>
                    <Text color="gray.400" fontSize="sm">
                      Configuration système
                    </Text>
                  </CardHeader>
                  <Divider borderColor="gray.600" />
                  <CardBody>
                    <VStack spacing={4} align="stretch">
                      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                        <FormControl>
                          <FormLabel color="gray.300">Taille max fichier (MB)</FormLabel>
                          <Input
                            type="number"
                            defaultValue="10"
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>
                        <FormControl>
                          <FormLabel color="gray.300">Rétention corbeille (jours)</FormLabel>
                          <Input
                            type="number"
                            defaultValue="30"
                            bg="gray.800"
                            color="white"
                            borderColor="gray.600"
                          />
                        </FormControl>
                      </SimpleGrid>
                      <Button colorScheme="blue" alignSelf="flex-end">
                        Sauvegarder
                      </Button>
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

export default SettingsTest; 