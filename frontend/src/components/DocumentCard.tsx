import React, { useState } from 'react';
import {
  Box,
  Card,
  CardBody,
  Checkbox,
  Flex,
  HStack,
  Heading,
  Icon,
  Image,
  Text,
  VStack,
  Badge
} from '@chakra-ui/react';
import { FiFile, FiClock, FiCheckCircle, FiXCircle, FiEdit } from 'react-icons/fi';
import { formatFileSize, formatDate, getStatusColor, getStatusLabel } from '../utils/formatters';
import ActionMenu from './ActionMenu';
import { ElementType } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { MoreVert as MoreVertIcon, Delete as DeleteIcon, Edit as EditIcon, Visibility as ViewIcon, Download as DownloadIcon, Archive as ArchiveIcon } from '@mui/icons-material';
import { CardContent, Typography, CardActions, Button as MuiButton, Chip, IconButton, Menu, MenuItem, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, TextField } from '@mui/material';

// Fonction pour obtenir la couleur du badge de statut
const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case 'BROUILLON':
      return 'gray';
    case 'EN_VALIDATION':
      return 'orange';
    case 'APPROUVE':
      return 'green';
    case 'REJETE':
      return 'red';
    default:
      return 'gray';
  }
};

// Fonction pour obtenir l'icône du statut
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'BROUILLON':
      return FiEdit as ElementType;
    case 'EN_VALIDATION':
      return FiClock as ElementType;
    case 'APPROUVE':
      return FiCheckCircle as ElementType;
    case 'REJETE':
      return FiXCircle as ElementType;
    default:
      return FiEdit as ElementType;
  }
};

interface DocumentCardProps {
  document: {
    id: number;
    titre: string;
    type_mime: string;
    taille: number;
    date_creation: string;
    proprietaire_nom?: string;
    proprietaire_prenom?: string;
    description?: string;
    thumbnail_url?: string;
    statut?: string;
    est_archive?: boolean;
    date_archivage?: string;
  };
  onSelect: (id: number) => void;
  selected?: boolean;
  onDelete: (id: number) => void;
  onDownload: (id: number) => void;
  onShare?: (id: number, title?: string) => void;
  onToggleFavorite: (id: number, isFavorite: boolean) => void;
  onMove?: (id: number, title?: string) => void;
  onView?: (id: number) => void;
  onEdit?: (id: number) => void;
  onVersions?: (id: number) => void;
  onSubmitWorkflow?: (id: number) => void;
  onRequestArchive?: (id: number, commentaire: string) => void;
  isFavorite: boolean;
  isAdmin?: boolean;
}

