import React, { useState, useEffect } from 'react';
import {
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Switch,
  Button,
  useToast,
  Text,
  Divider,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Icon,
  Select,
  Box,
  Badge,
  Flex,
} from '@chakra-ui/react';
import {
  FiBell,
  FiMail,
  FiFileText,
  FiUsers,
  FiMessageCircle,
  FiShare2,
  FiAtSign,
  FiSettings,
  FiClock,
  FiSave,
} from 'react-icons/fi';
import { ElementType } from 'react';

interface NotificationPreferences {
  email_notifications: boolean;
  app_notifications: boolean;
  document_notifications: boolean;
  workflow_notifications: boolean;
  comment_notifications: boolean;
  share_notifications: boolean;
  mention_notifications: boolean;
  system_notifications: boolean;
  digest_frequency: string;
  quiet_hours_start: string;
  quiet_hours_end: string;
  weekend_notifications: boolean;
}

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: string;
}

interface NotificationSettingsProps {
  currentUser: User | null;
}

const NotificationSettings: React.FC<NotificationSettingsProps> = ({ currentUser }) => {
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email_notifications: true,
    app_notifications: true,
    document_notifications: true,
    workflow_notifications: true,
    comment_notifications: true,
    share_notifications: true,
    mention_notifications: true,
    system_notifications: true,
    digest_frequency: 'daily',
    quiet_hours_start: '22:00',
    quiet_hours_end: '08:00',
    weekend_notifications: false,
  });
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/notifications/preferences', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des préférences:', error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/notifications/preferences', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Préférences de notification sauvegardées",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      } else {
        throw new Error('Erreur lors de la sauvegarde');
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de sauvegarder les préférences",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const notificationTypes = [
    {
      key: 'email_notifications',
      label: 'Notifications par email',
      description: 'Recevoir les notifications par email',
      icon: FiMail,
      color: 'blue',
    },
    {
      key: 'app_notifications',
      label: 'Notifications dans l\'application',
      description: 'Afficher les notifications dans l\'interface',
      icon: FiBell,
      color: 'green',
    },
    {
      key: 'document_notifications',
      label: 'Documents',
      description: 'Notifications pour les nouveaux documents et modifications',
      icon: FiFileText,
      color: 'purple',
    },
    {
      key: 'workflow_notifications',
      label: 'Workflows',
      description: 'Notifications pour les workflows et validations',
      icon: FiUsers,
      color: 'orange',
    },
    {
      key: 'comment_notifications',
      label: 'Commentaires',
      description: 'Notifications pour les nouveaux commentaires',
      icon: FiMessageCircle,
      color: 'cyan',
    },
    {
      key: 'share_notifications',
      label: 'Partages',
      description: 'Notifications quand un document est partagé avec vous',
      icon: FiShare2,
      color: 'pink',
    },
    {
      key: 'mention_notifications',
      label: 'Mentions',
      description: 'Notifications quand vous êtes mentionné',
      icon: FiAtSign,
      color: 'yellow',
    },
    {
      key: 'system_notifications',
      label: 'Système',
      description: 'Notifications système et de maintenance',
      icon: FiSettings,
      color: 'red',
    },
  ];

  return (
    <VStack spacing={6} align="stretch">
      {/* Types de notifications */}
      <Box>
        <Text fontSize="xl" fontWeight="bold" color="white" mb={4}>
          Types de notifications
        </Text>
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
          {notificationTypes.map((type) => (
            <Card key={type.key} bg="gray.600">
              <CardBody>
                <Flex align="center" justify="space-between">
                  <HStack spacing={3}>
                    <Icon as={type.icon as ElementType} color={`${type.color}.400`} boxSize={5} />
                    <VStack align="start" spacing={0}>
                      <Text fontWeight="medium" color="white">
                        {type.label}
                      </Text>
                      <Text fontSize="sm" color="gray.400">
                        {type.description}
                      </Text>
                    </VStack>
                  </HStack>
                  <Switch
                    isChecked={preferences[type.key as keyof NotificationPreferences] as boolean}
                    onChange={(e) => setPreferences({
                      ...preferences,
                      [type.key]: e.target.checked
                    })}
                    colorScheme={type.color}
                  />
                </Flex>
              </CardBody>
            </Card>
          ))}
        </SimpleGrid>
      </Box>

      <Divider borderColor="gray.600" />

      {/* Paramètres avancés */}
      <Box>
        <Text fontSize="xl" fontWeight="bold" color="white" mb={4}>
          Paramètres avancés
        </Text>
        
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
          {/* Fréquence des résumés */}
          <Card bg="gray.600">
            <CardHeader>
              <HStack>
                <Icon as={FiClock as ElementType} color="blue.400" />
                <Text fontWeight="bold" color="white">Résumé par email</Text>
              </HStack>
            </CardHeader>
            <CardBody pt={0}>
              <FormControl>
                <FormLabel color="gray.300" fontSize="sm">
                  Fréquence des résumés
                </FormLabel>
                <Select
                  value={preferences.digest_frequency}
                  onChange={(e) => setPreferences({
                    ...preferences,
                    digest_frequency: e.target.value
                  })}
                  bg="gray.700"
                  color="white"
                  borderColor="gray.600"
                >
                  <option value="never" style={{ backgroundColor: '#2D3748' }}>Jamais</option>
                  <option value="daily" style={{ backgroundColor: '#2D3748' }}>Quotidien</option>
                  <option value="weekly" style={{ backgroundColor: '#2D3748' }}>Hebdomadaire</option>
                  <option value="monthly" style={{ backgroundColor: '#2D3748' }}>Mensuel</option>
                </Select>
              </FormControl>
            </CardBody>
          </Card>

          {/* Heures silencieuses */}
          <Card bg="gray.600">
            <CardHeader>
              <HStack>
                <Icon as={FiBell as ElementType} color="purple.400" />
                <Text fontWeight="bold" color="white">Heures silencieuses</Text>
              </HStack>
            </CardHeader>
            <CardBody pt={0}>
              <VStack spacing={3}>
                <FormControl>
                  <FormLabel color="gray.300" fontSize="sm">
                    Début
                  </FormLabel>
                  <Select
                    value={preferences.quiet_hours_start}
                    onChange={(e) => setPreferences({
                      ...preferences,
                      quiet_hours_start: e.target.value
                    })}
                    bg="gray.700"
                    color="white"
                    borderColor="gray.600"
                  >
                    {Array.from({ length: 24 }, (_, i) => {
                      const hour = i.toString().padStart(2, '0');
                      return (
                        <option key={hour} value={`${hour}:00`} style={{ backgroundColor: '#2D3748' }}>
                          {hour}:00
                        </option>
                      );
                    })}
                  </Select>
                </FormControl>
                
                <FormControl>
                  <FormLabel color="gray.300" fontSize="sm">
                    Fin
                  </FormLabel>
                  <Select
                    value={preferences.quiet_hours_end}
                    onChange={(e) => setPreferences({
                      ...preferences,
                      quiet_hours_end: e.target.value
                    })}
                    bg="gray.700"
                    color="white"
                    borderColor="gray.600"
                  >
                    {Array.from({ length: 24 }, (_, i) => {
                      const hour = i.toString().padStart(2, '0');
                      return (
                        <option key={hour} value={`${hour}:00`} style={{ backgroundColor: '#2D3748' }}>
                          {hour}:00
                        </option>
                      );
                    })}
                  </Select>
                </FormControl>
              </VStack>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Options supplémentaires */}
        <Card bg="gray.600" mt={4}>
          <CardBody>
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <VStack align="start" spacing={0}>
                <FormLabel color="white" mb={0}>
                  Notifications le week-end
                </FormLabel>
                <Text fontSize="sm" color="gray.400">
                  Recevoir des notifications les samedi et dimanche
                </Text>
              </VStack>
              <Switch
                isChecked={preferences.weekend_notifications}
                onChange={(e) => setPreferences({
                  ...preferences,
                  weekend_notifications: e.target.checked
                })}
                colorScheme="blue"
              />
            </FormControl>
          </CardBody>
        </Card>
      </Box>

      <Divider borderColor="gray.600" />

      {/* Aperçu des paramètres */}
      <Card bg="gray.600">
        <CardHeader>
          <Text fontWeight="bold" color="white">Résumé de vos préférences</Text>
        </CardHeader>
        <CardBody pt={0}>
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <VStack>
              <Badge colorScheme={preferences.email_notifications ? 'green' : 'red'}>
                Email
              </Badge>
              <Text fontSize="xs" color="gray.400" textAlign="center">
                {preferences.email_notifications ? 'Activé' : 'Désactivé'}
              </Text>
            </VStack>
            
            <VStack>
              <Badge colorScheme={preferences.app_notifications ? 'green' : 'red'}>
                App
              </Badge>
              <Text fontSize="xs" color="gray.400" textAlign="center">
                {preferences.app_notifications ? 'Activé' : 'Désactivé'}
              </Text>
            </VStack>
            
            <VStack>
              <Badge colorScheme="blue">
                Résumé
              </Badge>
              <Text fontSize="xs" color="gray.400" textAlign="center">
                {preferences.digest_frequency === 'never' ? 'Jamais' : 
                 preferences.digest_frequency === 'daily' ? 'Quotidien' :
                 preferences.digest_frequency === 'weekly' ? 'Hebdomadaire' : 'Mensuel'}
              </Text>
            </VStack>
            
            <VStack>
              <Badge colorScheme={preferences.weekend_notifications ? 'green' : 'orange'}>
                Week-end
              </Badge>
              <Text fontSize="xs" color="gray.400" textAlign="center">
                {preferences.weekend_notifications ? 'Activé' : 'Désactivé'}
              </Text>
            </VStack>
          </SimpleGrid>
        </CardBody>
      </Card>

      {/* Bouton de sauvegarde */}
      <Flex justify="flex-end">
        <Button
          leftIcon={<Icon as={FiSave as ElementType} />}
          colorScheme="blue"
          onClick={handleSave}
          isLoading={loading}
          loadingText="Sauvegarde..."
          size="lg"
        >
          Sauvegarder les préférences
        </Button>
      </Flex>
    </VStack>
  );
};

export default NotificationSettings;