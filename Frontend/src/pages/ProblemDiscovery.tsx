import { useState, useEffect } from 'react';
import ProblemForm, { FormData } from '../components/ProblemForm';

import LoadingSpinner from '../components/LoadingSpinner';
import ProcessingStatus from '../components/ProcessingStatus';
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
        // Handle specific API errors (like token expiration)
        console.error('API Error:', error.message);
      }
      setIsLoading(false);
    }
  };

  return (
    <div className="responsive-spacing-md pb-8">
      {/* Hero Section */}
      <div className="glass border-border/50 rounded-2xl p-8 md:p-12 text-center glow-sm bg-white/5 backdrop-blur-xl">
        <div className="mb-6 flex justify-center">
          <div className="rounded-2xl bg-gradient-to-br from-accent to-primary p-4 glow-sm shadow-lg">
            <Sparkles className="h-10 w-10 text-white" />
          </div>
        </div>
        <h1 className="mb-4 text-3xl md:text-5xl font-bold text-white animate-in fade-in slide-in-from-bottom-4 duration-700">
          Welcome back, {user?.full_name?.split(' ')[0]}!
        </h1>
        <p className="mx-auto max-w-2xl text-base md:text-lg text-muted-foreground leading-relaxed animate-in fade-in slide-in-from-bottom-4 duration-700 delay-150">
          Uncover real problems from online communities and identify opportunities worth pursuing
        </p>
      </div>

      {/* Form */}
      <ProblemForm onSubmit={handleSubmit} isLoading={isLoading} />

      {/* Interactive Processing Status */}
      {isLoading && processingStatus && <ProcessingStatus status={processingStatus} />}

      {/* Simple Loading for non-status cases */}
      {isLoading && !processingStatus && <LoadingSpinner size="lg" />}

      {/* Pain Points Display - Priority Display */}
      {!isLoading && showPainPoints && currentRequestId && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <PainPointsDisplay inputId={currentRequestId} />
        </div>
      )}





      {!isLoading && hasSearched && !showPainPoints && (
        <div className="glass rounded-2xl border-dashed border-2 border-border/50 p-16 text-center">
          <p className="text-muted-foreground text-lg">
            No problems found. Try adjusting your search criteria.
          </p>
        </div>
      )}
    </div>
  );
};

export default ProblemDiscovery;
