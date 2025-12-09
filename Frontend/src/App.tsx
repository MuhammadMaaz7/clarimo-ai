import { lazy, Suspense } from "react";
import { Toaster } from "./components/ui/toaster";
import { Toaster as Sonner } from "./components/ui/sonner";
import { TooltipProvider } from "./components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { SidebarProvider } from "./contexts/SidebarContext";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { AnalysisProvider } from "./contexts/AnalysisContext";
import { ValidationProvider } from "./contexts/ValidationContext";
import { CompetitorProvider } from "./contexts/CompetitorContext";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import ProblemDiscovery from "./pages/ProblemDiscovery";
import ProtectedRoute from "./components/ProtectedRoute";
import ComingSoon from "./pages/ComingSoon";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Profile from "./pages/Profile";
import LoadingSpinner from "./components/LoadingSpinner";
import { useTokenValidation } from "./hooks/useTokenValidation";

// Lazy load heavy components for better performance
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
const CompetitorAnalysisNew = lazy(() => import("./pages/CompetitorAnalysisNew")); // Production-ready
const CompetitorAnalysisHistory = lazy(() => import("./pages/CompetitorAnalysisHistory"));
const CompetitorAnalysisDetail = lazy(() => import("./pages/CompetitorAnalysisDetail"));

const queryClient = new QueryClient();



const AppContent = () => {
  const { user, loading } = useAuth();
  
  // Enable periodic token validation (every 5 minutes)
  useTokenValidation(5);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <Routes>
      {/* Authentication routes - full screen without navbar */}
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/signup" element={user ? <Navigate to="/" replace /> : <Signup />} />
      
      {/* Main app routes - with navbar and sidebar */}
      <Route path="/*" element={
        <SidebarProvider>
          <div className="min-h-screen bg-gradient-to-br from-accent/20 via-primary/10 to-background relative">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,hsl(var(--accent))_0%,transparent_50%)] opacity-20" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_70%,hsl(var(--primary))_0%,transparent_50%)] opacity-20" />
            
            <Navbar />
            <div className="flex min-h-[calc(100vh-4rem)] relative z-10">
              {user && <Sidebar />}
              <main className={`flex-1 ${user ? 'lg:ml-4' : ''}`}>
                <div className="responsive-container min-h-[calc(100vh-4rem)]">
                  <Suspense fallback={
                    <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
                      <LoadingSpinner />
                    </div>
                  }>
                    <Routes>
                      <Route path="/" element={
                        <ProtectedRoute>
                          <ProblemDiscovery />
                        </ProtectedRoute>
                      } />
                      <Route path="/profile" element={
                        <ProtectedRoute>
                          <Profile />
                        </ProtectedRoute>
                      } />
                      <Route path="/analysis/:inputId" element={
                        <ProtectedRoute>
                          <AnalysisView />
                        </ProtectedRoute>
                      } />
                      <Route path="/discovered-problems" element={
                        <ProtectedRoute>
                          <DiscoveredProblems />
                        </ProtectedRoute>
                      } />
                      <Route path="/ideas" element={
                        <ProtectedRoute>
                          <IdeaList />
                        </ProtectedRoute>
                      } />
                      <Route path="/ideas/new" element={
                        <ProtectedRoute>
                          <IdeaNew />
                        </ProtectedRoute>
                      } />
                      <Route path="/ideas/compare" element={
                        <ProtectedRoute>
                          <IdeaComparison />
                        </ProtectedRoute>
                      } />
                      <Route path="/ideas/:ideaId" element={
                        <ProtectedRoute>
                          <IdeaDetail />
                        </ProtectedRoute>
                      } />
                      <Route path="/ideas/:ideaId/validate" element={
                        <ProtectedRoute>
                          <IdeaValidation />
                        </ProtectedRoute>
                      } />
                      <Route path="/ideas/:ideaId/history" element={
                        <ProtectedRoute>
                          <IdeaValidationHistory />
                        </ProtectedRoute>
                      } />
                      <Route path="/ideas/:ideaId/history/compare" element={
                        <ProtectedRoute>
                          <IdeaVersionComparison />
                        </ProtectedRoute>
                      } />
                      <Route path="/idea-validation" element={
                        <ProtectedRoute>
                          <IdeaList />
                        </ProtectedRoute>
                      } />
                      <Route path="/competitor-analysis" element={
                        <ProtectedRoute>
                          <CompetitorAnalysis />
                        </ProtectedRoute>
                      } />
                      <Route path="/competitor-analysis/new" element={
                        <ProtectedRoute>
                          <CompetitorAnalysisNew />
                        </ProtectedRoute>
                      } />
                      <Route path="/competitor-analysis/history" element={
                        <ProtectedRoute>
                          <CompetitorAnalysisHistory />
                        </ProtectedRoute>
                      } />
                      <Route path="/competitor-analysis/:productId" element={
                        <ProtectedRoute>
                          <CompetitorAnalysisDetail />
                        </ProtectedRoute>
                      } />
                      <Route path="/customer-finding" element={
                        <ProtectedRoute>
                          <ComingSoon />
                        </ProtectedRoute>
                      } />
                      <Route path="/launch-planning" element={
                        <ProtectedRoute>
                          <ComingSoon />
                        </ProtectedRoute>
                      } />
                      <Route path="/go-to-market" element={
                        <ProtectedRoute>
                          <ComingSoon />
                        </ProtectedRoute>
                      } />
                      <Route path="*" element={<ComingSoon />} />
                    </Routes>
                  </Suspense>
                </div>
              </main>
            </div>
          </div>
        </SidebarProvider>
      } />
    </Routes>
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
