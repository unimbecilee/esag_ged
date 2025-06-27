import { useCallback } from 'react';
import { useLoading } from '../contexts/LoadingContext';
import { useToast } from '@chakra-ui/react';
import { getErrorMessage } from '../utils/errorHandling';

interface UseLoadingStateOptions {
  loadingMessage?: string;
  successMessage?: string;
  errorMessage?: string;
}

export const useLoadingState = () => {
  const { isLoading, showLoading, hideLoading } = useLoading();
  const toast = useToast();

  const withLoading = useCallback(async <T>(
    asyncFunction: () => Promise<T>,
    {
      loadingMessage = "Chargement en cours...",
      successMessage = "",
      errorMessage = "Une erreur est survenue"
    }: UseLoadingStateOptions = {}
  ): Promise<T | undefined> => {
    try {
      showLoading(loadingMessage);
      
      const result = await asyncFunction();
      
      if (successMessage) {
        toast({
          title: "Succès",
          description: successMessage,
          status: "success",
          duration: 5000,
          isClosable: true,
        });
      }
      
      return result;
    } catch (error: unknown) {
      toast({
        title: "Erreur",
        description: getErrorMessage(error, errorMessage),
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      return undefined;
    } finally {
      hideLoading();
    }
  }, [showLoading, hideLoading, toast]);

  return { isLoading, withLoading };
}; 
