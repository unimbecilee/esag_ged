import React from "react";
import {
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Flex,
  Icon,
  Text,
  VStack,
  HStack,
  Progress,
  Tooltip,
  CircularProgress,
  CircularProgressLabel
} from "@chakra-ui/react";
import { FiFileText, FiCpu, FiStar, FiEye } from "react-icons/fi";
import { ElementType } from "react";
import ActionMenu from "./ActionMenu";

interface Document {
  id: number;
  titre: string;
  type_document: string;
  taille_formatee: string;
  date_creation: string | null;
  proprietaire_nom?: string;
  proprietaire_prenom?: string;
  statut?: string;
  relevance_score?: number;
  matched_content?: string;
  highlight_snippets?: string[];
  has_ocr?: boolean;
  ocr_confidence?: number;
  ocr_preview?: string;
}

interface DocumentListProps {
  documents: Document[];
  onPreview: (documentId: number, title?: string) => void;
  onOCR: (documentId: number, title?: string) => void;
  onDownload: (documentId: number) => void;
  onShare: (documentId: number) => void;
  onEdit: (documentId: number) => void;
  onDelete: (documentId: number) => void;
  showOwner?: boolean;
  showRelevance?: boolean;
  showSnippets?: boolean;
}

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return 'Non définie';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return 'Date invalide';
  }
};

const getTypeColor = (type: string | null | undefined) => {
  if (!type) return 'gray';
  
  switch (type.toLowerCase()) {
    case 'pdf': return 'red';
    case 'doc':
    case 'docx': return 'blue';
    case 'xls':
    case 'xlsx': return 'green';
    case 'ppt':
    case 'pptx': return 'orange';
    case 'txt': return 'gray';
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
    case 'tiff':
    case 'bmp': return 'purple';
    default: return 'gray';
  }
};

const getStatusColor = (status: string) => {
  switch (status?.toLowerCase()) {
    case 'actif': return 'green';
    case 'archivé': return 'gray';
    case 'brouillon': return 'orange';
    case 'en révision': return 'blue';
    case 'approuvé': return 'green';
    case 'publié': return 'teal';
    default: return 'gray';
  }
};

const getOCRConfidenceColor = (confidence: number) => {
  if (confidence >= 90) return 'green';
  if (confidence >= 70) return 'yellow';
  if (confidence >= 50) return 'orange';
  return 'red';
};

