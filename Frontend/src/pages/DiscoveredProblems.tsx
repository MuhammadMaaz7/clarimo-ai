import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { History, BarChart3, Calendar, ExternalLink, AlertCircle, FileText, Trash2 } from 'lucide-react';
import ConfirmationModal from '../components/ConfirmationModal';
import { UnifiedLoadingSpinner, ErrorState, EmptyState, PageHeader, StatCard } from '../components/shared';
import { unifiedToast } from '../lib/toast-utils';
import { api } from '../lib/api';

interface HistoryItem {
  input_id: string;
  original_query: string;
  pain_points_count: number;
  total_clusters: number;
  analysis_timestamp: string;
  created_at: string;
}

interface UserStats {
  total_analyses: number;
  total_pain_points: number;
  total_clusters: number;
  latest_analysis: string | null;
}

const DiscoveredProblems = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    inputId: string;
    query: string;
  }>({ isOpen: false, inputId: '', query: '' });

  useEffect(() => {
    fetchAnalysisData();
  }, []);

  const fetchAnalysisData = async () => {
    try {
      setLoading(true);

      // Fetch both history and stats
      const [historyResponse, statsResponse] = await Promise.all([
        api.painPoints.getHistory(),
        api.painPoints.getStats()
      ]);

      if (historyResponse.success) {
        setHistory(historyResponse.history);
      }

      if (statsResponse.success) {
        setStats(statsResponse.stats);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const viewAnalysis = (inputId: string) => {
    window.location.href = `/analysis/${inputId}`;
  };

  const openDeleteConfirmation = (inputId: string, query: string) => {
    setConfirmModal({ isOpen: true, inputId, query });
  };

  const closeDeleteConfirmation = () => {
    setConfirmModal({ isOpen: false, inputId: '', query: '' });
  };

  const handleDeleteConfirm = async () => {
    try {
      await api.userInputs.deleteAnalysis(confirmModal.inputId);
      
      unifiedToast.success({
        description: 'Analysis deleted successfully!',
      });
      
      await fetchAnalysisData();
    } catch (error) {
      console.error('Error deleting analysis:', error);
      
      unifiedToast.error({
        description: 'Failed to delete analysis. Please try again later.',
      });
    }
  };

  if (loading) {
    return (
      <div className="responsive-container">
        <UnifiedLoadingSpinner size="lg" text="Loading your discoveries..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="responsive-container">
        <ErrorState
          title="Failed to load discoveries"
          message={error}
          onRetry={fetchAnalysisData}
        />
      </div>
    );
  }

  return (
    <div className="responsive-container">
      <PageHeader
        title="My Discovered Problems"
        description="View and explore the problems you've discovered from online communities"
        icon={FileText}
      />

      {/* Stats Cards */}
      {stats && (
        <div className="responsive-grid-2col mt-8">
          <StatCard
            title="Discoveries"
            value={stats.total_analyses}
            icon={BarChart3}
            description="Total analyses run"
          />
          
          <StatCard
            title="Problems Found"
            value={stats.total_pain_points}
            icon={AlertCircle}
            description="Unique problems discovered"
            iconClassName="bg-success/10"
          />
          
          <StatCard
            title="Discussion Themes"
            value={stats.total_clusters}
            icon={History}
            description="Conversation clusters"
            iconClassName="bg-accent/10"
          />
          
          <StatCard
            title="Latest Discovery"
            value={stats.latest_analysis ? formatDate(stats.latest_analysis).split(',')[0] : 'Never'}
            icon={Calendar}
            description="Most recent analysis"
          />
        </div>
      )}

      {/* Analysis History */}
      <Card className="glass border-border/50 bg-white/5 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-xl text-white flex items-center gap-3">
            <History className="h-6 w-6 text-blue-400" />
            Your Discovered Problems
          </CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No Problems Discovered Yet"
              description="Start discovering problems from online communities to see them here."
              actionLabel="Start Problem Discovery"
              onAction={() => window.location.href = '/'}
            />
          ) : (
            <div className="space-y-4">
              {history.map((item) => (
                <div
                  key={item.input_id}
                  className="glass border-border/30 bg-white/5 rounded-lg p-4 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-white font-medium mb-2 leading-relaxed">
                        "{item.original_query}"
                      </h3>
                      <div className="flex items-center gap-6 text-sm text-gray-400">
                        <span className="flex items-center gap-1">
                          <AlertCircle className="h-4 w-4 text-green-400" />
                          {item.pain_points_count} problems discovered
                        </span>
                        <span className="flex items-center gap-1">
                          <History className="h-4 w-4 text-purple-400" />
                          {item.total_clusters} discussion themes
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4 text-orange-400" />
                          {formatDate(item.created_at)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openDeleteConfirmation(item.input_id, item.original_query)}
                        className="text-red-400/70 hover:text-red-400 hover:bg-red-500/10"
                        title="Delete analysis"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => viewAnalysis(item.input_id)}
                        className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                      >
                        View Problems <ExternalLink className="h-4 w-4 ml-1" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={confirmModal.isOpen}
        onClose={closeDeleteConfirmation}
        onConfirm={handleDeleteConfirm}
        title="Delete Analysis?"
        message="Are you sure you want to delete this analysis?"
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default DiscoveredProblems;