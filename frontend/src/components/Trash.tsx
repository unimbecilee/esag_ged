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
  Tooltip,
  Select,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  Grid,
  GridItem,
  Stack,
  Divider,
} from "@chakra-ui/react";
import { FiTrash2, FiRefreshCw, FiFileText, FiBriefcase, FiRotateCcw, FiEye } from "react-icons/fi";
import { ElementType } from "react";

interface TrashItem {
  id: number;
  item_id: number;
  item_type: string;
  item_data: any;
  deleted_at: string;
  deleted_by_name: string;
}

const Trash: React.FC = () => {
  const [items, setItems] = useState<TrashItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<TrashItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedItem, setSelectedItem] = useState<TrashItem | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const toast = useToast();

  useEffect(() => {
    fetchTrashItems();
  }, []);

  useEffect(() => {
    filterItems();
  }, [selectedType, items]);

  const filterItems = () => {
    if (selectedType === "all") {
      setFilteredItems(items);
    } else {
      setFilteredItems(items.filter(item => item.item_type === selectedType));
    }
  };

  const fetchTrashItems = async () => {
    console.log("Début de la récupération des éléments de la corbeille");
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("Token d'authentification non trouvé");
        toast({
          title: "Erreur d'authentification",
          description: "Veuillez vous reconnecter",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
        return;
      }

      console.log("Envoi de la requête vers /api/trash");
      const response = await fetch("http://localhost:5000/api/trash", {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log("Statut de la réponse:", response.status);
      if (response.ok) {
        const data = await response.json();
        console.log(`${data.length} éléments récupérés de la corbeille`);
        setItems(data);
      } else if (response.status === 401) {
        console.error("Session expirée ou invalide");
        toast({
          title: "Session expirée",
          description: "Veuillez vous reconnecter",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      } else {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error("Erreur lors de la récupération des éléments:", error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les éléments supprimés",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (trashId: number) => {
    console.log(`Tentative de restauration de l'élément ${trashId}`);
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("Token d'authentification non trouvé");
        toast({
          title: "Erreur d'authentification",
          description: "Veuillez vous reconnecter",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
        return;
      }

      const response = await fetch(
        `http://localhost:5000/api/trash/${trashId}/restore`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      console.log("Statut de la restauration:", response.status);
      if (response.ok) {
        console.log(`Élément ${trashId} restauré avec succès`);
        toast({
          title: "Succès",
          description: "Élément restauré avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        fetchTrashItems();
      } else if (response.status === 401) {
        console.error("Session expirée ou invalide");
        toast({
          title: "Session expirée",
          description: "Veuillez vous reconnecter",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      } else {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error("Erreur lors de la restauration:", error);
      toast({
        title: "Erreur",
        description: "Impossible de restaurer l'élément",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleDeletePermanently = async (trashId: number) => {
    console.log(`Tentative de suppression définitive de l'élément ${trashId}`);
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("Token d'authentification non trouvé");
        toast({
          title: "Erreur d'authentification",
          description: "Veuillez vous reconnecter",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
        return;
      }

      const response = await fetch(
        `http://localhost:5000/api/trash/${trashId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      console.log("Statut de la suppression:", response.status);
      if (response.ok) {
        console.log(`Élément ${trashId} supprimé définitivement`);
        toast({
          title: "Succès",
          description: "Élément supprimé définitivement",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        fetchTrashItems();
      } else if (response.status === 401) {
        console.error("Session expirée ou invalide");
        toast({
          title: "Session expirée",
          description: "Veuillez vous reconnecter",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      } else {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error("Erreur lors de la suppression définitive:", error);
      toast({
        title: "Erreur",
        description: "Impossible de supprimer définitivement l'élément",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const getItemIcon = (itemType: string) => {
    switch (itemType) {
      case 'document':
        return FiFileText;
      case 'organisation':
        return FiBriefcase;
      default:
        return FiFileText;
    }
  };

  const getItemName = (item: TrashItem) => {
    switch (item.item_type) {
      case 'document':
        return item.item_data.titre || 'Document sans titre';
      case 'organisation':
        return item.item_data.nom || 'Organisation sans nom';
      default:
        return 'Élément inconnu';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleViewDetails = (item: TrashItem) => {
    setSelectedItem(item);
    setIsDetailModalOpen(true);
  };

  const renderDetailContent = (item: TrashItem) => {
    if (!item) return null;

    switch (item.item_type) {
      case 'document':
        return (
          <Grid templateColumns="1fr 2fr" gap={4}>
            <GridItem>
              <Text color="gray.400">Titre</Text>
            </GridItem>
            <GridItem>
              <Text color="white">{item.item_data.titre || 'Sans titre'}</Text>
            </GridItem>
            <GridItem>
              <Text color="gray.400">Type</Text>
            </GridItem>
            <GridItem>
              <Text color="white">{item.item_data.type_document || '-'}</Text>
            </GridItem>
            <GridItem>
              <Text color="gray.400">Description</Text>
            </GridItem>
            <GridItem>
              <Text color="white">{item.item_data.description || '-'}</Text>
            </GridItem>
            <GridItem>
              <Text color="gray.400">Taille</Text>
            </GridItem>
            <GridItem>
              <Text color="white">{item.item_data.taille ? `${(item.item_data.taille / 1024).toFixed(2)} KB` : '-'}</Text>
            </GridItem>
          </Grid>
        );

      case 'organisation':
        return (
          <Grid templateColumns="1fr 2fr" gap={4}>
            <GridItem>
              <Text color="gray.400">Nom</Text>
            </GridItem>
            <GridItem>
              <Text color="white">{item.item_data.nom || 'Sans nom'}</Text>
            </GridItem>
            <GridItem>
              <Text color="gray.400">Description</Text>
            </GridItem>
            <GridItem>
              <Text color="white">{item.item_data.description || '-'}</Text>
            </GridItem>
            <GridItem>
              <Text color="gray.400">Adresse</Text>
            </GridItem>
            <GridItem>
              <Text color="white">{item.item_data.adresse || '-'}</Text>
            </GridItem>
            <GridItem>
              <Text color="gray.400">Email</Text>
            </GridItem>
            <GridItem>
              <Text color="white">{item.item_data.email_contact || '-'}</Text>
            </GridItem>
            <GridItem>
              <Text color="gray.400">Téléphone</Text>
            </GridItem>
            <GridItem>
              <Text color="white">{item.item_data.telephone_contact || '-'}</Text>
            </GridItem>
            <GridItem>
              <Text color="gray.400">Statut</Text>
            </GridItem>
            <GridItem>
              <Badge colorScheme={item.item_data.statut === 'ACTIVE' ? 'green' : 'red'}>
                {item.item_data.statut || '-'}
              </Badge>
            </GridItem>
          </Grid>
        );

      default:
        return <Text color="white">Détails non disponibles</Text>;
    }
  };

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading color="white" size="lg">
          Corbeille
        </Heading>
        <Flex gap={4}>
          <Select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            bg="#20243a"
            color="white"
            width="200px"
          >
            <option value="all">Tous les éléments</option>
            <option value="document">Documents</option>
            <option value="organisation">Organisations</option>
          </Select>
          <Button
            leftIcon={<Icon as={FiRefreshCw as ElementType} />}
            onClick={fetchTrashItems}
            isLoading={loading}
            colorScheme="blue"
            variant="ghost"
          >
            Actualiser
          </Button>
        </Flex>
      </Flex>

      {loading ? (
        <Text color="white" textAlign="center">
          Chargement...
        </Text>
      ) : filteredItems.length === 0 ? (
        <Box
          bg="#20243a"
          borderRadius="lg"
          p={6}
          textAlign="center"
          color="white"
        >
          <Icon
            as={FiTrash2 as ElementType}
            boxSize={8}
            color="gray.400"
            mb={2}
          />
          <Text>
            {selectedType === "all" 
              ? "La corbeille est vide" 
              : `Aucun élément de type ${selectedType === "document" ? "document" : "organisation"} dans la corbeille`}
          </Text>
        </Box>
      ) : (
        <Box bg="#20243a" borderRadius="lg" p={6} overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">Élément</Th>
                <Th color="white">Type</Th>
                <Th color="white">Supprimé par</Th>
                <Th color="white">Date de suppression</Th>
                <Th color="white">Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredItems.map((item) => (
                <Tr key={item.id}>
                  <Td>
                    <Flex align="center">
                      <Icon
                        as={getItemIcon(item.item_type) as ElementType}
                        color="#3a8bfd"
                        mr={2}
                      />
                      <Text color="white">{getItemName(item)}</Text>
                    </Flex>
                  </Td>
                  <Td>
                    <Badge colorScheme={item.item_type === 'document' ? 'blue' : 'purple'}>
                      {item.item_type === 'document' ? 'Document' : 'Organisation'}
                    </Badge>
                  </Td>
                  <Td color="white">{item.deleted_by_name}</Td>
                  <Td color="white">{formatDate(item.deleted_at)}</Td>
                  <Td>
                    <Flex>
                      <Tooltip label="Voir les détails">
                        <Button
                          size="sm"
                          leftIcon={<Icon as={FiEye as ElementType} />}
                          colorScheme="gray"
                          variant="ghost"
                          mr={2}
                          onClick={() => handleViewDetails(item)}
                        >
                          Détails
                        </Button>
                      </Tooltip>
                      <Tooltip label="Restaurer">
                        <Button
                          size="sm"
                          leftIcon={<Icon as={FiRotateCcw as ElementType} />}
                          colorScheme="blue"
                          variant="ghost"
                          mr={2}
                          onClick={() => handleRestore(item.id)}
                        >
                          Restaurer
                        </Button>
                      </Tooltip>
                      <Tooltip label="Supprimer définitivement">
                        <Button
                          size="sm"
                          leftIcon={<Icon as={FiTrash2 as ElementType} />}
                          colorScheme="red"
                          variant="ghost"
                          onClick={() => handleDeletePermanently(item.id)}
                        >
                          Supprimer
                        </Button>
                      </Tooltip>
                    </Flex>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}

      {/* Modal de détails */}
      <Modal isOpen={isDetailModalOpen} onClose={() => setIsDetailModalOpen(false)} size="xl">
        <ModalOverlay />
        <ModalContent bg="#1a1f37">
          <ModalHeader color="white">
            <Flex align="center" gap={2}>
              <Icon as={getItemIcon(selectedItem?.item_type || '') as ElementType} />
              <Text>Détails de l'élément</Text>
            </Flex>
          </ModalHeader>
          <ModalCloseButton color="white" />
          <ModalBody>
            {selectedItem && (
              <VStack spacing={6} align="stretch">
                {renderDetailContent(selectedItem)}
                <Divider />
                <Stack spacing={2}>
                  <Text color="gray.400">Informations de suppression</Text>
                  <Grid templateColumns="1fr 2fr" gap={4}>
                    <GridItem>
                      <Text color="gray.400">Supprimé par</Text>
                    </GridItem>
                    <GridItem>
                      <Text color="white">{selectedItem.deleted_by_name}</Text>
                    </GridItem>
                    <GridItem>
                      <Text color="gray.400">Date de suppression</Text>
                    </GridItem>
                    <GridItem>
                      <Text color="white">{formatDate(selectedItem.deleted_at)}</Text>
                    </GridItem>
                  </Grid>
                </Stack>
              </VStack>
            )}
          </ModalBody>
          <ModalFooter>
            <Button
              colorScheme="blue"
              mr={3}
              leftIcon={<Icon as={FiRotateCcw as ElementType} />}
              onClick={() => {
                if (selectedItem) {
                  handleRestore(selectedItem.id);
                  setIsDetailModalOpen(false);
                }
              }}
            >
              Restaurer
            </Button>
            <Button
              colorScheme="red"
              leftIcon={<Icon as={FiTrash2 as ElementType} />}
              onClick={() => {
                if (selectedItem) {
                  handleDeletePermanently(selectedItem.id);
                  setIsDetailModalOpen(false);
                }
              }}
            >
              Supprimer définitivement
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Trash; 