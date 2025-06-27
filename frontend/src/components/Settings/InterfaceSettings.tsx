import React, { useState, useEffect } from 'react';
import {
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Select,
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
  Badge,
  Flex,
} from '@chakra-ui/react';

interface InterfaceSettings {
  langue: string;
  theme: string;
  format_date: string;
  fuseau_horaire: string;
  compact_mode: boolean;
  animations: boolean;
  high_contrast: boolean;
}

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: string;
}

interface InterfaceSettingsProps {
  currentUser: User | null;
}

const InterfaceSettings: React.FC<InterfaceSettingsProps> = ({ currentUser }) => {
  const [settings, setSettings] = useState<InterfaceSettings>({
    langue: 'fr',
    theme: 'dark',
    format_date: 'DD/MM/YYYY',
    fuseau_horaire: 'Europe/Paris',
    compact_mode: false,
    animations: true,
    high_contrast: false,
  });
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/settings/interface', {
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
      const response = await fetch('/api/settings/interface', {
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
          description: "Paramètres d'interface sauvegardés",
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

  const langues = [
    { value: 'fr', label: 'Français', flag: '🇫🇷' },
    { value: 'en', label: 'English', flag: '🇺🇸' },
    { value: 'es', label: 'Español', flag: '🇪🇸' },
    { value: 'de', label: 'Deutsch', flag: '🇩🇪' },
    { value: 'it', label: 'Italiano', flag: '🇮🇹' },
  ];

  const themes = [
    { value: 'dark', label: 'Sombre', icon: '🌙', description: 'Interface sombre pour réduire la fatigue oculaire' },
    { value: 'light', label: 'Clair', icon: '☀️', description: 'Interface claire et lumineuse' },
    { value: 'system', label: 'Système', icon: '💻', description: 'Suit les préférences de votre système' },
  ];

  const formatsDate = [
    { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY', example: '13/06/2025' },
    { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY', example: '06/13/2025' },
    { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD', example: '2025-06-13' },
    { value: 'DD MMM YYYY', label: 'DD MMM YYYY', example: '13 Jun 2025' },
  ];

  const fuseauxHoraires = [
    { value: 'Europe/Paris', label: 'Europe/Paris (GMT+1)' },
    { value: 'Europe/London', label: 'Europe/London (GMT+0)' },
    { value: 'America/New_York', label: 'America/New_York (GMT-5)' },
    { value: 'America/Los_Angeles', label: 'America/Los_Angeles (GMT-8)' },
    { value: 'Asia/Tokyo', label: 'Asia/Tokyo (GMT+9)' },
    { value: 'Australia/Sydney', label: 'Australia/Sydney (GMT+10)' },
  ];

  return (
    <VStack spacing={6} align="stretch">
      {/* Langue et localisation */}
      <Card bg="gray.600">
        <CardHeader>
          <HStack>
            <Text fontSize="2xl">🌐</Text>
            <Text fontSize="xl" fontWeight="bold" color="white">
              Langue et localisation
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <FormControl>
              <FormLabel color="gray.300">Langue de l'interface</FormLabel>
              <Select
                value={settings.langue}
                onChange={(e) => setSettings({ ...settings, langue: e.target.value })}
                bg="gray.700"
                color="white"
                borderColor="gray.600"
              >
                {langues.map((langue) => (
                  <option key={langue.value} value={langue.value} style={{ backgroundColor: '#2D3748' }}>
                    {langue.flag} {langue.label}
                  </option>
                ))}
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel color="gray.300">Fuseau horaire</FormLabel>
              <Select
                value={settings.fuseau_horaire}
                onChange={(e) => setSettings({ ...settings, fuseau_horaire: e.target.value })}
                bg="gray.700"
                color="white"
                borderColor="gray.600"
              >
                {fuseauxHoraires.map((fuseau) => (
                  <option key={fuseau.value} value={fuseau.value} style={{ backgroundColor: '#2D3748' }}>
                    {fuseau.label}
                  </option>
                ))}
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel color="gray.300">Format de date</FormLabel>
              <Select
                value={settings.format_date}
                onChange={(e) => setSettings({ ...settings, format_date: e.target.value })}
                bg="gray.700"
                color="white"
                borderColor="gray.600"
              >
                {formatsDate.map((format) => (
                  <option key={format.value} value={format.value} style={{ backgroundColor: '#2D3748' }}>
                    {format.label} - {format.example}
                  </option>
                ))}
              </Select>
            </FormControl>
          </SimpleGrid>
        </CardBody>
      </Card>

      <Divider borderColor="gray.600" />

      {/* Thème et apparence */}
      <Card bg="gray.600">
        <CardHeader>
          <HStack>
            <Text fontSize="2xl">🎨</Text>
            <Text fontSize="xl" fontWeight="bold" color="white">
              Thème et apparence
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel color="gray.300">Thème</FormLabel>
              <SimpleGrid columns={{ base: 1, md: 3 }} spacing={3}>
                {themes.map((theme) => (
                  <Card
                    key={theme.value}
                    bg={settings.theme === theme.value ? 'blue.600' : 'gray.700'}
                    borderWidth={2}
                    borderColor={settings.theme === theme.value ? 'blue.400' : 'transparent'}
                    cursor="pointer"
                    onClick={() => setSettings({ ...settings, theme: theme.value })}
                    _hover={{ bg: settings.theme === theme.value ? 'blue.600' : 'gray.650' }}
                  >
                    <CardBody textAlign="center" py={4}>
                      <Text fontSize="3xl" mb={2}>{theme.icon}</Text>
                      <Text fontWeight="bold" color="white" mb={1}>
                        {theme.label}
                      </Text>
                      <Text fontSize="xs" color="gray.300">
                        {theme.description}
                      </Text>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            </FormControl>

            <Divider borderColor="gray.600" />

            {/* Options d'accessibilité */}
            <Box>
              <Text fontSize="lg" fontWeight="bold" color="white" mb={4}>
                Options d'accessibilité
              </Text>
              <VStack spacing={4}>
                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <VStack align="start" spacing={0}>
                    <FormLabel color="white" mb={0}>
                      Mode compact
                    </FormLabel>
                    <Text fontSize="sm" color="gray.400">
                      Réduire l'espacement pour afficher plus de contenu
                    </Text>
                  </VStack>
                  <Switch
                    isChecked={settings.compact_mode}
                    onChange={(e) => setSettings({ ...settings, compact_mode: e.target.checked })}
                    colorScheme="blue"
                  />
                </FormControl>

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <VStack align="start" spacing={0}>
                    <FormLabel color="white" mb={0}>
                      Animations
                    </FormLabel>
                    <Text fontSize="sm" color="gray.400">
                      Activer les animations et transitions
                    </Text>
                  </VStack>
                  <Switch
                    isChecked={settings.animations}
                    onChange={(e) => setSettings({ ...settings, animations: e.target.checked })}
                    colorScheme="blue"
                  />
                </FormControl>

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <VStack align="start" spacing={0}>
                    <FormLabel color="white" mb={0}>
                      Contraste élevé
                    </FormLabel>
                    <Text fontSize="sm" color="gray.400">
                      Améliorer la lisibilité avec un contraste plus élevé
                    </Text>
                  </VStack>
                  <Switch
                    isChecked={settings.high_contrast}
                    onChange={(e) => setSettings({ ...settings, high_contrast: e.target.checked })}
                    colorScheme="blue"
                  />
                </FormControl>
              </VStack>
            </Box>
          </VStack>
        </CardBody>
      </Card>

      {/* Aperçu des paramètres */}
      <Card bg="gray.600">
        <CardHeader>
          <Text fontWeight="bold" color="white">Aperçu de vos paramètres</Text>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <VStack>
              <Badge colorScheme="blue">
                {langues.find(l => l.value === settings.langue)?.flag}
              </Badge>
              <Text fontSize="xs" color="gray.400" textAlign="center">
                {langues.find(l => l.value === settings.langue)?.label}
              </Text>
            </VStack>
            
            <VStack>
              <Badge colorScheme="purple">
                {themes.find(t => t.value === settings.theme)?.label}
              </Badge>
              <Text fontSize="xs" color="gray.400" textAlign="center">
                Thème
              </Text>
            </VStack>
            
            <VStack>
              <Badge colorScheme="green">
                {settings.format_date}
              </Badge>
              <Text fontSize="xs" color="gray.400" textAlign="center">
                Format date
              </Text>
            </VStack>
            
            <VStack>
              <Badge colorScheme={settings.compact_mode ? 'orange' : 'gray'}>
                {settings.compact_mode ? 'Compact' : 'Normal'}
              </Badge>
              <Text fontSize="xs" color="gray.400" textAlign="center">
                Mode affichage
              </Text>
            </VStack>
          </SimpleGrid>
        </CardBody>
      </Card>

      {/* Bouton de sauvegarde */}
      <Flex justify="flex-end">
        <Button
          colorScheme="blue"
          onClick={handleSave}
          isLoading={loading}
          loadingText="Sauvegarde..."
          size="lg"
        >
          💾 Sauvegarder les paramètres
        </Button>
      </Flex>
    </VStack>
  );
};

export default InterfaceSettings; 

