/**
 * Formate une taille de fichier en bytes en une chaîne lisible
 * @param bytes - Taille en bytes
 * @returns Chaîne formatée (ex: "1.5 MB")
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Formate une date en format lisible
 * @param dateString - La date à formater
 * @returns La date formatée
 */
export const formatDate = (dateString: string): string => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

/**
 * Obtient la couleur correspondant au statut d'un document
 * @param status - Le statut du document
 * @returns La couleur correspondante
 */
export const getStatusColor = (status?: string): string => {
  if (!status) return 'gray';
  
  switch (status.toUpperCase()) {
    case 'BROUILLON':
      return 'gray';
    case 'EN_VALIDATION':
      return 'orange';
    case 'APPROUVE':
      return 'green';
    case 'REJETE':
      return 'red';
    case 'ARCHIVE':
      return 'blue';
    default:
      return 'gray';
  }
};

/**
 * Obtient le libellé correspondant au statut d'un document
 * @param status - Le statut du document
 * @returns Le libellé correspondant
 */
export const getStatusLabel = (status?: string): string => {
  if (!status) return 'Brouillon';
  
  switch (status.toUpperCase()) {
    case 'BROUILLON':
      return 'Brouillon';
    case 'EN_VALIDATION':
      return 'En validation';
    case 'APPROUVE':
      return 'Approuvé';
    case 'REJETE':
      return 'Rejeté';
    case 'ARCHIVE':
      return 'Archivé';
    default:
      return status;
  }
}; 