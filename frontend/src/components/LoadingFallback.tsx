import React from "react";
import { Center, Spinner, Text, VStack } from "@chakra-ui/react";

const LoadingFallback: React.FC = () => {
  return (
    <Center h="100vh" bg="#202a46">
      <VStack spacing={4}>
        <Spinner
          thickness="4px"
          speed="0.65s"
          emptyColor="gray.700"
          color="blue.500"
          size="xl"
        />
        <Text color="white" fontSize="lg">
          Chargement...
        </Text>
      </VStack>
    </Center>
  );
};

export default LoadingFallback;
