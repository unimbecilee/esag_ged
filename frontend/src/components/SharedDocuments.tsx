import React from "react";
import { Box, Heading, Text, Icon } from "@chakra-ui/react";
import { FiShare2 } from "react-icons/fi";
import { ElementType } from "react";

const SharedDocuments: React.FC = () => {
  return (
    <Box p={5}>
      <Heading mb={6} size="lg" color="white">
        <Icon as={FiShare2 as ElementType} mr={3} />
        Documents Partagés
      </Heading>
      
      <Text color="white">Implémentation complète en cours...</Text>
    </Box>
  );
};

export default SharedDocuments; 