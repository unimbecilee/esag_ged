import { useToast } from '@chakra-ui/react';

interface OperationOptions {
  loadingMessage?: string;
  successMessage?: string;
  errorMessage?: string;
}

interface OperationResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export const executeOperation = async <T>(
  operation: () => Promise<T>,
  options: OperationOptions = {}
): Promise<T | null> => {
  try {
    const result = await operation();
    return result;
  } catch (error) {
    console.error('Operation failed:', error);
    throw error;
  }
};

// Hook pour utiliser executeOperation avec toast
export const useExecuteOperation = () => {
  const toast = useToast();

  const execute = async <T>(
    operation: () => Promise<T>,
    options: OperationOptions = {}
  ): Promise<T | null> => {
    try {
      if (options.loadingMessage) {
        toast({
          title: options.loadingMessage,
          status: "loading",
          duration: null,
          isClosable: false,
        });
      }

      const result = await operation();

      toast.closeAll();

      if (options.successMessage) {
        toast({
          title: options.successMessage,
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      }

      return result;
    } catch (error) {
      toast.closeAll();

      const errorMessage = options.errorMessage || 
        (error instanceof Error ? error.message : 'Une erreur est survenue');
      
      toast({
        title: "Erreur",
        description: errorMessage,
        status: "error",
        duration: 5000,
        isClosable: true,
      });

      return null;
    }
  };

  return { execute };
}; 