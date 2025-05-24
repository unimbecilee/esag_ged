import React, { useEffect, useState } from "react";
import {
  Box,
  Heading,
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
  useDisclosure,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
} from "@chakra-ui/react";
import { FiFileText, FiSearch, FiDownload, FiShare2, FiTrash2, FiMoreVertical, FiEdit2 } from "react-icons/fi";
import { ElementType } from "react";
import ShareModal from "./ShareModal";

interface Document {
  id: number;
  titre: string;
  type_document: string;
  date_creation: string;
  taille: number;
  taille_formatee: string;
  statut: string;
}

const MyDocuments: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("");
  const [selectedDocument, setSelectedDocument] = useState<number | null>(null);
  const toast = useToast();
  
  // Modals state
  const { isOpen: isShareOpen, onOpen: onShareOpen, onClose: onShareClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const cancelRef = React.useRef<HTMLButtonElement>(null);

  useEffect(() => {
    fetchMyDocuments();
  }, []);

  const fetchMyDocuments = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/documents/my", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      } else {
        throw new Error("Erreur lors de la récupération des documents");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger vos documents",
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

  const handleDelete = async () => {
    if (!selectedDocument) return;
    
    try {
      const response = await fetch(
        `http://localhost:5000/api/documents/${selectedDocument}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Document supprimé avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        fetchMyDocuments();
      } else {
        throw new Error("Erreur lors de la suppression");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le document",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      onDeleteClose();
    }
  };

  const handleShareClick = (documentId: number) => {
    setSelectedDocument(documentId);
    onShareOpen();
  };

  const handleDeleteClick = (documentId: number) => {
    setSelectedDocument(documentId);
    onDeleteOpen();
  };

  const handleEditClick = (documentId: number) => {
    // Redirection vers la page d'édition
    window.location.href = `/documents/edit/${documentId}`;
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.titre.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === "" || doc.type_document === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <Box>
      <Heading color="white" mb={6}>
        Mes Documents
      </Heading>

      <Flex gap={4} mb={6}>
        <InputGroup flex={1}>
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
          <option value="PDF">PDF</option>
          <option value="Word">Word</option>
          <option value="Excel">Excel</option>
          <option value="Image">Image</option>
          <option value="Autre">Autre</option>
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
          <Text>Aucun document trouvé</Text>
        </Box>
      ) : (
        <Box bg="#20243a" borderRadius="lg" p={6} overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">Document</Th>
                <Th color="white">Type</Th>
                <Th color="white">Date de création</Th>
                <Th color="white">Taille</Th>
                <Th color="white">Statut</Th>
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
                  <Td color="white">
                    {new Date(doc.date_creation).toLocaleDateString()}
                  </Td>
                  <Td color="white">
                    {doc.taille_formatee}
                  </Td>
                  <Td>
                    <Badge
                      colorScheme={
                        doc.statut === "DISPONIBLE" ? "green" : "yellow"
                      }
                    >
                      {doc.statut}
                    </Badge>
                  </Td>
                  <Td>
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
                        <MenuItem
                          icon={<Icon as={FiTrash2 as ElementType} />}
                          onClick={() => handleDeleteClick(doc.id)}
                          _hover={{ bg: "#20243a" }}
                          color="red.400"
                        >
                          Supprimer
                        </MenuItem>
                      </MenuList>
                    </Menu>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}

      {/* Share Modal */}
      <ShareModal
        isOpen={isShareOpen}
        onClose={onShareClose}
        documentId={selectedDocument || 0}
        onShareSuccess={fetchMyDocuments}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        isOpen={isDeleteOpen}
        leastDestructiveRef={cancelRef}
        onClose={onDeleteClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent bg="#20243a">
            <AlertDialogHeader fontSize="lg" fontWeight="bold" color="white">
              Supprimer le document
            </AlertDialogHeader>

            <AlertDialogBody color="white">
              Êtes-vous sûr ? Cette action ne peut pas être annulée.
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button
                ref={cancelRef}
                onClick={onDeleteClose}
                variant="ghost"
                color="white"
                _hover={{ bg: "#232946" }}
              >
                Annuler
              </Button>
              <Button colorScheme="red" onClick={handleDelete} ml={3}>
                Supprimer
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Box>
  );
};

export default MyDocuments; 