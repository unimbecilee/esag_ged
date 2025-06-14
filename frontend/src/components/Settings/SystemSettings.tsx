import React, { useState, useEffect } from 'react';
import {
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Input,
  Button,
  useToast,
  Text,
  Divider,
  SimpleGrid,
  Card,
  CardBody,
  CardHeader,
  Switch,
  Box,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
} from '@chakra-ui/react';

interface SystemSettings {
  taille_max_fichier: number;
  retention_corbeille: number;
  max_users: number;
  session_timeout: number;
  maintenance_mode: boolean;
  auto_backup: boolean;
  backup_frequency: number;
}

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: string;
}

interface SystemSettingsProps {
  currentUser: User | null;
}

const SystemSettings: React.FC<SystemSettingsProps> = ({ currentUser }) => {
  const [settings, setSettings] = useState<SystemSettings>({
    taille_max_fichier: 10,
    retention_corbeille: 30,
    max_users: 100,
    session_timeout: 60,
    maintenance_mode: false,
    auto_backup: true,
    backup_frequency: 24,
  });
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/settings/system', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des paramètres:', error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/settings/system', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Paramètres système sauvegardés",
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
        description: "Impossible de sauvegarder les paramètres",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  if (currentUser?.role !== 'admin') {
    return (
      <Box textAlign="center" py={8}>
        <Text color="red.400" fontSize="lg">
          ⚠️ Accès réservé aux administrateurs
        </Text>
      </Box>
    );
  }

  return (
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

      {/* Stockage et fichiers */}
      <Card bg="gray.600">
        <CardHeader>
          <HStack>
            <Text fontSize="2xl">💾</Text>
            <Text fontSize="xl" fontWeight="bold" color="white">
              Stockage et fichiers
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <FormControl>
              <FormLabel color="gray.300">Taille max fichier (MB)</FormLabel>
              <NumberInput
                value={settings.taille_max_fichier}
                onChange={(_, value) => setSettings({ ...settings, taille_max_fichier: value || 0 })}
                min={1}
                max={1000}
              >
                <NumberInputField bg="gray.700" color="white" borderColor="gray.600" />
                <NumberInputStepper>
                  <NumberIncrementStepper color="gray.300" />
                  <NumberDecrementStepper color="gray.300" />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>

            <FormControl>
              <FormLabel color="gray.300">Rétention corbeille (jours)</FormLabel>
              <NumberInput
                value={settings.retention_corbeille}
                onChange={(_, value) => setSettings({ ...settings, retention_corbeille: value || 0 })}
                min={1}
                max={365}
              >
                <NumberInputField bg="gray.700" color="white" borderColor="gray.600" />
                <NumberInputStepper>
                  <NumberIncrementStepper color="gray.300" />
                  <NumberDecrementStepper color="gray.300" />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>
          </SimpleGrid>
        </CardBody>
      </Card>

      <Divider borderColor="gray.600" />

      {/* Utilisateurs et sessions */}
      <Card bg="gray.600">
        <CardHeader>
          <HStack>
            <Text fontSize="2xl">👥</Text>
            <Text fontSize="xl" fontWeight="bold" color="white">
              Utilisateurs et sessions
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <FormControl>
              <FormLabel color="gray.300">Nombre max d'utilisateurs</FormLabel>
              <NumberInput
                value={settings.max_users}
                onChange={(_, value) => setSettings({ ...settings, max_users: value || 0 })}
                min={1}
                max={10000}
              >
                <NumberInputField bg="gray.700" color="white" borderColor="gray.600" />
                <NumberInputStepper>
                  <NumberIncrementStepper color="gray.300" />
                  <NumberDecrementStepper color="gray.300" />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>

            <FormControl>
              <FormLabel color="gray.300">Timeout session (minutes)</FormLabel>
              <NumberInput
                value={settings.session_timeout}
                onChange={(_, value) => setSettings({ ...settings, session_timeout: value || 0 })}
                min={5}
                max={1440}
              >
                <NumberInputField bg="gray.700" color="white" borderColor="gray.600" />
                <NumberInputStepper>
                  <NumberIncrementStepper color="gray.300" />
                  <NumberDecrementStepper color="gray.300" />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>
          </SimpleGrid>
        </CardBody>
      </Card>

      <Divider borderColor="gray.600" />

      {/* Options système */}
      <Card bg="gray.600">
        <CardHeader>
          <HStack>
            <Text fontSize="2xl">⚙️</Text>
            <Text fontSize="xl" fontWeight="bold" color="white">
              Options système
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <VStack align="start" spacing={0}>
                <FormLabel color="white" mb={0}>
                  Mode maintenance
                </FormLabel>
                <Text fontSize="sm" color="gray.400">
                  Bloquer l'accès aux utilisateurs non-admin
                </Text>
              </VStack>
              <Switch
                isChecked={settings.maintenance_mode}
                onChange={(e) => setSettings({ ...settings, maintenance_mode: e.target.checked })}
                colorScheme="red"
              />
            </FormControl>

            <FormControl display="flex" alignItems="center" justifyContent="space-between">
              <VStack align="start" spacing={0}>
                <FormLabel color="white" mb={0}>
                  Sauvegarde automatique
                </FormLabel>
                <Text fontSize="sm" color="gray.400">
                  Activer les sauvegardes automatiques du système
                </Text>
              </VStack>
              <Switch
                isChecked={settings.auto_backup}
                onChange={(e) => setSettings({ ...settings, auto_backup: e.target.checked })}
                colorScheme="green"
              />
            </FormControl>

            {settings.auto_backup && (
              <FormControl>
                <FormLabel color="gray.300">Fréquence de sauvegarde (heures)</FormLabel>
                <NumberInput
                  value={settings.backup_frequency}
                  onChange={(_, value) => setSettings({ ...settings, backup_frequency: value || 0 })}
                  min={1}
                  max={168}
                >
                  <NumberInputField bg="gray.700" color="white" borderColor="gray.600" />
                  <NumberInputStepper>
                    <NumberIncrementStepper color="gray.300" />
                    <NumberDecrementStepper color="gray.300" />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
            )}
          </VStack>
        </CardBody>
      </Card>

      {/* Bouton de sauvegarde */}
      <HStack justify="flex-end">
        <Button
          colorScheme="blue"
          onClick={handleSave}
          isLoading={loading}
          loadingText="Sauvegarde..."
          size="lg"
        >
          💾 Sauvegarder les paramètres
        </Button>
      </HStack>
    </VStack>
  );
};

export default SystemSettings; 