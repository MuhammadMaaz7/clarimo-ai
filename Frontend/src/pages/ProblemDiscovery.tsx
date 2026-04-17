import { useState, useEffect, useRef } from 'react';
import ProblemForm, { FormData, ProblemFormRef } from '../components/ProblemForm';
import SimpleLoadingStatus from '../components/SimpleLoadingStatus';
import PainPointsDisplay from '../components/PainPointsDisplay';
import { PremiumButton } from '../components/ui/premium/PremiumButton';
import { PremiumCard } from '../components/ui/premium/PremiumCard';
import { Sparkles, X, RotateCcw } from 'lucide-react';
import { useAnalysis } from '../contexts/AnalysisContext';
import { api, ApiError } from '../lib/api';
import { getBackgroundTaskMonitor, TaskType } from '../services/BackgroundTaskMonitor';
import { motion, AnimatePresence } from 'framer-motion';
import { ModuleHeader } from '../components/ui/ModuleHeader';

const ProblemDiscovery = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [isValidationError, setIsValidationError] = useState(false);
  const [validationMessage, setValidationMessage] = useState('');
  const statusPollingIntervalRef = useRef<number | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const { currentAnalysis, setCurrentAnalysis, clearAnalysis, hasActiveAnalysis } = useAnalysis();
  const problemFormRef = useRef<ProblemFormRef>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (statusPollingIntervalRef.current) {
        clearInterval(statusPollingIntervalRef.current);
        statusPollingIntervalRef.current = null;
      }
    };
  }, []);

  const startStatusPolling = (inputId: string) => {
    const pollStatus = async () => {
      try {
        const status = await api.status.getProcessingStatus(inputId);

        const isCompleted =
          status.overall_status === 'completed' ||
          (status.progress_percentage && status.progress_percentage === 100) ||
          status.current_stage === 'completed';

        if (isCompleted) {
          if (statusPollingIntervalRef.current) {
            clearInterval(statusPollingIntervalRef.current);
            statusPollingIntervalRef.current = null;
          }
          const taskMonitor = getBackgroundTaskMonitor();
          taskMonitor.unregisterTask(`problem_discovery_${inputId}`);
          const painPointsCount = status.pain_points_count || 5;
          setCurrentAnalysis({
            inputId,
            query: currentQuery,
            timestamp: Date.now(),
            painPointsCount,
            totalClusters: painPointsCount,
          });
          setIsLoading(false);
        } else if (status.overall_status === 'failed' || status.overall_status === 'error') {
          if (statusPollingIntervalRef.current) {
            clearInterval(statusPollingIntervalRef.current);
            statusPollingIntervalRef.current = null;
          }
          const taskMonitor = getBackgroundTaskMonitor();
          taskMonitor.unregisterTask(`problem_discovery_${inputId}`);
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Error polling status:', error);
        if (statusPollingIntervalRef.current) {
          clearInterval(statusPollingIntervalRef.current);
          statusPollingIntervalRef.current = null;
        }
        setIsLoading(false);
      }
    };

    const interval = setInterval(pollStatus, 3000);
    statusPollingIntervalRef.current = interval as unknown as number;
    pollStatus(); // initial poll
  };

  const handleSubmit = async (data: FormData) => {
    setIsLoading(true);
    setHasSearched(true);
    setIsValidationError(false);
    setValidationMessage('');
    clearAnalysis();
    setCurrentQuery(data.problemDescription);

    try {
      const result = await api.problems.discover(data);
      if (result.success && result.input_id) {
        const taskMonitor = getBackgroundTaskMonitor();
        taskMonitor.registerTask({
          id: `problem_discovery_${result.input_id}`,
          type: TaskType.PROBLEM_DISCOVERY,
          startTime: new Date(),
          description: `Problem discovery for: ${data.problemDescription.substring(0, 50)}...`,
        });
        startStatusPolling(result.input_id);
      } else {
        setIsLoading(false);
      }
    } catch (error) {
      if (error instanceof ApiError) {
        setIsValidationError(true);
        setValidationMessage(
          error.status === 409
            ? 'Processing already in progress for this input. Please wait.'
            : error.message
        );
      } else {
        setIsValidationError(true);
        setValidationMessage('Network error. Please check your connection and try again.');
      }
      setIsLoading(false);
    }
  };

  return (
    <div className="responsive-container-dashboard">
      <div className="max-w-4xl mx-auto space-y-8">
        <ModuleHeader
          icon={Sparkles}
          title="Problem Discovery"
          description={
            !hasSearched && !hasActiveAnalysis 
              ? "Discover real problems from online communities and identify untapped business opportunities."
              : "Search for new problems or view current results."
          }
          actions={
            (hasSearched || hasActiveAnalysis) && (
              <PremiumButton
                 variant="outlined"
                 onClick={() => {
                   setHasSearched(false);
                   setIsValidationError(false);
                   setValidationMessage('');
                 }}
              >
                <RotateCcw className="mr-2 h-4 w-4" /> New Search
              </PremiumButton>
            )
          }
        />

        <div className="space-y-6">
          <ProblemForm
            ref={problemFormRef}
            onSubmit={handleSubmit}
            isLoading={isLoading}
            compact={hasSearched || hasActiveAnalysis}
          />

          {(isLoading || isValidationError) && (
            <SimpleLoadingStatus
              isValidationError={isValidationError}
              validationMessage={validationMessage}
              onRetry={() => {
                setIsValidationError(false);
                setValidationMessage('');
                setHasSearched(false);
              }}
            />
          )}
        </div>

        {/* Results Section */}
        <AnimatePresence>
          {!isLoading && hasActiveAnalysis && currentAnalysis && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              <PremiumCard variant="glass" className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">Analysis Results</h3>
                  <p className="text-sm text-muted-foreground mt-0.5">"{currentAnalysis.query}"</p>
                  <p className="text-xs text-muted-foreground/60 mt-0.5">
                    {currentAnalysis.painPointsCount} problems found
                  </p>
                </div>
                <PremiumButton
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    clearAnalysis();
                    setHasSearched(false);
                    problemFormRef.current?.resetForm();
                  }}
                  aria-label="Close results"
                >
                  <X className="h-5 w-5" />
                </PremiumButton>
              </PremiumCard>

              <PainPointsDisplay inputId={currentAnalysis.inputId} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* No Results */}
        {!isLoading && hasSearched && !hasActiveAnalysis && !isValidationError && (
          <PremiumCard variant="default" className="text-center py-16 border-dashed border-[#442754]">
            <Sparkles className="h-10 w-10 mx-auto text-fuchsia-200/20 mb-4" />
            <p className="text-muted-foreground font-medium">No problems found.</p>
            <p className="text-sm text-muted-foreground/50 mt-1">Try adjusting your search criteria.</p>
          </PremiumCard>
        )}
      </div>
    </div>
  );
};

export default ProblemDiscovery;
