import React from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  VStack,
  Icon,
  useColorModeValue,
} from '@chakra-ui/react';
import { FiLock, FiHome } from 'react-icons/fi';
import { asElementType } from '../utils/iconUtils';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const AccessDenied: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const bgColor = useColorModeValue('white', '#1A1D2D');
  const textColor = useColorModeValue('gray.600', 'gray.300');

  return (
    <Container maxW="container.md" py={20}>
      <Box
        bg={bgColor}
        borderRadius="lg"
        p={8}
        textAlign="center"
        boxShadow="xl"
      >
        <VStack spacing={6}>
          {/* Icône d'accès refusé */}
          <Box
            bg="red.100"
            borderRadius="full"
            p={4}
            display="inline-flex"
          >
            <Icon
              as={asElementType(FiLock)}
              w={12}
              h={12}
              color="red.500"
            />
          </Box>

          {/* Titre */}
          <Heading
            size="xl"
            color="red.500"
            mb={2}
          >
            Accès refusé
          </Heading>

          {/* Message principal */}
          <Text
            fontSize="lg"
            color={textColor}
            mb={4}
          >
            Vous n'avez pas les permissions nécessaires pour accéder à cette page.
          </Text>

          {/* Informations sur le rôle */}
          {user && (
            <Box
              bg="gray.50"
              borderRadius="md"
              p={4}
              borderLeft="4px solid"
              borderLeftColor="blue.500"
            >
              <Text fontSize="sm" color="gray.600">
                <strong>Votre rôle actuel :</strong> {user.role}
              </Text>
              <Text fontSize="sm" color="gray.600" mt={1}>
                Contactez votre administrateur si vous pensez que c'est une erreur.
              </Text>
            </Box>
          )}

          {/* Boutons d'action */}
          <VStack spacing={3} pt={4}>
            <Button
              leftIcon={<Icon as={asElementType(FiHome)} />}
              colorScheme="blue"
              size="lg"
              onClick={() => navigate('/dashboard')}
            >
              Retour au tableau de bord
            </Button>
            
            <Button
              variant="ghost"
              size="md"
              onClick={() => navigate(-1)}
            >
              Retour à la page précédente
            </Button>
          </VStack>
        </VStack>
      </Box>
    </Container>
  );
};

export default AccessDenied; 

