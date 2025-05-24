import React, { useEffect, useState } from "react";
import {
  Box,
  Heading,
  VStack,
  Text,
  Button,
  useToast,
  Flex,
  Icon,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
} from "@chakra-ui/react";
import { FiSearch, FiFileText, FiDownload, FiShare2, FiMoreVertical, FiUser } from "react-icons/fi";
import { ElementType } from "react";

interface SharedDocument {
  id: number;
  titre: string;
  type_document: string;
  date_partage: string;
  proprietaire_nom: string;
  proprietaire_prenom: string;
  taille: number;
  taille_formatee: string;
  permissions: string[];
}

const Shared: React.FC = () => {
  const [documents, setDocuments] = useState<SharedDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("");
  const toast = useToast();

  useEffect(() => {
    fetchSharedDocuments();
  }, []);

  const fetchSharedDocuments = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/documents/shared", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      } else {
        throw new Error("Erreur lors de la récupération des documents partagés");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les documents partagés",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

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

  const handleShare = async (documentId: number) => {
    // Implémenter la logique de partage
    toast({
      title: "Info",
      description: "Fonctionnalité de partage à implémenter",
      status: "info",
      duration: 5000,
      isClosable: true,
    });
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch =
      doc.titre.toLowerCase().includes(searchTerm.toLowerCase()) ||
      `${doc.proprietaire_prenom} ${doc.proprietaire_nom}`
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
    const matchesType = filterType === "" || doc.type_document === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <Box>
      <Heading color="white" mb={6}>
        Documents Partagés
      </Heading>

      <Flex gap={4} mb={6}>
        <InputGroup flex={1}>
          <InputLeftElement pointerEvents="none">
            <Icon as={FiSearch as ElementType} color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Rechercher un document partagé..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
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
        <Select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          bg="#232946"
          color="white"
          borderColor="#232946"
          w="200px"
          _hover={{ borderColor: "#3a8bfd" }}
          _focus={{
            borderColor: "#3a8bfd",
            boxShadow: "0 0 0 1.5px #3a8bfd",
          }}
        >
          <option value="">Tous les types</option>
          <option value="facture">Facture</option>
          <option value="contrat">Contrat</option>
          <option value="rapport">Rapport</option>
          <option value="autre">Autre</option>
        </Select>
      </Flex>

      {loading ? (
        <Text color="white" textAlign="center">
          Chargement...
        </Text>
      ) : filteredDocuments.length === 0 ? (
        <Box
          bg="#20243a"
          borderRadius="lg"
          p={6}
          textAlign="center"
          color="white"
        >
          <Icon
            as={FiFileText as ElementType}
            boxSize={8}
            color="gray.400"
            mb={2}
          />
          <Text>Aucun document partagé trouvé</Text>
        </Box>
      ) : (
        <Box bg="#20243a" borderRadius="lg" p={6} overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">Document</Th>
                <Th color="white">Type</Th>
                <Th color="white">Propriétaire</Th>
                <Th color="white">Date de partage</Th>
                <Th color="white">Permissions</Th>
                <Th color="white">Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredDocuments.map((doc) => (
                <Tr key={doc.id}>
                  <Td>
                    <Flex align="center">
                      <Icon
                        as={FiFileText as ElementType}
                        color="#3a8bfd"
                        mr={2}
                      />
                      <Text color="white">{doc.titre}</Text>
                    </Flex>
                  </Td>
                  <Td>
                    <Badge colorScheme="blue">{doc.type_document}</Badge>
                  </Td>
                  <Td>
                    <Flex align="center">
                      <Icon
                        as={FiUser as ElementType}
                        color="gray.400"
                        mr={2}
                      />
                      <Text color="white">
                        {doc.proprietaire_prenom} {doc.proprietaire_nom}
                      </Text>
                    </Flex>
                  </Td>
                  <Td color="white">
                    {new Date(doc.date_partage).toLocaleDateString()}
                  </Td>
                  <Td>
                    <Flex gap={2}>
                      {doc.permissions.map((permission) => (
                        <Badge
                          key={permission}
                          colorScheme={
                            permission === "read" ? "green" : "blue"
                          }
                        >
                          {permission}
                        </Badge>
                      ))}
                    </Flex>
                  </Td>
                  <Td>
                    <Flex>
                      <Button
                        size="sm"
                        leftIcon={<Icon as={FiDownload as ElementType} />}
                        colorScheme="blue"
                        variant="ghost"
                        mr={2}
                        onClick={() => handleDownload(doc.id)}
                      >
                        Télécharger
                      </Button>
                      <Menu>
                        <MenuButton
                          as={Button}
                          size="sm"
                          variant="ghost"
                          colorScheme="blue"
                        >
                          <Icon as={FiMoreVertical as ElementType} />
                        </MenuButton>
                        <MenuList bg="#232946">
                          <MenuItem
                            icon={<Icon as={FiShare2 as ElementType} />}
                            onClick={() => handleShare(doc.id)}
                            _hover={{ bg: "#20243a" }}
                          >
                            Partager
                          </MenuItem>
                        </MenuList>
                      </Menu>
                    </Flex>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}
    </Box>
  );
};

export default Shared; 