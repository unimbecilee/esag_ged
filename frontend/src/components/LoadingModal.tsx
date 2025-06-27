import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  Spinner,
  Text,
  VStack,
} from '@chakra-ui/react';

interface LoadingModalProps {
  isOpen: boolean;
  message?: string;
}

const LoadingModal: React.FC<LoadingModalProps> = ({ isOpen, message = "Chargement en cours..." }) => {
  return (
    <Modal isOpen={isOpen} onClose={() => {}} isCentered closeOnOverlayClick={false}>
      <ModalOverlay
        bg="blackAlpha.700"
        backdropFilter="blur(4px)"
      />
      <ModalContent
        bg="transparent"
        boxShadow="none"
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        <VStack spacing={4}>
          <Spinner
            thickness="4px"
            speed="0.65s"
            emptyColor="gray.600"
            color="#3a8bfd"
            size="xl"
          />
          <Text color="white" fontSize="lg" fontWeight="medium">
            {message}
          </Text>
        </VStack>
      </ModalContent>
    </Modal>
  );
};

export default LoadingModal; 

