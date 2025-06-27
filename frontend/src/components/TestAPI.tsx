import React, { useState } from "react";
import {
  Box,
  Button,
  VStack,
  Text,
  Code,
  Card,
  CardBody,
  Heading,
  useToast,
  Alert,
  AlertIcon,
} from "@chakra-ui/react";

const TestAPI: React.FC = () => {
  const [result, setResult] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const testConnection = async () => {
    setLoading(true);
    setResult("");

    try {
      // Test 1: Connexion simple
      setResult("🔍 Test 1: Connexion au serveur Flask...\n");
      
      const healthResponse = await fetch("http://localhost:5000/", {
        method: "GET",
        mode: "cors",
      });
      
      setResult(prev => prev + `Status: ${healthResponse.status}\n`);
      setResult(prev => prev + `Headers: ${JSON.stringify(Object.fromEntries(healthResponse.headers.entries()))}\n\n`);

      // Test 2: Login
      setResult(prev => prev + "🔐 Test 2: Connexion utilisateur...\n");
      
      const loginResponse = await fetch("http://localhost:5000/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: "admin@esag.com",
          password: "admin123"
        }),
        mode: "cors",
      });

      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        const token = loginData.token;
        setResult(prev => prev + `✅ Login réussi, token: ${token.substring(0, 20)}...\n\n`);

        // Test 3: API Trash
        setResult(prev => prev + "🗑️ Test 3: API Trash...\n");
        
        const trashResponse = await fetch("http://localhost:5000/api/trash", {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          mode: "cors",
        });

        setResult(prev => prev + `Status: ${trashResponse.status}\n`);
        setResult(prev => prev + `Content-Type: ${trashResponse.headers.get('Content-Type')}\n`);

        if (trashResponse.ok) {
          const trashData = await trashResponse.json();
          setResult(prev => prev + `✅ API Trash OK\n`);
          setResult(prev => prev + `Items: ${trashData.items ? trashData.items.length : 0}\n`);
          setResult(prev => prev + `Total: ${trashData.total || 'N/A'}\n`);
          
          if (trashData.items && trashData.items.length > 0) {
            setResult(prev => prev + `Premier élément: ${trashData.items[0].title || 'Sans titre'}\n`);
          }
        } else {
          const errorText = await trashResponse.text();
          setResult(prev => prev + `❌ Erreur API Trash: ${errorText.substring(0, 200)}\n`);
        }
      } else {
        const loginError = await loginResponse.text();
        setResult(prev => prev + `❌ Erreur login: ${loginError}\n`);
      }

    } catch (error) {
      setResult(prev => prev + `❌ Erreur réseau: ${error}\n`);
      toast({
        title: "Erreur",
        description: `Erreur de connexion: ${error}`,
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const testProxy = async () => {
    setLoading(true);
    setResult("");

    try {
      setResult("🔍 Test avec proxy React...\n");
      
      // Test avec URL relative (via proxy)
      const response = await fetch("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: "admin@esag.com",
          password: "admin123"
        }),
      });

      setResult(prev => prev + `Status: ${response.status}\n`);
      setResult(prev => prev + `URL: ${response.url}\n`);
      
      if (response.ok) {
        const data = await response.json();
        setResult(prev => prev + `✅ Proxy fonctionne!\n`);
        setResult(prev => prev + `Token: ${data.token.substring(0, 20)}...\n`);
      } else {
        const errorText = await response.text();
        setResult(prev => prev + `❌ Erreur proxy: ${errorText.substring(0, 200)}\n`);
      }

    } catch (error) {
      setResult(prev => prev + `❌ Erreur proxy: ${error}\n`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box p={6} maxW="800px" mx="auto">
      <VStack spacing={6} align="stretch">
        <Heading size="lg">🧪 Test de l'API ESAG GED</Heading>
        
        <Alert status="info">
          <AlertIcon />
          Ce composant teste la communication entre React et Flask
        </Alert>

        <VStack spacing={4}>
          <Button
            onClick={testConnection}
            isLoading={loading}
            colorScheme="blue"
            size="lg"
            w="full"
          >
            🔗 Test connexion directe (localhost:5000)
          </Button>

          <Button
            onClick={testProxy}
            isLoading={loading}
            colorScheme="green"
            size="lg"
            w="full"
          >
            🔄 Test avec proxy React
          </Button>
        </VStack>

        {result && (
          <Card>
            <CardBody>
              <Text fontWeight="bold" mb={2}>Résultats du test:</Text>
              <Code p={4} w="full" whiteSpace="pre-wrap" fontSize="sm">
                {result}
              </Code>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Box>
  );
};

export default TestAPI; 