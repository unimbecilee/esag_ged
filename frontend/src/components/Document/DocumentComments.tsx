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
  Box,
  Text,
  Flex,
  Avatar,
  Textarea,
  IconButton,
  useToast,
  Divider,
  Badge,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Icon,
  Alert,
  AlertIcon,
  Collapse,
} from '@chakra-ui/react';
import { 
  FiMessageCircle, 
  FiSend, 
  FiMoreVertical, 
  FiEdit2, 
  FiTrash2,
  FiCornerUpLeft,
  FiChevronDown,
  FiChevronRight
} from 'react-icons/fi';
import { asElementType } from '../../utils/iconUtils';
import config from '../../config';
import { useAsyncOperation } from '../../hooks/useAsyncOperation';

interface Comment {
  comment: {
    id: number;
    content: string;
    created_at: string;
    updated_at?: string;
    created_by: number;
    user_nom: string;
    user_prenom: string;
    parent_id?: number;
  };
  replies: Comment[];
}

interface DocumentCommentsProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number;
  documentTitle: string;
}

const DocumentComments: React.FC<DocumentCommentsProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle
}) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [replyTo, setReplyTo] = useState<number | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [editingComment, setEditingComment] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedReplies, setExpandedReplies] = useState<Set<number>>(new Set());
  const { executeOperation } = useAsyncOperation();
  const toast = useToast();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const fetchComments = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/comments`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setComments(data.comments || []);
      } else {
        throw new Error('Erreur lors du chargement des commentaires');
      }
    } catch (error) {
      toast({
        title: 'Erreur',
        description: 'Impossible de charger les commentaires',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;

    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/comments`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: newComment.trim() })
      });

      if (response.ok) {
        setNewComment('');
        fetchComments();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de l\'ajout du commentaire');
      }
    }, {
      loadingMessage: 'Ajout du commentaire...',
      successMessage: 'Commentaire ajouté avec succès',
      errorMessage: 'Erreur lors de l\'ajout du commentaire'
    });
  };

  const handleReply = async (parentId: number) => {
    if (!replyContent.trim()) return;

    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/comments/${parentId}/reply`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: replyContent.trim() })
      });

      if (response.ok) {
        setReplyTo(null);
        setReplyContent('');
        fetchComments();
        // Expand replies to show the new one
        setExpandedReplies(prev => new Set(prev).add(parentId));
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de l\'ajout de la réponse');
      }
    }, {
      loadingMessage: 'Ajout de la réponse...',
      successMessage: 'Réponse ajoutée avec succès',
      errorMessage: 'Erreur lors de l\'ajout de la réponse'
    });
  };

  const handleEditComment = async (commentId: number) => {
    if (!editContent.trim()) return;

    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/comments/${commentId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: editContent.trim() })
      });

      if (response.ok) {
        setEditingComment(null);
        setEditContent('');
        fetchComments();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de la modification');
      }
    }, {
      loadingMessage: 'Modification en cours...',
      successMessage: 'Commentaire modifié avec succès',
      errorMessage: 'Erreur lors de la modification'
    });
  };

  const handleDeleteComment = async (commentId: number) => {
    await executeOperation(async () => {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/documents/${documentId}/comments/${commentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        fetchComments();
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Erreur lors de la suppression');
      }
    }, {
      loadingMessage: 'Suppression en cours...',
      successMessage: 'Commentaire supprimé avec succès',
      errorMessage: 'Erreur lors de la suppression'
    });
  };

  const toggleReplies = (commentId: number) => {
    setExpandedReplies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(commentId)) {
        newSet.delete(commentId);
      } else {
        newSet.add(commentId);
      }
      return newSet;
    });
  };

  const renderComment = (commentData: Comment, isReply = false) => {
    const { comment, replies } = commentData;
    const hasReplies = replies && replies.length > 0;
    const isExpanded = expandedReplies.has(comment.id);
    const currentUserId = 1; // TODO: Get from auth context

    return (
      <Box key={comment.id} ml={isReply ? 8 : 0} mb={4}>
        <Flex gap={3}>
          <Avatar 
            size="sm" 
            name={`${comment.user_prenom} ${comment.user_nom}`}
            bg="#3a8bfd"
          />
          <Box flex={1}>
            <Flex justify="space-between" align="start" mb={2}>
              <Box>
                <Text fontWeight="bold" fontSize="sm">
                  {comment.user_prenom} {comment.user_nom}
                </Text>
                <Text fontSize="xs" color="gray.400">
                  {formatDate(comment.created_at)}
                  {comment.updated_at && comment.updated_at !== comment.created_at && (
                    <Badge ml={2} colorScheme="orange" fontSize="xs">
                      Modifié
                    </Badge>
                  )}
                </Text>
              </Box>
              
              {comment.created_by === currentUserId && (
                <Menu>
                  <MenuButton
                    as={IconButton}
                    icon={<Icon as={asElementType(FiMoreVertical)} />}
                    variant="ghost"
                    size="xs"
                  />
                  <MenuList bg="#2a3657" borderColor="#3a445e">
                    <MenuItem
                      icon={<Icon as={asElementType(FiEdit2)} />}
                      onClick={() => {
                        setEditingComment(comment.id);
                        setEditContent(comment.content);
                      }}
                      _hover={{ bg: "#363b5a" }}
                    >
                      Modifier
                    </MenuItem>
                    <MenuItem
                      icon={<Icon as={asElementType(FiTrash2)} />}
                      onClick={() => handleDeleteComment(comment.id)}
                      _hover={{ bg: "#363b5a" }}
                      color="red.400"
                    >
                      Supprimer
                    </MenuItem>
                  </MenuList>
                </Menu>
              )}
            </Flex>

            {editingComment === comment.id ? (
              <VStack align="stretch" spacing={2}>
                <Textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  bg="#2a3657"
                  borderColor="#3a445e"
                  resize="vertical"
                  minH="80px"
                />
                <Flex gap={2}>
                  <Button
                    size="sm"
                    colorScheme="blue"
                    onClick={() => handleEditComment(comment.id)}
                  >
                    Sauvegarder
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setEditingComment(null);
                      setEditContent('');
                    }}
                  >
                    Annuler
                  </Button>
                </Flex>
              </VStack>
            ) : (
              <>
                <Text mb={2} whiteSpace="pre-wrap">
                  {comment.content}
                </Text>
                
                <Flex gap={2} align="center">
                  {!isReply && (
                    <Button
                      leftIcon={<Icon as={asElementType(FiCornerUpLeft)} />}
                      size="xs"
                      variant="ghost"
                      onClick={() => {
                        setReplyTo(comment.id);
                        setReplyContent('');
                      }}
                    >
                      Répondre
                    </Button>
                  )}
                  
                  {hasReplies && (
                    <Button
                      leftIcon={<Icon as={asElementType(isExpanded ? FiChevronDown : FiChevronRight)} />}
                      size="xs"
                      variant="ghost"
                      onClick={() => toggleReplies(comment.id)}
                    >
                      {replies.length} réponse{replies.length > 1 ? 's' : ''}
                    </Button>
                  )}
                </Flex>

                {replyTo === comment.id && (
                  <Box mt={3} p={3} bg="#2a3657" borderRadius="md">
                    <Textarea
                      placeholder="Écrivez votre réponse..."
                      value={replyContent}
                      onChange={(e) => setReplyContent(e.target.value)}
                      bg="#20243a"
                      borderColor="#3a445e"
                      resize="vertical"
                      minH="80px"
                      mb={2}
                    />
                    <Flex gap={2}>
                      <Button
                        leftIcon={<Icon as={asElementType(FiSend)} />}
                        size="sm"
                        colorScheme="blue"
                        onClick={() => handleReply(comment.id)}
                        isDisabled={!replyContent.trim()}
                      >
                        Répondre
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setReplyTo(null);
                          setReplyContent('');
                        }}
                      >
                        Annuler
                      </Button>
                    </Flex>
                  </Box>
                )}

                {hasReplies && (
                  <Collapse in={isExpanded} animateOpacity>
                    <Box mt={3}>
                      {replies.map(reply => renderComment(reply, true))}
                    </Box>
                  </Collapse>
                )}
              </>
            )}
          </Box>
        </Flex>
      </Box>
    );
  };

  useEffect(() => {
    if (isOpen) {
      fetchComments();
    }
  }, [isOpen, documentId]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl">
      <ModalOverlay bg="blackAlpha.700" />
      <ModalContent bg="#20243a" color="white" maxH="90vh">
        <ModalHeader>
          <Flex align="center" gap={3}>
            <Icon as={asElementType(FiMessageCircle)} color="#3a8bfd" />
            <Text>Commentaires - "{documentTitle}"</Text>
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody overflowY="auto">
          {/* Nouveau commentaire */}
          <Box mb={6} p={4} bg="#2a3657" borderRadius="md">
            <Text mb={3} fontWeight="bold">Ajouter un commentaire</Text>
            <Textarea
              placeholder="Écrivez votre commentaire..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              bg="#20243a"
              borderColor="#3a445e"
              resize="vertical"
              minH="100px"
              mb={3}
            />
            <Button
              leftIcon={<Icon as={asElementType(FiSend)} />}
              colorScheme="blue"
              onClick={handleAddComment}
              isDisabled={!newComment.trim()}
            >
              Publier
            </Button>
          </Box>

          <Divider mb={6} />

          {/* Liste des commentaires */}
          {loading ? (
            <Box textAlign="center" py={8}>
              <Text>Chargement des commentaires...</Text>
            </Box>
          ) : comments.length === 0 ? (
            <Alert status="info" bg="#2a3657" color="white">
              <AlertIcon color="#3a8bfd" />
              Aucun commentaire pour ce document. Soyez le premier à commenter !
            </Alert>
          ) : (
            <VStack align="stretch" spacing={4}>
              {comments.map(comment => renderComment(comment))}
            </VStack>
          )}
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

export default DocumentComments; 

