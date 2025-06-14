import React, { useState, useEffect } from 'react';
import { Menu, MenuButton, MenuList, MenuItem, MenuDivider, IconButton, Icon, Box } from '@chakra-ui/react';
import { FiMoreVertical, FiDownload, FiStar, FiShare2, FiMove, FiClock, FiLock, FiMessageSquare, FiBell, FiTag, FiEye, FiTrash2 } from 'react-icons/fi';
import { ElementType } from 'react';
import { Archive as ArchiveIcon } from '@mui/icons-material';

interface ActionMenuProps {
  documentId: number;
  documentTitle?: string;
  onDownload: (id: number) => void;
  onEdit?: (id: number) => void;
  onDelete?: (id: number) => void;
  onShare?: (id: number, title?: string) => void;
  onToggleFavorite?: (id: number, isFavorite: boolean) => void;
  onMove?: (id: number, title?: string) => void;
  onShowCheckout?: (id: number) => void;
  onShowComments?: (id: number) => void;
  onShowSubscription?: (id: number) => void;
  onShowTags?: (id: number) => void;
  onShowPreview?: (id: number, title?: string) => void;
  onShowOCR?: (id: number, title?: string) => void;
  onShowVersions?: (id: number) => void;
  onSubmitForValidation?: (id: number) => void;
  documentStatus?: string;
  onRequestArchive?: (id: number) => void;
  isFavorite?: boolean;
  isArchived?: boolean;
}

const ActionMenu: React.FC<ActionMenuProps> = ({
  documentId,
  documentTitle,
  onDownload,
  onEdit,
  onDelete,
  onShare,
  onToggleFavorite,
  onMove,
  onShowCheckout,
  onShowComments,
  onShowSubscription,
  onShowTags,
  onShowPreview,
  onShowOCR,
  onShowVersions,
  isFavorite = false,
  onSubmitForValidation,
  documentStatus = 'BROUILLON',
  onRequestArchive,
  isArchived = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = React.useRef(null);

  // Fermer le menu lorsque l'utilisateur clique en dehors
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !(menuRef.current as any).contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [menuRef]);

  // Déterminer si le document peut être soumis pour validation
  const canSubmitForValidation = documentStatus === 'BROUILLON' || documentStatus === 'REJETE';
  
  // Déterminer si le document peut être archivé
  const canRequestArchive = documentStatus === 'APPROUVE' && !isArchived;
  
  // Débogage pour le menu d'action
  console.log('🔍 [DEBUG] ActionMenu - Document ID:', documentId);
  console.log('🔍 [DEBUG] ActionMenu - Status:', documentStatus);
  console.log('🔍 [DEBUG] ActionMenu - isArchived:', isArchived);
  console.log('🔍 [DEBUG] ActionMenu - canRequestArchive:', canRequestArchive);
  console.log('🔍 [DEBUG] ActionMenu - onRequestArchive défini:', !!onRequestArchive);

  return (
    <Box position="relative" ref={menuRef}>
      <Menu>
        <MenuButton
          as={IconButton}
          aria-label="Options"
          icon={<Icon as={FiMoreVertical as ElementType} />}
          variant="ghost"
          size="sm"
        />
        <MenuList>
          <MenuItem icon={<Icon as={FiDownload as ElementType} />} onClick={() => {
            onDownload(documentId);
            setIsOpen(false);
          }}>
            Télécharger
          </MenuItem>
          
          <MenuItem 
            icon={<Icon as={FiStar as ElementType} color={isFavorite ? "yellow.500" : "gray.500"} />} 
            onClick={() => {
              onToggleFavorite && onToggleFavorite(documentId, isFavorite);
              setIsOpen(false);
            }}
          >
            {isFavorite ? "Retirer des favoris" : "Ajouter aux favoris"}
          </MenuItem>
          
          <MenuItem 
            icon={<Icon as={FiShare2 as ElementType} />} 
            onClick={() => {
              onShare && onShare(documentId, documentTitle);
              setIsOpen(false);
            }}
          >
            Partager
          </MenuItem>
          
          {/* Option Déplacer désactivée temporairement
          {onMove && (
            <MenuItem 
              icon={<Icon as={FiMove as ElementType} />} 
              onClick={() => {
                onMove(documentId, documentTitle);
                setIsOpen(false);
              }}
            >
              Déplacer
            </MenuItem>
          )}
          */}
          
          {onShowCheckout && (
            <MenuItem 
              icon={<Icon as={FiLock as ElementType} />} 
              onClick={() => {
                onShowCheckout(documentId);
                setIsOpen(false);
              }}
            >
              Verrouillage
            </MenuItem>
          )}
          
          {onShowComments && (
            <MenuItem 
              icon={<Icon as={FiMessageSquare as ElementType} />} 
              onClick={() => {
                onShowComments(documentId);
                setIsOpen(false);
              }}
            >
              Commentaires
            </MenuItem>
          )}
          
          {onShowSubscription && (
            <MenuItem 
              icon={<Icon as={FiBell as ElementType} />} 
              onClick={() => {
                onShowSubscription(documentId);
                setIsOpen(false);
              }}
            >
              Abonnement
            </MenuItem>
          )}
          
          {onShowTags && (
            <MenuItem 
              icon={<Icon as={FiTag as ElementType} />} 
              onClick={() => {
                onShowTags(documentId);
                setIsOpen(false);
              }}
            >
              Tags
            </MenuItem>
          )}
          
          {onShowPreview && (
            <MenuItem 
              icon={<Icon as={FiEye as ElementType} />} 
              onClick={() => {
                onShowPreview(documentId, documentTitle);
                setIsOpen(false);
              }}
            >
              Aperçu
            </MenuItem>
          )}
          
          {onSubmitForValidation && canSubmitForValidation && (
            <>
              <MenuDivider />
              <MenuItem 
                icon={<Icon as={FiClock as ElementType} />} 
                onClick={() => {
                  onSubmitForValidation(documentId);
                  setIsOpen(false);
                }}
              >
                Soumettre pour validation
              </MenuItem>
            </>
          )}
          
          {onRequestArchive && canRequestArchive && (
            <>
              <MenuDivider />
              <MenuItem 
                icon={<Icon as={ArchiveIcon as ElementType} />} 
                onClick={() => {
                  onRequestArchive(documentId);
                  setIsOpen(false);
                }}
              >
                Demander l'archivage
              </MenuItem>
            </>
          )}
          
          {onDelete && (
            <>
              <MenuDivider />
              <MenuItem 
                icon={<Icon as={FiTrash2 as ElementType} color="red.500" />} 
                onClick={() => {
                  onDelete(documentId);
                  setIsOpen(false);
                }}
              >
                Supprimer
              </MenuItem>
            </>
          )}
        </MenuList>
      </Menu>
    </Box>
  );
};

export default ActionMenu; 