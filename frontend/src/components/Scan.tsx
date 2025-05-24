import React, { useState } from "react";
import {
  Box,
  Button,
  Heading,
  VStack,
  Text,
  useToast,
  Flex,
  Icon,
  Input,
  FormControl,
  FormLabel,
  Select,
} from "@chakra-ui/react";
import { FiUpload, FiCamera, FiFileText } from "react-icons/fi";
import { ElementType } from "react";

const Scan: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState("");
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFile || !documentType) {
      toast({
        title: "Erreur",
        description: "Veuillez sélectionner un fichier et un type de document",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("type", documentType);

    try {
      const response = await fetch("http://localhost:5000/api/documents/scan", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: formData,
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Document numérisé avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        setSelectedFile(null);
        setDocumentType("");
      } else {
        throw new Error("Erreur lors de la numérisation");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de numériser le document",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Heading color="white" mb={6}>
        Numérisation de Documents
      </Heading>

      <Box bg="#20243a" borderRadius="lg" p={6}>
        <form onSubmit={handleSubmit}>
          <VStack spacing={6}>
            <FormControl isRequired>
              <FormLabel color="white">Type de document</FormLabel>
              <Select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                bg="#232946"
                color="white"
                borderColor="#232946"
                _hover={{ borderColor: "#3a8bfd" }}
                _focus={{
                  borderColor: "#3a8bfd",
                  boxShadow: "0 0 0 1.5px #3a8bfd",
                }}
              >
                <option value="">Sélectionner un type</option>
                <option value="facture">Facture</option>
                <option value="contrat">Contrat</option>
                <option value="rapport">Rapport</option>
                <option value="autre">Autre</option>
              </Select>
            </FormControl>

            <FormControl isRequired>
              <FormLabel color="white">Document à numériser</FormLabel>
              <Flex
                border="2px dashed"
                borderColor="#3a8bfd"
                borderRadius="md"
                p={6}
                justify="center"
                align="center"
                direction="column"
                cursor="pointer"
                onClick={() => document.getElementById("fileInput")?.click()}
                _hover={{ borderColor: "#6f6cff" }}
              >
                <Input
                  type="file"
                  id="fileInput"
                  display="none"
                  onChange={handleFileChange}
                  accept=".pdf,.jpg,.jpeg,.png"
                />
                <Icon
                  as={FiUpload as ElementType}
                  boxSize={8}
                  color="#3a8bfd"
                  mb={2}
                />
                <Icon
                  as={(selectedFile ? FiFileText : FiCamera) as ElementType}
                  boxSize={8}
                  color="#3a8bfd"
                  mb={2}
                />
                <Text color="white" textAlign="center">
                  {selectedFile
                    ? selectedFile.name
                    : "Cliquez pour sélectionner un fichier"}
                </Text>
                <Text color="gray.400" fontSize="sm" mt={1}>
                  PDF, JPG, JPEG, PNG
                </Text>
              </Flex>
            </FormControl>

            <Button
              type="submit"
              colorScheme="blue"
              bgGradient="linear(to-r, #3a8bfd, #6f6cff)"
              _hover={{ bgGradient: "linear(to-r, #6f6cff, #3a8bfd)" }}
              size="lg"
              width="full"
              isLoading={loading}
              leftIcon={<Icon as={FiUpload as ElementType} />}
            >
              Numériser
            </Button>
          </VStack>
        </form>
      </Box>
    </Box>
  );
};

export default Scan; 