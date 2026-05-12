/**
 * Customer Insights Detail Page
 * Shows detailed analysis results with communities, segments, and insights
 */

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Users, 
  MessageSquare, 
  TrendingUp,
  Lightbulb,
  Loader2
} from 'lucide-react';
import { PageHeader, StatCard, UnifiedLoadingSpinner } from '../components/shared';
import { customerInsightsApi } from '../services/customerInsightsApi';
import { unifiedToast } from '../lib/toast-utils';
import CommunityCard from '../components/customer-insights/CommunityCard';
import SegmentCard from '../components/customer-insights/SegmentCard';
import InsightsView from '../components/customer-insights/InsightsView';
import AnalysisStatus from '../components/customer-insights/AnalysisStatus';

export default function CustomerInsightsDetail() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('segments');
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (analysisId) {
      fetchAnalysis();
      
      // Poll for updates
      intervalRef.current = setInterval(() => {
        fetchAnalysis();
      }, 5000);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [analysisId]);

  const fetchAnalysis = async () => {
    try {
      const data = await customerInsightsApi.getAnalysis(analysisId!);
      setAnalysis(data);
      setLoading(false);
      
      // Stop polling if analysis is completed or failed
      if ((data.status === 'completed' || data.status === 'failed') && intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } catch (error: any) {
      console.error('Failed to fetch analysis:', error);
      unifiedToast.error({
        description: error.message || 'Failed to load analysis',
      });
      setLoading(false);
    }
  };

  // Show progress view while loading or processing
  if (loading || !analysis || analysis.status === 'processing') {
    const progressPercentage = analysis?.progress_percentage || 0;
    const currentStage = analysis?.current_stage || 'data_collection';
    
    return (
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <Card className="glass border-border/50">
          <CardContent className="pt-12 pb-12">
            <div className="space-y-8">
              {/* Animated Spinner */}
              <div className="flex justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 rounded-full blur-2xl animate-pulse" />
                  <div className="relative rounded-full bg-gradient-to-br from-primary to-accent p-6">
                    <Loader2 className="h-16 w-16 text-white animate-spin" />
                  </div>
                </div>
              </div>

              {/* Status Text */}
              <div className="text-center space-y-3">
                <h2 className="text-2xl font-bold">
                  {currentStage === 'data_collection' && 'Collecting Discussions'}
                  {currentStage === 'insights_generation' && 'Generating Insights'}
                  {currentStage === 'finalizing' && 'Almost Done'}
                  {!['data_collection', 'insights_generation', 'finalizing'].includes(currentStage) && 'Analyzing'}
                </h2>
                <p className="text-muted-foreground">
                  {currentStage === 'data_collection' && 'Searching Reddit and Product Hunt'}
                  {currentStage === 'insights_generation' && 'Identifying customer segments'}
                  {currentStage === 'finalizing' && 'Preparing your insights'}
                  {!['data_collection', 'insights_generation', 'finalizing'].includes(currentStage) && 'Processing your analysis'}
                </p>
              </div>

              {/* Progress Bar */}
              {analysis && (
                <div className="space-y-2">
                  <div className="relative h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary to-accent transition-all duration-500 ease-out"
                      style={{ width: `${progressPercentage}%` }}
                    />
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-semibold text-primary">{progressPercentage}%</span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show error if failed
  if (analysis.status === 'failed') {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <PageHeader
            title="Customer Insights Analysis"
            description={analysis.startup_idea}
            icon={Users}
            backTo="/customer-insights"
            backLabel="Back to Analyses"
          />
          
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <p className="text-destructive mb-4">
                  Analysis failed: {analysis.error_message || 'Unknown error'}
                </p>
                <Button onClick={() => navigate('/customer-insights')}>
                  Back to Analyses
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="space-y-6">
        {/* Header */}
        <PageHeader
          title="Customer Insights Analysis"
          description={analysis.startup_idea}
          icon={Users}
          backTo="/customer-insights"
          backLabel="Back to Analyses"
        />

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-3">
          <StatCard
            title="Total Discussions"
            value={analysis.total_discussions}
            icon={MessageSquare}
            description="Analyzed from Reddit and Product Hunt"
          />
          <StatCard
            title="Customer Segments"
            value={analysis.insights?.customer_segments?.length || 0}
            icon={Users}
            description="Distinct customer groups identified"
          />
          <StatCard
            title="Key Insights"
            value={analysis.insights?.key_insights ? Object.keys(analysis.insights.key_insights).length : 0}
            icon={Lightbulb}
            description="Actionable insights discovered"
          />
        </div>

        {/* Results Tabs */}
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="segments">
                  <Users className="mr-2 h-4 w-4" />
                  Customer Segments
                </TabsTrigger>
                <TabsTrigger value="insights">
                  <Lightbulb className="mr-2 h-4 w-4" />
                  Key Insights
                </TabsTrigger>
                <TabsTrigger value="communities">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Communities
                </TabsTrigger>
              </TabsList>

              <TabsContent value="segments" className="space-y-4 mt-6">
                {!analysis.insights?.customer_segments || analysis.insights.customer_segments.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    No customer segments identified
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {analysis.insights.customer_segments.map((segment: any, index: number) => (
                      <Card key={index} className="glass border-border/50">
                        <CardContent className="pt-6">
                          <h3 className="text-lg font-semibold mb-2">{segment.name}</h3>
                          <p className="text-sm text-muted-foreground mb-4">{segment.description}</p>
                          
                          <div className="space-y-3">
                            <div>
                              <h4 className="text-sm font-medium mb-2">Pain Points:</h4>
                              <ul className="list-disc list-inside space-y-1">
                                {segment.pain_points?.map((point: string, idx: number) => (
                                  <li key={idx} className="text-sm text-muted-foreground">{point}</li>
                                ))}
                              </ul>
                            </div>
                            
                            <div>
                              <h4 className="text-sm font-medium mb-2">Needs:</h4>
                              <ul className="list-disc list-inside space-y-1">
                                {segment.needs?.map((need: string, idx: number) => (
                                  <li key={idx} className="text-sm text-muted-foreground">{need}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="insights" className="space-y-4 mt-6">
                {!analysis.insights?.key_insights ? (
                  <div className="text-center py-12 text-muted-foreground">
                    No insights available
                  </div>
                ) : (
                  <div className="space-y-4">
                    {analysis.insights.key_insights.main_problems && (
                      <Card className="glass border-border/50">
                        <CardContent className="pt-6">
                          <h3 className="text-lg font-semibold mb-3">Main Problems</h3>
                          <ul className="list-disc list-inside space-y-2">
                            {analysis.insights.key_insights.main_problems.map((problem: string, idx: number) => (
                              <li key={idx} className="text-sm">{problem}</li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    )}
                    
                    {analysis.insights.key_insights.unmet_needs && (
                      <Card className="glass border-border/50">
                        <CardContent className="pt-6">
                          <h3 className="text-lg font-semibold mb-3">Unmet Needs</h3>
                          <ul className="list-disc list-inside space-y-2">
                            {analysis.insights.key_insights.unmet_needs.map((need: string, idx: number) => (
                              <li key={idx} className="text-sm">{need}</li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    )}
                    
                    {analysis.insights.key_insights.common_frustrations && (
                      <Card className="glass border-border/50">
                        <CardContent className="pt-6">
                          <h3 className="text-lg font-semibold mb-3">Common Frustrations</h3>
                          <ul className="list-disc list-inside space-y-2">
                            {analysis.insights.key_insights.common_frustrations.map((frustration: string, idx: number) => (
                              <li key={idx} className="text-sm">{frustration}</li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    )}
                    
                    {analysis.insights.recommendations && (
                      <Card className="glass border-border/50 bg-primary/5">
                        <CardContent className="pt-6">
                          <h3 className="text-lg font-semibold mb-3">Recommendations</h3>
                          <ul className="space-y-2">
                            {analysis.insights.recommendations.map((rec: string, idx: number) => (
                              <li key={idx} className="text-sm flex items-start gap-2">
                                <span className="text-primary mt-0.5">→</span>
                                <span>{rec}</span>
                              </li>
                            ))}
                          </ul>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="communities" className="space-y-4 mt-6">
                {!analysis.insights?.recommended_communities || analysis.insights.recommended_communities.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    No highly relevant communities identified
                  </div>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2">
                    {analysis.insights.recommended_communities.map((community: any, index: number) => (
                      <Card key={index} className="glass border-border/50 hover:border-primary/50 transition-colors">
                        <CardContent className="pt-6">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <h3 className="text-lg font-semibold mb-1">r/{community.name}</h3>
                              <p className="text-sm text-muted-foreground">{community.description}</p>
                            </div>
                            {community.relevance && (
                              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                community.relevance === 'high' 
                                  ? 'bg-green-500/20 text-green-600 border border-green-500/30' 
                                  : 'bg-yellow-500/20 text-yellow-600 border border-yellow-500/30'
                              }`}>
                                {community.relevance}
                              </span>
                            )}
                          </div>
                          {community.url && (
                            <a
                              href={community.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-primary hover:underline"
                            >
                              Visit Community →
                            </a>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
