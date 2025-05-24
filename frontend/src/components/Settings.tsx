import React, { useState, useEffect } from "react";
import {
  Box,
  Heading,
  VStack,
  Text,
  Button,
  useToast,
  FormControl,
  FormLabel,
  Input,
  Divider,
  Flex,
  Icon,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
} from "@chakra-ui/react";
import { FiUser, FiLock, FiSave } from "react-icons/fi";
import { ElementType } from "react";
import api from "../services/api";

interface UserProfile {
  id: number;
  nom: string;
  prenom: string;
  email: string;
  role: string;
}

interface PasswordForm {
  ancien_mdp: string;
  nouveau_mdp: string;
  confirmer_mdp: string;
}

const Settings: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [passwordForm, setPasswordForm] = useState<PasswordForm>({
    ancien_mdp: "",
    nouveau_mdp: "",
    confirmer_mdp: "",
  });
  const toast = useToast();

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await api.get("/auth/me");
      setProfile(response.data);
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les informations du profil",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordForm.nouveau_mdp !== passwordForm.confirmer_mdp) {
      toast({
        title: "Erreur",
        description: "Les mots de passe ne correspondent pas",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setLoading(true);
    try {
      await api.put("/auth/password", passwordForm);
      toast({
        title: "Succès",
        description: "Mot de passe modifié avec succès",
        status: "success",
        duration: 5000,
        isClosable: true,
      });
      setIsPasswordModalOpen(false);
      setPasswordForm({
        ancien_mdp: "",
        nouveau_mdp: "",
        confirmer_mdp: "",
      });
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.message || "Erreur lors de la modification du mot de passe",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  if (!profile) {
    return null;
  }

  return (
    <Box>
      <Heading color="white" mb={6}>
        Paramètres
      </Heading>

      <VStack spacing={8} align="stretch">
        <Box bg="#20243a" borderRadius="lg" p={6}>
          <Flex align="center" mb={4}>
            <Icon as={FiUser as ElementType} color="#3a8bfd" boxSize={6} mr={2} />
            <Heading size="md" color="white">
              Informations Personnelles
            </Heading>
          </Flex>
          <VStack spacing={4}>
            <FormControl>
              <FormLabel color="white">Nom</FormLabel>
              <Input
                value={profile.nom}
                isReadOnly
                bg="#232946"
                color="white"
                borderColor="#232946"
              />
            </FormControl>
            <FormControl>
              <FormLabel color="white">Prénom</FormLabel>
              <Input
                value={profile.prenom}
                isReadOnly
                bg="#232946"
                color="white"
                borderColor="#232946"
              />
            </FormControl>
            <FormControl>
              <FormLabel color="white">Email</FormLabel>
              <Input
                value={profile.email}
                isReadOnly
                bg="#232946"
                color="white"
                borderColor="#232946"
              />
            </FormControl>
            <FormControl>
              <FormLabel color="white">Rôle</FormLabel>
              <Input
                value={profile.role}
                isReadOnly
                bg="#232946"
                color="white"
                borderColor="#232946"
              />
            </FormControl>
          </VStack>
        </Box>

        <Box bg="#20243a" borderRadius="lg" p={6}>
          <Flex align="center" mb={4}>
            <Icon as={FiLock as ElementType} color="#3a8bfd" boxSize={6} mr={2} />
            <Heading size="md" color="white">
              Sécurité
            </Heading>
          </Flex>
          <Button
            colorScheme="blue"
            onClick={() => setIsPasswordModalOpen(true)}
            leftIcon={<Icon as={FiLock as ElementType} />}
          >
            Modifier le mot de passe
          </Button>
        </Box>
      </VStack>

      <Modal 
        isOpen={isPasswordModalOpen} 
        onClose={() => {
          setIsPasswordModalOpen(false);
          setPasswordForm({
            ancien_mdp: "",
            nouveau_mdp: "",
            confirmer_mdp: "",
          });
        }}
      >
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white">
          <ModalHeader>Modifier le mot de passe</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <form onSubmit={handlePasswordChange}>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Ancien mot de passe</FormLabel>
                  <Input
                    type="password"
                    value={passwordForm.ancien_mdp}
                    onChange={(e) => setPasswordForm({ ...passwordForm, ancien_mdp: e.target.value })}
                    bg="#232946"
                    borderColor="#232946"
                  />
                </FormControl>
                <FormControl isRequired>
                  <FormLabel>Nouveau mot de passe</FormLabel>
                  <Input
                    type="password"
                    value={passwordForm.nouveau_mdp}
                    onChange={(e) => setPasswordForm({ ...passwordForm, nouveau_mdp: e.target.value })}
                    bg="#232946"
                    borderColor="#232946"
                  />
                </FormControl>
                <FormControl isRequired>
                  <FormLabel>Confirmer le nouveau mot de passe</FormLabel>
                  <Input
                    type="password"
                    value={passwordForm.confirmer_mdp}
                    onChange={(e) => setPasswordForm({ ...passwordForm, confirmer_mdp: e.target.value })}
                    bg="#232946"
                    borderColor="#232946"
                  />
                </FormControl>
                <Button
                  type="submit"
                  colorScheme="blue"
                  width="full"
                  isLoading={loading}
                >
                  Modifier le mot de passe
                </Button>
              </VStack>
            </form>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Settings; 