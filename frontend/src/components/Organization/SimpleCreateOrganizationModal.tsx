import React, { useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  useToast,
  VStack
} from '@chakra-ui/react';
import config from '../../config';

interface SimpleCreateOrganizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const SimpleCreateOrganizationModal: React.FC<SimpleCreateOrganizationModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [nom, setNom] = useState('');
  const [description, setDescription] = useState('');
  const [adresse, setAdresse] = useState('');
  const [email, setEmail] = useState('');
  const [telephone, setTelephone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const handleSubmit = async () => {
    if (!nom) {
      toast({
        title: 'Erreur',
        description: "Le nom de l'organisation est requis",
        status: 'error',
        duration: 3000,
        isClosable: true
      });
      return;
    }
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
              const response = await fetch(`${config.API_URL}/api/organizations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          nom,
          description,
          adresse,
          email_contact: email,
          telephone_contact: telephone
        })
      });
      if (!response.ok) throw new Error('Erreur lors de la création de l\'organisation');
      toast({
        title: 'Succès',
        description: 'Organisation créée avec succès',
        status: 'success',
        duration: 3000,
        isClosable: true
      });
      if (onSuccess) onSuccess();
      onClose();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: "Impossible de créer l'organisation",
        status: 'error',
        duration: 3000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalOverlay />
      <ModalContent bg="#1a1f37">
        <ModalHeader color="white">Nouvelle organisation</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel color="white">Nom</FormLabel>
              <Input value={nom} onChange={e => setNom(e.target.value)} placeholder="Nom de l'organisation" bg="#20243a" color="white" />
            </FormControl>
            <FormControl>
              <FormLabel color="white">Description</FormLabel>
              <Textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Description de l'organisation" bg="#20243a" color="white" />
            </FormControl>
            <FormControl>
              <FormLabel color="white">Adresse</FormLabel>
              <Input value={adresse} onChange={e => setAdresse(e.target.value)} placeholder="Adresse" bg="#20243a" color="white" />
            </FormControl>
            <FormControl>
              <FormLabel color="white">Email de contact</FormLabel>
              <Input value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" bg="#20243a" color="white" />
            </FormControl>
            <FormControl>
              <FormLabel color="white">Téléphone</FormLabel>
              <Input value={telephone} onChange={e => setTelephone(e.target.value)} placeholder="Téléphone" bg="#20243a" color="white" />
            </FormControl>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose} isDisabled={isLoading}>
            Annuler
          </Button>
          <Button colorScheme="blue" onClick={handleSubmit} isLoading={isLoading}>
            Créer
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default SimpleCreateOrganizationModal; 

