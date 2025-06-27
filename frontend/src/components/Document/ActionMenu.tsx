import React from "react";
import {
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  Icon,
  useToast,
} from "@chakra-ui/react";
import {
  FiMoreVertical,
  FiEye,
  FiDownload,
  FiShare2,
  FiTrash2,
} from "react-icons/fi";
import { ElementType } from "react";

interface ActionMenuProps {
  document?: {
    id: number;
    titre: string;
    type_document: string;
    taille_formatee: string;
    date_creation: string;
  };
  documentId?: number;
  documentTitle?: string;
  onUpdate?: () => void;
  onDelete?: () => void;
  onDownload?: (id: number) => void;
  onShare?: (id: number) => void;
  onEdit?: (id: number) => void;
  onShowPreview?: (id: number, title?: string) => void;
  onShowOCR?: (id: number, title?: string) => void;
}

export const ActionMenu: React.FC<ActionMenuProps> = ({
  document,
  documentId,
  documentTitle,
  onUpdate,
  onDelete,
  onDownload,
  onShare,
  onEdit,
  onShowPreview,
  onShowOCR,
}) => {
  const toast = useToast();

  const docId = document?.id || documentId;
  const docTitle = document?.titre || documentTitle;

  if (!docId) {
    return null;
  }

  const handleDownload = () => {
    if (onDownload) {
      onDownload(docId);
    } else {
      toast({
        title: "Téléchargement",
        description: "Le téléchargement sera disponible prochainement",
        status: "info",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleShare = () => {
    if (onShare) {
      onShare(docId);
    } else {
      toast({
        title: "Partage",
        description: "Le partage sera disponible prochainement",
        status: "info",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handlePreview = () => {
    if (onShowPreview) {
      onShowPreview(docId, docTitle);
    } else {
      toast({
        title: "Aperçu",
        description: "L'aperçu sera disponible prochainement",
        status: "info",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete();
    } else {
      toast({
        title: "Suppression",
        description: "La suppression sera disponible prochainement",
        status: "info",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  return (
    <Menu>
      <MenuButton
        as={IconButton}
        icon={<Icon as={FiMoreVertical as ElementType} />}
        variant="ghost"
        size="sm"
        color="gray.400"
        _hover={{ color: "white", bg: "rgba(58, 139, 253, 0.1)" }}
      />
      <MenuList bg="#2a3657" borderColor="#3a445e">
        <MenuItem
          icon={<Icon as={FiEye as ElementType} />}
          onClick={handlePreview}
          bg="transparent"
          color="white"
          _hover={{ bg: "rgba(58, 139, 253, 0.1)" }}
        >
          Aperçu
        </MenuItem>
        <MenuItem
          icon={<Icon as={FiDownload as ElementType} />}
          onClick={handleDownload}
          bg="transparent"
          color="white"
          _hover={{ bg: "rgba(58, 139, 253, 0.1)" }}
        >
          Télécharger
        </MenuItem>
        <MenuItem
          icon={<Icon as={FiShare2 as ElementType} />}
          onClick={handleShare}
          bg="transparent"
          color="white"
          _hover={{ bg: "rgba(58, 139, 253, 0.1)" }}
        >
          Partager
        </MenuItem>
        <MenuItem
          icon={<Icon as={FiTrash2 as ElementType} />}
          onClick={handleDelete}
          bg="transparent"
          color="red.400"
          _hover={{ bg: "rgba(255, 0, 0, 0.1)" }}
        >
          Supprimer
        </MenuItem>
      </MenuList>
    </Menu>
  );
};

