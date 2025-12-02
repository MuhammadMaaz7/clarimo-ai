/**
 * ValidationProgress Component
 * 
 * Real-time progress indicator for validation execution.
 * Polls validation status endpoint and updates UI based on status changes.
 * 
 * Requirements: 11.1, 13.1
 */

import { useEffect, useState } from 'react';
import { Sparkles, CheckCircle, Target, AlertCircle, TrendingUp, DollarSign, Shield, Users } from 'lucide-react';
import { useValidation } from '../contexts/ValidationContext';

interface ValidationProgressProps {
  validationId: string;
  ideaTitle: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
  onRetry?: () => void;
}

export function ValidationProgress({
  validationId,
  ideaTitle,
  onComplete,
  onError,
  onRetry,
}: ValidationProgressProps) {
  const { pollValidationStatus, stopPolling, validationProgress, currentValidation, validationError } = useValidation();
  const [currentStage, setCurrentStage] = useState<string>('Initializing');
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<string>('Calculating...');
  const [hasNotifiedCompletion, setHasNotifiedCompletion] = useState(false);
  const [hasNotifiedError, setHasNotifiedError] = useState(false);

  useEffect(() => {
    // Start polling when component mounts
    pollValidationStatus(validationId);

    // Cleanup: stop polling when component unmounts
    return () => {
      stopPolling();
    };
  }, [validationId, pollValidationStatus, stopPolling]);

  useEffect(() => {
    // Update current stage based on progress
    if (validationProgress < 10) {
      setCurrentStage('Initializing validation');
      setEstimatedTimeRemaining('3-5 minutes');
    } else if (validationProgress < 20) {
      setCurrentStage('Analyzing problem clarity');
      setEstimatedTimeRemaining('2-4 minutes');
    } else if (validationProgress < 35) {
      setCurrentStage('Assessing market demand');
      setEstimatedTimeRemaining('2-3 minutes');
    } else if (validationProgress < 50) {
      setCurrentStage('Evaluating solution fit');
      setEstimatedTimeRemaining('1-2 minutes');
    } else if (validationProgress < 60) {
      setCurrentStage('Analyzing differentiation');
      setEstimatedTimeRemaining('1-2 minutes');
    } else if (validationProgress < 70) {
      setCurrentStage('Assessing technical feasibility');
      setEstimatedTimeRemaining('1 minute');
    } else if (validationProgress < 80) {
      setCurrentStage('Estimating market size');
      setEstimatedTimeRemaining('30-60 seconds');
    } else if (validationProgress < 90) {
      setCurrentStage('Evaluating monetization potential');
      setEstimatedTimeRemaining('30 seconds');
    } else if (validationProgress < 95) {
      setCurrentStage('Assessing risks');
      setEstimatedTimeRemaining('15 seconds');
    } else if (validationProgress < 100) {
      setCurrentStage('Generating report');
      setEstimatedTimeRemaining('10 seconds');
    } else {
      setCurrentStage('Completed');
      setEstimatedTimeRemaining('Done');
    }
  }, [validationProgress]);

  useEffect(() => {
    // Handle completion and errors
    if (currentValidation) {
      if (currentValidation.status === 'completed' && !hasNotifiedCompletion) {
        setHasNotifiedCompletion(true);
        if (onComplete) {
          onComplete();
        }
      } else if (currentValidation.status === 'failed' && !hasNotifiedError) {
        setHasNotifiedError(true);
        if (onError) {
          onError(currentValidation.error_message || 'Validation failed');
        }
      }
    }
    
    // Handle polling errors
    if (validationError && !hasNotifiedError) {
      setHasNotifiedError(true);
      if (onError) {
        onError(validationError);
      }
    }
  }, [currentValidation, validationError, onComplete, onError, hasNotifiedCompletion, hasNotifiedError]);

  const getStageIcon = (progress: number) => {
    if (progress < 20) return <Sparkles className="h-8 w-8 text-white" />;
    if (progress < 35) return <TrendingUp className="h-8 w-8 text-white" />;
    if (progress < 50) return <Target className="h-8 w-8 text-white" />;
    if (progress < 70) return <Shield className="h-8 w-8 text-white" />;
    if (progress < 90) return <DollarSign className="h-8 w-8 text-white" />;
    if (progress < 100) return <Users className="h-8 w-8 text-white" />;
    return <CheckCircle className="h-8 w-8 text-white" />;
  };

  const getAnimationClass = (progress: number) => {
    if (progress >= 100) return '';
    if (progress >= 90) return 'animate-pulse';
    return 'animate-spin';
  };

  const stages = [
    { key: 'problem_clarity', icon: '○', label: 'Problem Clarity', range: [0, 20] },
    { key: 'market_demand', icon: '△', label: 'Market Demand', range: [20, 35] },
    { key: 'solution_fit', icon: '□', label: 'Solution Fit', range: [35, 50] },
    { key: 'differentiation', icon: '◇', label: 'Differentiation', range: [50, 70] },
    { key: 'report', icon: '◆', label: 'Report', range: [95, 100] },
  ];

  const getStageStatus = (stageRange: number[]) => {
    const [start, end] = stageRange;
    if (validationProgress >= end) return 'completed';
    if (validationProgress >= start && validationProgress < end) return 'in_progress';
    return 'pending';
  };

  const isError = currentValidation?.status === 'failed';
  const isComplete = currentValidation?.status === 'completed';

  return (
    <div className={`glass rounded-2xl border-border/50 p-8 text-center glow-sm backdrop-blur-xl ${
      isError ? 'bg-red-500/10 border-red-500/30' : 'bg-white/5'
    }`}>
      <div className="mb-6 flex justify-center">
        <div className={`rounded-2xl p-4 glow-sm shadow-lg ${getAnimationClass(validationProgress)} ${
          isError 
            ? 'bg-gradient-to-br from-red-500 to-red-600' 
            : isComplete
              ? 'bg-gradient-to-br from-green-500 to-green-600'
              : 'bg-gradient-to-br from-accent to-primary'
        }`}>
          {isError ? (
            <AlertCircle className="h-8 w-8 text-white" />
          ) : (
            getStageIcon(validationProgress)
          )}
        </div>
      </div>
      
      <h2 className={`text-2xl md:text-3xl font-bold mb-4 ${
        isError ? 'text-red-400' : isComplete ? 'text-green-400' : 'text-white'
      }`}>
        {isError 
          ? 'Validation Failed' 
          : isComplete 
            ? 'Validation Complete!' 
            : `Validating "${ideaTitle}"`
        }
      </h2>
      
      <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
        {isError 
          ? currentValidation?.error_message || 'An error occurred during validation'
          : isComplete
            ? 'Your validation report is ready to view'
            : currentStage
        }
      </p>
      
      {isError && (
        <div className="mb-6 p-4 bg-destructive/10 border border-destructive/30 rounded-lg">
          <p className="text-destructive font-medium mb-2">
            Validation Error
          </p>
          <p className="text-destructive/80 text-sm mb-3">
            {currentValidation?.error_message || validationError || 'Please try again or contact support if the issue persists.'}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-destructive hover:bg-destructive/90 text-destructive-foreground rounded-lg transition-colors duration-200 text-sm font-medium"
            >
              Retry Validation
            </button>
          )}
        </div>
      )}
      
      {/* Progress Bar - Hide for errors */}
      {!isError && (
        <>
          <div className="w-full bg-border/30 rounded-full h-3 mb-4 overflow-hidden">
            <div 
              className={`h-full transition-all duration-1000 ease-out rounded-full glow-sm ${
                isComplete 
                  ? 'bg-gradient-to-r from-green-500 to-green-600'
                  : 'bg-gradient-to-r from-primary to-accent'
              }`}
              style={{ width: `${validationProgress}%` }}
            />
          </div>
          
          <div className="flex justify-between text-sm text-muted-foreground mb-6">
            <span>{validationProgress}% Complete</span>
            <span>ETA: {estimatedTimeRemaining}</span>
          </div>
        </>
      )}
      
      {/* Stage Indicators - Hide for errors */}
      {!isError && (
        <div className="grid grid-cols-3 md:grid-cols-5 gap-3 max-w-4xl mx-auto">
          {stages.map((stage) => {
            const stageStatus = getStageStatus(stage.range);
            const isActive = stageStatus === 'in_progress';
            const isCompleted = stageStatus === 'completed';
            
            return (
              <div 
                key={stage.key}
                className={`p-3 rounded-xl border transition-all duration-300 ${
                  isActive 
                    ? 'border-primary bg-primary/10' 
                    : isCompleted 
                      ? 'border-primary/50 bg-primary/5' 
                      : 'border-border/30 bg-card/20'
                }`}
              >
                <div className="text-2xl mb-1 font-bold text-primary">{stage.icon}</div>
                <div className="text-xs font-medium">{stage.label}</div>
                {isActive && (
                  <div className="text-xs text-primary mt-1">Processing...</div>
                )}
                {isCompleted && (
                  <div className="text-xs text-primary/70 mt-1">Complete</div>
                )}
              </div>
            );
          })}
        </div>
      )}
      
      {isComplete && (
        <div className="mt-6 p-4 bg-primary/10 border border-primary/30 rounded-xl">
          <CheckCircle className="h-6 w-6 text-primary mx-auto mb-2" />
          <p className="text-primary font-medium">Validation Complete!</p>
          <p className="text-sm text-muted-foreground mt-1">
            Your comprehensive validation report is ready. Review your scores and recommendations.
          </p>
        </div>
      )}
      
      <p className="text-sm text-muted-foreground mt-6">
        {isError 
          ? 'You can try validating again or modify your idea details.'
          : isComplete
            ? 'Navigate to the report to see detailed analysis and recommendations.'
            : 'You can navigate away and return later. We\'ll save your progress.'
        }
      </p>
    </div>
  );
}
