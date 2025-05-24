import React, { useState, useEffect } from "react";
import {
  Box,
  Heading,
  VStack,
  Text,
  Button,
  useToast,
  Flex,
  Icon,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Select,
  Input,
} from "@chakra-ui/react";
import { FiGitBranch, FiPlus, FiTrash2, FiEdit2 } from "react-icons/fi";
import { ElementType } from "react";

interface WorkflowStep {
  id: number;
  nom: string;
  description: string;
  ordre: number;
  statut: string;
}

interface Workflow {
  id: number;
  nom: string;
  description: string;
  etapes: WorkflowStep[];
  date_creation: string;
}

const Workflow: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const toast = useToast();

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/workflows", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setWorkflows(data);
      } else {
        throw new Error("Erreur lors de la récupération des workflows");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les workflows",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkflow = () => {
    setSelectedWorkflow(null);
    setIsModalOpen(true);
  };

  const handleEditWorkflow = (workflow: Workflow) => {
    setSelectedWorkflow(workflow);
    setIsModalOpen(true);
  };

  const handleDeleteWorkflow = async (workflowId: number) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer ce workflow ?")) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:5000/api/workflows/${workflowId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        toast({
          title: "Succès",
          description: "Workflow supprimé avec succès",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
        fetchWorkflows();
      } else {
        throw new Error("Erreur lors de la suppression");
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le workflow",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading color="white" size="lg">
          Gestion des Workflows
        </Heading>
        <Button
          leftIcon={<Icon as={FiPlus as ElementType} />}
          colorScheme="blue"
          onClick={handleCreateWorkflow}
        >
          Nouveau Workflow
        </Button>
      </Flex>

      {loading ? (
        <Text color="white" textAlign="center">
          Chargement...
        </Text>
      ) : workflows.length === 0 ? (
        <Box
          bg="#20243a"
          borderRadius="lg"
          p={6}
          textAlign="center"
          color="white"
        >
          <Icon
            as={FiGitBranch as ElementType}
            boxSize={8}
            color="gray.400"
            mb={2}
          />
          <Text>Aucun workflow trouvé</Text>
        </Box>
      ) : (
        <Box bg="#20243a" borderRadius="lg" p={6} overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th color="white">Nom</Th>
                <Th color="white">Description</Th>
                <Th color="white">Nombre d'étapes</Th>
                <Th color="white">Date de création</Th>
                <Th color="white">Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {workflows.map((workflow) => (
                <Tr key={workflow.id}>
                  <Td color="white">{workflow.nom}</Td>
                  <Td color="white">{workflow.description}</Td>
                  <Td color="white">{workflow.etapes.length}</Td>
                  <Td color="white">
                    {new Date(workflow.date_creation).toLocaleDateString()}
                  </Td>
                  <Td>
                    <Flex>
                      <Button
                        size="sm"
                        leftIcon={<Icon as={FiEdit2 as ElementType} />}
                        colorScheme="blue"
                        variant="ghost"
                        mr={2}
                        onClick={() => handleEditWorkflow(workflow)}
                      >
                        Modifier
                      </Button>
                      <Button
                        size="sm"
                        leftIcon={<Icon as={FiTrash2 as ElementType} />}
                        colorScheme="red"
                        variant="ghost"
                        onClick={() => handleDeleteWorkflow(workflow.id)}
                      >
                        Supprimer
                      </Button>
                    </Flex>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="xl">
        <ModalOverlay />
        <ModalContent bg="#20243a" color="white">
          <ModalHeader>
            {selectedWorkflow ? "Modifier le workflow" : "Nouveau workflow"}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4}>
              <FormControl>
                <FormLabel>Nom</FormLabel>
                <Input
                  placeholder="Nom du workflow"
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Description</FormLabel>
                <Input
                  placeholder="Description du workflow"
                  bg="#232946"
                  borderColor="#232946"
                  _hover={{ borderColor: "#3a8bfd" }}
                  _focus={{
                    borderColor: "#3a8bfd",
                    boxShadow: "0 0 0 1.5px #3a8bfd",
                  }}
                />
              </FormControl>
              <Button
                colorScheme="blue"
                width="full"
                mt={4}
                onClick={() => {
                  // Implémenter la logique de sauvegarde
                  setIsModalOpen(false);
                }}
              >
                {selectedWorkflow ? "Mettre à jour" : "Créer"}
              </Button>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Workflow; 