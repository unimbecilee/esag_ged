/**
 * Utilitaire pour la gestion des erreurs dans l'application
 */

/**
 * Extrait le message d'erreur d'une erreur inconnue
 * @param error L'erreur à traiter
 * @param defaultMessage Message par défaut si l'erreur n'a pas de message
 * @returns Le message d'erreur formaté
 */
export const getErrorMessage = (error: unknown, defaultMessage: string = "Une erreur est survenue"): string => {
  if (error instanceof Error) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as { message: unknown }).message);
  }
  
  return defaultMessage;
};

/**
 * Vérifie si un token est présent dans le localStorage
 * @returns Le token s'il existe, sinon lance une erreur
 */
export const checkAuthToken = (): string => {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Token d\'authentification non trouvé');
  }
  return token;
};

/**
 * Gère les erreurs de réponse HTTP
 * @param response La réponse HTTP
 * @param defaultErrorMessage Message d'erreur par défaut
 */
export const handleHttpError = async (response: Response, defaultErrorMessage: string): Promise<void> => {
  if (!response.ok) {
    let errorMessage = defaultErrorMessage;
    try {
      const errorData = await response.json();
      if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // Si on ne peut pas parser le JSON, on utilise le message par défaut
    }
    throw new Error(errorMessage);
  }
}; 
