import React, { useState, FormEvent, ChangeEvent, useEffect } from "react";
import {
  Box,
  Button,
  FormControl,
  Input,
  InputGroup,
  InputLeftElement,
  VStack,
  Heading,
  Text,
  useToast,
  Link,
  Icon,
  Flex,
} from "@chakra-ui/react";
import { EmailIcon, LockIcon } from "@chakra-ui/icons";
import { useNavigate } from "react-router-dom";
import config from "../config";

const API_URL = config.API_URL;

interface LoginProps {
  onAuthSuccess?: () => void;
}

const Login: React.FC<LoginProps> = ({ onAuthSuccess }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [loginSuccess, setLoginSuccess] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  // Vérifier si l'utilisateur est déjà connecté au chargement
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      console.log("Token trouvé au chargement, redirection vers dashboard");
      navigate("/dashboard");
    }
  }, [navigate]);

  // Redirection après connexion réussie
  useEffect(() => {
    if (loginSuccess) {
      console.log("Redirection après connexion réussie...");
      setTimeout(() => {
        navigate("/dashboard");
      }, 1000); // Court délai pour laisser le toast s'afficher
    }
  }, [loginSuccess, navigate]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    try {
      console.log("=== Début de la tentative de connexion ===");
      console.log("URL de l'API:", `${API_URL}/login`);
      console.log("Données envoyées:", { email, password: "***" });

      const response = await fetch(`${API_URL}/login`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      console.log("Statut de la réponse:", response.status);
      console.log("Headers de la réponse:", Object.fromEntries(response.headers));
      
      const data = await response.json();
      console.log("Données reçues:", data);

      if (response.ok) {
        if (data.access_token) {
          console.log("Token reçu, sauvegarde dans localStorage");
          localStorage.setItem("token", data.access_token);
          if (data.user) {
            console.log("Données utilisateur reçues:", data.user);
            localStorage.setItem("user", JSON.stringify(data.user));
          }
          
          // Appeler le callback si fourni
          if (onAuthSuccess) {
            console.log("Appel du callback onAuthSuccess");
            onAuthSuccess();
          }
          
          // Marquer la connexion comme réussie pour déclencher la redirection
          setLoginSuccess(true);
          
          toast({
            title: "Connexion réussie",
            description: "Bienvenue dans votre espace",
            status: "success",
            duration: 3000,
            isClosable: true,
          });
        } else {
          console.error("Token manquant dans la réponse");
          throw new Error("Token manquant dans la réponse");
        }
      } else {
        console.error("Erreur de connexion:", data.message);
        throw new Error(data.message || "Erreur lors de la connexion");
      }
    } catch (error) {
      console.error("Erreur complète:", error);
      toast({
        title: "Erreur de connexion",
        description: error instanceof Error ? error.message : "Identifiants invalides",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleEmailChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.trim();
    console.log("Email saisi:", value);
    setEmail(value);
  };

  const handlePasswordChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    console.log("Mot de passe saisi (longueur):", value.length);
    setPassword(value);
  };

  return (
    <Flex
      minH="100vh"
      align="center"
      justify="center"
      bgGradient="radial(ellipse at top, #232946 60%, #121629 100%)"
    >
      <Box
        bg="#181c2f"
        borderRadius="16px"
        boxShadow="0 0 24px 2px #3a3f5a, 0 0 0 4px #fff3"
        p={8}
        minW={{ base: "90vw", sm: "400px" }}
        maxW="400px"
        textAlign="center"
        border="2px solid #fff2"
      >
        <Flex align="center" justify="center" mb={4}>
          <Box
            bgGradient="linear(to-br, #3a8bfd, #6f6cff)"
            borderRadius="full"
            w="48px"
            h="48px"
            display="flex"
            alignItems="center"
            justifyContent="center"
            boxShadow="0 0 0 4px #fff3"
          >
            <Icon viewBox="0 0 200 200" color="white" boxSize={7}>
              <path d="M100,20 A80,80 0 1,0 100,180 A80,80 0 1,0 100,20" fill="currentColor" />
            </Icon>
          </Box>
        </Flex>
        <Heading color="white" size="lg" mb={1}>
          ESAG GED
        </Heading>
        <Text color="gray.300" mb={8} fontSize="md">
          Bienvenue sur la plateforme GED de l'ESAG.
        </Text>
        <form onSubmit={handleSubmit}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <InputGroup>
                <InputLeftElement pointerEvents="none">
                  <EmailIcon color="gray.400" />
                </InputLeftElement>
                <Input
                  type="email"
                  placeholder="Adresse email"
                  value={email}
                  onChange={handleEmailChange}
                  bg="#232946"
                  color="white"
                  borderColor="#232946"
                  _placeholder={{ color: "gray.400" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </InputGroup>
            </FormControl>
            <FormControl isRequired>
              <InputGroup>
                <InputLeftElement pointerEvents="none">
                  <LockIcon color="gray.400" />
                </InputLeftElement>
                <Input
                  type="password"
                  placeholder="Mot de passe"
                  value={password}
                  onChange={handlePasswordChange}
                  bg="#232946"
                  color="white"
                  borderColor="#232946"
                  _placeholder={{ color: "gray.400" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </InputGroup>
            </FormControl>
            <Button
              type="submit"
              color="white"
              bgGradient="linear(to-r, #3a8bfd, #6f6cff)"
              _hover={{ bgGradient: "linear(to-r, #6f6cff, #3a8bfd)" }}
              size="lg"
              fontWeight="bold"
              mt={2}
              isLoading={loading}
              loadingText="Connexion en cours..."
              borderRadius="8px"
              boxShadow="0 2px 8px #3a8bfd44"
            >
              Se Connecter
            </Button>
          </VStack>
        </form>
        <Link
          color="#6f6cff"
          mt={4}
          display="block"
          fontSize="sm"
          href="#"
          _hover={{ textDecoration: "underline" }}
        >
          Mot de passe oublié ?
        </Link>
      </Box>
    </Flex>
  );
};

export default Login;
