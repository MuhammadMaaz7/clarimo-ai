/**
 * Customer Insights History Page
 * Shows all past analyses
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { 
  Users, 
  Clock, 
  Loader2,
  CheckCircle2,
  XCircle,
  Plus,
  ArrowLeft
} from 'lucide-react';
import { customerInsightsApi } from '../services/customerInsightsApi';
import { UnifiedLoadingSpinner, EmptyState } from '../components/shared';

export default function CustomerInsightsHistory() {
  const navigate = useNavigate();
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      console.log('Fetching customer insights history...');
      const data = await customerInsightsApi.getHistory();
      console.log('Received history data:', data);
      setHistory(data);
    } catch (error: any) {
      console.error('Failed to fetch history:', error);
      console.error('Error details:', {
        message: error.message,
        status: error.status,
        isTokenExpired: error.isTokenExpired
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-success" />;
      case 'processing':
        return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-destructive" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, any> = {
      completed: 'default',
      processing: 'secondary',
      failed: 'destructive',
    };

    return (
      <Badge variant={variants[status] || 'outline'} className="capitalize">
        {status}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <UnifiedLoadingSpinner text="Loading analysis history..." />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/customer-insights')}
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold">Analysis History</h1>
              <p className="text-sm text-muted-foreground">
                View all your customer insights analyses
              </p>
            </div>
          </div>
          <Button onClick={() => navigate('/customer-insights')}>
            <Plus className="mr-2 h-4 w-4" />
            New Analysis
          </Button>
        </div>

        {/* History List */}
        {history.length === 0 ? (
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <EmptyState
                icon={Users}
                title="No Analyses Yet"
                description="Start your first customer insights analysis to discover where your target audience is active"
                action={
                  <Button onClick={() => navigate('/customer-insights')}>
                    <Plus className="mr-2 h-4 w-4" />
                    Start First Analysis
                  </Button>
                }
              />
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {history.map((analysis) => (
              <Card
                key={analysis.analysis_id}
                className="glass border-border/50 hover:border-primary/50 transition-all cursor-pointer"
                onClick={() => navigate(`/customer-insights/${analysis.analysis_id}`)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {getStatusIcon(analysis.status)}
                        <CardTitle className="text-lg">
                          {analysis.startup_idea}
                        </CardTitle>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(analysis.created_at).toLocaleDateString()} at{' '}
                          {new Date(analysis.created_at).toLocaleTimeString()}
                        </span>
                        {analysis.status === 'completed' && (
                          <>
                            <span className="flex items-center gap-1">
                              <Users className="h-3 w-3" />
                              {analysis.segments_found || 0} segments
                            </span>
                            <span className="flex items-center gap-1">
                              {analysis.communities_found || 0} communities
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                    {getStatusBadge(analysis.status)}
                  </div>
                </CardHeader>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
