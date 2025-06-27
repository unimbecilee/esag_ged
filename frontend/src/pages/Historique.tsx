import React from 'react';
import {
    Box,
    Heading,
    Tabs,
    TabList,
    TabPanels,
    Tab,
    TabPanel,
    Container
} from '@chakra-ui/react';
import HistoryLog from '../components/HistoryLog';

const Historique: React.FC = () => {
    return (
        <Container maxW="container.xl" py={5}>
            <Box bg="#1b1f38" p={5} borderRadius="lg" boxShadow="xl">
                <Heading color="white" size="lg" mb={6}>
                    Historique
                </Heading>

                <Tabs variant="enclosed">
                    <TabList>
                        <Tab 
                            color="white" 
                            _selected={{ color: 'white', bg: '#20243a' }}
                        >
                            Actions Système
                        </Tab>
                        <Tab 
                            color="white" 
                            _selected={{ color: 'white', bg: '#20243a' }}
                        >
                            Actions Utilisateurs
                        </Tab>
                    </TabList>

                    <TabPanels>
                        <TabPanel>
                            <HistoryLog filterType="all" />
                        </TabPanel>
                        <TabPanel>
                            <HistoryLog filterType="user_activity" />
                        </TabPanel>
                    </TabPanels>
                </Tabs>
            </Box>
        </Container>
    );
};

export default Historique; 

