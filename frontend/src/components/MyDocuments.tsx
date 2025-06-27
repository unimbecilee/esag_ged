import React, { useState, useEffect, useRef, ElementType } from "react";
import {
  Box,
  Flex,
  Heading,
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Text,
  SimpleGrid,
  Card,
  CardBody,
  Icon,
  VStack,
  HStack,
  Badge,
  Divider,
  useDisclosure,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  useToast,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Tooltip,
  Portal,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
  FormControl,
  FormLabel,
  Textarea
} from "@chakra-ui/react";
import {
  FiUpload,
  FiSearch,
  FiDownload,
  FiShare2,
  FiTrash2,
  FiEdit2,
  FiMoreVertical,
  FiFile,
  FiImage,
  FiFileText,
  FiFolder,
  FiHome,
  FiChevronRight,
  FiFolderPlus,
  FiArrowLeft,
  FiMove,
  FiClock,
  FiHeart,
  FiEdit,
  FiStar,
  FiCheckCircle,
  FiXCircle,
  FiEye,
  FiArchive
} from "react-icons/fi";
import { useAuthStatus } from "../hooks/useAuthStatus";
import { useAsyncOperation } from "../hooks/useAsyncOperation";
import FileUploadModal from "./FileUploadModal";
import ShareModal from "./ShareModal";
import DocumentPreview from "./DocumentPreview";
import DocumentOCR from "./DocumentOCR";
import CreateFolderModal from "./CreateFolderModal";
import DocumentMoveModal from "./DocumentMoveModal";
import DocumentVersions from "./DocumentVersions";
import config from "../config";
import StartWorkflowModal from './Document/StartWorkflowModal';
import ArchiveRequestModal from './Document/ArchiveRequestModal';
import ValidationWorkflowButton from './ValidationWorkflow/ValidationWorkflowButton';

interface Document {
  id: number;
  titre: string;
  type_document: string;
  date_creation: string | null;
  derniere_modification: string | null;
  taille: number;
  taille_formatee: string;
  statut: string;
  proprietaire_nom?: string;
  proprietaire_prenom?: string;
  proprietaire_id?: number;
  dossier_id?: number | null;
  est_archive?: boolean;
  workflow_statut?: string | null;
  workflow_nom?: string | null;
}

interface Folder {
  id: number;
  titre: string;
  date_creation: string;
  documents_count: number;
  sous_dossiers_count: number;
  parent_id?: number | null;
}

interface BreadcrumbItem {
  id: number | null;
  titre: string;
}

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return "Non défini";
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("fr-FR", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "Date invalide";
  }
};

