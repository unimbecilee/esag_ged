/**
 * Service pour les appels API du workflow de validation
 */

import config from '../config';
import { checkAuthToken } from '../utils/errorHandling';
import {
  ApiResponse,
  StartWorkflowRequest,
  StartWorkflowResponse,
  ProcessApprovalRequest,
  ProcessApprovalResponse,
  PendingApproval,
  WorkflowInstanceDetails,
  DocumentWorkflowStatus,
  WorkflowStatistics
} from '../types/workflow';

class ValidationWorkflowService {
  private readonly baseUrl: string;

  constructor() {
    this.baseUrl = `${config.API_URL}/validation-workflow`;
  }

  /**
   * Démarre un workflow de validation pour un document
   */
  async startValidationWorkflow(request: StartWorkflowRequest): Promise<StartWorkflowResponse> {
    const token = checkAuthToken();
    
    const response = await fetch(`${this.baseUrl}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    const data: ApiResponse<StartWorkflowResponse> = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Erreur lors du démarrage du workflow');
    }

    if (!data.success || !data.data) {
      throw new Error(data.message || 'Réponse invalide du serveur');
    }

    return data.data;
  }

  /**
   * Traite une approbation ou un rejet
   */
  async processApproval(request: ProcessApprovalRequest): Promise<ProcessApprovalResponse> {
    const token = checkAuthToken();
    
    const response = await fetch(`${this.baseUrl}/approve`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    const data: ApiResponse<ProcessApprovalResponse> = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Erreur lors du traitement de l\'approbation');
    }

    if (!data.success || !data.data) {
      throw new Error(data.message || 'Réponse invalide du serveur');
    }

    return data.data;
  }

  /**
   * Récupère les approbations en attente pour l'utilisateur connecté
   */
  async getPendingApprovals(): Promise<PendingApproval[]> {
    const token = checkAuthToken();
    
    const response = await fetch(`${this.baseUrl}/pending`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data: ApiResponse<PendingApproval[]> = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Erreur lors de la récupération des approbations en attente');
    }

    if (!data.success) {
      throw new Error(data.message || 'Réponse invalide du serveur');
    }

    return data.data || [];
  }

  /**
   * Récupère les détails d'une instance de workflow
   */
  async getWorkflowInstanceDetails(instanceId: number): Promise<WorkflowInstanceDetails> {
    const token = checkAuthToken();
    
    const response = await fetch(`${this.baseUrl}/instance/${instanceId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data: ApiResponse<WorkflowInstanceDetails> = await response.json();

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Instance de workflow non trouvée');
      }
      throw new Error(data.message || 'Erreur lors de la récupération des détails');
    }

    if (!data.success || !data.data) {
      throw new Error(data.message || 'Réponse invalide du serveur');
    }

    return data.data;
  }

  /**
   * Récupère le statut du workflow pour un document
   */
  async getDocumentWorkflowStatus(documentId: number): Promise<DocumentWorkflowStatus> {
    const token = checkAuthToken();
    
    const response = await fetch(`${this.baseUrl}/document/${documentId}/status`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data: ApiResponse<DocumentWorkflowStatus> = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Erreur lors de la récupération du statut');
    }

    if (!data.success || !data.data) {
      throw new Error(data.message || 'Réponse invalide du serveur');
    }

    return data.data;
  }

  /**
   * Récupère les statistiques des workflows (admin uniquement)
   */
  async getWorkflowStatistics(): Promise<WorkflowStatistics> {
    const token = checkAuthToken();
    
    const response = await fetch(`${this.baseUrl}/statistics`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    const data: ApiResponse<WorkflowStatistics> = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Erreur lors de la récupération des statistiques');
    }

    if (!data.success || !data.data) {
      throw new Error(data.message || 'Réponse invalide du serveur');
    }

    return data.data;
  }

  /**
   * Vérifie si un utilisateur peut démarrer un workflow pour un document
   */
  async canStartWorkflow(documentId: number): Promise<boolean> {
    try {
      const status = await this.getDocumentWorkflowStatus(documentId);
      // Ne peut pas démarrer si un workflow est déjà en cours
      return !status.has_workflow || status.statut !== 'EN_COURS';
    } catch (error) {
      console.error('Erreur lors de la vérification du statut:', error);
      return false;
    }
  }

  /**
   * Formate une date pour l'affichage
   */
  formatDate(dateString: string): string {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return dateString;
    }
  }

  /**
   * Retourne la couleur appropriée pour un statut de workflow
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'EN_COURS':
        return 'blue';
      case 'APPROUVE':
        return 'green';
      case 'REJETE':
        return 'red';
      case 'ANNULE':
        return 'gray';
      default:
        return 'gray';
    }
  }

  /**
   * Retourne le libellé français pour un statut
   */
  getStatusLabel(status: string): string {
    switch (status) {
      case 'EN_COURS':
        return 'En cours';
      case 'APPROUVE':
        return 'Approuvé';
      case 'REJETE':
        return 'Rejeté';
      case 'ANNULE':
        return 'Annulé';
      case 'EN_ATTENTE':
        return 'En attente';
      default:
        return status;
    }
  }

  /**
   * Retourne l'icône appropriée pour un statut
   */
  getStatusIcon(status: string): string {
    switch (status) {
      case 'EN_COURS':
        return 'FiClock';
      case 'APPROUVE':
        return 'FiCheckCircle';
      case 'REJETE':
        return 'FiXCircle';
      case 'ANNULE':
        return 'FiMinusCircle';
      case 'EN_ATTENTE':
        return 'FiClock';
      default:
        return 'FiCircle';
    }
  }
}

// Instance singleton du service
export const validationWorkflowService = new ValidationWorkflowService();
export default validationWorkflowService; 