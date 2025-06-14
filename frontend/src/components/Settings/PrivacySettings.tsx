import React from 'react';
import {
  VStack,
  Text,
  Card,
  CardBody,
  Icon,
  Box,
} from '@chakra-ui/react';
import { FiEye } from 'react-icons/fi';
import { ElementType } from 'react';

interface User {
  id: number;
  email: string;
  nom: string;
  prenom: string;
  role: string;
}

interface PrivacySettingsProps {
  currentUser: User | null;
}

const PrivacySettings: React.FC<PrivacySettingsProps> = ({ currentUser }) => {
  return (
    <VStack spacing={6} align="stretch">
      <Card bg="gray.600">
        <CardBody textAlign="center" py={8}>
          <Icon as={FiEye as ElementType} boxSize={12} color="blue.400" mb={4} />
          <Text fontSize="xl" fontWeight="bold" color="white" mb={2}>
            Paramètres de confidentialité
          </Text>
          <Text color="gray.400">
            Les paramètres de confidentialité seront disponibles prochainement.
          </Text>
        </CardBody>
      </Card>
    </VStack>
  );
};

export default PrivacySettings; 