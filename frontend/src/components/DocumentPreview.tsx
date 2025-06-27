import React, { useState, useEffect, useCallback, ElementType } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Text,
  Center,
  Icon,
  VStack,
  HStack,
  Button,
  Box,
  Spinner,
  useToast,
  Badge,
  Divider
} from '@chakra-ui/react';
import { FiFileText, FiDownload, FiExternalLink } from 'react-icons/fi';
import config from '../config';

interface DocumentPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: number | null;
  documentTitle: string;
}

interface DocumentDetails {
  id: number;
  titre: string;
  fichier: string;
  cloudinary_url?: string;
  cloudinary_public_id?: string;
  mime_type: string;
  taille: number;
  taille_formatee: string;
  date_creation: string;
  date_ajout: string;
  derniere_modification: string;
  type_document: string;
  categorie: string;
  description?: string;
  proprietaire_id: number;
  proprietaire_nom?: string;
  proprietaire_prenom?: string;
  service?: string;
  organisation_id?: number;
  version_courante_id?: number;
  dossier_id?: number;
  content?: string;
  modifie_par?: number;
}

const DocumentPreview: React.FC<DocumentPreviewProps> = ({
  isOpen,
  onClose,
  documentId,
  documentTitle
}) => {
  const [document, setDocument] = useState<DocumentDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [autoDownloadStarted, setAutoDownloadStarted] = useState(false);
  const toast = useToast();

  // Fonction pour vérifier si un type de fichier peut être prévisualisé
  const canPreview = (mimeType: string) => {
    const previewable = [
      'application/pdf',
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/webp',
      'text/plain',
      'text/html'
    ].includes(mimeType);
    
    console.log(`🔍 [PREVIEW DEBUG] Type: ${mimeType}, Prévisualisable: ${previewable}`);
    return previewable;
  };

  // Fonction d'auto-téléchargement
  const handleAutoDownloadAndOpen = async () => {
    try {
      console.log('🚀 [AUTO-DOWNLOAD] Début de l\'auto-téléchargement');
      
      toast({
        title: 'Téléchargement automatique',
        description: 'Ce type de fichier va être téléchargé et ouvert automatiquement',
        status: 'info',
        duration: 3000,
      });

      // Si on a l'URL Cloudinary directe, l'utiliser directement
      if (document?.cloudinary_url) {
        console.log('📎 [AUTO-DOWNLOAD] Utilisation Cloudinary URL:', document.cloudinary_url);
        // Ouvrir directement dans un nouvel onglet
        window.open(document.cloudinary_url, '_blank');
        
        toast({
          title: 'Ouverture réussie',
          description: 'Le document a été ouvert dans un nouvel onglet',
          status: 'success',
          duration: 3000,
        });
        
        // Fermer la modal après l'ouverture automatique
        setTimeout(() => {
          onClose();
        }, 2000);
        
        return;
      }

      // Sinon, utiliser l'API de téléchargement
      console.log('🔗 [AUTO-DOWNLOAD] Utilisation API de téléchargement');
      const token = localStorage.getItem('token');
      const downloadUrl = `${config.API_URL}/api/documents/${documentId}/download`;
      
      console.log('🔗 [AUTO-DOWNLOAD] URL:', downloadUrl);
      // Ouvrir dans un nouvel onglet avec authentification
      window.open(`${downloadUrl}?token=${token}`, '_blank');
      
      toast({
        title: 'Ouverture réussie',
        description: 'Le document a été ouvert dans un nouvel onglet',
        status: 'success',
        duration: 3000,
      });
      
      // Fermer la modal après l'ouverture automatique
      setTimeout(() => {
        onClose();
      }, 2000);

    } catch (error) {
      console.error('❌ [AUTO-DOWNLOAD] Erreur:', error);
      toast({
        title: 'Erreur d\'ouverture automatique',
        description: error instanceof Error ? error.message : 'Erreur inconnue',
        status: 'error',
        duration: 5000,
      });
    }
  };

  useEffect(() => {
    if (isOpen && documentId) {
      setAutoDownloadStarted(false); // Reset l'état lors d'une nouvelle ouverture
      loadDocumentDetails();
    }
  }, [isOpen, documentId]);

  // Auto-téléchargement pour les fichiers non prévisualisables
  useEffect(() => {
    console.log('🔍 [AUTO-DOWNLOAD DEBUG] État actuel:', {
      document: document ? document.mime_type : 'null',
      loading,
      error,
      canPreview: document ? canPreview(document.mime_type) : 'N/A',
      autoDownloadStarted
    });

    if (document && !loading && !error && !canPreview(document.mime_type) && !autoDownloadStarted) {
      console.log('🚀 [AUTO-DOWNLOAD] Déclenchement de l\'auto-téléchargement pour:', document.mime_type);
      setAutoDownloadStarted(true);
      
      // Déclencher immédiatement l'auto-téléchargement INLINE
      console.log('⏰ [AUTO-DOWNLOAD] Appel immédiat de handleAutoDownloadAndOpen');
      
      // Logique directe d'ouverture sans fonction séparée
      try {
        console.log('🚀 [AUTO-DOWNLOAD] Début de l\'auto-téléchargement INLINE');
        
        toast({
          title: 'Téléchargement automatique',
          description: 'Ce type de fichier va être ouvert automatiquement',
          status: 'info',
          duration: 3000,
        });

        // Si on a l'URL Cloudinary directe, l'utiliser directement
        if (document?.cloudinary_url) {
          console.log('📎 [AUTO-DOWNLOAD] Utilisation Cloudinary URL:', document.cloudinary_url);
          window.open(document.cloudinary_url, '_blank');
          
          toast({
            title: 'Ouverture réussie',
            description: 'Le document a été ouvert dans un nouvel onglet',
            status: 'success',
            duration: 3000,
          });
          
          setTimeout(() => onClose(), 2000);
          return;
        }

        // Sinon, utiliser l'API de téléchargement
        console.log('🔗 [AUTO-DOWNLOAD] Utilisation API de téléchargement');
        const token = localStorage.getItem('token');
        const downloadUrl = `${config.API_URL}/api/documents/${documentId}/download`;
        
        console.log('🔗 [AUTO-DOWNLOAD] URL:', downloadUrl);
        window.open(`${downloadUrl}?token=${token}`, '_blank');
        
        toast({
          title: 'Ouverture réussie',
          description: 'Le document a été ouvert dans un nouvel onglet',
          status: 'success',
          duration: 3000,
        });
        
        setTimeout(() => onClose(), 2000);

      } catch (error) {
        console.error('❌ [AUTO-DOWNLOAD] Erreur INLINE:', error);
        toast({
          title: 'Erreur d\'ouverture automatique',
          description: 'Une erreur est survenue',
          status: 'error',
          duration: 5000,
        });
      }
    }
  }, [document, loading, error, autoDownloadStarted]);

  const loadDocumentDetails = async () => {
    if (!documentId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Token d\'authentification manquant');
      }

      console.log(`📋 [DEBUG] Chargement document ${documentId} avec token:`, token ? 'présent' : 'manquant');
      
      const response = await fetch(`${config.API_URL}/api/documents/${documentId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log(`📋 [DEBUG] Réponse API documents/${documentId}:`, response.status, response.statusText);

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Session expirée, veuillez vous reconnecter');
        } else if (response.status === 403) {
          throw new Error('Accès non autorisé à ce document');
        } else if (response.status === 404) {
          throw new Error('Document non trouvé');
        } else {
          throw new Error('Impossible de charger le document');
        }
      }

      const data = await response.json();
      console.log(`📋 [DEBUG] Données document reçues:`, data);
      
      setDocument(data);
      
      // Construire l'URL d'aperçu
      if (data.cloudinary_url) {
        setPreviewUrl(data.cloudinary_url);
      } else if (data.fichier) {
        // Fallback vers fichier local
        setPreviewUrl(`${config.API_URL}/api/documents/${documentId}/download`);
      } else {
        throw new Error('Aucun fichier associé à ce document');
      }
      
    } catch (error) {
      console.error('Erreur chargement document:', error);
      setError(error instanceof Error ? error.message : 'Erreur inconnue');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      // Si on a l'URL Cloudinary directe, l'utiliser directement
      if (document?.cloudinary_url) {
        window.open(document.cloudinary_url, '_blank');
        toast({
          title: 'Téléchargement démarré',
          description: 'Le document va s\'ouvrir dans un nouvel onglet',
          status: 'success',
          duration: 3000,
        });
        return;
      }

      // Sinon, utiliser l'API de téléchargement
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${config.API_URL}/api/documents/${documentId}/download`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Accès non autorisé à ce document');
        } else if (response.status === 404) {
          throw new Error('Document non trouvé');
        } else {
          throw new Error('Erreur lors du téléchargement');
        }
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = document?.titre || 'document';
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);

      toast({
        title: 'Téléchargement démarré',
        status: 'success',
        duration: 3000,
      });

    } catch (error) {
      toast({
        title: 'Erreur de téléchargement',
        description: error instanceof Error ? error.message : 'Erreur inconnue',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const openInNewTab = () => {
    if (previewUrl) {
      const token = localStorage.getItem('token');
      window.open(`${previewUrl}?token=${token}`, '_blank');
    }
  };

  const renderPreview = () => {
    if (!document || !previewUrl) return null;

    const token = localStorage.getItem('token');
    const authPreviewUrl = `${previewUrl}?token=${token}`;

    if (document.mime_type.startsWith('image/')) {
      return (
        <Box w="100%" h="400px" display="flex" justifyContent="center" alignItems="center">
          <img
            src={authPreviewUrl}
            alt={document.titre}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain'
            }}
            onError={() => setError('Impossible de charger l\'image')}
          />
        </Box>
      );
    } else if (document.mime_type === 'application/pdf') {
      return (
        <Box w="100%" h="600px">
          <iframe
            src={`${authPreviewUrl}#toolbar=1`}
            width="100%"
            height="100%"
            style={{ border: 'none' }}
            title={`Aperçu de ${document.titre}`}
          />
        </Box>
      );
    } else if (document.mime_type.startsWith('text/')) {
      return (
        <Box w="100%" h="400px" bg="#1a202c" p={4} borderRadius="md" overflow="auto">
          <iframe
            src={authPreviewUrl}
            width="100%"
            height="100%"
            style={{ border: 'none', background: 'white' }}
            title={`Aperçu de ${document.titre}`}
          />
        </Box>
      );
    }

    return null;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="6xl">
      <ModalOverlay />
      <ModalContent bg="#2a3657" color="white" maxH="90vh">
        <ModalHeader>
          <HStack justify="space-between">
            <HStack>
              <Icon as={FiFileText as ElementType} />
              <Text>Aperçu du document</Text>
            </HStack>
            <HStack spacing={2}>
              <Button
                size="sm"
                leftIcon={<Icon as={FiDownload as ElementType} />}
                onClick={handleDownload}
                isDisabled={!document}
              >
                Télécharger
              </Button>
              {previewUrl && (
                <Button
                  size="sm"
                  leftIcon={<Icon as={FiExternalLink as ElementType} />}
                  onClick={openInNewTab}
                  variant="outline"
                >
                  Ouvrir
                </Button>
              )}
            </HStack>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6} overflow="auto">
          {loading && (
            <Center py={10}>
              <VStack spacing={4}>
                <Spinner size="xl" color="blue.500" />
                <Text>Chargement du document...</Text>
              </VStack>
            </Center>
          )}

          {error && (
            <Center py={10}>
              <VStack spacing={4}>
                <Icon as={FiFileText as ElementType} boxSize={16} color="red.400" />
                <Text color="red.400" textAlign="center">
                  {error}
                </Text>
                <Button onClick={loadDocumentDetails} size="sm">
                  Réessayer
                </Button>
              </VStack>
            </Center>
          )}

          {document && !loading && !error && (
            <VStack spacing={4} align="stretch">
              {/* Informations du document */}
              <Box bg="#1a202c" p={4} borderRadius="md">
                <VStack spacing={3} align="stretch">
                  <HStack justify="space-between">
                    <Text fontWeight="bold" fontSize="lg">{document.titre}</Text>
                    <Badge colorScheme="blue">{document.type_document}</Badge>
                  </HStack>
                  
                  <Divider borderColor="#4a5568" />
                  
                  <HStack justify="space-between">
                    <VStack align="start" spacing={1}>
                      <Text fontSize="sm" color="gray.300">Type de fichier</Text>
                      <Text fontSize="sm">{document.mime_type}</Text>
                    </VStack>
                    <VStack align="start" spacing={1}>
                      <Text fontSize="sm" color="gray.300">Taille</Text>
                      <Text fontSize="sm">{document.taille_formatee}</Text>
                    </VStack>
                    <VStack align="end" spacing={1}>
                      <Text fontSize="sm" color="gray.300">Créé le</Text>
                      <Text fontSize="sm">
                        {new Date(document.date_creation).toLocaleDateString('fr-FR')}
                      </Text>
                    </VStack>
                  </HStack>
                </VStack>
              </Box>

              {/* Aperçu du contenu */}
              <Box>
                {canPreview(document.mime_type) ? (
                  <Box>
                    <Text fontWeight="bold" mb={3}>Aperçu du contenu</Text>
                    {renderPreview()}
                  </Box>
                ) : (
                  <Center py={10} bg="#1a202c" borderRadius="md">
                    <VStack spacing={4}>
                      <Icon as={FiFileText as ElementType} boxSize={16} color="blue.400" />
                      <Text color="blue.400" textAlign="center" fontWeight="bold">
                        Ouverture automatique en cours...
                      </Text>
                      <Text fontSize="sm" color="gray.400" textAlign="center">
                        Ce type de fichier ({document.mime_type}) va être téléchargé et ouvert automatiquement
                      </Text>
                      <Spinner size="md" color="blue.400" />
                      <HStack spacing={2}>
                        <Button 
                          onClick={handleDownload} 
                          size="sm" 
                          variant="outline"
                          ref={(button) => {
                            // Auto-clic après 1 seconde si le fichier n'est pas prévisualisable
                            if (button && document && !canPreview(document.mime_type) && !autoDownloadStarted) {
                              setTimeout(() => {
                                console.log('🎯 [AUTO-CLICK] Clic automatique sur télécharger');
                                button.click();
                              }, 1000);
                            }
                          }}
                        >
                          Télécharger manuellement
                        </Button>
                        <Button onClick={onClose} size="sm" variant="ghost">
                          Annuler
                        </Button>
                      </HStack>
                    </VStack>
                  </Center>
                )}
              </Box>
            </VStack>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

export default DocumentPreview; 


