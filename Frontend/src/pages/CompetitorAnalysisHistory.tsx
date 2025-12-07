/**
 * Competitor Analysis History Page
 * Shows all previous analyses for the user
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { History, Plus, TrendingUp, Calendar } from 'lucide-react';
import api from '../lib/api';
import LoadingSpinner from '../components/LoadingSpinner';

export default function CompetitorAnalysisHistory() {
  const navigate = useNavigate();
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    try {
      setLoading(true);
      const result = await api.competitorAnalyses.list();
      setAnalyses(result.analyses);
    } catch (error: any) {
      console.error('Failed to load analyses:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <LoadingSpinner />
              <p className="text-muted-foreground mt-4">Loading analyses...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Analysis History</h1>
            <p className="text-muted-foreground">
              View and manage your previous competitor analyses
            </p>
          </div>
          <Button onClick={() => navigate('/competitor-analysis/new')}>
            <Plus className="mr-2 h-4 w-4" />
            New Analysis
          </Button>
        </div>

        {/* Analyses List */}
        {analyses.length === 0 ? (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <History className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">No Analyses Yet</h3>
                <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                  Start by creating your first competitor analysis to discover market opportunities
                </p>
                <Button onClick={() => navigate('/competitor-analysis/new')}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create First Analysis
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {analyses.map((analysis) => (
              <Card
                key={analysis.analysis_id}
                className="glass border-border/50 hover:border-primary/50 transition-all cursor-pointer group"
                onClick={() => navigate(`/competitor-analysis/new?id=${analysis.analysis_id}`)}
              >
                <CardHeader>
                  <CardTitle className="text-lg group-hover:text-primary transition-colors">
                    {analysis.product_name}
                  </CardTitle>
                  <CardDescription className="flex items-center gap-2">
                    <Calendar className="h-3 w-3" />
                    {formatDate(analysis.created_at)}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Competitors Found</span>
                      <span className="font-medium flex items-center gap-1">
                        <TrendingUp className="h-3 w-3 text-primary" />
                        {analysis.competitors_found}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Status</span>
                      <span className="text-green-500 font-medium">
                        {analysis.status === 'completed' ? 'Completed' : analysis.status}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