const getRelevanceColor = (score: number) => {
  if (score >= 1.5) return 'green';
  if (score >= 1.0) return 'yellow';
  if (score >= 0.8) return 'orange';
  return 'gray';
};

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onPreview,
  onOCR,
  onDownload,
  onShare,
  onEdit,
  onDelete,
  showOwner = false,
  showRelevance = false,
  showSnippets = false
}) => {
  if (documents.length === 0) {
    return (
      <Flex
        justify="center"
        align="center"
        direction="column"
        h="200px"
        color="gray.400"
      >
        <Icon as={FiFileText as ElementType} boxSize={12} mb={4} />
        <Text>Aucun document trouvé</Text>
      </Flex>
    );
  }

  return (
    <Box bg="#2a3657" borderRadius="lg" overflow="hidden" shadow="md">
      <Table variant="simple" size="sm">
        <Thead bg="#1c2338">
          <Tr>
            <Th color="white" borderColor="#3a445e">Document</Th>
            <Th color="white" borderColor="#3a445e">Type & OCR</Th>
            {showOwner && <Th color="white" borderColor="#3a445e">Propriétaire</Th>}
            <Th color="white" borderColor="#3a445e">Date création</Th>
            <Th color="white" borderColor="#3a445e">Taille</Th>
            {showRelevance && <Th color="white" borderColor="#3a445e">Pertinence</Th>}
            <Th color="white" borderColor="#3a445e">Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {documents.map((doc) => (
            <Tr key={`doc-${doc.id}`} _hover={{ bg: "#374269" }}>
              <Td color="white" borderColor="#3a445e" minW="250px">
                <VStack align="start" spacing={2}>
                  <Flex align="center" w="full">
                    <Icon as={FiFileText as ElementType} mr={2} color="#3a8bfd" />
                    <Text fontWeight="bold" fontSize="sm" noOfLines={2} flex={1}>
                      {doc.titre}
                    </Text>
                  </Flex>
                  
                  <HStack spacing={2} wrap="wrap">
                    {doc.statut && (
                      <Badge size="xs" colorScheme={getStatusColor(doc.statut)}>
                        {doc.statut}
                      </Badge>
                    )}
                    
                    {doc.has_ocr && (
                      <Tooltip label={`OCR disponible - Confiance: ${doc.ocr_confidence?.toFixed(1) || 0}%`}>
                        <Badge size="xs" colorScheme="purple" display="flex" alignItems="center" gap={1}>
                          <Icon as={FiCpu as ElementType} />
                          OCR
                        </Badge>
                      </Tooltip>
                    )}
                    
                    {showRelevance && doc.relevance_score && doc.relevance_score > 1.0 && (
                      <Tooltip label={`Score de pertinence: ${doc.relevance_score.toFixed(2)}`}>
                        <Badge size="xs" colorScheme="yellow" display="flex" alignItems="center" gap={1}>
                          <Icon as={FiStar as ElementType} />
                          Top
                        </Badge>
                      </Tooltip>
                    )}
                  </HStack>
                  
                  {showSnippets && doc.matched_content && (
                    <Text fontSize="xs" color="gray.400" noOfLines={2} fontStyle="italic">
                      📄 {doc.matched_content}
                    </Text>
                  )}
                  
                  {showSnippets && doc.ocr_preview && (
                    <Text fontSize="xs" color="purple.300" noOfLines={2} fontStyle="italic">
                      🔍 OCR: {doc.ocr_preview}
                    </Text>
                  )}
                  
                  {showSnippets && doc.highlight_snippets && doc.highlight_snippets.length > 0 && (
                    <VStack align="start" spacing={1} w="full">
                      {doc.highlight_snippets.slice(0, 3).map((snippet, index) => (
                        <Box
                          key={index}
                          bg="rgba(255, 255, 0, 0.1)"
                          px={2}
                          py={1}
                          borderRadius="md"
                          borderLeft="3px solid"
                          borderLeftColor="yellow.400"
                          w="full"
                        >
                          <Text
                            fontSize="xs"
                            color="yellow.200"
                            noOfLines={1}
                          >
                            💡 {snippet}
                          </Text>
                        </Box>
                      ))}
                    </VStack>
                  )}
                </VStack>
              </Td>
              
              <Td color="white" borderColor="#3a445e">
                <VStack align="start" spacing={2}>
                  <Badge colorScheme={getTypeColor(doc.type_document)} size="sm">
                    {doc.type_document || "Non défini"}
                  </Badge>
                  
                  {doc.has_ocr && doc.ocr_confidence !== undefined && (
                    <Tooltip label={`Confiance OCR: ${doc.ocr_confidence.toFixed(1)}%`}>
                      <Box>
                        <CircularProgress
                          value={doc.ocr_confidence}
                          color={getOCRConfidenceColor(doc.ocr_confidence)}
                          size="30px"
                          thickness="8px"
                        >
                          <CircularProgressLabel fontSize="8px" fontWeight="bold">
                            {Math.round(doc.ocr_confidence)}%
                          </CircularProgressLabel>
                        </CircularProgress>
                      </Box>
                    </Tooltip>
                  )}
                </VStack>
              </Td>
              
              {showOwner && (
                <Td color="white" borderColor="#3a445e">
                  <Text fontSize="sm">
                    {doc.proprietaire_prenom && doc.proprietaire_nom
                      ? `${doc.proprietaire_prenom} ${doc.proprietaire_nom}`
                      : "Non défini"
                    }
                  </Text>
                </Td>
              )}
              
              <Td color="white" borderColor="#3a445e">
                <Text fontSize="sm" color="gray.300">
                  {formatDate(doc.date_creation)}
                </Text>
              </Td>
              
              <Td color="white" borderColor="#3a445e">
                <Text fontSize="sm" fontWeight="medium">
                  {doc.taille_formatee}
                </Text>
              </Td>
              
              {showRelevance && (
                <Td color="white" borderColor="#3a445e">
                  {doc.relevance_score !== undefined && (
                    <VStack align="center" spacing={1}>
                      <CircularProgress
                        value={(doc.relevance_score / 2.0) * 100}  // Normaliser sur 2.0 max
                        color={getRelevanceColor(doc.relevance_score)}
                        size="35px"
                        thickness="6px"
                      >
                        <CircularProgressLabel fontSize="10px" fontWeight="bold">
                          {doc.relevance_score.toFixed(1)}
                        </CircularProgressLabel>
                      </CircularProgress>
                      
                      <Progress
                        value={(doc.relevance_score / 2.0) * 100}
                        colorScheme={getRelevanceColor(doc.relevance_score)}
                        size="xs"
                        w="40px"
                        borderRadius="md"
                      />
                    </VStack>
                  )}
                </Td>
              )}
              
              <Td color="white" borderColor="#3a445e">
                <Flex justify="center">
                  <ActionMenu
                    documentId={doc.id}
                    documentTitle={doc.titre}
                    onDownload={onDownload}
                    onShare={onShare}
                    onEdit={onEdit}
                    onDelete={onDelete}
                    onShowPreview={onPreview}
                    onShowOCR={onOCR}
                  />
                </Flex>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
      
      {/* Footer avec statistiques rapides */}
      <Box bg="#1c2338" p={3} borderTop="1px solid #3a445e">
        <HStack justify="space-between" fontSize="xs" color="gray.400">
          <Text>
            📄 {documents.length} document{documents.length > 1 ? 's' : ''}
          </Text>
          
          {documents.some(doc => doc.has_ocr) && (
            <Text>
              🤖 {documents.filter(doc => doc.has_ocr).length} avec OCR
            </Text>
          )}
          
          {showRelevance && documents.some(doc => doc.relevance_score && doc.relevance_score > 1.0) && (
            <Text>
              ⭐ {documents.filter(doc => doc.relevance_score && doc.relevance_score > 1.0).length} très pertinent{documents.filter(doc => doc.relevance_score && doc.relevance_score > 1.0).length > 1 ? 's' : ''}
            </Text>
          )}
          
          {documents.some(doc => doc.highlight_snippets && doc.highlight_snippets.length > 0) && (
            <Text>
              💡 {documents.filter(doc => doc.highlight_snippets && doc.highlight_snippets.length > 0).length} avec extraits
            </Text>
          )}
        </HStack>
      </Box>
    </Box>
  );
};

export default DocumentList;

