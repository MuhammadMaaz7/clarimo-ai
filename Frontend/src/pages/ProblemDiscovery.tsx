import { useState, useEffect, useRef } from 'react';
import ProblemForm, { FormData, ProblemFormRef } from '../components/ProblemForm';
import SimpleLoadingStatus from '../components/SimpleLoadingStatus';
import PainPointsDisplay from '../components/PainPointsDisplay';
import { Sparkles, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useAnalysis } from '../contexts/AnalysisContext';
import { api, ApiError } from '../lib/api';
import { getBackgroundTaskMonitor, TaskType } from '../services/BackgroundTaskMonitor';

const ProblemDiscovery = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [isValidationError, setIsValidationError] = useState(false);
  const [validationMessage, setValidationMessage] = useState('');
  const statusPollingIntervalRef = useRef<number | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const { user } = useAuth();
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

  // Poll for processing status
  const startStatusPolling = (inputId: string) => {
    const pollStatus = async () => {
      try {
        const status = await api.status.getProcessingStatus(inputId);

        // 🔍 DEBUG: Log the entire status response
        console.log('🔍 FULL STATUS RESPONSE:', JSON.stringify(status, null, 2));

        // ✅ FIXED: Use only the properties that exist in the type
        const isCompleted = status.overall_status === 'completed' ||
          (status.progress_percentage && status.progress_percentage === 100) ||
          status.current_stage === 'completed';

        const canShowResults = status.can_view_results ||
          status.pain_points_available ||
          (status.pain_points_count && status.pain_points_count > 0);

        console.log('✅ Completion Check:', {
          isCompleted,
          overall_status: status.overall_status,
          progress_percentage: status.progress_percentage,
          current_stage: status.current_stage,
          canShowResults,
          can_view_results: status.can_view_results,
          pain_points_available: status.pain_points_available,
          pain_points_count: status.pain_points_count
        });

        if (isCompleted) {
          console.log('🎉 PROCESSING COMPLETED! Stopping polling...');

          // Stop polling
          if (statusPollingIntervalRef.current) {
            clearInterval(statusPollingIntervalRef.current);
            statusPollingIntervalRef.current = null;
          }

          // Unregister background task
          const taskMonitor = getBackgroundTaskMonitor();
          const taskId = `problem_discovery_${inputId}`;
          taskMonitor.unregisterTask(taskId);

          // Always set analysis when completed - use actual count or fallback
          const painPointsCount = status.pain_points_count || 5;
          console.log('📊 Setting analysis with pain points:', painPointsCount);

          setCurrentAnalysis({
            inputId: inputId,
            query: currentQuery,
            timestamp: Date.now(),
            painPointsCount: painPointsCount,
            totalClusters: painPointsCount
          });

          setIsLoading(false);
        } else if (status.overall_status === 'failed' || status.overall_status === 'error') {
          console.log('❌ PROCESSING FAILED! Stopping polling...');

          // Stop polling on failure
          if (statusPollingIntervalRef.current) {
            clearInterval(statusPollingIntervalRef.current);
            statusPollingIntervalRef.current = null;
          }

          // Unregister background task on failure
          const taskMonitor = getBackgroundTaskMonitor();
          const taskId = `problem_discovery_${inputId}`;
          taskMonitor.unregisterTask(taskId);

          setIsLoading(false);
        } else {
          console.log('🔄 Still processing... current status:', status.overall_status);
        }
      } catch (error) {
        console.error('❌ Error polling status:', error);
        if (statusPollingIntervalRef.current) {
          clearInterval(statusPollingIntervalRef.current);
          statusPollingIntervalRef.current = null;
        }
        setIsLoading(false);
      }
    };

    // Poll every 3 seconds
    const interval = setInterval(pollStatus, 3000);
    statusPollingIntervalRef.current = interval as unknown as number;

    // Initial poll
    pollStatus();
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

      if (result.success && result.input_id) { // ✅ FIXED: input_id, not request_id
        // Register background task for session protection
        const taskMonitor = getBackgroundTaskMonitor();
        const taskId = `problem_discovery_${result.input_id}`;
        taskMonitor.registerTask({
          id: taskId,
          type: TaskType.PROBLEM_DISCOVERY,
          startTime: new Date(),
          description: `Problem discovery for: ${data.problemDescription.substring(0, 50)}...`
        });

        // Start polling for status updates
        startStatusPolling(result.input_id);

      } else {
        console.error('API response format error:', result);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error calling problem discovery API:', error);
      if (error instanceof ApiError) {
        // Handle validation failures and lock conflicts
        if (error.status === 409) {
          setIsValidationError(true);
          setValidationMessage('Processing already in progress for this input. Please wait for it to complete.');
        } else {
          setIsValidationError(true);
          setValidationMessage(error.message);
        }
      } else {
        setIsValidationError(true);
        setValidationMessage('Network error. Please check your connection and try again.');
      }
      setIsLoading(false);
    }
  };

  return (
    <div className="px-4 md:px-6 lg:px-8 pt-4 pb-8 relative">
      {/* Subtle Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 right-10 w-32 h-32 bg-primary/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-40 left-10 w-24 h-24 bg-accent/5 rounded-full blur-2xl"></div>
      </div>

      <div className="relative z-10">
        {/* Welcome Section - Only show when no results */}
        {!hasSearched && !hasActiveAnalysis && (
          <div className="glass border-border/50 rounded-2xl p-6 md:p-8 text-center glow-sm bg-white/5 backdrop-blur-xl mb-8">
            <div className="mb-4 flex justify-center">
              <div className="rounded-xl bg-gradient-to-br from-accent to-primary p-3 glow-sm shadow-lg">
                <Sparkles className="h-8 w-8 text-white" />
              </div>
            </div>
            <h1 className="mb-3 text-2xl md:text-3xl font-bold text-white animate-in fade-in slide-in-from-bottom-4 duration-700">
              Welcome back, {user?.full_name?.split(' ')[0]}
            </h1>
            <p className="mx-auto max-w-2xl text-base text-muted-foreground leading-relaxed animate-in fade-in slide-in-from-bottom-4 duration-700 delay-150">
              Discover real problems from online communities and identify business opportunities
            </p>
          </div>
        )}

        {/* Compact Search Bar - Always visible at top when results exist */}
        {(hasSearched || hasActiveAnalysis) && (
          <div className="glass border-border/50 rounded-xl p-4 bg-white/5 backdrop-blur-xl mb-6 sticky top-4 z-10">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-gradient-to-br from-accent to-primary p-2">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-white">Problem Discovery</h2>
                <p className="text-sm text-muted-foreground">Search for new problems or view current results</p>
              </div>
              <button
                onClick={() => {
                  setHasSearched(false);
                  setIsValidationError(false);
                  setValidationMessage('');
                  // Don't clear analysis here - let user explicitly close it
                }}
                className="px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 rounded-lg transition-colors text-sm"
              >
                New Search
              </button>
            </div>
          </div>
        )}

        {/* Form - Full size when no results, compact when results exist */}
        <div className={(hasSearched || hasActiveAnalysis) ? "mb-4" : ""}>
          <ProblemForm
            ref={problemFormRef}
            onSubmit={handleSubmit}
            isLoading={isLoading}
            compact={hasSearched || hasActiveAnalysis}
          />
        </div>



        {/* Loading Status - Appears right below form */}
        {(isLoading || isValidationError) && (
          <div className="mt-6">
            <SimpleLoadingStatus
              isValidationError={isValidationError}
              validationMessage={validationMessage}
              onRetry={() => {
                setIsValidationError(false);
                setValidationMessage('');
                setHasSearched(false);
              }}
            />
          </div>
        )}

        {/* Results Display - Appears right below form/loading */}
        {!isLoading && hasActiveAnalysis && currentAnalysis && (
          <div className="mt-6 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Results Header with Actions */}
            <div className="flex items-center justify-between bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <Sparkles className="h-5 w-5 text-blue-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">Analysis Results</h3>
                  <p className="text-sm text-gray-300 mb-1">"{currentAnalysis.query}"</p>
                  <p className="text-sm text-gray-400">
                    {currentAnalysis.painPointsCount} problems found
                  </p>
                </div>
              </div>
              <button
                onClick={() => {
                  clearAnalysis();
                  setHasSearched(false);
                  problemFormRef.current?.resetForm();
                }}
                className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                title="Close results and clear inputs"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <PainPointsDisplay inputId={currentAnalysis.inputId} />
          </div>
        )}

        {/* No Results Message */}
        {!isLoading && hasSearched && !hasActiveAnalysis && !isValidationError && (
          <div className="glass rounded-2xl border-dashed border-2 border-border/50 p-16 text-center">
            <p className="text-muted-foreground text-lg">
              No problems found. Try adjusting your search criteria.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProblemDiscovery;
