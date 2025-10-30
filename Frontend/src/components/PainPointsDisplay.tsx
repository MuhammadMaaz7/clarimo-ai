import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ExternalLink, AlertCircle, ChevronDown, ChevronUp, MessageSquare } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';

interface PostReference {
  post_id: string;
  subreddit: string;
  created_utc: string;
  url: string;
  text: string;
  title?: string;
  score?: number;
  num_comments?: number;
}

interface PainPoint {
  cluster_id: string;
  problem_title: string;
  problem_description: string;
  post_references: PostReference[];
  analysis_timestamp: number;
  source: string;
}

interface PainPointsData {
  metadata: {
    total_clusters: number;
    analysis_timestamp: number;
    user_id: string;
    input_id: string;
  };
  pain_points: PainPoint[];
}

interface PainPointsDisplayProps {
  inputId: string;
}

const PainPointsDisplay: React.FC<PainPointsDisplayProps> = ({ inputId }) => {
  const [painPointsData, setPainPointsData] = useState<PainPointsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchPainPoints();
  }, [inputId]);

  const fetchPainPoints = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      
      const response = await fetch(`http://localhost:8000/api/pain-points/results/${inputId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch pain points');
      }

      const data = await response.json();
      setPainPointsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const toggleCardExpansion = (clusterId: string) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(clusterId)) {
      newExpanded.delete(clusterId);
    } else {
      newExpanded.add(clusterId);
    }
    setExpandedCards(newExpanded);
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
          <span className="text-lg font-medium text-white">Analyzing problems...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-8">
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
          <AlertCircle className="mx-auto h-12 w-12 text-red-400 mb-4" />
          <p className="text-red-300 mb-4">Error loading problems: {error}</p>
          <Button onClick={fetchPainPoints} variant="outline" className="border-red-500/20 text-red-300 hover:bg-red-500/10">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!painPointsData || painPointsData.pain_points.length === 0) {
    return (
      <div className="text-center p-12">
        <AlertCircle className="mx-auto h-16 w-16 text-gray-400 mb-6" />
        <h3 className="text-xl font-semibold text-white mb-2">No Problems Found</h3>
        <p className="text-gray-400">No user problems were identified for this search.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 backdrop-blur-sm border border-white/10 rounded-xl p-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 bg-blue-500/20 rounded-lg">
            <AlertCircle className="h-8 w-8 text-blue-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Problems Discovered</h2>
            <p className="text-gray-300">
              {painPointsData.pain_points.length} real user problems identified from online discussions
            </p>
          </div>
        </div>
      </div>

      {/* Problems Grid */}
      <div className="space-y-4">
        {painPointsData.pain_points.map((painPoint, index) => {
          const isExpanded = expandedCards.has(painPoint.cluster_id);
          
          return (
            <Card 
              key={painPoint.cluster_id} 
              className="bg-white/5 backdrop-blur-sm border-white/10 hover:bg-white/10 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/10"
            >
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="px-3 py-1 bg-blue-500/20 text-blue-300 text-sm font-medium rounded-full border border-blue-500/30">
                        Problem #{parseInt(painPoint.cluster_id) + 1}
                      </span>
                      <span className="text-sm text-gray-400">
                        {painPoint.post_references.length} user discussions
                      </span>
                    </div>
                    <CardTitle className="text-xl text-white mb-3 leading-relaxed">
                      {painPoint.problem_title}
                    </CardTitle>
                    <p className="text-gray-300 leading-relaxed">
                      {painPoint.problem_description}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleCardExpansion(painPoint.cluster_id)}
                    className="text-gray-400 hover:text-white hover:bg-white/10 ml-4"
                  >
                    {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                  </Button>
                </div>
              </CardHeader>

              <Collapsible open={isExpanded}>
                <CollapsibleContent>
                  <CardContent className="pt-0">
                    <div className="border-t border-white/10 pt-6">
                      <div className="flex items-center gap-2 mb-4">
                        <MessageSquare className="h-5 w-5 text-green-400" />
                        <span className="font-semibold text-white">
                          Real User Evidence ({painPoint.post_references.length} posts)
                        </span>
                      </div>
                      <div className="space-y-3">
                        {painPoint.post_references.map((post, postIndex) => (
                          <div 
                            key={post.post_id} 
                            className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
                          >
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-3">
                                <span className="px-2 py-1 bg-orange-500/20 text-orange-300 text-xs font-medium rounded border border-orange-500/30">
                                  r/{post.subreddit}
                                </span>
                                <span className="text-xs text-gray-400">
                                  {formatDate(new Date(post.created_utc).getTime() / 1000)}
                                </span>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => window.open(post.url, '_blank')}
                                className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 h-8 px-3 text-xs"
                              >
                                View Post <ExternalLink className="h-3 w-3 ml-1" />
                              </Button>
                            </div>
                            <p className="text-gray-300 text-sm leading-relaxed">
                              {post.text}
                            </p>
                            {post.title && (
                              <p className="text-xs text-gray-400 mt-2 italic">
                                "{post.title}"
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </CollapsibleContent>
              </Collapsible>

              {/* Quick Stats */}
              {!isExpanded && (
                <CardContent className="pt-0 pb-4">
                  <div className="flex items-center justify-between pt-4 border-t border-white/10">
                    <div className="flex items-center gap-4 text-sm text-gray-400">
                      <span>{painPoint.post_references.length} user posts</span>
                      <span>•</span>
                      <span>Analyzed {formatDate(painPoint.analysis_timestamp)}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleCardExpansion(painPoint.cluster_id)}
                      className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                    >
                      View Evidence
                    </Button>
                  </div>
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>

      {/* Footer Stats */}
      <div className="text-center pt-6 border-t border-white/10">
        <p className="text-gray-400 text-sm">
          Found {painPointsData.pain_points.length} problems from {painPointsData.metadata.total_clusters} discussion themes
        </p>
      </div>
    </div>
  );
};

export default PainPointsDisplay;