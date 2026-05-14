import { useState, useCallback, useEffect } from 'react';
import { api } from '../lib/api';
import { useAsyncAction } from './useAsyncAction';
import { Score } from '../types/validation';

interface ValidationResult {
  validation_id: string;
  idea_id: string;
  user_id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  overall_score: number | null;
  individual_scores: {
    problem_clarity?: Score;
    market_demand?: Score;
    solution_fit?: Score;
    differentiation?: Score;
  } | null;
  report_data: any | null;
  created_at: string;
  error_message: string | null;
}

interface ValidationStatus {
  status: string;
  progress: number;
  current_stage: string;
}

export function useIdeaValidation(ideaId?: string) {
  const [idea, setIdea] = useState<any>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [status, setStatus] = useState<ValidationStatus | null>(null);
  
  const { execute: execFetch, loading: loadingIdea } = useAsyncAction();
  const { execute: execStatus, loading: loadingStatus } = useAsyncAction();
  
  const { execute: execAction, loading: isActionRunning } = useAsyncAction({
    loadingMessage: 'Processing validation request...',
    successMessage: 'Action priority established'
  });

  const fetchValidation = useCallback(async (validationId: string) => {
    const result = await execStatus(() => api.validations.getResult(validationId));
    if (result) {
      console.log('✓ Fetched validation:', {
        validation_id: result.validation_id,
        status: result.status,
        overall_score: result.overall_score,
        has_individual_scores: !!result.individual_scores,
        has_report_data: !!result.report_data,
      });
      setValidation(result);
    }
  }, [execStatus]);

  const fetchIdea = useCallback(async (id: string) => {
    const result = await execFetch(() => api.ideas.getById(id));
    if (result) {
      console.log('✓ Fetched idea:', {
        id: result.id,
        title: result.title,
        has_latest_validation: !!result.latest_validation,
        latest_validation_id: result.latest_validation?.validation_id,
      });
      setIdea(result);
      // If the idea has a latest validation, fetch it
      if (result.latest_validation?.validation_id) {
        console.log('→ Fetching validation:', result.latest_validation.validation_id);
        fetchValidation(result.latest_validation.validation_id);
      }
    }
  }, [execFetch, fetchValidation]);

  const pollStatus = useCallback(async (validationId: string) => {
    try {
      const result = await api.validations.getStatus(validationId);
      if (result) {
        setStatus(result);
        if (result.status === 'completed') {
          fetchValidation(validationId);
          return true;
        }
        if (result.status === 'failed') {
          return true;
        }
      }
    } catch (e) {
      console.error('Polling error:', e);
    }
    return false;
  }, [fetchValidation]);

  const startValidation = async (config?: any) => {
    if (!ideaId) return;
    const result = await execAction(() => api.validations.validate(ideaId, config));
    if (result) {
      setValidation(result);
      setStatus({ status: 'pending', progress: 0, current_stage: 'Starting' });
    }
  };

  const exportReport = async (format: 'json' | 'pdf') => {
    if (!validation?.validation_id) return;

    await execAction(async () => {
      if (format === 'json') {
        const data = await api.validations.exportJson(validation.validation_id);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `validation-${validation.validation_id}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        const blob = await api.validations.exportPdf(validation.validation_id);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `validation-${validation.validation_id}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    });
  };

  useEffect(() => {
    if (ideaId) fetchIdea(ideaId);
  }, [ideaId, fetchIdea]);

  useEffect(() => {
    let interval: any;
    if (validation?.validation_id && (status?.status === 'pending' || status?.status === 'in_progress')) {
      interval = setInterval(async () => {
        const done = await pollStatus(validation.validation_id);
        if (done) clearInterval(interval);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [validation?.validation_id, status?.status, pollStatus]);

  return {
    idea,
    validation,
    status,
    loading: loadingIdea || loadingStatus,
    isActionRunning,
    startValidation,
    exportReport,
    fetchIdea,
    fetchValidation
  };
}
