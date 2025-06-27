import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Flex,
  Text,
  Icon,
  Button,
  Input,
  HStack,
  VStack,
  Heading,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
} from "@chakra-ui/react";
import {
  FiFolder,
  FiChevronRight,
  FiFolderPlus,
  FiPlus,
  FiHome,
  FiCornerUpLeft,
} from "react-icons/fi";
import { ElementType } from "react";
import config from "../config";

const API_URL = config.API_URL;

interface Folder {
  id: number;
  titre: string;
  description?: string;
  parent_id: number | null;
  date_creation: string;
  derniere_modification: string;
  proprietaire_id: number;
  proprietaire_nom?: string;
  proprietaire_prenom?: string;
}

interface BreadcrumbItem {
  id: number;
  titre: string;
}

interface FolderBrowserProps {
  onFolderSelect?: (folderId: number | null) => void;
  selectedFolderId?: number | null;
  currentFolderId?: number | null;
  onFolderChange?: (folderId: number | null) => void;
  onRefresh?: () => Promise<void>;
}

const FolderBrowser: React.FC<FolderBrowserProps> = ({ 
  onFolderSelect, 
  selectedFolderId,
  currentFolderId: externalCurrentFolderId,
  onFolderChange,
  onRefresh
}) => {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentFolderId, setCurrentFolderId] = useState<number | null>(externalCurrentFolderId || null);
  const [breadcrumb, setBreadcrumb] = useState<BreadcrumbItem[]>([]);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [newFolderName, setNewFolderName] = useState("");
  const toast = useToast();
  const newFolderInputRef = useRef<HTMLInputElement>(null);

  // Charger les dossiers initiaux au montage du composant
  useEffect(() => {
    fetchFolders();
  }, [currentFolderId]);

  // Mettre à jour le breadcrumb si on change de dossier
  useEffect(() => {
    if (currentFolderId !== null) {
      fetchBreadcrumb();
    } else {
      setBreadcrumb([]);
    }
  }, [currentFolderId]);
  
  // Synchroniser le currentFolderId externe s'il change
  useEffect(() => {
    if (externalCurrentFolderId !== undefined && externalCurrentFolderId !== currentFolderId) {
      setCurrentFolderId(externalCurrentFolderId);
    }
  }, [externalCurrentFolderId]);

  const fetchFolders = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("Token non trouvé");
      }

      console.log(`Récupération des dossiers: parent_id=${currentFolderId || ''}`);

      const response = await fetch(`${API_URL}/api/folders/?parent_id=${currentFolderId || ''}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        mode: 'cors'
      });

      console.log("Réponse reçue:", response.status, response.statusText);

      if (!response.ok) {
        throw new Error("Erreur lors du chargement des dossiers");
      }

      const data = await response.json();
      console.log("Données reçues:", data);
      
      if (Array.isArray(data)) {
        setFolders(data);
      } else if (data.data && Array.isArray(data.data)) {
        setFolders(data.data);
      } else {
        console.error("Format de données inattendu:", data);
        setFolders([]);
      }
    } catch (error) {
      console.error("Erreur:", error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les dossiers.",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchBreadcrumb = async () => {
    if (currentFolderId === null) return;

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("Token non trouvé");
      }

      console.log(`Récupération du breadcrumb pour le dossier: ${currentFolderId}`);

      const response = await fetch(`${API_URL}/api/folders/${currentFolderId}/breadcrumb`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        mode: 'cors'
      });

      console.log("Réponse breadcrumb:", response.status, response.statusText);

      if (!response.ok) {
        throw new Error("Erreur lors du chargement du breadcrumb");
      }

      const data = await response.json();
      console.log("Données breadcrumb reçues:", data);
      
      if (Array.isArray(data)) {
        setBreadcrumb(data);
      } else if (data.data && Array.isArray(data.data)) {
        setBreadcrumb(data.data);
      } else {
        console.error("Format de données inattendu:", data);
        setBreadcrumb([]);
      }
    } catch (error) {
      console.error("Erreur:", error);
    }
  };

  const handleFolderClick = (folder: Folder) => {
    setCurrentFolderId(folder.id);
    onFolderSelect?.(folder.id);
    onFolderChange?.(folder.id);
  };

  const handleBackClick = async () => {
    if (breadcrumb.length > 1) {
      // Aller au dossier parent
      const parentFolder = breadcrumb[breadcrumb.length - 2];
      setCurrentFolderId(parentFolder.id);
      onFolderSelect?.(parentFolder.id);
      onFolderChange?.(parentFolder.id);
    } else {
      // Retourner à la racine
      setCurrentFolderId(null);
      onFolderSelect?.(null);
      onFolderChange?.(null);
    }
  };

  const handleHomeClick = () => {
    setCurrentFolderId(null);
    onFolderSelect?.(null);
    onFolderChange?.(null);
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      toast({
        title: "Erreur",
        description: "Le nom du dossier ne peut pas être vide.",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("Token non trouvé");
      }

      const folderData = {
        titre: newFolderName,
        description: "",
        parent_id: currentFolderId,
      };
      
      console.log("Création du dossier avec les données:", folderData);
      console.log("URL de l'API:", `${API_URL}/folders`);
      console.log("Token présent:", !!token);

      const response = await fetch(`${API_URL}/api/folders/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        mode: 'cors',
        body: JSON.stringify(folderData),
      });

      console.log("Réponse création dossier:", response.status, response.statusText);
      const responseHeaders: Record<string, string> = {};
      response.headers.forEach((value, key) => {
        responseHeaders[key] = value;
      });
      console.log("En-têtes de réponse:", responseHeaders);

      const responseText = await response.text();
      console.log("Réponse brute:", responseText);
      
      if (!response.ok) {
        let errorMessage = "Erreur lors de la création du dossier";
        
        try {
          if (responseText) {
            const errorData = JSON.parse(responseText);
            if (errorData && errorData.message) {
              errorMessage = errorData.message;
            }
          }
        } catch (e) {
          console.error("Erreur lors du parsing de la réponse:", e);
          errorMessage = `Erreur lors de la création du dossier (${response.status}: ${response.statusText})`;
        }
        
        throw new Error(errorMessage);
      }

      // Traiter la réponse comme JSON si possible
      let responseData;
      try {
        if (responseText) {
          responseData = JSON.parse(responseText);
          console.log("Réponse JSON:", responseData);
        }
      } catch (e) {
        console.error("La réponse n'est pas un JSON valide:", e);
      }

      // Rafraîchir la liste des dossiers
      fetchFolders();
      if (onRefresh) {
        await onRefresh();
      }
      
      setNewFolderName("");
      onClose();

      toast({
        title: "Succès",
        description: "Dossier créé avec succès.",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error("Erreur:", error);
      
      // Corriger l'erreur de type en vérifiant si error est une instance d'Error
      let errorMessage = "Impossible de créer le dossier.";
      
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      toast({
        title: "Erreur",
        description: errorMessage,
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleBreadcrumbClick = (folderId: number) => {
    setCurrentFolderId(folderId);
    onFolderSelect?.(folderId);
    onFolderChange?.(folderId);
  };

  return (
    <Box mb={6}>
      {/* Entête avec breadcrumb et boutons d'action */}
      <Flex 
        justify="space-between" 
        align="center" 
        bg="#2a3657" 
        p={3} 
        borderRadius="md" 
        mb={4}
      >
        <Flex align="center">
          <Button
            size="sm"
            variant="ghost"
            colorScheme="blue"
            leftIcon={<Icon as={FiHome as ElementType} />}
            onClick={handleHomeClick}
            mr={2}
          >
            Racine
          </Button>

          <Icon as={FiChevronRight as ElementType} mx={1} color="gray.400" />

          <Breadcrumb separator={<Icon as={FiChevronRight as ElementType} color="gray.400" />}>
            {breadcrumb.map((item, index) => (
              <BreadcrumbItem key={item.id} isCurrentPage={index === breadcrumb.length - 1}>
                <BreadcrumbLink
                  onClick={() => handleBreadcrumbClick(item.id)}
                  color={index === breadcrumb.length - 1 ? "blue.300" : "white"}
                  fontWeight={index === breadcrumb.length - 1 ? "bold" : "normal"}
                >
                  {item.titre}
                </BreadcrumbLink>
              </BreadcrumbItem>
            ))}
          </Breadcrumb>
        </Flex>

        <HStack>
          {currentFolderId !== null && (
            <Button
              size="sm"
              variant="ghost"
              colorScheme="blue"
              leftIcon={<Icon as={FiCornerUpLeft as ElementType} />}
              onClick={handleBackClick}
            >
              Retour
            </Button>
          )}
          <Button
            size="sm"
            colorScheme="green"
            onClick={fetchFolders}
          >
            Rafraîchir
          </Button>
          <Button
            size="sm"
            colorScheme="blue"
            leftIcon={<Icon as={FiFolderPlus as ElementType} />}
            onClick={onOpen}
          >
            Nouveau dossier
          </Button>
        </HStack>
      </Flex>

      {/* Liste des dossiers */}
      <Box>
        <Flex flexWrap="wrap" gap={4}>
          {isLoading ? (
            <Text color="white">Chargement des dossiers...</Text>
          ) : folders.length === 0 ? (
            <Text color="white">Aucun dossier trouvé.</Text>
          ) : (
            folders.map((folder) => (
              <Box
                key={folder.id}
                onClick={() => handleFolderClick(folder)}
                bg="#2a3657"
                borderRadius="md"
                p={3}
                cursor="pointer"
                _hover={{ bg: "#374269" }}
                transition="all 0.2s"
                minW="200px"
                maxW="250px"
              >
                <Flex align="center">
                  <Icon as={FiFolder as ElementType} color="#3a8bfd" boxSize={5} mr={3} />
                  <VStack align="start" spacing={0}>
                    <Text fontWeight="medium" noOfLines={1} color="white">
                      {folder.titre}
                    </Text>
                    <Text fontSize="xs" color="gray.400">
                      {new Date(folder.date_creation).toLocaleDateString()}
                    </Text>
                  </VStack>
                </Flex>
              </Box>
            ))
          )}
        </Flex>
      </Box>

      {/* Modal pour créer un nouveau dossier */}
      <Modal isOpen={isOpen} onClose={onClose} initialFocusRef={newFolderInputRef}>
        <ModalOverlay backdropFilter="blur(4px)" />
        <ModalContent bg="#1c2338" color="white">
          <ModalHeader>Créer un nouveau dossier</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Input
              ref={newFolderInputRef}
              placeholder="Nom du dossier"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              bg="#2a3657"
              borderColor="#3a445e"
              _hover={{ borderColor: "#0066ff" }}
              _focus={{ borderColor: "#0066ff", boxShadow: "0 0 0 1px #0066ff" }}
            />
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Annuler
            </Button>
            <Button colorScheme="blue" onClick={handleCreateFolder}>
              Créer
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default FolderBrowser;

 


