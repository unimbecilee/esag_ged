// Helpers de gestion des rôles et permissions
import { User } from '../contexts/AuthContext';

export const hasRole = (user: User | null, roles: string[]): boolean => {
  if (!user || !user.role) return false;
  // Normaliser les rôles en minuscules pour la comparaison
  const userRole = user.role.toLowerCase();
  const normalizedRoles = roles.map(role => role.toLowerCase());
  return normalizedRoles.includes(userRole);
};

// === PERMISSIONS D'ACCÈS AUX MENUS SELON LE TABLEAU ===

// Tableau de bord - Accessible à tous
export const canAccessDashboard = (user: User | null) => 
  hasRole(user, ['Admin', 'chef_de_service', 'Utilisateur', 'validateur', 'archiviste']);

// Utilisateurs - Admin uniquement
export const canAccessUsers = (user: User | null) => hasRole(user, ['Admin']);
export const canManageUsers = (user: User | null) => hasRole(user, ['Admin']);

// Mes Documents - Tous les rôles (vue filtrée selon les droits)
export const canAccessMyDocuments = (user: User | null) => 
  hasRole(user, ['Admin', 'chef_de_service', 'Utilisateur', 'validateur', 'archiviste']);

// Recherche - Accessible à tous sauf utilisateur_standard pour certaines fonctionnalités avancées
export const canAccessSearch = (user: User | null) => 
  hasRole(user, ['Admin', 'chef_de_service', 'Utilisateur', 'archiviste', 'validateur']);

// Historique - Admin et archiviste uniquement (traçabilité complète)
export const canAccessHistory = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);
export const canSeeAllHistory = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);

// Notifications - Tous les rôles (notifications personnelles)
export const canAccessNotifications = (user: User | null) => 
  hasRole(user, ['Admin', 'chef_de_service', 'Utilisateur', 'validateur', 'archiviste']);

// Workflows - Admin, chef_de_service, validateur
export const canAccessWorkflows = (user: User | null) => 
  hasRole(user, ['Admin', 'chef_de_service', 'validateur']);
export const canManageWorkflows = (user: User | null) => 
  hasRole(user, ['Admin', 'chef_de_service']);
export const canValidateWorkflows = (user: User | null) => 
  hasRole(user, ['Admin', 'chef_de_service', 'validateur']);

// Organisation - Admin uniquement
export const canAccessOrganization = (user: User | null) => hasRole(user, ['Admin']);
export const canManageOrganizations = (user: User | null) => hasRole(user, ['Admin']);

// Corbeille - Admin et archiviste
export const canAccessTrash = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);
export const canRestoreFromTrash = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);
export const canEmptyTrash = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);

// === PERMISSIONS SPÉCIFIQUES PAR FONCTIONNALITÉ ===

// Gestion des rôles
export const canManageRoles = (user: User | null) => hasRole(user, ['Admin']);

// Documents
export const canDeleteDocuments = (user: User | null) => hasRole(user, ['Admin']);
export const canValidateDocuments = (user: User | null) => hasRole(user, ['Admin', 'chef_de_service', 'validateur']);
export const canShareDocuments = (user: User | null) => hasRole(user, ['Admin', 'chef_de_service']);
export const canManageTags = (user: User | null) => hasRole(user, ['Admin', 'chef_de_service']);

// Workflows - Permissions détaillées
export const canCreateWorkflows = (user: User | null) => hasRole(user, ['Admin', 'chef_de_service']);
export const canApproveWorkflows = (user: User | null) => hasRole(user, ['Admin', 'chef_de_service', 'validateur']);
export const canRejectWorkflows = (user: User | null) => hasRole(user, ['Admin', 'chef_de_service', 'validateur']);
export const canCommentWorkflows = (user: User | null) => hasRole(user, ['Admin', 'chef_de_service', 'validateur']);
export const canSeeApprovalHistory = (user: User | null) => hasRole(user, ['Admin', 'validateur']);

// Permissions utilisateur standard
export const canSendForValidation = (user: User | null) => hasRole(user, ['Admin', 'Utilisateur']);
export const canSeeOwnDocuments = (user: User | null) => hasRole(user, ['Admin', 'Utilisateur']);
export const canEditOwnDocuments = (user: User | null) => hasRole(user, ['Admin', 'Utilisateur']);
export const canDeleteOwnDocuments = (user: User | null) => hasRole(user, ['Admin', 'Utilisateur']);
export const canTagOwnDocuments = (user: User | null) => hasRole(user, ['Admin', 'Utilisateur']);
export const canSeeOwnWorkflows = (user: User | null) => hasRole(user, ['Admin', 'Utilisateur']);

// Archives
export const canAccessArchives = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);
export const canApplyArchivingRules = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);
export const canRestoreArchives = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);
export const canDeleteArchives = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);
export const canManageArchiveCategories = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);
export const canGenerateArchiveReports = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);
export const canClassifyDocuments = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);

// Statistiques et rapports
export const canAccessAllStats = (user: User | null) => hasRole(user, ['Admin']);
export const canSeeAllArchives = (user: User | null) => hasRole(user, ['Admin', 'archiviste']);

// === HELPERS POUR LA NAVIGATION ===

// Détermine si un utilisateur peut voir un élément de menu
export const canAccessMenuItem = (user: User | null, menuItem: string): boolean => {
  switch (menuItem.toLowerCase()) {
    case 'dashboard':
    case 'tableau-de-bord':
      return canAccessDashboard(user);
    case 'users':
    case 'utilisateurs':
      return canAccessUsers(user);
    case 'my-documents':
    case 'mes-documents':
      return canAccessMyDocuments(user);
    case 'search':
    case 'recherche':
      return canAccessSearch(user);
    case 'history':
    case 'historique':
      return canAccessHistory(user);
    case 'notifications':
      return canAccessNotifications(user);
    case 'workflows':
      return canAccessWorkflows(user);
    case 'organization':
    case 'organisations':
      return canAccessOrganization(user);
    case 'trash':
    case 'corbeille':
      return canAccessTrash(user);
    default:
      return false;
  }
}; 