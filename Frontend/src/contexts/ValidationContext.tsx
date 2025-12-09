/**
 * Validation Context
 * Manages state for idea validation features
 */

import { createContext, useContext, useState, useCallback, useRef, useEffect, ReactNode } from 'react';
import api from '../lib/api';
import {
  Idea,
  ValidationResult,
  ValidationReport,
  ValidationHistoryItem,
  ComparisonReport,
  VersionComparison,
  ValidationConfig,
} from '../types/validation';

interface ValidationContextType {
  // Ideas state
  ideas: Idea[];
  currentIdea: Idea | null;
  ideasLoading: boolean;
  ideasError: string | null;

  // Validation state
  currentValidation: ValidationResult | null;
  validationLoading: boolean;
  validationError: string | null;
  validationProgress: number;

  // Report state
  currentReport: ValidationReport | null;
  reportLoading: boolean;
  reportError: string | null;

  // History state
  validationHistory: ValidationHistoryItem[];
  historyLoading: boolean;

  // Comparison state
  comparisonReport: ComparisonReport | null;
  versionComparison: VersionComparison | null;

  // Idea operations
  fetchIdeas: () => Promise<void>;
  fetchIdeaById: (ideaId: string) => Promise<void>;
  createIdea: (data: any) => Promise<Idea>;
  updateIdea: (ideaId: string, data: any) => Promise<Idea>;
  deleteIdea: (ideaId: string) => Promise<void>;

  // Validation operations
  startValidation: (ideaId: string, config?: ValidationConfig) => Promise<ValidationResult>;
  fetchValidationResult: (validationId: string) => Promise<void>;
  pollValidationStatus: (validationId: string) => Promise<void>;
  stopPolling: () => void;

  // History operations
  fetchValidationHistory: (ideaId: string) => Promise<void>;

  // Comparison operations
  compareValidations: (validationIds: string[]) => Promise<void>;
  compareVersions: (validationId1: string, validationId2: string) => Promise<void>;

  // Export operations
  exportToJson: (validationId: string) => Promise<any>;
  exportToPdf: (validationId: string) => Promise<Blob>;

  // Clear operations
  clearCurrentIdea: () => void;
  clearCurrentValidation: () => void;
  clearErrors: () => void;
}

const ValidationContext = createContext<ValidationContextType | undefined>(undefined);

