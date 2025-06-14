import React, { useState, useEffect } from 'react';
import { Container, Box, TextField, InputAdornment, Button, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Typography } from '@mui/material';
import { Search as SearchIcon, Add as AddIcon } from '@mui/icons-material';
import { Grid } from '@chakra-ui/react';
import DocumentCard from '../components/DocumentCard';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-toastify';

interface Document {
  id: number;
  titre: string;
  description: string;
  date_creation: string;
  date_modification: string;
  taille: number;
  type: string;
  type_mime: string;
  auteur: string;
  statut: string;
  est_archive?: boolean;
  date_archivage?: string;
}

const MyDocuments: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [workflowComment, setWorkflowComment] = useState('');
  const [openWorkflowDialog, setOpenWorkflowDialog] = useState(false);
  const [openArchiveDialog, setOpenArchiveDialog] = useState(false);
  const [archiveComment, setArchiveComment] = useState('');
  
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    fetchDocuments();
    
    // Vérifier les workflows disponibles
    if (user) {
      axios.get('/api/workflows', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      .then(response => {
        console.log('🔍 [DEBUG] Workflows disponibles:', response.data);
        const archiveWorkflow = response.data.find((wf: { id: number; nom: string }) => 
          wf.nom.toLowerCase().includes('archivage')
        );
        if (!archiveWorkflow) {
          console.log('⚠️ [ALERTE] Aucun workflow d\'archivage trouvé!');
        } else {
          console.log('✅ [INFO] Workflow d\'archivage trouvé:', archiveWorkflow);
        }
      })
      .catch(err => {
        console.error('❌ [ERREUR] Impossible de récupérer les workflows:', err);
      });
    }
  }, [user]);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/documents', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      console.log('🔍 [DEBUG] Documents récupérés:', response.data);
      // Vérifier les statuts des documents et leur état d'archivage
      const documentsApprouves = response.data.filter((doc: Document) => doc.statut === 'APPROUVE');
      const documentsArchives = response.data.filter((doc: Document) => doc.est_archive === true);
      const documentsArchivables = response.data.filter((doc: Document) => doc.statut === 'APPROUVE' && !doc.est_archive);
      
      console.log('🔍 [DEBUG] Documents approuvés:', documentsApprouves.length);
      console.log('🔍 [DEBUG] Documents déjà archivés:', documentsArchives.length);
      console.log('🔍 [DEBUG] Documents archivables:', documentsArchivables.length);
      
      if (documentsArchivables.length === 0) {
        console.log('⚠️ [ALERTE] Aucun document n\'est éligible pour l\'archivage (statut APPROUVE et non archivé)');
      } else {
        console.log('✅ [INFO] Documents éligibles pour l\'archivage:', documentsArchivables.map((doc: Document) => ({id: doc.id, titre: doc.titre})));
      }
      setDocuments(response.data);
      setError('');
    } catch (err) {
      console.error('Erreur lors du chargement des documents:', err);
      setError('Erreur lors du chargement des documents. Veuillez réessayer plus tard.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };

  const filteredDocuments = documents.filter(doc => 
    doc.titre.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleViewDocument = (id: number) => {
    navigate(`/documents/${id}`);
  };

  const handleEditDocument = (id: number) => {
    navigate(`/documents/edit/${id}`);
  };

  const handleDeleteDocument = async (id: number) => {
    try {
      await axios.delete(`/api/documents/${id}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      setDocuments(documents.filter(doc => doc.id !== id));
      toast.success('Document supprimé avec succès');
    } catch (err) {
      console.error('Erreur lors de la suppression du document:', err);
      toast.error('Erreur lors de la suppression du document');
    }
  };

  const handleDownloadDocument = async (id: number) => {
    try {
      const response = await axios.get(`/api/documents/${id}/download`, {
        responseType: 'blob',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // Récupérer le nom du fichier depuis les headers ou utiliser un nom par défaut
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'document';
      
      if (contentDisposition) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(contentDisposition);
        if (matches != null && matches[1]) { 
          filename = matches[1].replace(/['"]/g, '');
        }
      }
      
      // Créer un URL pour le blob et déclencher le téléchargement
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      console.error('Erreur lors du téléchargement du document:', err);
      toast.error('Erreur lors du téléchargement du document');
    }
  };

  const handleCreateDocument = () => {
    navigate('/documents/create');
  };

  const handleOpenWorkflowDialog = (id: number) => {
    setSelectedDocumentId(id);
    setOpenWorkflowDialog(true);
  };

  const handleCloseWorkflowDialog = () => {
    setOpenWorkflowDialog(false);
    setWorkflowComment('');
    setSelectedDocumentId(null);
  };

  const handleSubmitWorkflow = async () => {
    if (!selectedDocumentId) return;
    
    try {
      // Rechercher l'ID du workflow de validation
      const workflowResponse = await axios.get('/api/workflows', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      const validationWorkflow = workflowResponse.data.find((wf: any) => 
        wf.nom.toLowerCase().includes('validation')
      );
      
      if (!validationWorkflow) {
        toast.error('Workflow de validation non trouvé');
        handleCloseWorkflowDialog();
        return;
      }
      
      // Créer une instance de workflow
      await axios.post('/api/workflow-instances', {
        workflow_id: validationWorkflow.id,
        document_id: selectedDocumentId,
        commentaire: workflowComment
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // Mettre à jour le statut du document localement
      setDocuments(documents.map(doc => 
        doc.id === selectedDocumentId ? { ...doc, statut: 'EN_VALIDATION' } : doc
      ));
      
      toast.success('Document soumis pour validation avec succès');
      handleCloseWorkflowDialog();
      
    } catch (err) {
      console.error('Erreur lors de la soumission du document pour validation:', err);
      toast.error('Erreur lors de la soumission du document pour validation');
      handleCloseWorkflowDialog();
    }
  };

  const handleOpenArchiveDialog = (id: number) => {
    setSelectedDocumentId(id);
    setOpenArchiveDialog(true);
  };

  const handleCloseArchiveDialog = () => {
    setOpenArchiveDialog(false);
    setArchiveComment('');
    setSelectedDocumentId(null);
  };

  const handleRequestArchive = async () => {
    if (!selectedDocumentId) return;
    
    try {
      // Rechercher l'ID du workflow d'archivage
      const workflowResponse = await axios.get('/api/workflows', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      console.log('Workflows disponibles:', workflowResponse.data);
      
      const archiveWorkflow = workflowResponse.data.find((wf: any) => 
        wf.nom.toLowerCase().includes('archivage')
      );
      
      console.log('Workflow d\'archivage trouvé:', archiveWorkflow);
      
      if (!archiveWorkflow) {
        toast.error('Workflow d\'archivage non trouvé');
        handleCloseArchiveDialog();
        return;
      }
      
      // Créer une instance de workflow d'archivage
      await axios.post('/api/workflow-instances', {
        workflow_id: archiveWorkflow.id,
        document_id: selectedDocumentId,
        commentaire: archiveComment
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      // Mettre à jour le statut du document localement
      setDocuments(documents.map(doc => 
        doc.id === selectedDocumentId ? { ...doc, statut: 'EN_VALIDATION' } : doc
      ));
      
      toast.success('Demande d\'archivage soumise avec succès');
      handleCloseArchiveDialog();
      
    } catch (err) {
      console.error('Erreur lors de la demande d\'archivage:', err);
      toast.error('Erreur lors de la demande d\'archivage');
      handleCloseArchiveDialog();
    }
  };

  // Vérifier si l'utilisateur est admin
  const isAdmin = user?.role === 'admin';
  console.log('User role:', user?.role, 'isAdmin:', isAdmin);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4">
          Mes Documents
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleCreateDocument}
        >
          Nouveau Document
        </Button>
      </Box>
      
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Rechercher des documents..."
        value={searchQuery}
        onChange={handleSearch}
        sx={{ mb: 4 }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
      />
      
      {loading ? (
        <Typography>Chargement des documents...</Typography>
      ) : error ? (
        <Typography color="error">{error}</Typography>
      ) : filteredDocuments.length === 0 ? (
        <Typography>Aucun document trouvé.</Typography>
      ) : (
        <Grid templateColumns="repeat(3, 1fr)" gap={6}>
          {filteredDocuments.map((doc) => (
            <DocumentCard
              key={doc.id}
              document={{
                ...doc,
                type_mime: doc.type_mime || 'application/octet-stream'
              }}
              onSelect={() => {}}
              selected={false}
              onView={handleViewDocument}
              onEdit={handleEditDocument}
              onDelete={isAdmin ? handleDeleteDocument : () => {}}
              onDownload={handleDownloadDocument}
              onToggleFavorite={() => {}}
              isFavorite={false}
              onSubmitWorkflow={handleOpenWorkflowDialog}
              onRequestArchive={handleOpenArchiveDialog}
            />
          ))}
        </Grid>
      )}

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
            value={workflowComment}
            onChange={(e) => setWorkflowComment(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseWorkflowDialog}>Annuler</Button>
          <Button onClick={handleSubmitWorkflow} variant="contained" color="primary">
            Soumettre
          </Button>
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
            value={archiveComment}
            onChange={(e) => setArchiveComment(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseArchiveDialog}>Annuler</Button>
          <Button onClick={handleRequestArchive} variant="contained" color="primary">
            Demander l'archivage
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default MyDocuments; 