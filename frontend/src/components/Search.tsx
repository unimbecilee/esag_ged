import React, { useState, useEffect } from "react";
import {
  Box,
  Input,
  InputGroup,
  InputLeftElement,
  Icon,
  VStack,
  Text,
  Heading,
  Flex,
  Badge,
  useToast,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useDisclosure,
} from "@chakra-ui/react";
import { FiSearch, FiFileText, FiDownload, FiShare2, FiMoreVertical, FiEdit2 } from "react-icons/fi";
import { ElementType } from "react";
import ShareModal from "./ShareModal";

interface Document {
  id: number;
  titre: string;
  type_document: string;
  date_creation: string;
  proprietaire_nom: string;
  proprietaire_prenom: string;
  taille: number;
  taille_formatee: string;
}

const Search: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<number | null>(null);
  const toast = useToast();
  
  // Modal state
  const { isOpen: isShareOpen, onOpen: onShareOpen, onClose: onShareClose } = useDisclosure();

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchTerm.length >= 2) {
        searchDocuments();
      } else if (searchTerm.length === 0) {
        setDocuments([]);
      }
    }, 500);

    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  const searchDocuments = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:5000/api/documents/search?q=${encodeURIComponent(
          searchTerm
        )}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      } else {
        throw new Error("Erreur lors de la recherche");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de rechercher les documents",
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

  const handleShareClick = (documentId: number) => {
    setSelectedDocument(documentId);
    onShareOpen();
  };

  const handleEditClick = (documentId: number) => {
    // Redirection vers la page d'édition
    window.location.href = `/documents/edit/${documentId}`;
  };

  return (
    <Box>
      <Heading color="white" mb={6}>
        Recherche de Documents
      </Heading>

      <Box bg="#20243a" borderRadius="lg" p={6} mb={6}>
        <InputGroup>
          <InputLeftElement pointerEvents="none">
            <Icon as={FiSearch as ElementType} color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Rechercher un document..."
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
      </Box>

      {loading ? (
        <Text color="white" textAlign="center">
          Recherche en cours...
        </Text>
      ) : (
        <VStack spacing={4} align="stretch">
          {documents.map((doc) => (
            <Box
              key={doc.id}
              bg="#20243a"
              borderRadius="lg"
              p={4}
              _hover={{ bg: "#232946" }}
              transition="background 0.2s"
            >
              <Flex justify="space-between" align="center">
                <Flex align="center">
                  <Icon
                    as={FiFileText as ElementType}
                    color="#3a8bfd"
                    boxSize={6}
                    mr={3}
                  />
                  <Box>
                    <Text color="white" fontWeight="bold">
                      {doc.titre}
                    </Text>
                    <Flex align="center" mt={1}>
                      <Badge colorScheme="blue" mr={2}>
                        {doc.type_document}
                      </Badge>
                      <Text color="gray.400" fontSize="sm">
                        {doc.taille_formatee} • {new Date(doc.date_creation).toLocaleDateString()}
                      </Text>
                    </Flex>
                    <Text color="gray.500" fontSize="sm" mt={1}>
                      Propriétaire : {doc.proprietaire_prenom} {doc.proprietaire_nom}
                    </Text>
                  </Box>
                </Flex>
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
                      icon={<Icon as={FiDownload as ElementType} />}
                      onClick={() => handleDownload(doc.id)}
                      _hover={{ bg: "#20243a" }}
                    >
                      Télécharger
                    </MenuItem>
                    <MenuItem
                      icon={<Icon as={FiShare2 as ElementType} />}
                      onClick={() => handleShareClick(doc.id)}
                      _hover={{ bg: "#20243a" }}
                    >
                      Partager
                    </MenuItem>
                    <MenuItem
                      icon={<Icon as={FiEdit2 as ElementType} />}
                      onClick={() => handleEditClick(doc.id)}
                      _hover={{ bg: "#20243a" }}
                    >
                      Modifier
                    </MenuItem>
                  </MenuList>
                </Menu>
              </Flex>
            </Box>
          ))}
          {searchTerm.length >= 2 && documents.length === 0 && !loading && (
            <Text color="white" textAlign="center">
              Aucun résultat trouvé
            </Text>
          )}
        </VStack>
      )}

      {/* Share Modal */}
      <ShareModal
        isOpen={isShareOpen}
        onClose={onShareClose}
        documentId={selectedDocument || 0}
        onShareSuccess={searchDocuments}
      />
    </Box>
  );
};

export default Search; 