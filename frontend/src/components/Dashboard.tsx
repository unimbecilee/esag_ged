import React, { useEffect, useState } from "react";
import { Box, Flex, Text, Icon, Heading, Badge, Button, useToast, Menu, MenuButton, MenuList, MenuItem, useDisclosure } from "@chakra-ui/react";
import { FiUsers, FiFileText, FiFolder, FiArchive, FiUpload, FiDownload, FiShare2, FiMoreVertical } from "react-icons/fi";
import { ElementType } from 'react';
import FileUploadModal from './FileUploadModal';
import ShareModal from './ShareModal';
import SearchBar from './SearchBar';

interface Document {
  id: number;
  titre: string;
  type_document: string;
  taille: number;
  taille_formatee: string;
  date_creation: string;
  proprietaire_nom: string;
  proprietaire_prenom: string;
  statut: string;
}

interface Stats {
  total_documents: number;
  documents_partages: number;
  espace_utilise: string;
  documents_par_type: {
    [key: string]: number;
  };
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [stats, setStats] = useState<Stats>({
    total_documents: 0,
    documents_partages: 0,
    espace_utilise: "0 B",
    documents_par_type: {}
  });
  const [recentDocs, setRecentDocs] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<number | null>(null);
  const { isOpen: isShareOpen, onOpen: onShareOpen, onClose: onShareClose } = useDisclosure();
  const toast = useToast();

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("Token d'authentification non trouvé");
      }

      const response = await fetch("http://localhost:5000/api/documents/stats", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const data = await response.json();
      setStats(data);
    } catch (e) {
      console.error("Erreur lors de la récupération des statistiques:", e);
      toast({
        title: "Erreur",
        description: "Impossible de charger les statistiques",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const fetchRecentDocs = async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("Token d'authentification non trouvé");
      }

      const response = await fetch("http://localhost:5000/api/documents/recent", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const data = await response.json();
      console.log("Données reçues de l'API:", data);

      if (!Array.isArray(data)) {
        throw new Error("Format de données invalide");
      }

      setRecentDocs(data);
    } catch (e) {
      console.error("Erreur lors de la récupération des documents récents:", e);
      toast({
        title: "Erreur",
        description: "Impossible de charger les documents récents",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchStats();
    fetchRecentDocs();
  }, []);

  const handleDownload = async (documentId: number) => {
    try {
      const response = await fetch(
        `http://localhost:5000/api/documents/${documentId}/download`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `document-${documentId}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        throw new Error("Erreur lors du téléchargement");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de télécharger le document",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleShareClick = (documentId: number) => {
    setSelectedDocument(documentId);
    onShareOpen();
  };

  if (loading) {
    return (
      <Flex align="center" justify="center" h="100%">
        <Text color="white">Chargement...</Text>
      </Flex>
    );
  }

  return (
    <Box>
      <Flex direction="column" gap={6}>
        <Flex justify="space-between" align="center">
          <Heading color="white">
            Tableau de bord
          </Heading>
          <Button
            leftIcon={<Icon as={FiUpload as ElementType} />}
            colorScheme="green"
            onClick={() => setIsUploadModalOpen(true)}
          >
            Upload Document
          </Button>
        </Flex>

        <SearchBar />

        {/* Statistiques */}
        <Flex gap={4} wrap="wrap">
          <Box bg="#20243a" borderRadius="lg" p={{ base: 4, md: 6 }} color="white" minW={{ base: "100%", md: "200px" }} mb={{ base: 2, md: 0 }}>
            <Text fontWeight="bold" mb={2}>
              <Icon as={FiFileText as ElementType} mr={2} />
              Documents totaux
            </Text>
            <Text fontSize="2xl" fontWeight="bold">
              {stats.total_documents}
            </Text>
          </Box>
          <Box bg="#20243a" borderRadius="lg" p={{ base: 4, md: 6 }} color="white" minW={{ base: "100%", md: "200px" }} mb={{ base: 2, md: 0 }}>
            <Text fontWeight="bold" mb={2}>
              <Icon as={FiShare2 as ElementType} mr={2} />
              Documents partagés
            </Text>
            <Text fontSize="2xl" fontWeight="bold">
              {stats.documents_partages}
            </Text>
          </Box>
          <Box bg="#20243a" borderRadius="lg" p={{ base: 4, md: 6 }} color="white" minW={{ base: "100%", md: "200px" }} mb={{ base: 2, md: 0 }}>
            <Text fontWeight="bold" mb={2}>
              <Icon as={FiFolder as ElementType} mr={2} />
              Espace utilisé
            </Text>
            <Text fontSize="2xl" fontWeight="bold">
              {stats.espace_utilise}
            </Text>
          </Box>
        </Flex>

        {/* Types de documents */}
        <Box bg="#20243a" borderRadius="lg" p={{ base: 4, md: 6 }} mb={8}>
          <Text color="white" fontWeight="bold" fontSize="lg" mb={4}>
            Types de documents
          </Text>
          <Flex gap={2} wrap="wrap">
            {Object.entries(stats.documents_par_type).map(([type, count]) => (
              <Badge key={type} colorScheme="blue" fontSize="sm" p={2}>
                {type}: {count}
              </Badge>
            ))}
          </Flex>
        </Box>

        {/* Documents récents */}
        <Box bg="#20243a" borderRadius="lg" p={{ base: 4, md: 6 }} mb={8}>
          <Text color="white" fontWeight="bold" fontSize="lg" mb={4}>
            Documents récents
          </Text>
          <Flex gap={4} wrap="wrap">
            {recentDocs.map((doc, index) => (
              <Box
                key={`${doc.id}-${index}`}
                bg="#232946"
                borderRadius="md"
                p={4}
                color="white"
                minW="250px"
                maxW="300px"
                mb={2}
              >
                <Flex direction="column" gap={2}>
                  <Text color="white" fontSize="md">
                    {doc.titre}
                  </Text>
                  <Flex align="center" gap={2}>
                    <Badge colorScheme="blue">
                      {doc.type_document}
                    </Badge>
                    <Text fontSize="sm" color="gray.400">
                      {doc.taille_formatee}
                    </Text>
                  </Flex>
                  <Text fontSize="sm" color="gray.500">
                    {new Date(doc.date_creation).toLocaleDateString('fr-FR')}
                  </Text>
                  {doc.statut && (
                    <Badge colorScheme={doc.statut === "DISPONIBLE" ? "green" : "yellow"}>
                      {doc.statut}
                    </Badge>
                  )}
                </Flex>
              </Box>
            ))}
          </Flex>
        </Box>

        <FileUploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onUploadSuccess={() => {
            toast({
              title: "Succès",
              description: "Le document a été uploadé avec succès",
              status: "success",
              duration: 5000,
              isClosable: true,
            });
            fetchStats();
            fetchRecentDocs();
          }}
        />

        <ShareModal
          isOpen={isShareOpen}
          onClose={onShareClose}
          documentId={selectedDocument || 0}
          onShareSuccess={() => {
            fetchStats();
            fetchRecentDocs();
          }}
        />
      </Flex>
    </Box>
  );
};

export default Dashboard;
