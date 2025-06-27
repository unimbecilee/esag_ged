import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Text,
  useToast,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Card,
  CardBody,
  Heading,
  Divider,
  HStack,
  useColorModeValue,
  Spinner
} from '@chakra-ui/react';
import { Link } from 'react-router-dom';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const PasswordReset: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const toast = useToast();

  const bgColor = useColorModeValue('white', '#1a202c');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError('L\'adresse email est requise');
      return;
    }

    if (!email.includes('@')) {
      setError('Veuillez entrer une adresse email valide');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setIsSuccess(true);
        toast({
          title: 'Demande envoyée',
          description: 'Si cet email existe, un nouveau mot de passe a été envoyé.',
          status: 'success',
          duration: 6000,
          isClosable: true,
        });
      } else {
        setError(data.message || 'Une erreur est survenue');
      }
    } catch (error) {
      console.error('Erreur lors de la réinitialisation:', error);
      setError('Erreur de connexion au serveur');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <Box
        minH="100vh"
        display="flex"
        alignItems="center"
        justifyContent="center"
        bg="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        p={4}
      >
        <Card
          maxW="md"
          w="full"
          bg={bgColor}
          borderColor={borderColor}
          boxShadow="2xl"
          borderRadius="xl"
        >
          <CardBody p={8}>
            <VStack spacing={6} align="center">
              <Box
                p={4}
                bg="green.100"
                borderRadius="full"
                color="green.600"
                display="flex"
                alignItems="center"
                justifyContent="center"
                fontSize="2xl"
              >
                ✉️
              </Box>
              
              <VStack spacing={2} textAlign="center">
                <Heading size="lg" color="green.600">
                  Email envoyé !
                </Heading>
                <Text color="gray.600">
                  Si votre adresse email est dans notre système, vous recevrez un nouveau mot de passe par email dans quelques minutes.
                </Text>
              </VStack>

              <Alert status="info" borderRadius="md">
                <AlertIcon />
                <Box>
                  <AlertTitle>Vérifiez votre boîte email</AlertTitle>
                  <AlertDescription>
                    N'oubliez pas de vérifier votre dossier spam si vous ne voyez pas l'email.
                  </AlertDescription>
                </Box>
              </Alert>

              <Divider />

              <Button
                as={Link}
                to="/auth/login"
                variant="outline"
                colorScheme="blue"
                w="full"
              >
                ← Retour à la connexion
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </Box>
    );
  }

  return (
    <Box
      minH="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
      bg="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
      p={4}
    >
      <Card
        maxW="md"
        w="full"
        bg={bgColor}
        borderColor={borderColor}
        boxShadow="2xl"
        borderRadius="xl"
      >
        <CardBody p={8}>
          <VStack spacing={6}>
            <VStack spacing={2} textAlign="center">
              <Box
                p={4}
                bg="blue.100"
                borderRadius="full"
                color="blue.600"
                display="flex"
                alignItems="center"
                justifyContent="center"
                fontSize="2xl"
              >
                🔑
              </Box>
              <Heading size="lg" color="gray.800">
                Réinitialiser le mot de passe
              </Heading>
              <Text color="gray.600">
                Entrez votre adresse email pour recevoir un nouveau mot de passe
              </Text>
            </VStack>

            <Box as="form" onSubmit={handleResetPassword} w="full">
              <VStack spacing={4}>
                {error && (
                  <Alert status="error" borderRadius="md">
                    <AlertIcon />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <FormControl isRequired>
                  <FormLabel>Adresse email</FormLabel>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="votre-email@exemple.com"
                    size="lg"
                    bg="gray.50"
                    border="1px"
                    borderColor="gray.300"
                    _hover={{ borderColor: 'blue.400' }}
                    _focus={{
                      borderColor: 'blue.500',
                      boxShadow: '0 0 0 1px blue.500',
                    }}
                  />
                </FormControl>

                <Button
                  type="submit"
                  colorScheme="blue"
                  size="lg"
                  w="full"
                  isLoading={isLoading}
                  loadingText="Envoi en cours..."
                  bg="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                  _hover={{
                    bg: "linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)",
                    transform: "translateY(-1px)",
                    boxShadow: "lg",
                  }}
                  _active={{
                    transform: "translateY(0)",
                  }}
                  transition="all 0.2s"
                >
                  {isLoading ? 'Envoi en cours...' : '📧 Envoyer le nouveau mot de passe'}
                </Button>
              </VStack>
            </Box>

            <Divider />

            <HStack spacing={4} w="full" justify="center">
              <Button
                as={Link}
                to="/auth/login"
                variant="ghost"
                size="sm"
              >
                ← Retour à la connexion
              </Button>
            </HStack>
          </VStack>
        </CardBody>
      </Card>
    </Box>
  );
};

export default PasswordReset; 