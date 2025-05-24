import React from "react";
import { Drawer, DrawerOverlay, DrawerContent, DrawerCloseButton, DrawerBody, Button, useDisclosure, Box } from "@chakra-ui/react";
import { SidebarContent } from "./Sidebar";

const SidebarDrawer: React.FC = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  return (
    <>
      <Box position="fixed" top={4} left={4} zIndex={1400}>
        <Button
          aria-label="Ouvrir le menu"
          onClick={onOpen}
          size="lg"
          colorScheme="blue"
          p={0}
          minW="40px"
          h="40px"
          fontSize="24px"
        >
          ☰
        </Button>
      </Box>
      <Drawer isOpen={isOpen} placement="left" onClose={onClose} size="xs">
        <DrawerOverlay />
        <DrawerContent bg="#181c2f">
          <DrawerCloseButton color="white" />
          <DrawerBody p={0}>
            <Box w="full" h="100vh">
              <SidebarContent />
            </Box>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </>
  );
};
export default SidebarDrawer;