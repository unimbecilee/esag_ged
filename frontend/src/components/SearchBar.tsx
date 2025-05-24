import React, { useState, useEffect } from 'react';
import {
  Input,
  InputGroup,
  InputLeftElement,
  Box,
  VStack,
  Text,
  Icon,
  Flex,
  Badge,
  useDisclosure,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  Spinner,
  Divider
} from '@chakra-ui/react';
import { FiSearch, FiFile, FiUser, FiFolder } from 'react-icons/fi';
import debounce from 'lodash/debounce';
import { ElementType } from 'react';

interface SearchResult {
  type: 'document' | 'utilisateur' | 'dossier';
  id: number;
  titre?: string;
  nom?: string;
  prenom?: string;
  type_document?: string;
  date_creation?: string;
  taille_formatee?: string;
  email?: string;
  description?: string;
}

const SearchBar: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { isOpen, onOpen, onClose } = useDisclosure();

  const performSearch = async (query: string) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error("Token d'authentification non trouvé");
      }

      setIsLoading(true);
      const response = await fetch(`http://localhost:5000/api/documents/search?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }

      const data = await response.json();
      if (!Array.isArray(data)) {
        throw new Error("Format de données invalide");
      }
      setResults(data);
    } catch (error) {
      console.error('Erreur lors de la recherche:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const debouncedSearch = debounce(performSearch, 300);

  useEffect(() => {
    if (searchQuery) {
      debouncedSearch(searchQuery);
      onOpen();
    } else {
      onClose();
    }

    return () => {
      debouncedSearch.cancel();
    };
  }, [searchQuery]);

  const renderResultItem = (result: SearchResult) => {
    switch (result.type) {
      case 'document':
        return (
          <Flex key={`${result.type}-${result.id}`} align="center" p={2} _hover={{ bg: '#2a2f4a' }} cursor="pointer">
            <Icon as={FiFile as ElementType} mr={2} color="blue.400" />
            <Box>
              <Text color="white" fontWeight="medium">{result.titre}</Text>
              <Flex gap={2} mt={1}>
                <Badge colorScheme="blue">{result.type_document}</Badge>
                <Text fontSize="sm" color="gray.400">{result.taille_formatee}</Text>
              </Flex>
            </Box>
          </Flex>
        );

      case 'utilisateur':
        return (
          <Flex key={`${result.type}-${result.id}`} align="center" p={2} _hover={{ bg: '#2a2f4a' }} cursor="pointer">
            <Icon as={FiUser as ElementType} mr={2} color="green.400" />
            <Box>
              <Text color="white" fontWeight="medium">{result.prenom} {result.nom}</Text>
              <Text fontSize="sm" color="gray.400">{result.email}</Text>
            </Box>
          </Flex>
        );

      case 'dossier':
        return (
          <Flex key={`${result.type}-${result.id}`} align="center" p={2} _hover={{ bg: '#2a2f4a' }} cursor="pointer">
            <Icon as={FiFolder as ElementType} mr={2} color="yellow.400" />
            <Box>
              <Text color="white" fontWeight="medium">{result.titre}</Text>
              <Text fontSize="sm" color="gray.400">{result.description}</Text>
            </Box>
          </Flex>
        );

      default:
        return null;
    }
  };

  return (
    <Box width="100%" maxW="600px">
      <Popover
        isOpen={isOpen && searchQuery.length > 0}
        onClose={onClose}
        placement="bottom-start"
        autoFocus={false}
      >
        <PopoverTrigger>
          <InputGroup>
            <InputLeftElement pointerEvents="none">
              <Icon as={FiSearch as ElementType} color="gray.400" />
            </InputLeftElement>
            <Input
              placeholder="Rechercher documents, utilisateurs, dossiers..."
              bg="#232946"
              border="1px solid"
              borderColor="#2a2f4a"
              _hover={{ borderColor: '#3c4269' }}
              _focus={{ borderColor: '#4299E1', boxShadow: 'none' }}
              color="white"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </InputGroup>
        </PopoverTrigger>
        <PopoverContent bg="#232946" borderColor="#2a2f4a" maxH="400px" overflowY="auto">
          <PopoverBody p={0}>
            {isLoading ? (
              <Flex justify="center" align="center" p={4}>
                <Spinner color="blue.400" />
              </Flex>
            ) : results.length > 0 ? (
              <VStack spacing={0} align="stretch" divider={<Divider borderColor="#2a2f4a" />}>
                {results.map(renderResultItem)}
              </VStack>
            ) : searchQuery ? (
              <Text color="gray.400" p={4} textAlign="center">
                Aucun résultat trouvé
              </Text>
            ) : null}
          </PopoverBody>
        </PopoverContent>
      </Popover>
    </Box>
  );
};

export default SearchBar; 