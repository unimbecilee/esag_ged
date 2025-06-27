import React, { useState, useEffect } from 'react';
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
  VStack,
  Switch,
  FormHelperText,
  InputGroup,
  InputLeftElement,
  Icon
} from '@chakra-ui/react';
import { FiMail, FiPhone, FiMapPin } from 'react-icons/fi';
import { ElementType } from 'react';

interface Organization {
  id: number;
  nom: string;
  description: string;
  adresse: string;
  email_contact: string;
  telephone_contact: string;
  statut: 'ACTIVE' | 'INACTIVE';
}

interface EditOrganizationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  organization: Organization;
}

const EditOrganizationModal: React.FC<EditOrganizationModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  organization
}) => {
  const [nom, setNom] = useState(organization.nom);
  const [description, setDescription] = useState(organization.description);
  const [adresse, setAdresse] = useState(organization.adresse);
  const [emailContact, setEmailContact] = useState(organization.email_contact);
  const [telephoneContact, setTelephoneContact] = useState(organization.telephone_contact);
  const [isActive, setIsActive] = useState(organization.statut === 'ACTIVE');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const toast = useToast();

  useEffect(() => {
    setNom(organization.nom);
    setDescription(organization.description);
    setAdresse(organization.adresse);
    setEmailContact(organization.email_contact);
    setTelephoneContact(organization.telephone_contact);
    setIsActive(organization.statut === 'ACTIVE');
  }, [organization]);

  const handleSubmit = async () => {
    if (!nom.trim()) {
      toast({
        title: 'Erreur',
        description: 'Le nom de l\'organisation est requis',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`https://web-production-ae27.up.railway.app/api/organizations/${organization.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          nom: nom.trim(),
          description: description.trim(),
          adresse: adresse.trim(),
          email_contact: emailContact.trim(),
          telephone_contact: telephoneContact.trim(),
          statut: isActive ? 'ACTIVE' : 'INACTIVE'
        })
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la modification de l\'organisation');
      }

      toast({
        title: 'Succès',
        description: 'Organisation modifiée avec succès',
        status: 'success',
        duration: 5000,
        isClosable: true
      });

      onSuccess();
      onClose();
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de modifier l\'organisation',
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay bg="blackAlpha.700" />
      <ModalContent bg="#20243a" color="white">
        <ModalHeader>Modifier l'organisation</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel>Nom de l'organisation</FormLabel>
              <Input
                placeholder="Entrez le nom de l'organisation"
                value={nom}
                onChange={(e) => setNom(e.target.value)}
                bg="#2a2f4a"
                border="1px solid"
                borderColor="#363b5a"
                _hover={{ borderColor: '#454b6a' }}
                _focus={{ borderColor: '#4299E1', boxShadow: 'none' }}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Description</FormLabel>
              <Textarea
                placeholder="Décrivez l'organisation"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                bg="#2a2f4a"
                border="1px solid"
                borderColor="#363b5a"
                _hover={{ borderColor: '#454b6a' }}
                _focus={{ borderColor: '#4299E1', boxShadow: 'none' }}
                rows={4}
              />
            </FormControl>

            <FormControl>
              <FormLabel>Adresse</FormLabel>
              <InputGroup>
                <InputLeftElement pointerEvents="none">
                  <Icon as={FiMapPin as ElementType} color="gray.400" />
                </InputLeftElement>
                <Input
                  placeholder="Adresse de l'organisation"
                  value={adresse}
                  onChange={(e) => setAdresse(e.target.value)}
                  bg="#2a2f4a"
                  border="1px solid"
                  borderColor="#363b5a"
                  _hover={{ borderColor: '#454b6a' }}
                  _focus={{ borderColor: '#4299E1', boxShadow: 'none' }}
                />
              </InputGroup>
            </FormControl>

            <FormControl>
              <FormLabel>Email de contact</FormLabel>
              <InputGroup>
                <InputLeftElement pointerEvents="none">
                  <Icon as={FiMail as ElementType} color="gray.400" />
                </InputLeftElement>
                <Input
                  type="email"
                  placeholder="Email de contact"
                  value={emailContact}
                  onChange={(e) => setEmailContact(e.target.value)}
                  bg="#2a2f4a"
                  border="1px solid"
                  borderColor="#363b5a"
                  _hover={{ borderColor: '#454b6a' }}
                  _focus={{ borderColor: '#4299E1', boxShadow: 'none' }}
                />
              </InputGroup>
            </FormControl>

            <FormControl>
              <FormLabel>Téléphone de contact</FormLabel>
              <InputGroup>
                <InputLeftElement pointerEvents="none">
                  <Icon as={FiPhone as ElementType} color="gray.400" />
                </InputLeftElement>
                <Input
                  type="tel"
                  placeholder="Numéro de téléphone"
                  value={telephoneContact}
                  onChange={(e) => setTelephoneContact(e.target.value)}
                  bg="#2a2f4a"
                  border="1px solid"
                  borderColor="#363b5a"
                  _hover={{ borderColor: '#454b6a' }}
                  _focus={{ borderColor: '#4299E1', boxShadow: 'none' }}
                />
              </InputGroup>
            </FormControl>

            <FormControl display="flex" alignItems="center">
              <FormLabel htmlFor="org-status" mb="0">
                Organisation active
              </FormLabel>
              <Switch
                id="org-status"
                isChecked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                colorScheme="green"
              />
              <FormHelperText ml={2} color="gray.400">
                {isActive ? 'Active' : 'Inactive'}
              </FormHelperText>
            </FormControl>
          </VStack>
        </ModalBody>

        <ModalFooter gap={2}>
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            colorScheme="blue"
            onClick={handleSubmit}
            isLoading={isSubmitting}
          >
            Enregistrer
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default EditOrganizationModal; 

