/**
 * Types TypeScript pour le système de workflow de validation
 */

export interface WorkflowInstance {
  id: number;
  workflow_id: number;
  document_id: number;
  initiateur_id: number;
  etape_courante_id: number | null;
  statut: WorkflowStatus;
  date_creation: string;
  date_fin: string | null;
  commentaire: string;
  workflow_nom?: string;
  document_titre?: string;
  etape_courante_nom?: string;
  initiateur_nom?: string;
  initiateur_prenom?: string;
}

export interface WorkflowEtape {
  id: number;
  workflow_id: number;
  nom: string;
  description: string;
  ordre: number;
  type_approbation: string;
  delai_max: number | null;
  statut_etape?: ApprovalStatus;
  date_decision?: string | null;
  commentaire_approbation?: string;
  approbateur_nom?: string;
  approbateur_prenom?: string;
}

export interface WorkflowApprobation {
  id: number;
  instance_id: number;
  etape_id: number;
  approbateur_id: number;
  decision: ApprovalDecision;
  date_decision: string;
  commentaire: string;
  etape_nom?: string;
  etape_ordre?: number;
  approbateur_nom?: string;
  approbateur_prenom?: string;
}

export interface PendingApproval {
  instance_id: number;
  document_id: number;
  document_titre: string;
  fichier?: string;
  date_debut: string;
  date_fin?: string;
  commentaire?: string;
  etape_id: number;
  etape_nom: string;
  etape_description?: string;
  type_approbation: 'SIMPLE' | 'MULTIPLE' | 'PARALLELE';
  initiateur_nom: string;
  initiateur_prenom: string;
  initiateur_role?: string;
  workflow_nom?: string;
  date_echeance?: string;
  priorite: number;
  description?: string;
  approbations_count: number;
  approbations_necessaires: number;
  instance_statut: WorkflowStatus;
}

export interface WorkflowInstanceDetails {
  instance: WorkflowInstance;
  approbations: WorkflowApprobation[];
  etapes: WorkflowEtape[];
}

export interface DocumentWorkflowStatus {
  has_workflow: boolean;
  document_id: number;
  instance_id?: number;
  workflow_nom?: string;
  statut?: WorkflowStatus;
  etape_courante_nom?: string;
  document_statut?: string;
  date_creation?: string;
  date_fin?: string;
}

export interface WorkflowStatistics {
  general: {
    total_instances: number;
    en_cours: number;
    approuves: number;
    rejetes: number;
    annules: number;
  };
  users: Array<{
    nom: string;
    prenom: string;
    role: string;
    workflows_inities: number;
    approbations_donnees: number;
  }>;
}

// Enums et types de base
export type WorkflowStatus = 'EN_COURS' | 'APPROUVE' | 'REJETE' | 'ANNULE';

export type ApprovalDecision = 'APPROUVE' | 'REJETE' | 'EN_ATTENTE';

export type ApprovalStatus = 'APPROUVE' | 'REJETE' | 'EN_ATTENTE';

export type UserRole = 'Admin' | 'chef_de_service' | 'Utilisateur' | 'archiviste' | 'validateur';

// Interfaces pour les requêtes API
export interface StartWorkflowRequest {
  document_id: number;
  commentaire?: string;
}

export interface ProcessApprovalRequest {
  instance_id: number;
  etape_id: number;
  decision: ApprovalDecision;
  commentaire?: string;
}

// Interfaces pour les réponses API
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  count?: number;
}

export interface StartWorkflowResponse {
  instance_id: number;
  workflow_id: number;
  etape_courante_id: number;
  status: WorkflowStatus;
  message: string;
}

export interface ProcessApprovalResponse {
  status: WorkflowStatus;
  message: string;
  final: boolean;
  etape_suivante_id?: number;
}

// Types pour les props des composants
export interface ValidationWorkflowButtonProps {
  documentId: number;
  documentTitle: string;
  onWorkflowStarted?: () => void;
  disabled?: boolean;
}

export interface PendingApprovalsProps {
  userId?: number;
  onApprovalProcessed?: () => void;
}

export interface WorkflowDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  instanceId: number | null;
}

export interface ApprovalActionProps {
  instanceId: number;
  etapeId: number;
  documentTitle: string;
  etapeName: string;
  onApprovalProcessed: (result: ProcessApprovalResponse) => void;
  disabled?: boolean;
}

export interface WorkflowStatusBadgeProps {
  status: WorkflowStatus;
  size?: 'sm' | 'md' | 'lg';
}

export interface WorkflowTimelineProps {
  etapes: WorkflowEtape[];
  approbations: WorkflowApprobation[];
  currentEtapeId?: number | null;
} 
