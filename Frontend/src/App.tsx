import { lazy, Suspense } from "react";
import { Toaster } from "./components/ui/toaster";
import { Toaster as Sonner } from "./components/ui/sonner";
import { TooltipProvider } from "./components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { SidebarProvider } from "./contexts/SidebarContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { AnalysisProvider } from "./contexts/AnalysisContext";
import { ValidationProvider } from "./contexts/ValidationContext";
import { CompetitorProvider } from "./contexts/CompetitorContext";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import ProblemDiscovery from "./pages/ProblemDiscovery";
import ProtectedRoute from "./components/ProtectedRoute";
import ComingSoon from "./pages/ComingSoon";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Profile from "./pages/Profile";
import LoadingSpinner from "./components/LoadingSpinner";
import { useTokenValidation } from "./hooks/useTokenValidation";
import ChatbotWidget from "./components/chatbot/ChatbotWidget";

// Lazy load heavy components
const Landing = lazy(() => import("./pages/Landing"));
const AnalysisView = lazy(() => import("./pages/AnalysisView"));
const DiscoveredProblems = lazy(() => import("./pages/DiscoveredProblems"));
const IdeaList = lazy(() => import("./pages/IdeaList"));
const IdeaNew = lazy(() => import("./pages/IdeaNew"));
const IdeaDetail = lazy(() => import("./pages/IdeaDetail"));
const IdeaValidation = lazy(() => import("./pages/IdeaValidation"));
const IdeaValidationHistory = lazy(() => import("./pages/IdeaValidationHistory"));
const IdeaVersionComparison = lazy(() => import("./pages/IdeaVersionComparison"));
const IdeaComparison = lazy(() => import("./pages/IdeaComparison"));
const CompetitorAnalysis = lazy(() => import("./pages/CompetitorAnalysis"));
const CompetitorAnalysisHistory = lazy(() => import("./pages/CompetitorAnalysisHistory"));
const CompetitorAnalysisDetail = lazy(() => import("./pages/CompetitorAnalysisDetail"));
const LaunchPlanning = lazy(() => import("./pages/LaunchPlanning"));
const LaunchPlanningHistory = lazy(() => import("./pages/LaunchPlanningHistory"));
const GoToMarket = lazy(() => import("./pages/GoToMarket"));
const GoToMarketHistory = lazy(() => import("./pages/GoToMarketHistory"));

const queryClient = new QueryClient();

const AuthenticatedLayout = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth();
  
  return (
    <div className="h-[100dvh] flex flex-col bg-[#211c37] overflow-hidden relative">
      {/* Unified Background Gradient */}
      <div className="fixed inset-0 bg-gradient-to-br from-accent/5 via-primary/5 to-transparent pointer-events-none" />
      
      {/* Background Mesh/Glow Effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
         <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent/20 blur-[120px] rounded-full opacity-20" />
         <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/20 blur-[120px] rounded-full opacity-20" />
      </div>
      
      <Navbar />
      <div className="flex flex-1 overflow-hidden relative z-10">
        {user && <Sidebar />}
        <main className="flex-1 min-w-0 overflow-y-auto transition-all duration-300 scroll-smooth">
          {children}
        </main>
      </div>
    </div>
  );
};

const AppContent = () => {
  const { user, loading } = useAuth();
  const location = useLocation();
  
  useTokenValidation(5);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  const getRootKey = (pathname: string) => {
    if (['/', '/login', '/signup'].includes(pathname)) return pathname;
    return 'dashboard-app'; 
  };

  return (
    <>
      <AnimatePresence mode="wait">
        <Routes location={location} key={getRootKey(location.pathname)}>
          <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />
          <Route path="/signup" element={user ? <Navigate to="/dashboard" replace /> : <Signup />} />
          <Route path="/" element={<Landing />} />
          
          <Route path="/*" element={
            <SidebarProvider>
              <AuthenticatedLayout>
                <Suspense fallback={
                  <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
                    <LoadingSpinner />
                  </div>
                }>
                  <Routes>
                    <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                    <Route path="/problem-discovery" element={<ProtectedRoute><ProblemDiscovery /></ProtectedRoute>} />
                    <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
                    <Route path="/analysis/:inputId" element={<ProtectedRoute><AnalysisView /></ProtectedRoute>} />
                    <Route path="/discovered-problems" element={<ProtectedRoute><DiscoveredProblems /></ProtectedRoute>} />
                    <Route path="/ideas" element={<ProtectedRoute><IdeaList /></ProtectedRoute>} />
                    <Route path="/ideas/new" element={<ProtectedRoute><IdeaNew /></ProtectedRoute>} />
                    <Route path="/ideas/compare" element={<ProtectedRoute><IdeaComparison /></ProtectedRoute>} />
                    <Route path="/ideas/:ideaId" element={<ProtectedRoute><IdeaDetail /></ProtectedRoute>} />
                    <Route path="/ideas/:ideaId/validate" element={<ProtectedRoute><IdeaValidation /></ProtectedRoute>} />
                    <Route path="/ideas/:ideaId/history" element={<ProtectedRoute><IdeaValidationHistory /></ProtectedRoute>} />
                    <Route path="/ideas/:ideaId/history/compare" element={<ProtectedRoute><IdeaVersionComparison /></ProtectedRoute>} />
                    <Route path="/idea-validation" element={<ProtectedRoute><IdeaList /></ProtectedRoute>} />
                    <Route path="/competitor-analysis" element={<ProtectedRoute><CompetitorAnalysis /></ProtectedRoute>} />
                    <Route path="/competitor-analysis/history" element={<ProtectedRoute><CompetitorAnalysisHistory /></ProtectedRoute>} />
                    <Route path="/competitor-analysis/history" element={<ProtectedRoute><CompetitorAnalysisHistory /></ProtectedRoute>} />
                    <Route path="/competitor-analysis/:productId" element={<ProtectedRoute><CompetitorAnalysisDetail /></ProtectedRoute>} />
                    <Route path="/customer-finding" element={<ProtectedRoute><ComingSoon /></ProtectedRoute>} />
                    <Route path="/launch-planning" element={<ProtectedRoute><LaunchPlanning /></ProtectedRoute>} />
                    <Route path="/launch-planning/history" element={<ProtectedRoute><LaunchPlanningHistory /></ProtectedRoute>} />
                    <Route path="/go-to-market" element={<ProtectedRoute><GoToMarket /></ProtectedRoute>} />
                    <Route path="/go-to-market/history" element={<ProtectedRoute><GoToMarketHistory /></ProtectedRoute>} />
                    <Route path="*" element={<ComingSoon />} />
                  </Routes>
                </Suspense>
              </AuthenticatedLayout>
            </SidebarProvider>
          } />
        </Routes>
      </AnimatePresence>
      <ChatbotWidget />
    </>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <BrowserRouter>
        <AuthProvider>
          <AnalysisProvider>
            <ValidationProvider>
              <CompetitorProvider>
                <AppContent />
                <Toaster />
                <Sonner />
              </CompetitorProvider>
            </ValidationProvider>
          </AnalysisProvider>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
