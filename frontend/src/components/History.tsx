import React, { useState, useEffect } from "react";
import HistoryLog from "./HistoryLog";
import RequireRole from './RequireRole';
import { 
  Box, 
  Heading, 
  Text, 
  Container, 
  Tabs, 
  TabList, 
  TabPanels, 
  Tab, 
  TabPanel,
  Flex,
  Badge,
  Tooltip,
  IconButton,
  useToast
} from "@chakra-ui/react";
import { InfoIcon, RepeatIcon } from "@chakra-ui/icons";

const History: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const toast = useToast();

  useEffect(() => {
    console.log('History component mounted, active tab:', activeTab);
    // Afficher un toast pour indiquer que le composant est chargé
    toast({
      title: "Chargement des logs",
      description: "Tentative de récupération des logs système...",
      status: "info",
      duration: 3000,
      isClosable: true,
    });
  }, []);

  const handleTabChange = (index: number) => {
    console.log('Tab changed to:', index);
    setActiveTab(index);
  };

  return (
    <RequireRole roles={["admin", "archiviste"]}>
      <Container maxW="container.xl" py={5}>
      <Box mb={6}>
        <Flex justify="space-between" align="center">
          <Box>
            <Heading color="white" size="lg" mb={2}>
              Historique des activités
            </Heading>
            <Text color="gray.400" mb={4}>
              Consultez l'historique complet des actions et événements du système
            </Text>
          </Box>
          <Tooltip label="Informations sur les logs">
            <IconButton
              aria-label="Informations"
              icon={<InfoIcon />}
              variant="ghost"
              colorScheme="blue"
            />
          </Tooltip>
        </Flex>
      </Box>
      <Box 
        bg="#1A1D2D" 
        borderRadius="lg" 
        p={6} 
        boxShadow="xl"
      >
        <Tabs 
          variant="soft-rounded" 
          colorScheme="blue" 
          mb={4} 
          index={activeTab} 
          onChange={handleTabChange}
        >
          <TabList>
            <Tab _selected={{ color: 'white', bg: '#3182CE' }}>
              <Flex align="center" gap={2}>
                Tous les logs
                <Badge colorScheme="blue" borderRadius="full">Système</Badge>
              </Flex>
            </Tab>
            <Tab _selected={{ color: 'white', bg: '#3182CE' }}>
              <Flex align="center" gap={2}>
                Erreurs
                <Badge colorScheme="red" borderRadius="full">Important</Badge>
              </Flex>
            </Tab>
            <Tab _selected={{ color: 'white', bg: '#3182CE' }}>
              <Flex align="center" gap={2}>
                Activité utilisateurs
                <Badge colorScheme="green" borderRadius="full">Sécurité</Badge>
              </Flex>
            </Tab>
          </TabList>
          <TabPanels>
            <TabPanel p={0} pt={4}>
              <HistoryLog filterType="all" />
            </TabPanel>
            <TabPanel p={0} pt={4}>
              <HistoryLog filterType="errors" />
            </TabPanel>
            <TabPanel p={0} pt={4}>
              <HistoryLog filterType="user_activity" />
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Box>
    </Container>
    </RequireRole>
  );
};

export default History;