export function ValidationProvider({ children }: { children: ReactNode }) {
  // Ideas state
  const [ideas, setIdeas] = useState<Idea[]>([]);
  const [currentIdea, setCurrentIdea] = useState<Idea | null>(null);
  const [ideasLoading, setIdeasLoading] = useState(false);
  const [ideasError, setIdeasError] = useState<string | null>(null);

  // Validation state
  const [currentValidation, setCurrentValidation] = useState<ValidationResult | null>(null);
  const [validationLoading, setValidationLoading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [validationProgress, setValidationProgress] = useState(0);

  // Report state
  const [currentReport, setCurrentReport] = useState<ValidationReport | null>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  // History state
  const [validationHistory, setValidationHistory] = useState<ValidationHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Comparison state
  const [comparisonReport, setComparisonReport] = useState<ComparisonReport | null>(null);
  const [versionComparison, setVersionComparison] = useState<VersionComparison | null>(null);

  // Polling state - use ref to avoid stale closures
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Idea operations
  const fetchIdeas = useCallback(async () => {
    // Check if user is authenticated before fetching
    const token = localStorage.getItem('auth_token');
    if (!token) {
      console.log('No auth token found, skipping ideas fetch');
      setIdeas([]);
      setIdeasLoading(false);
      return;
    }

    setIdeasLoading(true);
    setIdeasError(null);
    try {
      const fetchedIdeas = await api.ideas.getAll();
      setIdeas(fetchedIdeas as Idea[]);
    } catch (error: any) {
      setIdeasError(error.message || 'Failed to fetch ideas');
      console.error('Error fetching ideas:', error);
    } finally {
      setIdeasLoading(false);
    }
  }, []);

  const fetchIdeaById = useCallback(async (ideaId: string) => {
    setIdeasLoading(true);
    setIdeasError(null);
    try {
      const idea = await api.ideas.getById(ideaId);
      setCurrentIdea(idea);
    } catch (error: any) {
      setIdeasError(error.message || 'Failed to fetch idea');
      console.error('Error fetching idea:', error);
    } finally {
      setIdeasLoading(false);
    }
  }, []);

  const createIdea = useCallback(async (data: any): Promise<Idea> => {
    setIdeasLoading(true);
    setIdeasError(null);
    try {
      const newIdea = await api.ideas.create(data);
      setIdeas((prev) => [newIdea, ...prev]);
      setCurrentIdea(newIdea);
      return newIdea;
    } catch (error: any) {
      setIdeasError(error.message || 'Failed to create idea');
      console.error('Error creating idea:', error);
      throw error;
    } finally {
      setIdeasLoading(false);
    }
  }, []);

  const updateIdea = useCallback(async (ideaId: string, data: any): Promise<Idea> => {
    setIdeasLoading(true);
    setIdeasError(null);
    try {
      const updatedIdea = await api.ideas.update(ideaId, data);
      setIdeas((prev) => prev.map((idea) => (idea.id === ideaId ? updatedIdea : idea)));
      if (currentIdea?.id === ideaId) {
        setCurrentIdea(updatedIdea);
      }
      return updatedIdea;
    } catch (error: any) {
      setIdeasError(error.message || 'Failed to update idea');
      console.error('Error updating idea:', error);
      throw error;
    } finally {
      setIdeasLoading(false);
    }
  }, [currentIdea]);

  const deleteIdea = useCallback(async (ideaId: string) => {
    setIdeasLoading(true);
    setIdeasError(null);
    try {
      await api.ideas.delete(ideaId);
      setIdeas((prev) => prev.filter((idea) => idea.id !== ideaId));
      if (currentIdea?.id === ideaId) {
        setCurrentIdea(null);
      }
    } catch (error: any) {
      setIdeasError(error.message || 'Failed to delete idea');
      console.error('Error deleting idea:', error);
      throw error;
    } finally {
      setIdeasLoading(false);
    }
  }, [currentIdea]);



  // Validation operations
  const startValidation = useCallback(async (
    ideaId: string,
    config?: ValidationConfig
  ): Promise<ValidationResult> => {
    setValidationLoading(true);
    setValidationError(null);
    setValidationProgress(0);
    try {
      // Validation is now SYNCHRONOUS - it waits for completion
      // The API call will take 30-60 seconds but returns complete results
      const result = await api.validations.validate(ideaId, config);
      setCurrentValidation(result as ValidationResult);
      
      // Set progress to 100% since validation is complete
      setValidationProgress(100);
      
      // NO POLLING NEEDED - validation is already complete!
      
      return result as ValidationResult;
    } catch (error: any) {
      setValidationError(error.message || 'Failed to validate idea');
      console.error('Error validating idea:', error);
      throw error;
    } finally {
      setValidationLoading(false);
    }
  }, []);

  const fetchValidationResult = useCallback(async (validationId: string) => {
    setReportLoading(true);
    setReportError(null);
    try {
      const result = await api.validations.getResult(validationId);
      setCurrentValidation(result as ValidationResult);
      
      // If result has report data, set it as current report
      if (result.report_data && result.individual_scores) {
        // Get idea title from result or current idea
        const ideaTitle = currentIdea?.title || result.idea_id || 'Untitled Idea';
        
        const report: ValidationReport = {
          validation_id: result.validation_id,
          idea_id: result.idea_id,
          idea_title: ideaTitle,
          overall_score: result.overall_score || 0,
          validation_date: result.created_at,
          ...result.individual_scores,
          strengths: result.report_data.strengths || [],
          weaknesses: result.report_data.weaknesses || [],
          critical_recommendations: result.report_data.recommendations || [],
          radar_chart_data: {},
          score_distribution: {},
          executive_summary: result.report_data.executive_summary,
          detailed_analysis: result.report_data.detailed_analysis,
          next_steps: result.report_data.next_steps || [],
        };
        setCurrentReport(report);
      }
    } catch (error: any) {
      setReportError(error.message || 'Failed to fetch validation result');
      console.error('Error fetching validation result:', error);
    } finally {
      setReportLoading(false);
    }
  }, [currentIdea]);

  // REMOVED: Polling is no longer needed - validation is now synchronous
  const pollValidationStatus = useCallback(async (validationId: string) => {
    // This method is kept for backward compatibility but does nothing
    // Validation now completes synchronously, so no polling needed
    console.warn('pollValidationStatus called but polling is deprecated - validation is now synchronous');
  }, []);

  const stopPolling = useCallback(() => {
    // This method is kept for backward compatibility but does nothing
    // No polling to stop since validation is synchronous
  }, []);

  // History operations
  const fetchValidationHistory = useCallback(async (ideaId: string) => {
    setHistoryLoading(true);
    try {
      const history = await api.validations.getHistory(ideaId);
      setValidationHistory(history as ValidationHistoryItem[]);
    } catch (error: any) {
      console.error('Error fetching validation history:', error);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // Comparison operations
  const compareValidations = useCallback(async (validationIds: string[]) => {
    setReportLoading(true);
    setReportError(null);
    try {
      const comparison = await api.validations.compare(validationIds);
      setComparisonReport(comparison);
    } catch (error: any) {
      setReportError(error.message || 'Failed to compare validations');
      console.error('Error comparing validations:', error);
    } finally {
      setReportLoading(false);
    }
  }, []);

  const compareVersions = useCallback(async (validationId1: string, validationId2: string) => {
    setReportLoading(true);
    setReportError(null);
    try {
      const comparison = await api.validations.compareVersions(validationId1, validationId2);
      setVersionComparison(comparison);
    } catch (error: any) {
      setReportError(error.message || 'Failed to compare versions');
      console.error('Error comparing versions:', error);
    } finally {
      setReportLoading(false);
    }
  }, []);

  // Export operations
  const exportToJson = useCallback(async (validationId: string) => {
    try {
      const data = await api.validations.exportJson(validationId);
      return data;
    } catch (error: any) {
      console.error('Error exporting to JSON:', error);
      throw error;
    }
  }, []);

  const exportToPdf = useCallback(async (validationId: string) => {
    try {
      const blob = await api.validations.exportPdf(validationId);
      return blob;
    } catch (error: any) {
      console.error('Error exporting to PDF:', error);
      throw error;
    }
  }, []);

  // Clear operations
  const clearCurrentIdea = useCallback(() => {
    setCurrentIdea(null);
  }, []);

  const clearCurrentValidation = useCallback(() => {
    setCurrentValidation(null);
    setCurrentReport(null);
    setValidationProgress(0);
    stopPolling();
  }, [stopPolling]);

  const clearErrors = useCallback(() => {
    setIdeasError(null);
    setValidationError(null);
    setReportError(null);
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);

  const value: ValidationContextType = {
    // State
    ideas,
    currentIdea,
    ideasLoading,
    ideasError,
    currentValidation,
    validationLoading,
    validationError,
    validationProgress,
    currentReport,
    reportLoading,
    reportError,
    validationHistory,
    historyLoading,
    comparisonReport,
    versionComparison,

    // Operations
    fetchIdeas,
    fetchIdeaById,
    createIdea,
    updateIdea,
    deleteIdea,
    startValidation,
    fetchValidationResult,
    pollValidationStatus,
    stopPolling,
    fetchValidationHistory,
    compareValidations,
    compareVersions,
    exportToJson,
    exportToPdf,
    clearCurrentIdea,
    clearCurrentValidation,
    clearErrors,
  };

  return <ValidationContext.Provider value={value}>{children}</ValidationContext.Provider>;
}

export function useValidation() {
  const context = useContext(ValidationContext);
  if (context === undefined) {
    throw new Error('useValidation must be used within a ValidationProvider');
  }
  return context;
}
