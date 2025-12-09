import { useState, useEffect, useRef } from 'react';
import ProblemForm, { FormData, ProblemFormRef } from '../components/ProblemForm';
import SimpleLoadingStatus from '../components/SimpleLoadingStatus';
import PainPointsDisplay from '../components/PainPointsDisplay';
import { Button } from '../components/ui/button';
import { X } from 'lucide-react';
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
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="space-y-6">
        {/* Header - Always visible */}
        {!hasSearched && !hasActiveAnalysis && (
          <div className="text-center space-y-2 mb-8">
            <h1 className="text-3xl font-bold">Problem Discovery</h1>
            <p className="text-muted-foreground">
              Discover real problems from online communities and identify business opportunities
            </p>
          </div>
        )}

        {/* Compact Header - When results exist */}
        {(hasSearched || hasActiveAnalysis) && (
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">Problem Discovery</h2>
              <p className="text-sm text-muted-foreground">Search for new problems or view current results</p>
            </div>
            <Button
              onClick={() => {
                setHasSearched(false);
                setIsValidationError(false);
                setValidationMessage('');
              }}
              variant="outline"
            >
              New Search
            </Button>
          </div>
        )}

        {/* Form */}
        <ProblemForm
          ref={problemFormRef}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          compact={hasSearched || hasActiveAnalysis}
        />

        {/* Loading Status */}
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

        {/* Results Display */}
        {!isLoading && hasActiveAnalysis && currentAnalysis && (
          <div className="space-y-6">
            {/* Results Header */}
            <div className="flex items-center justify-between glass border-border/50 rounded-xl p-4">
              <div>
                <h3 className="text-lg font-semibold">Analysis Results</h3>
                <p className="text-sm text-muted-foreground">"{currentAnalysis.query}"</p>
                <p className="text-xs text-muted-foreground">
                  {currentAnalysis.painPointsCount} problems found
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  clearAnalysis();
                  setHasSearched(false);
                  problemFormRef.current?.resetForm();
                }}
                title="Close results and clear inputs"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <PainPointsDisplay inputId={currentAnalysis.inputId} />
          </div>
        )}

        {/* No Results Message */}
        {!isLoading && hasSearched && !hasActiveAnalysis && !isValidationError && (
          <div className="glass border-border/50 rounded-xl p-12 text-center">
            <p className="text-muted-foreground">
              No problems found. Try adjusting your search criteria.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProblemDiscovery;
