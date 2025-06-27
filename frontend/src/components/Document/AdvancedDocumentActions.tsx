import React, { useState } from 'react';
import { useDisclosure } from '@chakra-ui/react';
import ActionMenu from '../ActionMenu';
import DocumentCheckout from './DocumentCheckout';
import DocumentComments from './DocumentComments';
import DocumentSubscription from './DocumentSubscription';
import DocumentTags from './DocumentTags';
import DocumentPreview from './DocumentPreview';

interface AdvancedDocumentActionsProps {
  documentId: number;
  documentTitle: string;
  onDownload: (id: number) => void;
  onShare: (id: number) => void;
  onDelete: (id: number) => void;
  onRefresh?: () => void;
}

const AdvancedDocumentActions: React.FC<AdvancedDocumentActionsProps> = ({
  documentId,
  documentTitle,
  onDownload,
  onShare,
  onDelete,
  onRefresh
}) => {
  // Modales pour les différentes fonctionnalités
  const { 
    isOpen: isCommentsOpen, 
    onOpen: onCommentsOpen, 
    onClose: onCommentsClose 
  } = useDisclosure();
  
  const { 
    isOpen: isTagsOpen, 
    onOpen: onTagsOpen, 
    onClose: onTagsClose 
  } = useDisclosure();

  const { 
    isOpen: isPreviewOpen, 
    onOpen: onPreviewOpen, 
    onClose: onPreviewClose 
  } = useDisclosure();

  const [showCheckout, setShowCheckout] = useState(false);
  const [showSubscription, setShowSubscription] = useState(false);

  const handleShowCheckout = () => {
    setShowCheckout(true);
  };

  const handleShowComments = () => {
    onCommentsOpen();
  };

  const handleShowSubscription = () => {
    setShowSubscription(true);
  };

  const handleShowTags = () => {
    onTagsOpen();
  };

  const handleShowPreview = () => {
    onPreviewOpen();
  };

  const handleStatusChange = () => {
    onRefresh && onRefresh();
  };

  const handleTagsChanged = () => {
    onRefresh && onRefresh();
  };

  return (
    <>
      {/* Menu d'actions principal */}
      <ActionMenu
        documentId={documentId}
        documentTitle={documentTitle}
        onDownload={onDownload}
        onShare={onShare}
        onDelete={onDelete}
        onShowCheckout={handleShowCheckout}
        onShowComments={handleShowComments}
        onShowSubscription={handleShowSubscription}
        onShowTags={handleShowTags}
        onShowPreview={handleShowPreview}
      />

      {/* Composants de checkout et subscription inline */}
      {showCheckout && (
        <DocumentCheckout
          documentId={documentId}
          onStatusChange={handleStatusChange}
        />
      )}

      {showSubscription && (
        <DocumentSubscription
          documentId={documentId}
          onSubscriptionChange={handleStatusChange}
        />
      )}

      {/* Modales pour les fonctionnalités avancées */}
      <DocumentComments
        isOpen={isCommentsOpen}
        onClose={onCommentsClose}
        documentId={documentId}
        documentTitle={documentTitle}
      />

      <DocumentTags
        isOpen={isTagsOpen}
        onClose={onTagsClose}
        documentId={documentId}
        documentTitle={documentTitle}
        onTagsChanged={handleTagsChanged}
      />

      <DocumentPreview
        isOpen={isPreviewOpen}
        onClose={onPreviewClose}
        documentId={documentId}
        documentTitle={documentTitle}
      />
    </>
  );
};

export default AdvancedDocumentActions; 

