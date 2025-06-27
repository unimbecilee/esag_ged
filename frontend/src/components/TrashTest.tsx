import React from "react";
import { Container, Heading, Text, VStack } from "@chakra-ui/react";

const TrashTest: React.FC = () => {
  console.log("TrashTest component loaded!");
  
  return (
    <Container maxW="7xl" py={8}>
      <VStack spacing={6} align="stretch">
        <Heading size="lg" color="white">
          🗑️ Test Corbeille
        </Heading>
        <Text color="white">
          Ce composant de test fonctionne ! Le problème n'est pas React.
        </Text>
        <Text color="gray.300">
          Si tu vois ce message, React peut charger les composants.
        </Text>
      </VStack>
    </Container>
  );
};

export default TrashTest; 

