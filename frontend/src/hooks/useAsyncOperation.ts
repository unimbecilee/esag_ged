import { useState } from 'react';
import { useToast } from '@chakra-ui/react';

interface AsyncOperationOptions {
  loadingMessage?: string;
  successMessage?: string;
  errorMessage?: string;
  showLoading?: boolean;
  showSuccess?: boolean;
  showError?: boolean;
}

interface AsyncOperationState {
  isLoading: boolean;
  error: string | null;
  isSuccess: boolean;
}

export const useAsyncOperation = () => {
  const [state, setState] = useState<AsyncOperationState>({
    isLoading: false,
    error: null,
    isSuccess: false
  });
  
  const toast = useToast();

  const executeOperation = async <T>(
    operation: () => Promise<T>,
    options: AsyncOperationOptions = {}
  ): Promise<T | null> => {
    const {
      loadingMessage = "Opération en cours...",
      successMessage,
      errorMessage = "Une erreur est survenue",
      showLoading = false,
      showSuccess = true,
      showError = true
    } = options;

    setState({ isLoading: true, error: null, isSuccess: false });

    let toastId: string | number | undefined;

    try {
      // Afficher le toast de loading si demandé
      if (showLoading && loadingMessage) {
        toastId = toast({
          title: loadingMessage,
          status: "loading",
          duration: null,
          isClosable: false,
        });
      }

      // Exécuter l'opération
      const result = await operation();

      // Fermer le toast de loading
      if (toastId) {
        toast.close(toastId);
      }

      // Afficher le toast de succès
      if (showSuccess && successMessage) {
        toast({
          title: "Succès",
          description: successMessage,
          status: "success",
          duration: 4000,
          isClosable: true,
        });
      }

      setState({ isLoading: false, error: null, isSuccess: true });
      return result;

    } catch (error) {
      // Fermer le toast de loading
      if (toastId) {
        toast.close(toastId);
      }

      const errorMsg = error instanceof Error ? error.message : errorMessage;
      
      // Afficher le toast d'erreur
      if (showError) {
        toast({
          title: "Erreur",
          description: errorMsg,
          status: "error",
          duration: 6000,
          isClosable: true,
        });
      }

      setState({ isLoading: false, error: errorMsg, isSuccess: false });
      return null;
    }
  };

  const resetState = () => {
    setState({ isLoading: false, error: null, isSuccess: false });
  };

  return {
    ...state,
    executeOperation,
    resetState
  };
};

// Hook spécialisé pour les opérations de fichiers
export const useFileOperation = () => {
  const { executeOperation, ...state } = useAsyncOperation();

  const uploadFile = async (
    file: File,
    uploadFn: (file: File) => Promise<any>,
    options?: AsyncOperationOptions
  ) => {
    return executeOperation(
      () => uploadFn(file),
      {
        loadingMessage: `Upload de ${file.name}...`,
        successMessage: `${file.name} uploadé avec succès`,
        errorMessage: `Erreur lors de l'upload de ${file.name}`,
        showLoading: true,
        ...options
      }
    );
  };

  const downloadFile = async (
    documentId: number,
    fileName: string,
    downloadFn: (id: number) => Promise<Blob>,
    options?: AsyncOperationOptions
  ) => {
    return executeOperation(
      async () => {
        const blob = await downloadFn(documentId);
        
        // Créer et déclencher le téléchargement
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        return blob;
      },
      {
        loadingMessage: `Téléchargement de ${fileName}...`,
        successMessage: `${fileName} téléchargé avec succès`,
        errorMessage: `Erreur lors du téléchargement de ${fileName}`,
        ...options
      }
    );
  };

  return {
    ...state,
    executeOperation,
    uploadFile,
    downloadFile
  };
};

// Hook pour les opérations de recherche avec debounce
export const useSearchOperation = (debounceMs: number = 300) => {
  const { executeOperation, ...state } = useAsyncOperation();
  const [searchTerm, setSearchTerm] = useState('');
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);

  const performSearch = async (
    term: string,
    searchFn: (term: string) => Promise<any>,
    options?: AsyncOperationOptions
  ) => {
    // Annuler le timer précédent
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // Créer un nouveau timer
    const timer = setTimeout(() => {
      if (term.trim()) {
        executeOperation(
          () => searchFn(term),
          {
            loadingMessage: `Recherche de "${term}"...`,
            showLoading: false,
            showSuccess: false,
            showError: true,
            ...options
          }
        );
      }
    }, debounceMs);

    setDebounceTimer(timer);
    setSearchTerm(term);
  };

  return {
    ...state,
    searchTerm,
    executeOperation,
    performSearch
  };
};

export default useAsyncOperation; 
