import React, { useState, useEffect } from "react";
import {
  Box,
  VStack,
  Icon,
  Text,
  Flex,
  Button,
  useColorModeValue,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Collapse,
  Divider,
} from "@chakra-ui/react";
import {
  FiHome,
  FiUsers,
  FiSearch,
  FiTrash2,
  FiFolder,
  FiClock,
  FiShare2,
  FiSettings,
  FiGitBranch,
  FiBriefcase,
  FiLogOut,
  FiChevronDown,
  FiChevronRight,
  FiHeart,
  FiStar,
} from "react-icons/fi";
import { IconType } from "react-icons";
import { useNavigate, useLocation } from "react-router-dom";
import { ElementType } from "react";
import config from '../config';
import { useAuth } from '../contexts/AuthContext';
import {
  canAccessUsers,
  canAccessHistory,
  canAccessNotifications,
  canAccessWorkflows,
  canAccessOrganization,
  canAccessTrash,
  canAccessSearch,
  canAccessMyDocuments,
} from '../utils/permissions';

interface NavItemProps {
  icon: IconType;
  children: React.ReactNode;
  to: string;
  isActive: boolean;
  badge?: number;
}

const NavItem: React.FC<NavItemProps> = ({ icon, children, to, isActive, badge }) => {
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
      color={isActive ? "white" : "gray.300"}
      _hover={{
        bg: isActive ? "#4a95fd" : "rgba(58, 139, 253, 0.15)",
        color: "white",
        transform: "translateX(3px)",
      }}
      onClick={() => navigate(to)}
      transition="all 0.2s"
      fontSize="md"
      h="auto"
      borderRadius="lg"
      fontWeight={isActive ? "bold" : "medium"}
      boxShadow={isActive ? "0 0 0 1px rgba(255,255,255,0.2)" : "none"}
      position="relative"
    >
      <Icon as={icon as ElementType} boxSize={6} mr={4} />
      <Text flex={1} textAlign="left">
        {children}
      </Text>
      {badge && badge > 0 && (
        <Box
          position="absolute"
          top={2}
          right={2}
          bg="red.500"
          color="white"
          borderRadius="full"
          minW="20px"
          h="20px"
          display="flex"
          alignItems="center"
          justifyContent="center"
          fontSize="xs"
          fontWeight="bold"
          boxShadow="0 0 0 2px #151930"
        >
          {badge > 99 ? "99+" : badge}
        </Box>
      )}
    </Button>
  );
};

interface NavItemWithSubmenuProps {
  icon: IconType;
  label: string;
  isActive: boolean;
  subItems: { label: string; path: string; icon?: IconType }[];
}

