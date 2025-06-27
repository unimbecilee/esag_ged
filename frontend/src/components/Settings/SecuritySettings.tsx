import React, { useState } from 'react';
import {
  VStack,
  HStack,
  FormControl,
  FormLabel,
  Input,
  Button,
  useToast,
  Text,
  Box,
  Progress,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Card,
  CardBody,
  CardHeader,
  Divider,
  SimpleGrid,
  Badge,
} from '@chakra-ui/react';

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: string;
  derniere_connexion?: string;
}

interface SecuritySettingsProps {
  currentUser: User | null;
}

const SecuritySettings: React.FC<SecuritySettingsProps> = ({ currentUser }) => {
  const [passwordData, setPasswordData] = useState({
    current: '',
    new: '',
    confirm: '',
  });
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

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

  const handleSubmit = async () => {
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

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auth/change-password', {
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

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Mot de passe changé avec succès",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
        setPasswordData({ current: '', new: '', confirm: '' });
        setPasswordStrength(0);
      } else {
        throw new Error('Erreur lors du changement de mot de passe');
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de changer le mot de passe",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <VStack spacing={6} align="stretch">
      {/* Statistiques de sécurité */}
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
        <Card bg="gray.600">
          <CardBody textAlign="center">
            <Text fontSize="4xl" mb={2}>🕐</Text>
            <Text fontSize="sm" color="gray.400">Dernière connexion</Text>
            <Text fontSize="lg" fontWeight="bold" color="white">
              {currentUser?.derniere_connexion 
                ? new Date(currentUser.derniere_connexion).toLocaleDateString('fr-FR')
                : 'N/A'
              }
            </Text>
          </CardBody>
        </Card>
        
        <Card bg="gray.600">
          <CardBody textAlign="center">
            <Text fontSize="4xl" mb={2}>🛡️</Text>
            <Text fontSize="sm" color="gray.400">Statut de sécurité</Text>
            <Badge colorScheme="green" fontSize="md" px={3} py={1}>
              Sécurisé
            </Badge>
          </CardBody>
        </Card>
      </SimpleGrid>

      <Divider borderColor="gray.600" />

      {/* Changement de mot de passe */}
      <Card bg="gray.600">
        <CardHeader>
          <HStack>
            <Text fontSize="2xl">🔑</Text>
            <Text fontSize="xl" fontWeight="bold" color="white">
              Changer le mot de passe
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel color="gray.300">Mot de passe actuel</FormLabel>
              <Input
                type="password"
                value={passwordData.current}
                onChange={(e) => setPasswordData({ ...passwordData, current: e.target.value })}
                bg="gray.700"
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
                bg="gray.700"
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
                bg="gray.700"
                color="white"
                borderColor="gray.600"
              />
            </FormControl>

            <Alert status="info" bg="blue.900" borderColor="blue.600">
              <AlertIcon />
              <Box>
                <AlertTitle>Conseils de sécurité</AlertTitle>
                <AlertDescription>
                  Utilisez au moins 8 caractères avec des majuscules, minuscules, chiffres et symboles.
                </AlertDescription>
              </Box>
            </Alert>

            <HStack justify="flex-end" pt={4}>
              <Button
                colorScheme="blue"
                onClick={handleSubmit}
                isLoading={loading}
                loadingText="Changement..."
                isDisabled={!passwordData.current || !passwordData.new || !passwordData.confirm}
              >
                💾 Changer le mot de passe
              </Button>
            </HStack>
          </VStack>
        </CardBody>
      </Card>

      {/* Conseils de sécurité */}
      <Card bg="gray.600">
        <CardHeader>
          <HStack>
            <Text fontSize="2xl">✅</Text>
            <Text fontSize="xl" fontWeight="bold" color="white">
              Conseils de sécurité
            </Text>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack align="start" spacing={3}>
            <HStack>
              <Text>✓</Text>
              <Text color="gray.300" fontSize="sm">
                Utilisez un mot de passe unique pour chaque compte
              </Text>
            </HStack>
            <HStack>
              <Text>✓</Text>
              <Text color="gray.300" fontSize="sm">
                Changez votre mot de passe régulièrement
              </Text>
            </HStack>
            <HStack>
              <Text>✓</Text>
              <Text color="gray.300" fontSize="sm">
                Ne partagez jamais vos identifiants
              </Text>
            </HStack>
            <HStack>
              <Text>✓</Text>
              <Text color="gray.300" fontSize="sm">
                Déconnectez-vous toujours après utilisation
              </Text>
            </HStack>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );
};

export default SecuritySettings; 

