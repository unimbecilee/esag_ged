import React from "react";
import {
  Box,
  VStack,
  Icon,
  Text,
  Flex,
  Button,
  useColorModeValue,
} from "@chakra-ui/react";
import {
  FiHome,
  FiUsers,
  FiFileText,
  FiSearch,
  FiTrash2,
  FiFolder,
  FiClock,
  FiShare2,
  FiSettings,
  FiGitBranch,
  FiBriefcase,
  FiLogOut,
} from "react-icons/fi";
import { IconType } from "react-icons";
import { useNavigate, useLocation } from "react-router-dom";
import { ElementType } from "react";

interface NavItemProps {
  icon: IconType;
  children: React.ReactNode;
  to: string;
  isActive: boolean;
}

const NavItem: React.FC<NavItemProps> = ({ icon, children, to, isActive }) => {
  const navigate = useNavigate();

  return (
    <Button
      w="full"
      variant="ghost"
      justifyContent="flex-start"
      alignItems="center"
      px={6}
      py={4}
      bg={isActive ? "#3a8bfd" : "transparent"}
      color={isActive ? "white" : "gray.400"}
      _hover={{
        bg: isActive ? "#3a8bfd" : "rgba(58, 139, 253, 0.1)",
        color: isActive ? "white" : "white",
      }}
      onClick={() => navigate(to)}
      transition="all 0.2s"
      fontSize="md"
      h="auto"
    >
      <Icon as={icon as ElementType} boxSize={6} mr={4} />
      <Text fontWeight={isActive ? "bold" : "normal"}>
        {children}
      </Text>
    </Button>
  );
};

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    { icon: FiHome, label: "Tableau de bord", path: "/dashboard" },
    { icon: FiUsers, label: "Utilisateurs", path: "/users" },
    { icon: FiFileText, label: "Scanner", path: "/scan" },
    { icon: FiSearch, label: "Rechercher", path: "/search" },
    { icon: FiTrash2, label: "Corbeille", path: "/trash" },
    { icon: FiFolder, label: "Mes Documents", path: "/my-documents" },
    { icon: FiClock, label: "Historique", path: "/history" },
    { icon: FiShare2, label: "Partagés", path: "/shared" },
    { icon: FiGitBranch, label: "Workflows", path: "/workflow" },
    { icon: FiBriefcase, label: "Organisation", path: "/organization" },
    { icon: FiSettings, label: "Paramètres", path: "/settings" },
  ];

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.reload();
  };

  return (
    <Box
      w={{ base: "full", md: "260px" }}
      bg="#181c2f"
      h="100vh"
      pos="fixed"
      left={0}
      top={0}
      borderRight="1px solid #232946"
      display="flex"
      flexDirection="column"
    >
      {/* Logo */}
      <Flex align="center" p={5} justify="center">
        <Box
          bgGradient="linear(to-br, #3a8bfd, #6f6cff)"
          borderRadius="full"
          w="44px"
          h="44px"
          display="flex"
          alignItems="center"
          justifyContent="center"
          boxShadow="0 0 0 4px #fff3"
          mr={3}
        >
          <Text
            fontWeight="bold"
            color="white"
            fontSize="2xl"
            letterSpacing="2px"
          >
            E
          </Text>
        </Box>
        <Text
          fontWeight="bold"
          fontSize="2xl"
          bgGradient="linear(to-r, #3a8bfd, #ffe066)"
          bgClip="text"
        >
          ESAG GED
        </Text>
      </Flex>

      {/* Navigation Items */}
      <VStack spacing={1} align="stretch" px={2} flex={1}>
        {navItems.map((item) => (
          <NavItem
            key={item.path}
            icon={item.icon}
            to={item.path}
            isActive={location.pathname === item.path}
          >
            {item.label}
          </NavItem>
        ))}
      </VStack>

      {/* User Profile Section */}
      <Box p={4} borderTop="1px solid #232946">
        <Flex align="center" mb={4}>
          <Box
            bgGradient="linear(to-br, #3a8bfd, #6f6cff)"
            borderRadius="full"
            w="32px"
            h="32px"
            display="flex"
            alignItems="center"
            justifyContent="center"
            mr={2}
          >
            <Text color="white" fontWeight="bold" fontSize="md">
              U
            </Text>
          </Box>
          <Box flex={1}>
            <Text color="white" fontWeight="bold" fontSize="sm">
              Mon Compte
            </Text>
          </Box>
        </Flex>
        <Button
          w="full"
          leftIcon={<Icon as={FiLogOut as ElementType} />}
          variant="solid"
          colorScheme="red"
          size="md"
          onClick={handleLogout}
          bg="rgba(255, 0, 0, 0.2)"
          _hover={{
            bg: "rgba(255, 0, 0, 0.3)",
          }}
        >
          Déconnexion
        </Button>
      </Box>
    </Box>
  );
};

export const SidebarContent = Sidebar;
