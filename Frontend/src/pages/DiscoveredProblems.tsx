import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { History, BarChart3, Calendar, ExternalLink, AlertCircle, FileText, Trash2, Search } from 'lucide-react';
import ConfirmationModal from '../components/ConfirmationModal';
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
  const [searchQuery, setSearchQuery] = useState('');
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
      
      closeDeleteConfirmation();
      await fetchAnalysisData();
    } catch (error) {
      console.error('Error deleting analysis:', error);
      
      unifiedToast.error({
        description: 'Failed to delete analysis. Please try again later.',
      });
    }
  };

  // Filter history based on search query
  const filteredHistory = history.filter((item) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return item.original_query.toLowerCase().includes(query);
  });

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <History className="h-12 w-12 animate-spin mx-auto text-primary mb-4" />
              <p className="text-muted-foreground">Loading your discoveries...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12 text-red-500">
              <AlertCircle className="h-12 w-12 mx-auto mb-4" />
              <p className="text-lg font-semibold">Failed to load discoveries</p>
              <p className="text-sm text-muted-foreground mt-2">{error}</p>
              <Button onClick={fetchAnalysisData} className="mt-4">
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <FileText className="h-8 w-8 text-primary" />
              My Discovered Problems
            </h1>
            <p className="text-muted-foreground mt-2">
              View and explore the problems you've discovered from online communities
            </p>
          </div>
          <Button
            onClick={() => window.location.href = '/problem-discovery'}
            size="lg"
            className="bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.02] transition-all duration-300"
          >
            <BarChart3 className="mr-2 h-5 w-5" />
            New Discovery
          </Button>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card className="glass border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{stats.total_analyses}</p>
                    <p className="text-xs text-muted-foreground">Total Discoveries</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="glass border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-500/10 rounded-lg">
                    <AlertCircle className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{stats.total_pain_points}</p>
                    <p className="text-xs text-muted-foreground">Problems Found</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="glass border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-500/10 rounded-lg">
                    <History className="h-5 w-5 text-purple-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{stats.total_clusters}</p>
                    <p className="text-xs text-muted-foreground">Discussion Themes</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="glass border-border/50">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-500/10 rounded-lg">
                    <Calendar className="h-5 w-5 text-orange-500" />
                  </div>
                  <div>
                    <p className="text-sm font-bold">{stats.latest_analysis ? formatDate(stats.latest_analysis).split(',')[0] : 'Never'}</p>
                    <p className="text-xs text-muted-foreground">Latest Discovery</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Search Bar */}
        {history.length > 0 && (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search discoveries by query..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 glass border-border/50"
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Analysis History */}
        {filteredHistory.length === 0 && history.length === 0 ? (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <FileText className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Problems Discovered Yet</h3>
                <p className="text-muted-foreground mb-6">
                  Start discovering problems from online communities to see them here
                </p>
                <Button
                  onClick={() => window.location.href = '/problem-discovery'}
                  className="bg-gradient-to-r from-accent to-primary text-white"
                >
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Start Problem Discovery
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : filteredHistory.length === 0 ? (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <Search className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Results Found</h3>
                <p className="text-muted-foreground mb-6">
                  Try adjusting your search query
                </p>
                <Button
                  variant="outline"
                  onClick={() => setSearchQuery('')}
                  className="glass border-border/50"
                >
                  Clear Search
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {filteredHistory.map((item) => (
              <Card
                key={item.input_id}
                className="glass border-border/50 hover:border-primary/50 transition-all duration-300 cursor-pointer"
                onClick={() => viewAnalysis(item.input_id)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-xl mb-2">"{item.original_query}"</CardTitle>
                      <CardDescription>
                        {item.pain_points_count} problems discovered • {item.total_clusters} discussion themes
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">
                        Created: {formatDate(item.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="glass border-border/50"
                      onClick={(e) => {
                        e.stopPropagation();
                        viewAnalysis(item.input_id);
                      }}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      View Problems
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="glass border-border/50 text-red-500 hover:text-red-600"
                      onClick={(e) => {
                        e.stopPropagation();
                        openDeleteConfirmation(item.input_id, item.original_query);
                      }}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Results Count */}
        {!loading && filteredHistory.length > 0 && (
          <div className="text-center text-sm text-muted-foreground">
            Showing {filteredHistory.length} of {history.length} discovery(ies)
          </div>
        )}
      </div>

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