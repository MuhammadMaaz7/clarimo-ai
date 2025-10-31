import { createContext, useContext, useState, ReactNode, useMemo } from 'react';

interface AnalysisResult {
  inputId: string;
  query: string;
  timestamp: number;
  painPointsCount?: number;
  totalClusters?: number;
}

interface AnalysisContextType {
  currentAnalysis: AnalysisResult | null;
  setCurrentAnalysis: (analysis: AnalysisResult | null) => void;
  clearAnalysis: () => void;
  hasActiveAnalysis: boolean;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const AnalysisProvider = ({ children }: { children: ReactNode }) => {
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(null);

  const clearAnalysis = () => {
    setCurrentAnalysis(null);
  };

  const hasActiveAnalysis = currentAnalysis !== null;

  const contextValue = useMemo(() => ({
    currentAnalysis,
    setCurrentAnalysis,
    clearAnalysis,
    hasActiveAnalysis
  }), [currentAnalysis]);

  return (
    <AnalysisContext.Provider value={contextValue}>
      {children}
    </AnalysisContext.Provider>
  );
};

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (context === undefined) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};