import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  Box,
  Text,
  Flex,
  Badge,
  IconButton,
  useToast,
  Input,
  FormControl,
  FormLabel,
  Select,
  Textarea,
  Alert,
  AlertIcon,
  Wrap,
  WrapItem,
  Tag,
  TagLabel,
  TagCloseButton,
  Icon,
} from '@chakra-ui/react';
import { 
  FiTag, 
  FiPlus, 
  FiX,
  FiEdit2,
  FiTrash2
} from 'react-icons/fi';
import { asElementType } from '../../utils/iconUtils';
import config from '../../config';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';

interface DocumentTag {
  id: number;
  nom: string;
  couleur: string;
  description: string;
}

interface AvailableTag extends DocumentTag {
  usage_count: number;
  created_by: string;
  created_at: string;
}

interface DocumentTagsProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number;
  documentTitle: string;
  onTagsChanged?: () => void;
}

const DocumentTags: React.FC<DocumentTagsProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  onTagsChanged
}) => {
  const [documentTags, setDocumentTags] = useState<DocumentTag[]>([]);
  const [availableTags, setAvailableTags] = useState<AvailableTag[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateTag, setShowCreateTag] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#3a8bfd');
  const [newTagDescription, setNewTagDescription] = useState('');
  const [selectedTagId, setSelectedTagId] = useState('');
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  const predefinedColors = [
    '#3a8bfd', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6b7280'
  ];

  const fetchDocumentTags = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/tags`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDocumentTags(data.tags || []);
      } else {
        throw new Error('Erreur lors du chargement des tags');
      }
    } catch (error) {
      console.error('Erreur tags:', error);
    }
  };

  const fetchAvailableTags = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/tags`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableTags(data.tags || []);
      } else {
        throw new Error('Erreur lors du chargement des tags disponibles');
      }
    } catch (error) {
      console.error('Erreur available tags:', error);
    }
  };

  const handleCreateTag = async () => {
    if (!newTagName.trim()) return;

    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/tags`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          nom: newTagName.trim(),
          couleur: newTagColor,
          description: newTagDescription.trim()
        })
      });

      if (response.ok) {
        setNewTagName('');
        setNewTagColor('#3a8bfd');
        setNewTagDescription('');
        setShowCreateTag(false);
        fetchAvailableTags();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de la création du tag');
      }
    }, {
      loadingMessage: 'Création du tag...',
      successMessage: 'Tag créé avec succès',
      errorMessage: 'Erreur lors de la création du tag'
    });
  };

  const handleAddTagToDocument = async () => {
    if (!selectedTagId) return;

    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/tags`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tag_id: parseInt(selectedTagId) })
      });

      if (response.ok) {
        setSelectedTagId('');
        fetchDocumentTags();
        onTagsChanged && onTagsChanged();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de l\'ajout du tag');
      }
    }, {
      loadingMessage: 'Ajout du tag...',
      successMessage: 'Tag ajouté avec succès',
      errorMessage: 'Erreur lors de l\'ajout du tag'
    });
  };

  const handleRemoveTagFromDocument = async (tagId: number) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/tags/${tagId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        fetchDocumentTags();
        onTagsChanged && onTagsChanged();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de la suppression du tag');
      }
    }, {
      loadingMessage: 'Suppression du tag...',
      successMessage: 'Tag supprimé avec succès',
      errorMessage: 'Erreur lors de la suppression du tag'
    });
  };

  const getAvailableTagsForDocument = () => {
    const documentTagIds = documentTags.map(tag => tag.id);
    return availableTags.filter(tag => !documentTagIds.includes(tag.id));
  };

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      Promise.all([fetchDocumentTags(), fetchAvailableTags()])
        .finally(() => setLoading(false));
    }
  }, [isOpen, documentId]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl">
      <ModalOverlay bg="blackAlpha.700" />
      <ModalContent bg="#20243a" color="white" maxH="90vh">
        <ModalHeader>
          <Flex align="center" gap={3}>
            <Icon as={asElementType(FiTag)} color="#3a8bfd" />
            <Text>Tags - "{documentTitle}"</Text>
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody overflowY="auto">
          <VStack align="stretch" spacing={6}>
            {/* Tags actuels du document */}
            <Box>
              <Text fontWeight="bold" mb={3}>Tags actuels</Text>
              {documentTags.length === 0 ? (
                <Alert status="info" bg="#2a3657" color="white">
                  <AlertIcon color="#3a8bfd" />
                  Aucun tag associé à ce document
                </Alert>
              ) : (
                <Wrap spacing={2}>
                  {documentTags.map((tag) => (
                    <WrapItem key={tag.id}>
                      <Tag
                        size="lg"
                        bg={tag.couleur}
                        color="white"
                        borderRadius="full"
                      >
                        <TagLabel>{tag.nom}</TagLabel>
                        <TagCloseButton
                          onClick={() => handleRemoveTagFromDocument(tag.id)}
                        />
                      </Tag>
                    </WrapItem>
                  ))}
                </Wrap>
              )}
            </Box>

            {/* Ajouter un tag existant */}
            <Box>
              <Text fontWeight="bold" mb={3}>Ajouter un tag existant</Text>
              <HStack>
                <Select
                  placeholder="Sélectionner un tag"
                  value={selectedTagId}
                  onChange={(e) => setSelectedTagId(e.target.value)}
                  bg="#2a3657"
                  borderColor="#3a445e"
                >
                  {getAvailableTagsForDocument().map((tag) => (
                    <option key={tag.id} value={tag.id}>
                      {tag.nom} ({tag.usage_count} utilisations)
                    </option>
                  ))}
                </Select>
                <Button
                  leftIcon={<Icon as={asElementType(FiPlus)} />}
                  colorScheme="blue"
                  onClick={handleAddTagToDocument}
                  isDisabled={!selectedTagId}
                >
                  Ajouter
                </Button>
              </HStack>
            </Box>

            {/* Créer un nouveau tag */}
            <Box>
              <Flex justify="space-between" align="center" mb={3}>
                <Text fontWeight="bold">Créer un nouveau tag</Text>
                <Button
                  leftIcon={<Icon as={asElementType(showCreateTag ? FiX : FiPlus)} />}
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCreateTag(!showCreateTag)}
                >
                  {showCreateTag ? 'Annuler' : 'Nouveau tag'}
                </Button>
              </Flex>

              {showCreateTag && (
                <VStack align="stretch" spacing={4} p={4} bg="#2a3657" borderRadius="md">
                  <FormControl isRequired>
                    <FormLabel>Nom du tag</FormLabel>
                    <Input
                      value={newTagName}
                      onChange={(e) => setNewTagName(e.target.value)}
                      placeholder="Nom du tag"
                      bg="#20243a"
                      borderColor="#3a445e"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Couleur</FormLabel>
                    <HStack spacing={2} mb={2}>
                      {predefinedColors.map((color) => (
                        <Box
                          key={color}
                          w={8}
                          h={8}
                          bg={color}
                          borderRadius="md"
                          cursor="pointer"
                          border={newTagColor === color ? "3px solid white" : "1px solid gray"}
                          onClick={() => setNewTagColor(color)}
                        />
                      ))}
                    </HStack>
                    <Input
                      type="color"
                      value={newTagColor}
                      onChange={(e) => setNewTagColor(e.target.value)}
                      w="60px"
                      h="40px"
                      p={1}
                      bg="#20243a"
                      borderColor="#3a445e"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Description (optionnelle)</FormLabel>
                    <Textarea
                      value={newTagDescription}
                      onChange={(e) => setNewTagDescription(e.target.value)}
                      placeholder="Description du tag"
                      bg="#20243a"
                      borderColor="#3a445e"
                      resize="vertical"
                      rows={3}
                    />
                  </FormControl>

                  <HStack>
                    <Button
                      colorScheme="blue"
                      onClick={handleCreateTag}
                      isDisabled={!newTagName.trim()}
                    >
                      Créer et ajouter
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => setShowCreateTag(false)}
                    >
                      Annuler
                    </Button>
                  </HStack>
                </VStack>
              )}
            </Box>

            {/* Aperçu des tags disponibles */}
            {availableTags.length > 0 && (
              <Box>
                <Text fontWeight="bold" mb={3}>Tous les tags disponibles</Text>
                <Wrap spacing={2}>
                  {availableTags.map((tag) => (
                    <WrapItem key={tag.id}>
                      <Tag
                        size="md"
                        bg={tag.couleur}
                        color="white"
                        borderRadius="full"
                      >
                        <TagLabel>
                          {tag.nom} ({tag.usage_count})
                        </TagLabel>
                      </Tag>
                    </WrapItem>
                  ))}
                </Wrap>
              </Box>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" onClick={onClose}>
            Fermer
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default DocumentTags; 

