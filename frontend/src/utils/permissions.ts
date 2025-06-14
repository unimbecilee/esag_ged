// Helpers de gestion des rôles et permissions
import { User } from '../contexts/AuthContext';

export const hasRole = (user: User | null, roles: string[]): boolean => {
  if (!user || !user.role) return false;
  return roles.includes(user.role.toLowerCase());
};

export const canManageUsers = (user: User | null) => hasRole(user, ['admin']);
export const canManageRoles = (user: User | null) => hasRole(user, ['admin']);
export const canManageOrganizations = (user: User | null) => hasRole(user, ['admin']);
export const canManageWorkflows = (user: User | null) => hasRole(user, ['admin']);
export const canDeleteDocuments = (user: User | null) => hasRole(user, ['admin']);
export const canSeeAllArchives = (user: User | null) => hasRole(user, ['admin', 'archiviste']);
export const canAccessAllStats = (user: User | null) => hasRole(user, ['admin']);

export const canValidateDocuments = (user: User | null) => hasRole(user, ['admin', 'chef_de_service', 'validateur']);
export const canFollowWorkflows = (user: User | null) => hasRole(user, ['admin', 'chef_de_service']);
export const canManageTags = (user: User | null) => hasRole(user, ['admin', 'chef_de_service']);
export const canShareDocuments = (user: User | null) => hasRole(user, ['admin', 'chef_de_service']);
export const canCommentWorkflows = (user: User | null) => hasRole(user, ['admin', 'chef_de_service', 'validateur']);

export const canApprove = (user: User | null) => hasRole(user, ['admin', 'validateur']);
export const canReject = (user: User | null) => hasRole(user, ['admin', 'validateur']);
export const canSeeApprovalHistory = (user: User | null) => hasRole(user, ['admin', 'validateur']);

export const canSendForValidation = (user: User | null) => hasRole(user, ['admin', 'utilisateur']);
export const canSeeOwnDocuments = (user: User | null) => hasRole(user, ['admin', 'utilisateur']);
export const canEditOwnDocuments = (user: User | null) => hasRole(user, ['admin', 'utilisateur']);
export const canDeleteOwnDocuments = (user: User | null) => hasRole(user, ['admin', 'utilisateur']);
export const canTagOwnDocuments = (user: User | null) => hasRole(user, ['admin', 'utilisateur']);
export const canSeeOwnWorkflows = (user: User | null) => hasRole(user, ['admin', 'utilisateur']);

export const canAccessArchives = (user: User | null) => hasRole(user, ['admin', 'archiviste']);
export const canApplyArchivingRules = (user: User | null) => hasRole(user, ['admin', 'archiviste']);
export const canRestoreArchives = (user: User | null) => hasRole(user, ['admin', 'archiviste']);
export const canDeleteArchives = (user: User | null) => hasRole(user, ['admin', 'archiviste']);
export const canManageArchiveCategories = (user: User | null) => hasRole(user, ['admin', 'archiviste']);
export const canGenerateArchiveReports = (user: User | null) => hasRole(user, ['admin', 'archiviste']);
export const canClassifyDocuments = (user: User | null) => hasRole(user, ['admin', 'archiviste']); 