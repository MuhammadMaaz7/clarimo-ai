import { useState, useCallback, useRef } from 'react';
import { unifiedToast } from '../lib/toast-utils';

interface UseAsyncActionOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  successMessage?: string;
  errorMessage?: string;
  loadingMessage?: string;
}

/**
 * A stable async action hook.
 * Options are stored in a ref so `execute` never changes its reference,
 * preventing dependency-cascade infinite loops in consuming hooks.
 */
export function useAsyncAction<T = any>(options: UseAsyncActionOptions<T> = {}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const loadingToastId = useRef<string | number | null>(null);

  // Store options in a ref so `execute` doesn't need options in its dep array
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // execute is now a STABLE reference — it will never be recreated
  const execute = useCallback(
    async (action: () => Promise<T>): Promise<T | null> => {
      const opts = optionsRef.current;
      setLoading(true);
      setError(null);

      if (opts.loadingMessage) {
        loadingToastId.current = unifiedToast.loading({
          description: opts.loadingMessage,
        });
      }

      try {
        const result = await action();

        if (loadingToastId.current !== null) {
          unifiedToast.dismiss(loadingToastId.current);
        }

        if (opts.successMessage) {
          unifiedToast.success({
            description: opts.successMessage,
          });
        }

        opts.onSuccess?.(result);
        return result;
      } catch (err) {
        if (loadingToastId.current !== null) {
          unifiedToast.dismiss(loadingToastId.current);
        }

        const error = err instanceof Error ? err : new Error('An unexpected error occurred');
        setError(error);

        const displayMessage = opts.errorMessage || error.message || 'Operation failed. Please try again.';

        unifiedToast.error({
          title: 'Action Failed',
          description: displayMessage,
        });

        opts.onError?.(error);
        return null;
      } finally {
        setLoading(false);
        loadingToastId.current = null;
      }
    },
    [] // ← empty: execute is permanently stable
  );

  return {
    loading,
    error,
    execute,
    setLoading,
  };
}