const NavItemWithSubmenu: React.FC<NavItemWithSubmenuProps> = ({
  icon,
  label,
  isActive,
  subItems,
}) => {
  const [isOpen, setIsOpen] = useState(isActive);
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box>
      <Button
        w="full"
        variant="ghost"
        justifyContent="space-between"
        alignItems="center"
        px={6}
        py={4}
        bg={isActive ? "#3a8bfd" : "transparent"}
        color={isActive ? "white" : "gray.300"}
        _hover={{
          bg: isActive ? "#4a95fd" : "rgba(58, 139, 253, 0.15)",
          color: "white",
          transform: "translateX(3px)",
        }}
        onClick={() => setIsOpen(!isOpen)}
        transition="all 0.2s"
        fontSize="md"
        h="auto"
        borderRadius="lg"
        fontWeight={isActive ? "bold" : "medium"}
        boxShadow={isActive ? "0 0 0 1px rgba(255,255,255,0.2)" : "none"}
      >
        <Flex align="center">
          <Icon as={icon as ElementType} boxSize={6} mr={4} />
          <Text>
            {label}
          </Text>
        </Flex>
        <Icon
          as={isOpen ? FiChevronDown as ElementType : FiChevronRight as ElementType}
          boxSize={4}
        />
      </Button>
      <Collapse in={isOpen} animateOpacity>
        <VStack spacing={1} align="stretch" pl={10} mt={1} mb={1}>
          {subItems.map((item) => (
            <Button
              key={item.path}
              w="full"
              variant="ghost"
              justifyContent="flex-start"
              alignItems="center"
              px={4}
              py={3}
              fontSize="sm"
              bg={location.pathname === item.path ? "rgba(58, 139, 253, 0.3)" : "transparent"}
              color={location.pathname === item.path ? "white" : "gray.400"}
              _hover={{
                bg: "rgba(58, 139, 253, 0.15)",
                color: "white",
                transform: "translateX(3px)",
              }}
              onClick={() => navigate(item.path)}
              borderRadius="md"
              fontWeight={location.pathname === item.path ? "bold" : "normal"}
              transition="all 0.2s"
            >
              {item.icon && <Icon as={item.icon as ElementType} mr={3} boxSize={4} />}
              {item.label}
            </Button>
          ))}
        </VStack>
      </Collapse>
    </Box>
  );
};

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [unreadNotifications, setUnreadNotifications] = useState(0);

  // Fonction pour récupérer le nombre de notifications non lues
  const fetchUnreadNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${config.API_URL}/api/notifications/unread-count`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUnreadNotifications(data.unread_count || 0);
      }
    } catch (error) {
      console.error('Erreur lors de la récupération des notifications:', error);
    }
  };

  // Récupérer les notifications au chargement et périodiquement
  useEffect(() => {
    fetchUnreadNotifications();
    
    // Vérifier toutes les 30 secondes
    const interval = setInterval(fetchUnreadNotifications, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Définir les sous-éléments pour "Mes Documents"
  const documentSubItems = [
    { label: "Tous mes documents", path: "/my-documents", icon: FiFolder },
    { label: "Documents récents", path: "/recent-documents", icon: FiClock },
    { label: "Documents favoris", path: "/favorite-documents", icon: FiHeart },
    { label: "Documents partagés", path: "/shared-documents", icon: FiShare2 },
  ];

  const navItems = [
    { icon: FiHome, label: "Tableau de bord", path: "/dashboard", show: true }, // Accessible à tous
    { icon: FiUsers, label: "Utilisateurs", path: "/users", show: canAccessUsers(user) }, // Admin uniquement
    { icon: FiClock, label: "Historique", path: "/history", show: canAccessHistory(user) }, // Admin et archiviste
    { icon: FiShare2, label: "Notifications", path: "/notifications", show: canAccessNotifications(user) }, // Tous les rôles
    { icon: FiGitBranch, label: "Workflows", path: "/workflow", show: canAccessWorkflows(user) }, // Admin, chef_de_service, validateur
    { icon: FiBriefcase, label: "Organisation", path: "/organization", show: canAccessOrganization(user) }, // Admin uniquement
    { icon: FiTrash2, label: "Corbeille", path: "/trash", show: canAccessTrash(user) }, // Admin et archiviste
    { icon: FiSettings, label: "Paramètres", path: "/settings", show: true }, // Accessible à tous
  ];

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem("token");
      if (token) {
        // Appeler l'API de déconnexion pour enregistrer l'action
        await fetch(`${config.API_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        });
      }
    } catch (error) {
      console.log('Erreur lors de la déconnexion:', error);
    } finally {
      // Supprimer le token et recharger la page
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.reload();
    }
  };

  return (
    <Box
      w={{ base: "full", md: "280px" }}
      bg="#151930"
      h="100vh"
      pos="fixed"
      left={0}
      top={0}
      borderRight="1px solid #2a3152"
      display="flex"
      flexDirection="column"
      overflowY="auto"
      boxShadow="0 0 20px rgba(0,0,0,0.3)"
      css={{
        '&::-webkit-scrollbar': {
          width: '6px',
        },
        '&::-webkit-scrollbar-track': {
          background: '#151930',
        },
        '&::-webkit-scrollbar-thumb': {
          background: '#3a3f59',
          borderRadius: '24px',
        },
        '&::-webkit-scrollbar-thumb:hover': {
          background: '#3a8bfd',
        },
        scrollbarWidth: 'thin',
        scrollbarColor: '#3a3f59 #151930',
      }}
    >
      {/* Logo */}
      <Flex align="center" p={5} justify="center" minH="80px">
        <Box
          bgGradient="linear(to-br, #3a8bfd, #6f6cff)"
          borderRadius="full"
          w="48px"
          h="48px"
          display="flex"
          alignItems="center"
          justifyContent="center"
          boxShadow="0 0 0 4px rgba(255,255,255,0.2)"
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

      <Divider mb={4} borderColor="#2a3152" />

      {/* Navigation Items */}
      <VStack spacing={2} align="stretch" px={3} flex={1} minH="0" overflowY="auto">
        {/* Section principale */}
        {navItems.slice(0, 2).filter(item => item.show).map((item) => (
          <NavItem
            key={item.path}
            icon={item.icon}
            to={item.path}
            isActive={location.pathname === item.path}
          >
            {item.label}
          </NavItem>
        ))}
        
        {/* Menu déroulant pour "Mes Documents" - Accessible à tous les rôles */}
        {canAccessMyDocuments(user) && (
          <NavItemWithSubmenu
            icon={FiFolder}
            label="Mes Documents"
            isActive={
              location.pathname === "/my-documents" ||
              location.pathname === "/recent-documents" ||
              location.pathname === "/favorite-documents" ||
              location.pathname === "/shared-documents"
            }
            subItems={documentSubItems}
          />
        )}

        {/* Lien Recherche - Accessible à tous les rôles */}
        {canAccessSearch(user) && (
          <NavItem
            icon={FiSearch}
            to="/search"
            isActive={location.pathname === "/search"}
          >
            Recherche
          </NavItem>
        )}

        <Divider my={2} borderColor="#2a3152" />

        {/* Section gestion */}
        {navItems.slice(2, 7).filter(item => item.show).map((item) => (
          <NavItem
            key={item.path}
            icon={item.icon}
            to={item.path}
            isActive={location.pathname === item.path}
            badge={item.path === '/notifications' ? unreadNotifications : undefined}
          >
            {item.label}
          </NavItem>
        ))}

        {/* Paramètres */}
        {navItems[7].show && (
          <NavItem
            key="/settings"
            icon={FiSettings}
            to="/settings"
            isActive={location.pathname === "/settings"}
          >
            Paramètres
          </NavItem>
        )}
      </VStack>

      {/* User Profile Section */}
      <Box p={5} borderTop="1px solid #2a3152" minH="120px" bg="#1a1f36">
        <Flex align="center" mb={4}>
          <Box
            bgGradient="linear(to-br, #3a8bfd, #6f6cff)"
            borderRadius="full"
            w="38px"
            h="38px"
            display="flex"
            alignItems="center"
            justifyContent="center"
            mr={3}
            boxShadow="0 0 10px rgba(58,139,253,0.5)"
          >
            <Text color="white" fontWeight="bold" fontSize="lg">
              U
            </Text>
          </Box>
          <Box flex={1}>
            <Text color="white" fontWeight="bold" fontSize="md">
              Mon Compte
            </Text>
            <Text color="gray.400" fontSize="xs">
              Utilisateur connecté
            </Text>
          </Box>
        </Flex>
        <Button
          w="full"
          leftIcon={<Icon as={FiLogOut as ElementType} boxSize={5} />}
          variant="solid"
          colorScheme="red"
          size="md"
          onClick={handleLogout}
          bg="rgba(229, 62, 62, 0.2)"
          _hover={{
            bg: "rgba(229, 62, 62, 0.4)",
            transform: "translateY(-2px)",
          }}
          transition="all 0.2s"
          fontWeight="bold"
          boxShadow="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
          borderRadius="lg"
        >
          Déconnexion
        </Button>
      </Box>
    </Box>
  );
};

export const SidebarContent = Sidebar;
export default Sidebar;
