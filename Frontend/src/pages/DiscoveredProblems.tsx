import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { History, BarChart3, Calendar, ExternalLink, AlertCircle, FileText } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
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
  const { user } = useAuth();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) {
    return (
      <div className="px-4 md:px-6 lg:px-8 pt-4 pb-8">
        <div className="flex items-center justify-center p-12">
          <div className="flex flex-col items-center space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
            <span className="text-lg font-medium text-white">Loading your discoveries...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-4 md:px-6 lg:px-8 pt-4 pb-8">
        <div className="text-center p-8">
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
            <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
            <p className="text-red-300 mb-4">Error loading your discoveries: {error}</p>
            <Button onClick={fetchAnalysisData} variant="outline" className="border-red-500/20 text-red-300 hover:bg-red-500/10">
              Try Again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 md:px-6 lg:px-8 pt-4 pb-8">
      {/* Header */}
      <div className="glass border-border/50 rounded-2xl p-6 md:p-8 bg-white/5 backdrop-blur-xl mb-8">
        <div className="flex items-center gap-4">
          <div className="rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 p-3 glow-sm shadow-lg">
            <FileText className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white">
              My Discovered Problems
            </h1>
            <p className="text-muted-foreground mt-1">
              View and explore the problems you've discovered from online communities
            </p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="glass border-border/50 bg-white/5 backdrop-blur-xl hover:bg-white/10 transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-blue-500/20 rounded-lg">
                  <BarChart3 className="h-6 w-6 text-blue-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{stats.total_analyses}</p>
                  <p className="text-sm text-gray-400">Discoveries</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass border-border/50 bg-white/5 backdrop-blur-xl hover:bg-white/10 transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-green-500/20 rounded-lg">
                  <AlertCircle className="h-6 w-6 text-green-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{stats.total_pain_points}</p>
                  <p className="text-sm text-gray-400">Problems Found</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass border-border/50 bg-white/5 backdrop-blur-xl hover:bg-white/10 transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-500/20 rounded-lg">
                  <History className="h-6 w-6 text-purple-400" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-white">{stats.total_clusters}</p>
                  <p className="text-sm text-gray-400">Discussion Themes</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass border-border/50 bg-white/5 backdrop-blur-xl hover:bg-white/10 transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-orange-500/20 rounded-lg">
                  <Calendar className="h-6 w-6 text-orange-400" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white">
                    {stats.latest_analysis ? formatDate(stats.latest_analysis).split(',')[0] : 'Never'}
                  </p>
                  <p className="text-sm text-gray-400">Latest Discovery</p>
                </div>
              </div>
            </CardContent>
          </Card>
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
            <div className="text-center py-12">
              <FileText className="mx-auto h-16 w-16 text-gray-400 mb-6" />
              <h3 className="text-xl font-semibold text-white mb-2">No Problems Discovered Yet</h3>
              <p className="text-gray-400 mb-6">Start discovering problems from online communities to see them here.</p>
              <Button 
                onClick={() => window.location.href = '/'}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                Start Problem Discovery
              </Button>
            </div>
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
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => viewAnalysis(item.input_id)}
                      className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 ml-4"
                    >
                      View Problems <ExternalLink className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DiscoveredProblems;