import React, { useEffect, useState } from "react";
import {
  Box,
  Heading,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  useToast,
  Flex,
  Icon,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Spinner,
  HStack,
  Button,
  useDisclosure,
} from "@chakra-ui/react";
import { FiFileText, FiSearch, FiHeart, FiRefreshCw } from "react-icons/fi";
import { ElementType } from "react";
import ActionMenu from "./ActionMenu";
import DocumentPreview from "./Document/DocumentPreview";
import DocumentOCR from "./Document/DocumentOCR";
import { useAsyncOperation } from '../hooks/useAsyncOperation';
import config from '../config';

interface FavoriteDocument {
  id: number;
  titre: string;
  type_document: string;
  date_creation: string | null;
  derniere_modification: string | null;
  taille: number;
  taille_formatee: string;
  statut: string;
  date_favori: string;
  proprietaire_nom: string;
  proprietaire_prenom: string;
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

const FavoriteDocuments: React.FC = () => {
  const { executeOperation } = useAsyncOperation();
  const [documents, setDocuments] = useState<FavoriteDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("");
  const toast = useToast();
  
  // Modales pour les nouvelles fonctionnalités
  const { isOpen: isPreviewOpen, onOpen: onPreviewOpen, onClose: onPreviewClose } = useDisclosure();
  const { isOpen: isOCROpen, onOpen: onOCROpen, onClose: onOCRClose } = useDisclosure();
  const [previewDocumentId, setPreviewDocumentId] = useState<number | null>(null);
  const [previewDocumentTitle, setPreviewDocumentTitle] = useState<string>("");
  const [ocrDocumentId, setOCRDocumentId] = useState<number | null>(null);
  const [ocrDocumentTitle, setOCRDocumentTitle] = useState<string>("");

  useEffect(() => {
    fetchFavoriteDocuments();
  }, []);

  const fetchFavoriteDocuments = async () => {
    setIsLoading(true);
    try {
      const result = await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/api/documents/favorites`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            credentials: 'include'
          });

          if (!response.ok) {
            throw new Error('Erreur lors de la récupération des documents favoris');
          }

          const data = await response.json();
          return data;
        },
        {
          loadingMessage: "Chargement des documents favoris...",
          errorMessage: "Impossible de charger les documents favoris"
        }
      );

      if (result) {
        setDocuments(result);
      }
    } catch (err) {
      // Pour le moment, utilisons des données de test
      setDocuments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async (documentId: number) => {
    try {
      await executeOperation(
        async () => {
          const token = localStorage.getItem("token");
          if (!token) {
            throw new Error('Token non trouvé');
          }
          
          const response = await fetch(
            `${config.API_URL}/api/documents/${documentId}/download`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );

          if (!response.ok) {
            throw new Error("Erreur lors du téléchargement");
          }

          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          
          const doc = documents.find(d => d.id === documentId);
          a.download = doc ? doc.titre : `document-${documentId}`;
          
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          
          return true;
        },
        {
          loadingMessage: "Téléchargement en cours...",
          successMessage: "Document téléchargé avec succès",
          errorMessage: "Impossible de télécharger le document"
        }
      );
    } catch (error) {
      // L'erreur est déjà gérée par executeOperation
    }
  };

  const removeFavorite = async (documentId: number) => {
    try {
      await executeOperation(
        async () => {
          const token = localStorage.getItem("token");
          if (!token) {
            throw new Error('Token non trouvé');
          }
          
          const response = await fetch(
            `${config.API_URL}/api/documents/${documentId}/favorite`,
            {
              method: 'DELETE',
              headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
            }
          );

          if (!response.ok) {
            throw new Error("Erreur lors de la suppression du favori");
          }
          
          return true;
        },
        {
          loadingMessage: "Suppression du favori...",
          successMessage: "Document retiré des favoris",
          errorMessage: "Impossible de retirer le document des favoris"
        }
      );
      
      // Rafraîchir la liste
      fetchFavoriteDocuments();
    } catch (error) {
      // L'erreur est déjà gérée par executeOperation
    }
  };

  const handleShowPreview = (documentId: number, title?: string) => {
    const doc = documents.find(d => d.id === documentId);
    setPreviewDocumentId(documentId);
    setPreviewDocumentTitle(title || doc?.titre || `Document ${documentId}`);
    onPreviewOpen();
  };

  const handleShowOCR = (documentId: number, title?: string) => {
    const doc = documents.find(d => d.id === documentId);
    setOCRDocumentId(documentId);
    setOCRDocumentTitle(title || doc?.titre || `Document ${documentId}`);
    onOCROpen();
  };

  const handleEdit = (documentId: number) => {
    toast({
      title: "Modification",
      description: "La modification sera disponible prochainement",
      status: "info",
      duration: 3000,
      isClosable: true,
    });
  };

  const handleShare = (documentId: number) => {
    toast({
      title: "Partage",
      description: "Le partage sera disponible prochainement",
      status: "info",
      duration: 3000,
      isClosable: true,
    });
  };

  const handleDelete = (documentId: number) => {
    toast({
      title: "Suppression",
      description: "La suppression sera disponible prochainement",
      status: "info",
      duration: 3000,
      isClosable: true,
    });
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.titre.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType ? doc.type_document === filterType : true;
    return matchesSearch && matchesType;
  });

  const documentTypes = Array.from(new Set(documents.map((doc) => doc.type_document)));

  return (
    <Box p={5}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg" color="white">
          <Icon as={FiHeart as ElementType} mr={3} color="#ff6b6b" />
          Documents Favoris
        </Heading>
        <Button
          leftIcon={<Icon as={FiRefreshCw as ElementType} />}
          colorScheme="blue"
          onClick={fetchFavoriteDocuments}
          isLoading={isLoading}
        >
          Actualiser
        </Button>
      </Flex>

      {/* Search and Filter */}
      <Flex mb={5} gap={4}>
        <InputGroup maxW="500px">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiSearch as ElementType} color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Rechercher dans les favoris..."
            bg="#2a3657"
            color="white"
            borderColor="#3a445e"
            _hover={{ borderColor: "#0066ff" }}
            _focus={{ borderColor: "#0066ff", boxShadow: "0 0 0 1px #0066ff" }}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </InputGroup>
        <Select
          placeholder="Tous les types"
          bg="#2a3657"
          color="white"
          borderColor="#3a445e"
          _hover={{ borderColor: "#0066ff" }}
          _focus={{ borderColor: "#0066ff", boxShadow: "0 0 0 1px #0066ff" }}
          maxW="200px"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          {documentTypes.map((type) => (
            <option key={type} value={type}>
              {type || "Non défini"}
            </option>
          ))}
        </Select>
      </Flex>

      {/* Documents Table */}
      {isLoading ? (
        <Flex justify="center" py={8}>
          <Spinner color="#3a8bfd" size="xl" />
        </Flex>
      ) : filteredDocuments.length > 0 ? (
        <Box bg="#2a3657" borderRadius="lg" overflow="hidden" shadow="md">
          <Table variant="simple">
            <Thead bg="#1c2338">
              <Tr>
                <Th color="white" borderColor="#3a445e">Nom</Th>
                <Th color="white" borderColor="#3a445e">Type</Th>
                <Th color="white" borderColor="#3a445e">Propriétaire</Th>
                <Th color="white" borderColor="#3a445e">Ajouté aux favoris</Th>
                <Th color="white" borderColor="#3a445e">Taille</Th>
                <Th color="white" borderColor="#3a445e">Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredDocuments.map((doc) => (
                <Tr key={`fav-doc-${doc.id}`} _hover={{ bg: "#374269" }}>
                  <Td color="white" borderColor="#3a445e">
                    <Flex align="center">
                      <Icon as={FiFileText as ElementType} mr={2} color="#3a8bfd" />
                      {doc.titre}
                    </Flex>
                  </Td>
                  <Td color="white" borderColor="#3a445e">
                    <Badge colorScheme="blue">{doc.type_document || "Non défini"}</Badge>
                  </Td>
                  <Td color="white" borderColor="#3a445e">
                    {doc.proprietaire_prenom} {doc.proprietaire_nom}
                  </Td>
                  <Td color="white" borderColor="#3a445e">{formatDate(doc.date_favori)}</Td>
                  <Td color="white" borderColor="#3a445e">{doc.taille_formatee || "N/A"}</Td>
                  <Td color="white" borderColor="#3a445e">
                    <HStack spacing={2}>
                      <Button
                        size="sm"
                        variant="ghost"
                        colorScheme="red"
                        leftIcon={<Icon as={FiHeart as ElementType} />}
                        onClick={() => removeFavorite(doc.id)}
                      >
                        Retirer
                      </Button>
                      <ActionMenu
                        documentId={doc.id}
                        documentTitle={doc.titre}
                        onDownload={handleDownload}
                        onShare={handleShare}
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                        onShowPreview={handleShowPreview}
                        onShowOCR={handleShowOCR}
                      />
                    </HStack>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      ) : (
        <Box
          p={10}
          textAlign="center"
          bg="#2a3657"
          color="white"
          borderRadius="lg"
          shadow="md"
        >
          <Icon as={FiHeart as ElementType} boxSize={12} color="gray.400" mb={4} />
          <Text fontSize="lg" color="white" mb={2}>
            Aucun document favori
          </Text>
          <Text color="gray.400">
            Ajoutez des documents à vos favoris pour les retrouver rapidement ici.
          </Text>
        </Box>
      )}

      {/* Document Preview Modal */}
      {previewDocumentId && (
        <DocumentPreview
          isOpen={isPreviewOpen}
          onClose={onPreviewClose}
          documentId={previewDocumentId}
          documentTitle={previewDocumentTitle}
        />
      )}

      {/* Document OCR Modal */}
      {ocrDocumentId && (
        <DocumentOCR
          isOpen={isOCROpen}
          onClose={onOCRClose}
          documentId={ocrDocumentId}
          documentTitle={ocrDocumentTitle}
        />
      )}
    </Box>
  );
};

export default FavoriteDocuments; 


