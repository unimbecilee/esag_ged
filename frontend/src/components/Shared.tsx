import React, { useEffect, useState } from "react";
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Button,
  useToast,
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  Icon,
  Select,
  Badge,
  Text,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
} from "@chakra-ui/react";
import { FiSearch, FiDownload, FiShare2, FiMoreVertical, FiEye, FiFileText, FiUser, FiTrash2, FiEdit2 } from "react-icons/fi";
import { ElementType } from "react";
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import { checkAuthToken } from '../utils/errorHandling';
import { API_URL } from '../config';
import { asElementType } from '../utils/iconUtils';
import { useLoading } from '../contexts/LoadingContext';

interface SharedDocument {
  id: number;
  document_id: number;
  document_titre: string;
  type_document: string;
  date_partage: string;
  partage_par: string;
  partage_avec: string;
  permissions: string[];
  statut: string;
}

const Shared: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const [sharedDocs, setSharedDocs] = useState<SharedDocument[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("");
  const { isLoading, showLoading, hideLoading } = useLoading();

  useEffect(() => {
    fetchSharedDocuments();
  }, []);

  const fetchSharedDocuments = async () => {
    try {
      showLoading("Chargement des documents partagés...");
      const token = checkAuthToken();
      const response = await fetch(`${API_URL}/api/documents/shared`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la récupération des documents partagés');
      }

      const data = await response.json();
      setSharedDocs(data);
    } catch (error) {
      console.error("Erreur:", error);
    } finally {
      hideLoading();
    }
  };

  const handleDownload = async (documentId: number) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/documents/${documentId}/download`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Erreur lors du téléchargement');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `document-${documentId}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      },
      {
        loadingMessage: "Téléchargement en cours...",
        successMessage: "Document téléchargé avec succès",
        errorMessage: "Impossible de télécharger le document"
      }
    );
  };

  const handleRemoveShare = async (shareId: number) => {
    await executeOperation(
      async () => {
        const token = checkAuthToken();
        const response = await fetch(`${API_URL}/api/documents/shared/${shareId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Erreur lors de la suppression du partage');
        }

        await fetchSharedDocuments();
      },
      {
        loadingMessage: "Suppression du partage...",
        successMessage: "Partage supprimé avec succès",
        errorMessage: "Impossible de supprimer le partage"
      }
    );
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const filteredDocuments = sharedDocs.filter((doc) => {
    const matchesSearch = doc.document_titre.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === "" || doc.type_document.toLowerCase() === filterType.toLowerCase();
    return matchesSearch && matchesType;
  });

  // Get unique document types for filter
  const documentTypes = Array.from(new Set(sharedDocs.map(doc => doc.type_document)));

  if (sharedDocs.length === 0) {
    return (
      <Box textAlign="center" color="white">
        <Text>Chargement...</Text>
      </Box>
    );
  }

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
          {documentTypes.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </Select>
      </Flex>

      <Box bg="#20243a" borderRadius="lg" p={6} overflowX="auto">
        {filteredDocuments.length === 0 ? (
          <Text color="white" textAlign="center">
            Aucun document partagé
          </Text>
        ) : (
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">Document</Th>
                <Th color="white">Type</Th>
                <Th color="white">Partagé par</Th>
                <Th color="white">Partagé avec</Th>
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
                      <Icon as={asElementType(FiFileText)} color="#3a8bfd" mr={2} />
                      <Text color="white">{doc.document_titre}</Text>
                    </Flex>
                  </Td>
                  <Td>
                    <Badge colorScheme="blue">{doc.type_document}</Badge>
                  </Td>
                  <Td>
                    <Flex align="center">
                      <Icon as={asElementType(FiUser)} mr={2} />
                      <Text color="white">{doc.partage_par}</Text>
                    </Flex>
                  </Td>
                  <Td>
                    <Flex align="center">
                      <Icon as={asElementType(FiUser)} mr={2} />
                      <Text color="white">{doc.partage_avec}</Text>
                    </Flex>
                  </Td>
                  <Td color="white">{formatDate(doc.date_partage)}</Td>
                  <Td>
                    <Flex gap={2}>
                      {doc.permissions.map((permission, index) => (
                        <Badge key={index} colorScheme="green">
                          {permission}
                        </Badge>
                      ))}
                    </Flex>
                  </Td>
                  <Td>
                    <Menu>
                      <MenuButton
                        as={Button}
                        size="sm"
                        variant="ghost"
                        colorScheme="blue"
                      >
                        <Icon as={asElementType(FiMoreVertical)} />
                      </MenuButton>
                      <MenuList bg="#232946">
                        <MenuItem
                          icon={<Icon as={asElementType(FiDownload)} />}
                          onClick={() => handleDownload(doc.document_id)}
                          _hover={{ bg: "#20243a" }}
                        >
                          Télécharger
                        </MenuItem>
                        {doc.permissions.includes("Édition") && (
                          <MenuItem
                            icon={<Icon as={asElementType(FiEdit2)} />}
                            onClick={() => {
                              // Handle edit
                            }}
                            _hover={{ bg: "#20243a" }}
                          >
                            Modifier
                          </MenuItem>
                        )}
                        <MenuItem
                          icon={<Icon as={asElementType(FiTrash2)} />}
                          onClick={() => handleRemoveShare(doc.id)}
                          _hover={{ bg: "#20243a" }}
                          color="red.400"
                        >
                          Supprimer le partage
                        </MenuItem>
                      </MenuList>
                    </Menu>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </Box>
    </Box>
  );
};

export default Shared; 


