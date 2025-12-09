/**
 * User-friendly error display component
 * Shows appropriate messages and actions based on error type
 */

import React from 'react';
import { AlertCircle, RefreshCw, Wifi, WifiOff } from 'lucide-react';

interface ErrorDisplayProps {
  error: string | null;
  onRetry?: () => void;
  variant?: 'inline' | 'card' | 'banner';
  showIcon?: boolean;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  variant = 'card',
  showIcon = true,
}) => {
  if (!error) return null;

  // Determine error type and appropriate icon
  const isNetworkError = error.toLowerCase().includes('network') || 
                        error.toLowerCase().includes('connection') ||
                        error.toLowerCase().includes('internet');
  
  const isTimeoutError = error.toLowerCase().includes('timeout') ||
                        error.toLowerCase().includes('timed out');
  
  const isServerError = error.toLowerCase().includes('server') ||
                       error.toLowerCase().includes('unavailable');

  const Icon = isNetworkError ? WifiOff : AlertCircle;

  // Enhance error message with helpful context
  let displayMessage = error;
  let helpText = '';

  if (isNetworkError) {
    helpText = 'Please check your internet connection and try again.';
  } else if (isTimeoutError) {
    helpText = 'The request took too long. Please try again.';
  } else if (isServerError) {
    helpText = 'Our servers are experiencing issues. Please try again in a moment.';
  }

  // Render based on variant
  if (variant === 'inline') {
    return (
      <div className="flex items-start gap-2 text-sm text-red-600">
        {showIcon && <Icon className="w-4 h-4 mt-0.5 flex-shrink-0" />}
        <div>
          <p>{displayMessage}</p>
          {helpText && <p className="text-xs text-gray-500 mt-1">{helpText}</p>}
        </div>
      </div>
    );
  }

  if (variant === 'banner') {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4">
        <div className="flex items-start">
          {showIcon && (
            <Icon className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          )}
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-red-800">{displayMessage}</p>
            {helpText && (
              <p className="text-sm text-red-700 mt-1">{helpText}</p>
            )}
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="ml-3 flex items-center gap-1 text-sm font-medium text-red-600 hover:text-red-800"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  // Default: card variant
  return (
    <div className="bg-white border border-red-200 rounded-lg p-6 shadow-sm">
      <div className="flex items-start gap-4">
        {showIcon && (
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <Icon className="w-6 h-6 text-red-600" />
            </div>
          </div>
        )}
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {isNetworkError ? 'Connection Error' : 'Something went wrong'}
          </h3>
          <p className="text-gray-700 mb-2">{displayMessage}</p>
          {helpText && (
            <p className="text-sm text-gray-600 mb-4">{helpText}</p>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Loading state with retry information
 */
interface LoadingWithRetryProps {
  isRetrying: boolean;
  retryCount: number;
  message?: string;
}

export const LoadingWithRetry: React.FC<LoadingWithRetryProps> = ({
  isRetrying,
  retryCount,
  message = 'Loading...',
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
      <p className="text-gray-700 font-medium">{message}</p>
      {isRetrying && (
        <p className="text-sm text-gray-500 mt-2">
          Retrying... (Attempt {retryCount})
        </p>
      )}
    </div>
  );
};

/**
 * Fallback message for when LLM services are unavailable
 */
export const LLMFallbackNotice: React.FC = () => {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-start gap-3">
        <Wifi className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm font-medium text-blue-900">
            Using Alternative Analysis Method
          </p>
          <p className="text-sm text-blue-700 mt-1">
            AI-powered analysis is temporarily unavailable. We're using our backup analysis system to provide you with results.
          </p>
        </div>
      </div>
    </div>
  );
};
