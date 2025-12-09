/**
 * Unified Toast Utilities
 * Consistent toast notifications across the application
 */

import { toast as sonnerToast } from 'sonner';

interface ToastOptions {
  title?: string;
  description: string;
  duration?: number;
}

export const unifiedToast = {
  success: ({ title = 'Success', description, duration = 4000 }: ToastOptions) => {
    sonnerToast.success(title, {
      description,
      duration,
    });
  },

  error: ({ title = 'Error', description, duration = 5000 }: ToastOptions) => {
    sonnerToast.error(title, {
      description,
      duration,
    });
  },

  info: ({ title = 'Info', description, duration = 4000 }: ToastOptions) => {
    sonnerToast.info(title, {
      description,
      duration,
    });
  },

  warning: ({ title = 'Warning', description, duration = 4000 }: ToastOptions) => {
    sonnerToast.warning(title, {
      description,
      duration,
    });
  },

  loading: ({ title = 'Loading', description }: Omit<ToastOptions, 'duration'>) => {
    return sonnerToast.loading(title, {
      description,
    });
  },

  promise: <T,>(
    promise: Promise<T>,
    {
      loading,
      success,
      error,
    }: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    }
  ) => {
    return sonnerToast.promise(promise, {
      loading,
      success,
      error,
    });
  },
};

export default unifiedToast;
