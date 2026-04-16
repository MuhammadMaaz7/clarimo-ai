import { useState, useCallback, useEffect } from 'react';
import { api } from '../lib/api';
import { useAsyncAction } from './useAsyncAction';

interface HistoryItem {
  input_id: string;
  original_query: string;
  pain_points_count: number;
  total_clusters: number;
  created_at: string;
}

interface UserStats {
  total_analyses: number;
  total_pain_points: number;
  total_clusters: number;
  latest_analysis: string | null;
}

export function useDiscoveredProblems() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const { execute: fetchMetadata, loading: isLoading } = useAsyncAction({
    loadingMessage: 'Synchronizing discovery history...',
    errorMessage: 'Failed to access the discovery archives.'
  });

  const { execute: deleteAction, loading: isDeleting } = useAsyncAction({
    successMessage: 'Environmental data purged.',
    loadingMessage: 'Deleting discovery entry...'
  });

  const loadData = useCallback(async () => {
    await fetchMetadata(async () => {
      const [historyResponse, statsResponse] = await Promise.all([
        api.painPoints.getHistory(),
        api.painPoints.getStats()
      ]);

      if (historyResponse.success) setHistory(historyResponse.history);
      if (statsResponse.success) setStats(statsResponse.stats);
    });
  }, [fetchMetadata]);

  const deleteAnalysis = useCallback(async (inputId: string) => {
    const success = await deleteAction(() => api.userInputs.deleteAnalysis(inputId));
    if (success !== null) {
      await loadData();
    }
  }, [deleteAction, loadData]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredHistory = history.filter((item) => {
    if (!searchQuery) return true;
    return item.original_query.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return {
    history,
    filteredHistory,
    stats,
    isLoading,
    isDeleting,
    searchQuery,
    setSearchQuery,
    deleteAnalysis,
    refresh: loadData
  };
}
