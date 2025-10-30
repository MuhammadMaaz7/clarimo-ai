import { useState, useEffect } from 'react';
import ProblemForm, { FormData } from '../components/ProblemForm';
import SimpleLoadingStatus from '../components/SimpleLoadingStatus';
import PainPointsDisplay from '../components/PainPointsDisplay';
import { Sparkles } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api, ApiError } from '../lib/api';
import { getBackgroundTaskMonitor, TaskType } from '../services/BackgroundTaskMonitor';

interface Problem {
  id: number;
  title: string;
  description: string;
  subreddit: string;
  score: number;
}

interface ProcessingStatus {
  input_id: string;
  overall_status: string;
  progress_percentage: number;
  current_stage: string;
  message: string;
  description: string;
  animation: string;
  next_action: string;
  estimated_time_remaining: string;
  can_view_results: boolean;
  pain_points_available?: boolean;
  pain_points_count?: number;
}

const ProblemDiscovery = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [problems, setProblems] = useState<Problem[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [isValidationError, setIsValidationError] = useState(false);
  const [validationMessage, setValidationMessage] = useState('');
  const [statusPollingInterval, setStatusPollingInterval] = useState<number | null>(null);
  const [showPainPoints, setShowPainPoints] = useState(false);
  const { user } = useAuth();

  // Removed mock data - now uses real API responses only

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (statusPollingInterval) {
        clearInterval(statusPollingInterval);
      }
    };
  }, [statusPollingInterval]);

  // Poll for processing status
  const startStatusPolling = (requestId: string) => {
    const pollStatus = async () => {
      try {
        const status = await api.status.getProcessingStatus(requestId);
        setProcessingStatus(status);

        if (status.overall_status === 'completed' && status.can_view_results) {
          // Stop polling and fetch results
          if (statusPollingInterval) {
            clearInterval(statusPollingInterval);
            setStatusPollingInterval(null);
          }

          // Unregister background task
          const taskMonitor = getBackgroundTaskMonitor();
          const taskId = `problem_discovery_${requestId}`;
          taskMonitor.unregisterTask(taskId);

          try {
            const results = await api.problems.getResults(requestId);
            if (results.success && results.data?.problems) {
              const transformedProblems = results.data.problems.map((problem: any) => ({
                id: problem.id,
                title: problem.title,
                description: problem.description,
                subreddit: problem.source?.replace('r/', '') || 'unknown',
                score: problem.score || 0
              }));
              setProblems(transformedProblems);
            }
          } catch (error) {
            console.error('Error fetching results:', error);
          }

          // Check if pain points are available
          if (status.pain_points_available && status.pain_points_count && status.pain_points_count > 0) {
            setShowPainPoints(true);
          }

          setIsLoading(false);
        } else if (status.overall_status === 'failed' || status.overall_status === 'error') {
          // Unregister background task on failure
          const taskMonitor = getBackgroundTaskMonitor();
          const taskId = `problem_discovery_${requestId}`;
          taskMonitor.unregisterTask(taskId);

          setIsLoading(false);
        }
      } catch (error) {
        console.error('Error polling status:', error);
        if (statusPollingInterval) {
          clearInterval(statusPollingInterval);
          setStatusPollingInterval(null);
        }
        setIsLoading(false);
      }
    };

    // Poll every 3 seconds
    const interval = setInterval(pollStatus, 3000);
    setStatusPollingInterval(interval as unknown as number);

    // Initial poll
    pollStatus();
  };

  const handleSubmit = async (data: FormData) => {
    setIsLoading(true);
    setHasSearched(true);
    setProblems([]);
    setProcessingStatus(null);
    setIsValidationError(false);
    setValidationMessage('');

    try {
      const result = await api.problems.discover(data);

      if (result.success && result.request_id) {
        setCurrentRequestId(result.request_id);

        // Register background task for session protection
        const taskMonitor = getBackgroundTaskMonitor();

        const taskId = `problem_discovery_${result.request_id}`;
        taskMonitor.registerTask({
          id: taskId,
          type: TaskType.PROBLEM_DISCOVERY,
          startTime: new Date(),
          description: `Problem discovery for: ${data.problemDescription.substring(0, 50)}...`
        });

        // Start polling for status updates
        startStatusPolling(result.request_id);

        // Set initial processing status from response
        if (result.data) {
          setProcessingStatus({
            input_id: result.request_id,
            overall_status: result.data.status || 'processing',
            progress_percentage: result.data.progress_percentage || 10,
            current_stage: result.data.current_stage || 'keyword_generation',
            message: result.message || 'Processing started...',
            description: 'Your request is being processed in the background.',
            animation: result.data.animation || 'startup',
            next_action: 'Please wait while we process your request...',
            estimated_time_remaining: result.data.estimated_completion_time || '10-15 minutes',
            can_view_results: false
          });
        }
      } else {
        console.error('API response format error:', result);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error calling problem discovery API:', error);
      if (error instanceof ApiError) {
        // Handle validation failures
        setIsValidationError(true);
        setValidationMessage(error.message);
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
      {!hasSearched && (
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
      {hasSearched && (
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
                setShowPainPoints(false);
                setIsValidationError(false);
                setValidationMessage('');
              }}
              className="px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 rounded-lg transition-colors text-sm"
            >
              New Search
            </button>
          </div>
        </div>
      )}

      {/* Form - Full size when no results, compact when results exist */}
      <div className={hasSearched ? "mb-4" : ""}>
        <ProblemForm onSubmit={handleSubmit} isLoading={isLoading} compact={hasSearched} />
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
      {!isLoading && showPainPoints && currentRequestId && (
        <div className="mt-6 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <PainPointsDisplay inputId={currentRequestId} />
        </div>
      )}

      {/* No Results Message */}
      {!isLoading && hasSearched && !showPainPoints && !isValidationError && (
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
