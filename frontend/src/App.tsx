import React, { Suspense, lazy, useCallback } from "react";
import { ChakraProvider, Box, Flex, Spinner, Center } from "@chakra-ui/react";
import { BrowserRouter as Router, Route, Routes, Navigate, useNavigate } from "react-router-dom";
import { theme } from "./theme";
import { useAuthStatus } from "./hooks/useAuthStatus";
import { SidebarContent } from "./components/Sidebar";
import Login from "./components/Login";
import { LoadingProvider } from "./contexts/LoadingContext";
import Trash from "./components/Trash";
import TestAPI from "./components/TestAPI";
import LoadingFallback from "./components/LoadingFallback";
import { AuthProvider } from "./contexts/AuthContext";

// Chargement paresseux des composants
const Dashboard = lazy(() => import("./components/Dashboard"));
const Scan = lazy(() => import("./components/Scan"));
const Users = lazy(() => import("./components/Users"));
const Workflow = lazy(() => import("./components/Workflow"));
const SearchPage = lazy(() => import("./components/SearchPage"));
const AdvancedSearchPage = lazy(() => import("./components/AdvancedSearchPage"));
const MyDocuments = lazy(() => import("./components/MyDocuments"));
const RecentDocuments = lazy(() => import("./components/RecentDocuments"));
const FavoriteDocuments = lazy(() => import("./components/FavoriteDocuments"));
const SharedDocuments = lazy(() => import("./components/SharedDocuments"));
const Settings = lazy(() => import("./components/SettingsSimple"));
const History = lazy(() => import("./components/History"));
const Organization = lazy(() => import("./components/Organization"));
const Notifications = lazy(() => import("./components/Notifications"));
const ImportExport = lazy(() => import("./components/ImportExport"));
const BatchOperations = lazy(() => import("./components/BatchOperations"));

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStatus();

  if (isLoading) {
    return <LoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <>{children}</>;
};

// Composant de Login avec navigation
const LoginWithNavigation: React.FC = () => {
  const navigate = useNavigate();
  
  const handleAuthSuccess = useCallback(() => {
    console.log("Auth success dans App.tsx, navigation vers /dashboard");
    navigate("/dashboard");
  }, [navigate]);
  
  return <Login onAuthSuccess={handleAuthSuccess} />;
};

function App() {
  return (
    <ChakraProvider theme={theme}>
      <AuthProvider>
        <LoadingProvider>
          <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/test-api" element={<TestAPI />} />
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </Router>
        </LoadingProvider>
      </AuthProvider>
    </ChakraProvider>
  );
}

const AppLayout: React.FC = () => {
  return (
    <Flex h="100vh" overflow="hidden">
      <SidebarContent />
      <Box
        ml={{ base: 0, md: "280px" }}
        w={{ base: "full", md: "calc(100% - 280px)" }}
        bg="#202a46"
        h="100vh"
        overflowY="auto"
      >
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/scan" element={<Scan />} />
            <Route path="/users" element={<Users />} />
            <Route path="/workflow" element={<Workflow />} />
            <Route path="/trash" element={<Trash />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/advanced-search" element={<AdvancedSearchPage />} />
            <Route path="/my-documents" element={<MyDocuments />} />
            <Route path="/recent-documents" element={<RecentDocuments />} />
            <Route path="/favorite-documents" element={<FavoriteDocuments />} />
            <Route path="/shared-documents" element={<SharedDocuments />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/history" element={<History />} />
            <Route path="/organization" element={<Organization />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/import-export" element={<ImportExport />} />
            <Route path="/batch-operations" element={<BatchOperations />} />
          </Routes>
        </Suspense>
      </Box>
    </Flex>
  );
};

export default App;
