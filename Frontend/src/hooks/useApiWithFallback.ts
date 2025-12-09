/**
 * Custom hook for API calls with graceful error handling
 * Provides user-friendly error messages and automatic retry logic
 */

import { useState, useCallback } from 'react';
import { ApiError } from '../lib/api';

interface UseApiOptions {
  retryAttempts?: number;
  retryDelay?: number;
  showGenericError?: boolean;
}

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  isRetrying: boolean;
  retryCount: number;
}

export function useApiWithFallback<T = any>(options: UseApiOptions = {}) {
  const {
    retryAttempts = 2,
    retryDelay = 1000,
    showGenericError = true,
  } = options;

  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null,
    isRetrying: false,
    retryCount: 0,
  });

  const execute = useCallback(
    async (apiCall: () => Promise<T>): Promise<T | null> => {
      setState({
        data: null,
        loading: true,
        error: null,
        isRetrying: false,
        retryCount: 0,
      });

      let lastError: Error | null = null;

      for (let attempt = 0; attempt <= retryAttempts; attempt++) {
        try {
          if (attempt > 0) {
            setState((prev) => ({
              ...prev,
              isRetrying: true,
              retryCount: attempt,
            }));

            // Wait before retrying
            await new Promise((resolve) => setTimeout(resolve, retryDelay * attempt));
          }

          const result = await apiCall();

          setState({
            data: result,
            loading: false,
            error: null,
            isRetrying: false,
            retryCount: attempt,
          });

          return result;
        } catch (error) {
          lastError = error as Error;

          // Don't retry on auth errors
          if (error instanceof ApiError && error.status === 401) {
            setState({
              data: null,
              loading: false,
              error: error.message,
              isRetrying: false,
              retryCount: attempt,
            });
            return null;
          }

          // Continue to next retry attempt
          if (attempt < retryAttempts) {
            console.log(`API call failed, retrying (${attempt + 1}/${retryAttempts})...`);
            continue;
          }
        }
      }

      // All retries failed
      const errorMessage = lastError instanceof ApiError
        ? lastError.message
        : showGenericError
        ? 'Unable to complete the request. Please try again later.'
        : lastError?.message || 'An error occurred';

      setState({
        data: null,
        loading: false,
        error: errorMessage,
        isRetrying: false,
        retryCount: retryAttempts,
      });

      return null;
    },
    [retryAttempts, retryDelay, showGenericError]
  );

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      isRetrying: false,
      retryCount: 0,
    });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

/**
 * Hook specifically for LLM-powered features
 * Shows appropriate messages when LLM services are unavailable
 */
export function useLLMApiWithFallback<T = any>() {
  const api = useApiWithFallback<T>({
    retryAttempts: 1, // LLM calls are expensive, retry once only
    retryDelay: 2000,
    showGenericError: false,
  });

  const executeLLM = useCallback(
    async (apiCall: () => Promise<T>): Promise<T | null> => {
      const result = await api.execute(apiCall);

      // If failed, show LLM-specific message
      if (!result && api.error) {
        // Check if it's a network error
        if (api.error.includes('network') || api.error.includes('connection')) {
          return null; // Let the original error show
        }

        // For other errors, provide context about LLM fallback
        console.info('LLM service unavailable, using fallback analysis');
      }

      return result;
    },
    [api]
  );

  return {
    ...api,
    executeLLM,
  };
}