const MyDocuments: React.FC = () => {
  const { user } = useAuthStatus();
  const { executeOperation } = useAsyncOperation();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [breadcrumb, setBreadcrumb] = useState<BreadcrumbItem[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("");
  const [selectedDocument, setSelectedDocument] = useState<number | null>(null);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<number[]>([]);
  const [selectedDocumentTitles, setSelectedDocumentTitles] = useState<string[]>([]);
  const [previewDocumentId, setPreviewDocumentId] = useState<number | null>(null);
  const [previewDocumentTitle, setPreviewDocumentTitle] = useState<string>("");
  const [ocrDocumentId, setOCRDocumentId] = useState<number | null>(null);
  const [ocrDocumentTitle, setOCRDocumentTitle] = useState<string>("");
  const [versionsDocumentId, setVersionsDocumentId] = useState<number | null>(null);
  const [versionsDocumentTitle, setVersionsDocumentTitle] = useState<string>("");
  
  // États pour les favoris
  const [favoriteStatuses, setFavoriteStatuses] = useState<Record<number, boolean>>({});

  // Détection automatique du statut admin
  const isAdmin = user?.role?.toLowerCase() === 'admin';
  
  // Mode admin automatique pour les admins uniquement
  const isAdminMode = isAdmin;

  // Modals
  const {
    isOpen: isUploadOpen,
    onOpen: onUploadOpen,
    onClose: onUploadClose,
  } = useDisclosure();
  const {
    isOpen: isShareOpen,
    onOpen: onShareOpen,
    onClose: onShareClose,
  } = useDisclosure();
  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  const {
    isOpen: isPreviewOpen,
    onOpen: onPreviewOpen,
    onClose: onPreviewClose,
  } = useDisclosure();
  const {
    isOpen: isOCROpen,
    onOpen: onOCROpen,
    onClose: onOCRClose,
  } = useDisclosure();
  const {
    isOpen: isCreateFolderOpen,
    onOpen: onCreateFolderOpen,
    onClose: onCreateFolderClose,
  } = useDisclosure();
  const {
    isOpen: isMoveOpen,
    onOpen: onMoveOpen,
    onClose: onMoveClose,
  } = useDisclosure();
  const {
    isOpen: isVersionsOpen,
    onOpen: onVersionsOpen,
    onClose: onVersionsClose,
  } = useDisclosure();

  const cancelRef = useRef<HTMLButtonElement>(null);
  const toast = useToast();

  // Modal pour soumettre un document pour validation
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<number | null>(null);
  const [availableWorkflows, setAvailableWorkflows] = useState<any[]>([]);
  const [documentToSubmit, setDocumentToSubmit] = useState<number | null>(null);
  const [submitComment, setSubmitComment] = useState('');

  // Workflow
  const [isWorkflowModalOpen, setIsWorkflowModalOpen] = useState(false);
  const [documentToWorkflow, setDocumentToWorkflow] = useState<{id: number, title: string} | null>(null);

  // Archive
  const [documentToArchive, setDocumentToArchive] = useState<{ id: number; title: string } | null>(null);
  const [isArchiveModalOpen, setIsArchiveModalOpen] = useState(false);

  useEffect(() => {
    // Ne charger que si l'utilisateur est connecté
    if (user) {
      console.log(`🔍 [DEBUG] Chargement initial des documents - Admin: ${isAdmin}, AdminMode: ${isAdminMode}`);
      loadCurrentView();
    }
  }, [currentFolderId, isAdminMode, user, isAdmin]);

  const loadCurrentView = async () => {
    setIsLoading(true);
    await Promise.all([
      fetchDocuments(),
      fetchFolders(),
      loadBreadcrumb()
    ]);
    setIsLoading(false);
  };

  const refreshDocuments = async () => {
    await loadCurrentView();
  };

  const fetchDocuments = async () => {
    try {
      const result = await executeOperation(
        async () => {
          const token = localStorage.getItem("token");
          if (!token) {
            throw new Error('Token non trouvé');
          }

          let url = `${config.API_URL}/api/documents/my`;
          const params = new URLSearchParams();
          
          if (currentFolderId !== null) {
            params.append('dossier_id', currentFolderId.toString());
          }
          
          if (isAdminMode && isAdmin) {
            params.append('admin_mode', 'true');
            console.log(`🔍 [DEBUG] Mode admin activé pour la requête`);
          } else {
            console.log(`🔍 [DEBUG] Mode normal pour la requête (isAdminMode: ${isAdminMode}, isAdmin: ${isAdmin})`);
          }
          
          if (params.toString()) {
            url += `?${params.toString()}`;
          }

          console.log(`🔍 [DEBUG] URL documents appelée: ${url}`);

          const response = await fetch(url, {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error(`Erreur ${response.status}: ${response.statusText}`);
          }

          const data = await response.json();
          console.log(`🔍 [DEBUG] ${data.length} documents reçus`);
          return data;
        },
        {
          loadingMessage: "Chargement des documents...",
          errorMessage: "Impossible de charger les documents",
          showLoading: false,
          showSuccess: false
        }
      );

      if (result) {
        setDocuments(result);
        // Charger les statuts favoris après avoir récupéré les documents
        loadFavoriteStatuses();
      }
    } catch (err) {
      toast({
        title: "Erreur",
        description: err instanceof Error ? err.message : "Erreur lors du chargement des documents",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const fetchFolders = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      let url = `${config.API_URL}/api/folders`;
      if (currentFolderId !== null) {
        url += `?parent_id=${currentFolderId}`;
      }

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setFolders(data);
        console.log(`🔍 [DEBUG] ${data.length} dossiers reçus`);
      }
    } catch (error) {
      console.error('Erreur chargement dossiers:', error);
    }
  };

  const loadBreadcrumb = async () => {
    if (!currentFolderId) {
      setBreadcrumb([]);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/api/folders/${currentFolderId}/breadcrumb`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setBreadcrumb(data || []);
      }
    } catch (error) {
      console.error('Erreur breadcrumb:', error);
    }
  };

  const navigateToFolder = (folderId: number | null) => {
    setCurrentFolderId(folderId);
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
            `${config.API_URL}/documents/${documentId}/download`,
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
      console.error("Erreur de téléchargement:", error);
    }
  };

  const handleDelete = async () => {
    if (!selectedDocument) return;
    
    try {
      const success = await executeOperation(
        async () => {
          const token = localStorage.getItem("token");
          if (!token) {
            throw new Error('Token non trouvé');
          }
          
          const response = await fetch(
            `${config.API_URL}/documents/${selectedDocument}`,
            {
              method: "DELETE",
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );

          if (!response.ok) {
            throw new Error("Erreur lors de la suppression");
          }
          
          return true;
        },
        {
          loadingMessage: "Suppression en cours...",
          successMessage: "Document supprimé avec succès",
          errorMessage: "Impossible de supprimer le document"
        }
      );
      
      if (success) {
        await fetchDocuments();
      }
    } catch (error) {
      console.error("Erreur de suppression:", error);
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
    const doc = documents.find(d => d.id === documentId);
    if (doc) {
      const newTitle = prompt('Nouveau titre du document:', doc.titre);
      if (newTitle && newTitle.trim() !== '' && newTitle.trim() !== doc.titre) {
        // Appel API pour renommer le document
        executeOperation(
          async () => {
            const token = localStorage.getItem("token");
            if (!token) {
              throw new Error('Token non trouvé');
            }

            const response = await fetch(`${config.API_URL}/documents/${documentId}`, {
              method: 'PUT',
              headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ titre: newTitle.trim() })
            });

            if (!response.ok) {
              throw new Error("Erreur lors de la modification du document");
            }
          },
          {
            loadingMessage: "Modification du document...",
            successMessage: "Document modifié avec succès",
            errorMessage: "Impossible de modifier le document"
          }
        ).then(() => {
          refreshDocuments();
        }).catch(error => {
          console.error("Erreur modification document:", error);
        });
      }
    } else {
      toast({
        title: "Modification",
        description: "Fonctionnalité de modification avancée en développement",
        status: "info",
        duration: 3000,
        isClosable: true,
      });
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

  const handleMoveDocuments = (documentIds: number[], documentTitles: string[]) => {
    setSelectedDocumentIds(documentIds);
    setSelectedDocumentTitles(documentTitles);
    onMoveOpen();
  };

  const handleMoveSuccess = () => {
    loadCurrentView();
    onMoveClose();
  };

  const handleShowVersions = (documentId: number) => {
    const doc = documents.find(d => d.id === documentId);
    setVersionsDocumentId(documentId);
    setVersionsDocumentTitle(doc?.titre || `Document ${documentId}`);
    onVersionsOpen();
  };

  const handleMoveDocument = (documentId: number, documentTitle: string) => {
    handleMoveDocuments([documentId], [documentTitle]);
  };

  const handleCreateFolderSuccess = () => {
    loadCurrentView();
    onCreateFolderClose();
  };

  // Nouvelles fonctions pour les actions sur les dossiers
  const handleDeleteFolder = async (folderId: number) => {
    try {
      await executeOperation(
        async () => {
          const token = localStorage.getItem("token");
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/folders/${folderId}`, {
            method: 'DELETE',
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error("Erreur lors de la suppression du dossier");
          }
        },
        {
          loadingMessage: "Suppression du dossier...",
          successMessage: "Dossier supprimé avec succès",
          errorMessage: "Impossible de supprimer le dossier"
        }
      );
      
      loadCurrentView();
    } catch (error) {
      console.error("Erreur suppression dossier:", error);
    }
  };

  const handleRenameFolder = async (folderId: number, newName: string) => {
    try {
      await executeOperation(
        async () => {
          const token = localStorage.getItem("token");
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/folders/${folderId}`, {
            method: 'PUT',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ titre: newName })
          });

          if (!response.ok) {
            throw new Error("Erreur lors du renommage du dossier");
          }
        },
        {
          loadingMessage: "Renommage du dossier...",
          successMessage: "Dossier renommé avec succès",
          errorMessage: "Impossible de renommer le dossier"
        }
      );
      
      loadCurrentView();
    } catch (error) {
      console.error("Erreur renommage dossier:", error);
    }
  };

  const handleFolderAction = (action: string, folderId: number, folderName?: string) => {
    switch (action) {
      case 'rename':
        const newName = prompt('Nouveau nom du dossier:', folderName);
        if (newName && newName.trim() !== '') {
          handleRenameFolder(folderId, newName.trim());
        }
        break;
      case 'delete':
        if (window.confirm('Êtes-vous sûr de vouloir supprimer ce dossier ?')) {
          handleDeleteFolder(folderId);
        }
        break;
      default:
        break;
    }
  };

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.titre.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType ? doc.type_document === filterType : true;
    return matchesSearch && matchesType;
  });

  const documentTypes = Array.from(new Set(documents.map((doc) => doc.type_document)));

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return FiFileText;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return FiImage;
      case 'doc':
      case 'docx':
        return FiFileText;
      default:
        return FiFile;
    }
  };

  const getDocumentOwnerDisplay = (doc: Document) => {
    if (!isAdminMode || !doc.proprietaire_nom) return null;
    return `${doc.proprietaire_nom} ${doc.proprietaire_prenom || ''}`.trim();
  };

  const getWorkflowStatusDisplay = (doc: Document) => {
    if (!doc.workflow_statut) {
      return null;
    }

    const statusConfig = {
      'EN_COURS': {
        label: 'En cours',
        color: 'orange',
        icon: FiClock
      },
      'TERMINE': {
        label: 'Approuvé',
        color: 'green',
        icon: FiCheckCircle
      },
      'REJETE': {
        label: 'Rejeté',
        color: 'red',
        icon: FiXCircle
      },
      'EN_ATTENTE': {
        label: 'En attente',
        color: 'yellow',
        icon: FiClock
      }
    };

    return statusConfig[doc.workflow_statut as keyof typeof statusConfig] || null;
  };

  const navigateBack = () => {
    if (breadcrumb.length > 0) {
      // Naviguer vers le dossier parent (avant-dernier élément du breadcrumb)
      const parentFolder = breadcrumb[breadcrumb.length - 2];
      navigateToFolder(parentFolder ? parentFolder.id : null);
    } else {
      // Si pas de breadcrumb, retourner à la racine
      navigateToFolder(null);
    }
  };

  // Fonction pour charger le statut des favoris
  const loadFavoriteStatuses = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const promises = documents.map(async (doc) => {
        try {
          const response = await fetch(`${config.API_URL}/documents/${doc.id}/favorite/status`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const data = await response.json();
            return { id: doc.id, isFavorite: data.is_favorite };
          }
        } catch (error) {
          console.error(`Erreur lors de la vérification du statut favori pour ${doc.id}:`, error);
        }
        return { id: doc.id, isFavorite: false };
      });

      const results = await Promise.all(promises);
      const statusMap: Record<number, boolean> = {};
      results.forEach(result => {
        statusMap[result.id] = result.isFavorite;
      });
      setFavoriteStatuses(statusMap);
    } catch (error) {
      console.error('Erreur lors du chargement des statuts favoris:', error);
    }
  };

  // Fonction pour basculer le statut favori
  const handleToggleFavorite = async (documentId: number) => {
    try {
      const isFavorite = favoriteStatuses[documentId] || false;
      const method = isFavorite ? 'DELETE' : 'POST';
      
      await executeOperation(
        async () => {
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('Token non trouvé');
          }

          const response = await fetch(`${config.API_URL}/documents/${documentId}/favorite`, {
            method,
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (!response.ok) {
            throw new Error(`Erreur lors de la ${isFavorite ? 'suppression du' : 'ajout au'} favori`);
          }

          return !isFavorite;
        },
        {
          loadingMessage: isFavorite ? "Suppression du favori..." : "Ajout aux favoris...",
          successMessage: isFavorite ? "Document retiré des favoris" : "Document ajouté aux favoris",
          errorMessage: `Impossible de ${isFavorite ? 'retirer le document des' : 'ajouter le document aux'} favoris`
        }
      );

      // Mettre à jour l'état local
      setFavoriteStatuses(prev => ({
        ...prev,
        [documentId]: !isFavorite
      }));
    } catch (error) {
      console.error('Erreur lors de la modification des favoris:', error);
    }
  };

  // Fonction pour ouvrir le modal de soumission pour validation
  const handleSubmitForValidation = (documentId: number) => {
    const document = documents.find(d => d.id === documentId);
    if (document) {
      setDocumentToWorkflow({
        id: documentId,
        title: document.titre
      });
      setIsWorkflowModalOpen(true);
    }
  };
  
  // Fonction appelée après le démarrage d'un workflow
  const handleWorkflowStarted = () => {
    // Recharger les documents pour mettre à jour leur statut
    loadCurrentView();
  };

  // Fonction pour ouvrir le modal de demande d'archive
  const handleRequestArchive = (documentId: number) => {
    const document = documents.find(d => d.id === documentId);
    if (document) {
      setDocumentToArchive({
        id: documentId,
        title: document.titre
      });
      setIsArchiveModalOpen(true);
    }
  };
  
  // Fonction appelée après la soumission d'une demande d'archive
  const handleArchiveRequested = () => {
    // Recharger les documents pour mettre à jour leur statut
    loadCurrentView();
  };

  return (
    <Box p={5}>
      {/* Header */}
      <Flex justify="space-between" align="center" mb={6}>
        <HStack spacing={4} align="center">
          {currentFolderId !== null && (
            <Button
              leftIcon={<Icon as={FiArrowLeft as ElementType} />}
              variant="ghost"
              colorScheme="blue"
              onClick={navigateBack}
              size="sm"
            >
              Retour
            </Button>
          )}
          <Heading size="lg" color="white">
            {isAdminMode ? "Tous les Documents" : "Mes Documents"}
          </Heading>
        </HStack>
        <Flex gap={3}>
          <Button
            leftIcon={<Icon as={FiUpload as ElementType} />}
            colorScheme="blue"
            onClick={onUploadOpen}
          >
            Uploader un document
          </Button>
          <Button
            leftIcon={<Icon as={FiFolderPlus as ElementType} />}
            colorScheme="green"
            variant="outline"
            onClick={onCreateFolderOpen}
          >
            Créer un dossier
          </Button>
        </Flex>
      </Flex>

      {/* Breadcrumb */}
      {breadcrumb.length > 0 && (
        <Breadcrumb spacing={2} separator={<Icon as={FiChevronRight as ElementType} color="gray.400" />} mb={4}>
          <BreadcrumbItem>
            <BreadcrumbLink 
              onClick={() => navigateToFolder(null)}
              color="blue.300"
              _hover={{ color: "blue.200" }}
            >
              <Icon as={FiHome as ElementType} mr={1} />
              Racine
            </BreadcrumbLink>
          </BreadcrumbItem>
          {breadcrumb.map((item, index) => (
            <BreadcrumbItem key={item.id || 0} isCurrentPage={index === breadcrumb.length - 1}>
              <BreadcrumbLink
                onClick={() => index < breadcrumb.length - 1 ? navigateToFolder(item.id) : undefined}
                color={index === breadcrumb.length - 1 ? "white" : "blue.300"}
                _hover={index < breadcrumb.length - 1 ? { color: "blue.200" } : {}}
                cursor={index < breadcrumb.length - 1 ? "pointer" : "default"}
              >
                {item.titre}
              </BreadcrumbLink>
            </BreadcrumbItem>
          ))}
        </Breadcrumb>
      )}

      {/* Search and Filter */}
      <Flex mb={5} gap={4}>
        <InputGroup maxW="500px">
          <InputLeftElement pointerEvents="none">
            <Icon as={FiSearch as ElementType} color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Rechercher un document..."
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
          zIndex={100}
          position="relative"
        >
          {documentTypes.map((type) => (
            <option key={type} value={type}>
              {type || "Non défini"}
            </option>
          ))}
        </Select>
      </Flex>

      {/* Content */}
      {isLoading ? (
        <Text color="white">Chargement...</Text>
      ) : (
        <Box>
          {/* Dossiers */}
          {folders.length > 0 && (
            <Box mb={6}>
              <Text fontWeight="bold" mb={3} color="white" fontSize="lg">
                Dossiers ({folders.length})
              </Text>
              <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={4}>
                {folders.map((folder) => (
                  <Card
                    key={folder.id}
                    bg="#2a3657"
                    borderColor="#3a445e"
                    transition="all 0.2s"
                    position="relative"
                  >
                    <CardBody 
                      textAlign="center" 
                      py={4}
                      cursor="pointer"
                      onClick={() => navigateToFolder(folder.id)}
                    >
                      <VStack spacing={2}>
                        <Flex justify="space-between" align="flex-start" width="100%" mb={2}>
                          <Box flex={1} />
                          <Menu>
                            <MenuButton
                              as={IconButton}
                              icon={<Icon as={FiMoreVertical as ElementType} />}
                              variant="ghost"
                              size="xs"
                              aria-label="Options du dossier"
                              color="gray.400"
                              _hover={{ color: "white", bg: "rgba(58, 139, 253, 0.1)" }}
                              onClick={(e) => e.stopPropagation()}
                            />
                            <MenuList 
                              bg="#1c2338" 
                              borderColor="#3a445e" 
                              zIndex={1500}
                              boxShadow="0 8px 16px rgba(0, 0, 0, 0.4)"
                              minW="150px"
                            >
                              <MenuItem
                                icon={<Icon as={FiEdit2 as ElementType} />}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleFolderAction('rename', folder.id, folder.titre);
                                }}
                                _hover={{ bg: "#2d3250" }}
                                color="white"
                              >
                                Renommer
                              </MenuItem>
                              <MenuItem
                                icon={<Icon as={FiTrash2 as ElementType} />}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleFolderAction('delete', folder.id);
                                }}
                                _hover={{ bg: "#2d3250" }}
                                color="red.300"
                              >
                                Supprimer
                              </MenuItem>
                            </MenuList>
                          </Menu>
                        </Flex>
                        <Icon as={FiFolder as ElementType} boxSize={8} color="#3a8bfd" />
                        <Text 
                          fontWeight="medium" 
                          noOfLines={1} 
                          color="white"
                          fontSize="sm"
                        >
                          {folder.titre}
                        </Text>
                        <HStack spacing={1}>
                          <Badge size="xs" colorScheme="blue">
                            {folder.documents_count || 0} doc(s)
                          </Badge>
                          <Badge size="xs" colorScheme="gray">
                            {folder.sous_dossiers_count || 0} dossier(s)
                          </Badge>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            </Box>
          )}

          {/* Divider */}
          {folders.length > 0 && filteredDocuments.length > 0 && (
            <Divider borderColor="#3a445e" mb={6} />
          )}

          {/* Documents */}
          {filteredDocuments.length > 0 ? (
            <Box>
              <Text fontWeight="bold" mb={3} color="white" fontSize="lg">
                Documents ({filteredDocuments.length})
              </Text>
              <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={4}>
                {filteredDocuments.map((doc) => {
                  const ownerDisplay = getDocumentOwnerDisplay(doc);
                  return (
                    <Card
                      key={doc.id}
                      bg="#2a3657"
                      borderColor={(() => {
                        const workflowStatus = getWorkflowStatusDisplay(doc);
                        if (workflowStatus) {
                          return workflowStatus.color === 'green' ? '#48BB78' : 
                                 workflowStatus.color === 'red' ? '#F56565' :
                                 workflowStatus.color === 'orange' ? '#ED8936' :
                                 workflowStatus.color === 'yellow' ? '#ECC94B' : '#3a445e';
                        }
                        return '#3a445e';
                      })()}
                      borderWidth={(() => {
                        const workflowStatus = getWorkflowStatusDisplay(doc);
                        return workflowStatus ? '2px' : '1px';
                      })()}
                      transition="all 0.2s"
                      position="relative"
                    >
                      <CardBody p={4}>
                        <VStack spacing={3} align="stretch">
                          {/* Indicateur de statut workflow en haut à gauche */}
                          {(() => {
                            const workflowStatus = getWorkflowStatusDisplay(doc);
                            if (workflowStatus) {
                              return (
                                <Box 
                                  position="absolute" 
                                  top={2} 
                                  left={2} 
                                  zIndex={50}
                                  bg={workflowStatus.color === 'green' ? 'green.500' : 
                                      workflowStatus.color === 'red' ? 'red.500' :
                                      workflowStatus.color === 'orange' ? 'orange.500' :
                                      workflowStatus.color === 'yellow' ? 'yellow.500' : 'gray.500'}
                                  borderRadius="full"
                                  p={1}
                                  boxShadow="md"
                                >
                                  <Icon 
                                    as={workflowStatus.icon as ElementType} 
                                    boxSize={3} 
                                    color="white" 
                                  />
                                </Box>
                              );
                            }
                            return null;
                          })()}
                          
                          <Box position="absolute" top={2} right={2} zIndex={100}>
                            <Menu>
                              <MenuButton
                                as={IconButton}
                                icon={<Icon as={FiMoreVertical as ElementType} />}
                                variant="ghost"
                                size="xs"
                                aria-label="Options du document"
                                color="gray.400"
                                _hover={{ color: "white", bg: "rgba(58, 139, 253, 0.1)" }}
                              />
                              <MenuList 
                                bg="#1c2338" 
                                borderColor="#3a445e" 
                                zIndex={2000}
                                boxShadow="0 8px 16px rgba(0, 0, 0, 0.4)"
                                minW="150px"
                              >
                                {/* Actions de consultation */}
                                <MenuItem
                                  icon={<Icon as={FiEye as ElementType} />}
                                  onClick={() => handleShowPreview(doc.id, doc.titre)}
                                  _hover={{ bg: "#2d3250" }}
                                  color="white"
                                >
                                  Aperçu
                                </MenuItem>
                                
                                {/* Séparateur */}
                                <Divider borderColor="#3a445e" />
                                
                                {/* Actions sur le fichier */}
                                <MenuItem
                                  icon={<Icon as={FiDownload as ElementType} />}
                                  onClick={() => handleDownload(doc.id)}
                                  _hover={{ bg: "#2d3250" }}
                                  color="white"
                                >
                                  Télécharger
                                </MenuItem>
                                <MenuItem
                                  icon={<Icon as={FiShare2 as ElementType} />}
                                  onClick={() => handleShareClick(doc.id)}
                                  _hover={{ bg: "#2d3250" }}
                                  color="white"
                                >
                                  Partager
                                </MenuItem>
                                
                                {/* Action de validation */}
                                <MenuItem
                                  icon={<Icon as={FiCheckCircle as ElementType} />}
                                  onClick={() => handleSubmitForValidation(doc.id)}
                                  _hover={{ bg: "#2d3250" }}
                                  color="green.300"
                                >
                                  Demander validation
                                </MenuItem>
                                
                                <MenuItem
                                  icon={<Icon as={FiHeart as ElementType} color={favoriteStatuses[doc.id] ? "#ff6b6b" : "#3a8bfd"} />}
                                  onClick={() => handleToggleFavorite(doc.id)}
                                  _hover={{ bg: "#2d3250" }}
                                  color="white"
                                >
                                  {favoriteStatuses[doc.id] ? "Retirer des favoris" : "Ajouter aux favoris"}
                                </MenuItem>
                                
                                {/* Séparateur */}
                                <Divider borderColor="#3a445e" />
                                
                                {/* Action d'archivage */}
                                {!doc.est_archive && (
                                  <MenuItem
                                    icon={<Icon as={FiArchive as ElementType} />}
                                    onClick={() => handleRequestArchive(doc.id)}
                                    _hover={{ bg: "#2d3250" }}
                                    color="orange.300"
                                  >
                                    Demander l'archivage
                                  </MenuItem>
                                )}
                                
                                {/* Action de suppression */}
                                <MenuItem
                                  icon={<Icon as={FiTrash2 as ElementType} />}
                                  onClick={() => handleDeleteClick(doc.id)}
                                  _hover={{ bg: "#2d3250" }}
                                  color="red.300"
                                >
                                  Supprimer
                                </MenuItem>
                              </MenuList>
                            </Menu>
                          </Box>
                          
                          <Flex justify="center" mt={4}>
                            <Icon 
                              as={getFileIcon(doc.titre) as ElementType} 
                              boxSize={8} 
                              color="#3a8bfd" 
                              zIndex={1}
                            />
                          </Flex>
                          
                          <VStack spacing={1} align="stretch">
                            <Tooltip label={doc.titre} placement="top">
                              <Text 
                                fontWeight="medium" 
                                noOfLines={2} 
                                color="white"
                                fontSize="sm"
                                textAlign="center"
                                minH="2.5em"
                              >
                                {doc.titre}
                              </Text>
                            </Tooltip>
                            
                            <HStack spacing={1} justify="center" wrap="wrap">
                              <Badge size="xs" colorScheme="blue">
                                {doc.type_document || 'Unknown'}
                              </Badge>
                              {(() => {
                                const workflowStatus = getWorkflowStatusDisplay(doc);
                                if (workflowStatus) {
                                  return (
                                    <Badge 
                                      size="xs" 
                                      colorScheme={workflowStatus.color}
                                      display="flex"
                                      alignItems="center"
                                      gap={1}
                                    >
                                      <Icon as={workflowStatus.icon as ElementType} boxSize={2} />
                                      {workflowStatus.label}
                                    </Badge>
                                  );
                                }
                                return null;
                              })()}
                            </HStack>
                            
                            <Text fontSize="xs" color="gray.400" textAlign="center">
                              {doc.taille_formatee}
                            </Text>
                            
                            {ownerDisplay && (
                              <Text fontSize="xs" color="yellow.300" textAlign="center">
                                📁 {ownerDisplay}
                              </Text>
                            )}
                          </VStack>
                        </VStack>
                      </CardBody>
                    </Card>
                  );
                })}
              </SimpleGrid>
            </Box>
          ) : (
            <Box textAlign="center" py={20}>
              <VStack spacing={3}>
                <Icon as={FiFolder as ElementType} boxSize={16} color="gray.400" />
                <Text color="gray.400" fontSize="lg">
                  {searchTerm || filterType ? "Aucun document ne correspond à vos critères" : "Aucun document dans ce dossier"}
                </Text>
              </VStack>
            </Box>
          )}
        </Box>
      )}

      {/* Modals */}
      <ShareModal
        open={isShareOpen}
        onClose={onShareClose}
        documentId={selectedDocument || 0}
        documentTitle={documents.find(d => d.id === selectedDocument)?.titre || "Document"}
        onShareSuccess={refreshDocuments}
      />

      <AlertDialog
        isOpen={isDeleteOpen}
        leastDestructiveRef={cancelRef}
        onClose={onDeleteClose}
      >
        <AlertDialogOverlay>
          <AlertDialogContent bg="#2a3657" color="white">
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Supprimer le document
            </AlertDialogHeader>
            <AlertDialogBody>
              Êtes-vous sûr de vouloir supprimer ce document ? Cette action ne peut pas être annulée.
            </AlertDialogBody>
            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onDeleteClose}>
                Annuler
              </Button>
              <Button colorScheme="red" onClick={handleDelete} ml={3}>
                Supprimer
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>

      <FileUploadModal
        isOpen={isUploadOpen}
        onClose={onUploadClose}
        onUploadSuccess={fetchDocuments}
        currentFolderId={currentFolderId}
      />

      {previewDocumentId && (
        <DocumentPreview
          isOpen={isPreviewOpen}
          onClose={onPreviewClose}
          documentId={previewDocumentId}
          documentTitle={previewDocumentTitle}
        />
      )}

      {ocrDocumentId && (
        <DocumentOCR
          isOpen={isOCROpen}
          onClose={onOCRClose}
          documentId={ocrDocumentId}
          documentTitle={ocrDocumentTitle}
        />
      )}

      <CreateFolderModal
        isOpen={isCreateFolderOpen}
        onClose={onCreateFolderClose}
        onSuccess={handleCreateFolderSuccess}
        parentFolderId={currentFolderId}
      />

      <DocumentMoveModal
        isOpen={isMoveOpen}
        onClose={onMoveClose}
        onSuccess={handleMoveSuccess}
        documentIds={selectedDocumentIds}
        documentTitles={selectedDocumentTitles}
      />

      {versionsDocumentId && (
        <DocumentVersions
          isOpen={isVersionsOpen}
          onClose={onVersionsClose}
          documentId={versionsDocumentId}
          documentTitle={versionsDocumentTitle}
        />
      )}

      {/* Modal pour soumettre un document pour validation */}
      {documentToWorkflow && (
        <Modal isOpen={isWorkflowModalOpen} onClose={() => setIsWorkflowModalOpen(false)} size="lg">
          <ModalOverlay />
          <ModalContent bg="#232946" color="white">
            <ModalHeader>Demander validation du document</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4} align="stretch">
                <ValidationWorkflowButton
                  documentId={documentToWorkflow.id}
                  documentTitle={documentToWorkflow.title}
                  onWorkflowStarted={() => {
                    handleWorkflowStarted();
                    setIsWorkflowModalOpen(false);
                  }}
                />
              </VStack>
            </ModalBody>
          </ModalContent>
        </Modal>
      )}

      {/* Modal de demande d'archive */}
      {documentToArchive && (
        <ArchiveRequestModal
          isOpen={isArchiveModalOpen}
          onClose={() => setIsArchiveModalOpen(false)}
          documentId={documentToArchive.id}
          documentTitle={documentToArchive.title}
          onArchiveRequested={handleArchiveRequested}
        />
      )}
    </Box>
  );
};

export default MyDocuments; 

