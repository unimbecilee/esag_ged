import React, { useState } from "react";
import { ChakraProvider, Box, Flex, theme, CSSReset } from "@chakra-ui/react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import { SidebarContent } from "./components/Sidebar";
import SidebarDrawer from "./components/SidebarDrawer";
import Dashboard from "./components/Dashboard";
import Users from "./components/Users";
import Scan from "./components/Scan";
import Search from "./components/Search";
import Trash from "./components/Trash";
import MyDocuments from "./components/MyDocuments";
import History from "./components/History";
import Shared from "./components/Shared";
import Settings from "./components/Settings";
import Workflow from "./components/Workflow";
import Organization from "./components/Organization";

function App() {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token")
  );

  const handleAuthSuccess = (newToken: string) => {
    setToken(newToken);
  };

  return (
    <ChakraProvider theme={theme}>
      <CSSReset />
      {!token ? (
        <Login onAuthSuccess={handleAuthSuccess} />
      ) : (
        <Router>
          <Flex bg="#161925" minH="100vh">
            <Box display={{ base: "none", md: "block" }}>
              <SidebarContent />
            </Box>
            <Box display={{ base: "block", md: "none" }}>
              <SidebarDrawer />
            </Box>
            <Box flex={1} ml={{ base: 0, md: "260px" }} p={{ base: 2, md: 10 }}>
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/users" element={<Users />} />
                <Route path="/scan" element={<Scan />} />
                <Route path="/search" element={<Search />} />
                <Route path="/trash" element={<Trash />} />
                <Route path="/my-documents" element={<MyDocuments />} />
                <Route path="/history" element={<History />} />
                <Route path="/shared" element={<Shared />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/workflow" element={<Workflow />} />
                <Route path="/organization" element={<Organization />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Box>
          </Flex>
        </Router>
      )}
    </ChakraProvider>
  );
}

export default App;