const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onSelect,
  selected = false,
  onDelete,
  onDownload,
  onShare,
  onToggleFavorite,
  onMove,
  onView,
  onEdit,
  onVersions,
  onSubmitWorkflow,
  onRequestArchive,
  isFavorite,
  isAdmin
}) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [openWorkflowDialog, setOpenWorkflowDialog] = useState(false);
  const [openArchiveDialog, setOpenArchiveDialog] = useState(false);
  const [commentaire, setCommentaire] = useState('');

  const handleCheckboxChange = () => {
    onSelect(document.id);
  };

  const handleViewClick = () => {
    if (onView) {
      onView(document.id);
    } else {
      navigate(`/documents/${document.id}`);
    }
  };

  const handleEditClick = () => {
    if (onEdit) {
      onEdit(document.id);
    } else {
      navigate(`/documents/edit/${document.id}`);
    }
  };

  const handleDownloadClick = () => {
    onDownload(document.id);
  };

  const handleOpenWorkflowDialog = () => {
    setOpenWorkflowDialog(true);
  };

  const handleCloseWorkflowDialog = () => {
    setOpenWorkflowDialog(false);
    setCommentaire('');
  };

  const handleSubmitWorkflow = () => {
    if (onSubmitWorkflow) {
      onSubmitWorkflow(document.id);
    }
    handleCloseWorkflowDialog();
  };

  const handleOpenArchiveDialog = () => {
    setOpenArchiveDialog(true);
  };

  const handleCloseArchiveDialog = () => {
    setOpenArchiveDialog(false);
    setCommentaire('');
  };

  const handleRequestArchive = () => {
    if (onRequestArchive) {
      onRequestArchive(document.id, commentaire);
    }
    handleCloseArchiveDialog();
  };

  const canEdit = document.statut === 'BROUILLON' || user?.role === 'admin';
  const canDelete = user?.role === 'admin';
  const canSubmitWorkflow = document.statut === 'BROUILLON' || document.statut === 'REJETE';
  const canRequestArchive = document.statut === 'APPROUVE' && !document.est_archive;
  
  // Débogage
  console.log('🔍 [DEBUG] Document:', document.id, document.titre);
  console.log('🔍 [DEBUG] Statut:', document.statut);
  console.log('🔍 [DEBUG] Est archivé:', document.est_archive);
  console.log('🔍 [DEBUG] Peut demander archivage:', canRequestArchive);
  
  // Vérifier si le document est éligible pour l'archivage
  if (document.statut !== 'APPROUVE') {
    console.log('⚠️ [ALERTE] Document non éligible pour l\'archivage - statut non APPROUVE:', document.statut);
  }
  if (document.est_archive) {
    console.log('⚠️ [ALERTE] Document déjà archivé');
  }

  return (
    <Card maxW='sm' variant='outline'>
      <CardBody>
        <HStack spacing={2} mb={2}>
          <Checkbox 
            isChecked={selected} 
            onChange={handleCheckboxChange} 
            colorScheme='blue'
          />
          <Badge 
            colorScheme={getStatusColor(document.statut || 'BROUILLON')}
            variant='solid'
            borderRadius='full'
            px={2}
          >
            {getStatusLabel(document.statut || 'BROUILLON')}
          </Badge>
        </HStack>
        
        <VStack align='stretch'>
          <HStack justify='space-between'>
            <Heading size='md' noOfLines={1} title={document.titre}>
              {document.titre}
            </Heading>
            <ActionMenu 
                  documentId={document.id}
                  documentTitle={document.titre}
                  onDownload={onDownload}
                  onDelete={onDelete}
                  onShare={onShare}
                  onEdit={handleEditClick}
                  onToggleFavorite={(id, isFav) => onToggleFavorite(id, isFav)}
                  isFavorite={isFavorite}
                  onMove={onMove}
                  onShowVersions={onVersions}
                  onSubmitForValidation={handleOpenWorkflowDialog}
                  onRequestArchive={handleOpenArchiveDialog}
                  documentStatus={document.statut}
                  isArchived={document.est_archive}
                />
          </HStack>
          
          <Text fontSize='sm' color='gray.500' noOfLines={2}>
            {document.description || "Aucune description"}
          </Text>
          
          <HStack justify='space-between' mt={2}>
            <Text fontSize='xs' color='gray.500'>
              {formatDate(document.date_creation)}
            </Text>
            <Text fontSize='xs' color='gray.500'>
              {formatFileSize(document.taille)}
            </Text>
          </HStack>
          
          <HStack justify='space-between'>
            <Text fontSize='xs' color='gray.500'>
              {document.proprietaire_prenom} {document.proprietaire_nom}
            </Text>
            <Text fontSize='xs' color='gray.500'>
              {document.type_mime?.split('/')[1] || 'Document'}
            </Text>
          </HStack>
        </VStack>
      </CardBody>

      <CardActions>
        <MuiButton size="small" startIcon={<ViewIcon />} onClick={handleViewClick}>
          Voir
        </MuiButton>
        {canEdit && (
          <MuiButton size="small" startIcon={<EditIcon />} onClick={handleEditClick}>
            Modifier
          </MuiButton>
        )}
        <MuiButton size="small" startIcon={<DownloadIcon />} onClick={handleDownloadClick}>
          Télécharger
        </MuiButton>
      </CardActions>

      {/* Dialog pour soumettre un document au workflow */}
      <Dialog open={openWorkflowDialog} onClose={handleCloseWorkflowDialog}>
        <DialogTitle>Soumettre pour validation</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Vous êtes sur le point de soumettre ce document pour validation. Veuillez ajouter un commentaire si nécessaire.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="commentaire"
            label="Commentaire (optionnel)"
            type="text"
            fullWidth
            variant="outlined"
            value={commentaire}
            onChange={(e) => setCommentaire(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <MuiButton onClick={handleCloseWorkflowDialog}>Annuler</MuiButton>
          <MuiButton onClick={handleSubmitWorkflow} variant="contained" color="primary">
            Soumettre
          </MuiButton>
        </DialogActions>
      </Dialog>

      {/* Dialog pour demander l'archivage */}
      <Dialog open={openArchiveDialog} onClose={handleCloseArchiveDialog}>
        <DialogTitle>Demande d'archivage</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Vous êtes sur le point de demander l'archivage de ce document. Cette action nécessite une validation par votre chef de service et un archiviste.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="commentaire-archive"
            label="Motif de l'archivage"
            type="text"
            fullWidth
            variant="outlined"
            value={commentaire}
            onChange={(e) => setCommentaire(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <MuiButton onClick={handleCloseArchiveDialog}>Annuler</MuiButton>
          <MuiButton onClick={handleRequestArchive} variant="contained" color="primary">
            Demander l'archivage
          </MuiButton>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default DocumentCard; 