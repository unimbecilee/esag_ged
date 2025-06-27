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
import { FiFileText, FiSearch, FiTrash2, FiMoreVertical, FiRefreshCw } from "react-icons/fi";
import { ElementType } from "react";
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import { API_URL } from '../config';

interface Document {
  id: number;
  titre: string;
  type_document: string;
  date_creation: string | null;
  date_suppression: string | null;
  taille: number;
  taille_formatee: string;
}

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return 'Non définie';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return 'Date invalide';
  }
};

const Corbeille: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("");
  const [selectedDocument, setSelectedDocument] = useState<number | null>(null);
  const toast = useToast();
  
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const { isOpen: isRestoreOpen, onOpen: onRestoreOpen, onClose: onRestoreClose } = useDisclosure();
  const cancelRef = React.useRef<HTMLButtonElement>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const result = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${API_URL}/api/trash`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });

          if (!response.ok) {
            throw new Error('Erreur lors de la récupération des documents');
          }

          const data = await response.json();
          return data;
        },
        {
          loadingMessage: "Chargement de la corbeille...",
          errorMessage: "Impossible de charger les documents supprimés"
        }
      );

      if (result) {
        setDocuments(result);
      }
    } catch (err) {
      toast({
        title: "Erreur",
        description: err instanceof Error ? err.message : "Erreur lors du chargement de la corbeille",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestore = async () => {
    if (!selectedDocument) return;
    
    try {
      const response = await fetch(
        `${API_URL}/api/trash/${selectedDocument}/restore`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Document restauré avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        fetchDocuments();
      } else {
        throw new Error("Erreur lors de la restauration");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de restaurer le document",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      onRestoreClose();
    }
  };

  const handlePermanentDelete = async () => {
    if (!selectedDocument) return;
    
    try {
      const response = await fetch(
        `${API_URL}/api/trash/${selectedDocument}`,
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
          description: "Document supprimé définitivement",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        fetchDocuments();
      } else {
        throw new Error("Erreur lors de la suppression");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer définitivement le document",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      onDeleteClose();
    }
  };

  const handleRestoreClick = (documentId: number) => {
    setSelectedDocument(documentId);
    onRestoreOpen();
  };

  const handleDeleteClick = (documentId: number) => {
    setSelectedDocument(documentId);
    onDeleteOpen();
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.titre.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = !filterType || doc.type_document === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading color="white">Corbeille</Heading>
      </Flex>

      <Flex wrap="wrap" gap={4} mb={6}>
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
            _placeholder={{ color: "gray.400" }}
          />
        </InputGroup>
        <Select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          bg="#232946"
          color="white"
          w="200px"
        >
          <option value="">Tous les types</option>
          <option value="PDF">PDF</option>
          <option value="DOCX">DOCX</option>
          <option value="XLSX">XLSX</option>
          <option value="JPG">JPG</option>
          <option value="PNG">PNG</option>
        </Select>
      </Flex>

      {isLoading ? (
        <Flex justify="center" align="center" h="200px">
          <Text color="white">Chargement...</Text>
        </Flex>
      ) : filteredDocuments.length === 0 ? (
        <Box bg="#20243a" borderRadius="lg" p={6} textAlign="center">
          <Icon as={FiTrash2 as ElementType} boxSize={8} color="gray.400" mb={2} />
          <Text color="white">La corbeille est vide</Text>
        </Box>
      ) : (
        <Box overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">NOM</Th>
                <Th color="white">TYPE</Th>
                <Th color="white">DATE DE CRÉATION</Th>
                <Th color="white">DATE DE SUPPRESSION</Th>
                <Th color="white">TAILLE</Th>
                <Th color="white">ACTIONS</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredDocuments.map((doc) => (
                <Tr key={doc.id}>
                  <Td>
                    <Flex align="center">
                      <Icon as={FiFileText as ElementType} color="#3a8bfd" mr={2} />
                      <Text color="white">{doc.titre}</Text>
                    </Flex>
                  </Td>
                  <Td>
                    <Badge colorScheme="blue">{doc.type_document}</Badge>
                  </Td>
                  <Td color="white">{formatDate(doc.date_creation)}</Td>
                  <Td color="white">{formatDate(doc.date_suppression)}</Td>
                  <Td color="white">{doc.taille_formatee}</Td>
                  <Td>
                    <Menu>
                      <MenuButton
                        as={Button}
                        variant="ghost"
                        colorScheme="blue"
                        size="sm"
                      >
                        <Icon as={FiMoreVertical as ElementType} />
                      </MenuButton>
                      <MenuList bg="#232946">
                        <MenuItem
                          icon={<Icon as={FiRefreshCw as ElementType} />}
                          onClick={() => handleRestoreClick(doc.id)}
                          _hover={{ bg: "#2d3250" }}
                        >
                          Restaurer
                        </MenuItem>
                        <MenuItem
                          icon={<Icon as={FiTrash2 as ElementType} />}
                          onClick={() => handleDeleteClick(doc.id)}
                          color="red.400"
                          _hover={{ bg: "#2d3250" }}
                        >
                          Supprimer définitivement
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

      {/* Restore Confirmation Dialog */}
      <AlertDialog
        isOpen={isRestoreOpen}
        leastDestructiveRef={cancelRef}
        onClose={onRestoreClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent bg="#20243a" color="white">
            <AlertDialogHeader>Restaurer le document</AlertDialogHeader>
            <AlertDialogBody>
              Voulez-vous restaurer ce document ?
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onRestoreClose}>
                Annuler
              </Button>
              <Button colorScheme="blue" onClick={handleRestore} ml={3}>
                Restaurer
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>

      {/* Permanent Delete Confirmation Dialog */}
      <AlertDialog
        isOpen={isDeleteOpen}
        leastDestructiveRef={cancelRef}
        onClose={onDeleteClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent bg="#20243a" color="white">
            <AlertDialogHeader>Suppression définitive</AlertDialogHeader>
            <AlertDialogBody>
              Attention ! Cette action est irréversible. Voulez-vous vraiment supprimer définitivement ce document ?
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onDeleteClose}>
                Annuler
              </Button>
              <Button colorScheme="red" onClick={handlePermanentDelete} ml={3}>
                Supprimer définitivement
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Box>
  );
};

export default Corbeille;


