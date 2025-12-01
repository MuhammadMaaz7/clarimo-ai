import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Checkbox } from './ui/checkbox';
import { Badge } from './ui/badge';
import {
  ArrowLeft,
  Search,
  Link as LinkIcon,
  Unlink,
  Loader2,
  CheckCircle2,
  ExternalLink,
  MessageSquare,
  ThumbsUp,
} from 'lucide-react';
import { useValidation } from '../contexts/ValidationContext';
import api from '../lib/api';

interface PainPoint {
  cluster_id: string;
  problem_title: string;
  problem_description: string;
  post_references: Array<{
    post_id: string;
    subreddit: string;
    created_utc: string;
    url: string;
    text: string;
    title?: string;
    score?: number;
    num_comments?: number;
  }>;
  analysis_timestamp: number;
  source: string;
}

export default function PainPointLinkingUI() {
  const { ideaId } = useParams<{ ideaId: string }>();
  const navigate = useNavigate();
  const { currentIdea, fetchIdeaById, linkPainPoints } = useValidation();

  const [availablePainPoints, setAvailablePainPoints] = useState<PainPoint[]>([]);
  const [selectedPainPointIds, setSelectedPainPointIds] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoadingPainPoints, setIsLoadingPainPoints] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch available pain points from Module 1
  useEffect(() => {
    const fetchPainPoints = async () => {
      setIsLoadingPainPoints(true);
      setError(null);
      try {
        // First, get all user inputs to find available pain points
        const inputs = await api.userInputs.getAll();
        const inputIdsWithPainPoints = inputs
          .filter((input) => input.status === 'completed')
          .map((input) => input.input_id);

        // Fetch pain points for each input
        const allPainPoints: PainPoint[] = [];
        for (const inputId of inputIdsWithPainPoints) {
          try {
            const result = await api.painPoints.getResults(inputId, false);
            if (result.success && result.pain_points) {
              allPainPoints.push(...result.pain_points);
            }
          } catch (err) {
            console.error(`Error fetching pain points for ${inputId}:`, err);
          }
        }

        setAvailablePainPoints(allPainPoints);
      } catch (err: any) {
        setError(err.message || 'Failed to load pain points');
        console.error('Error fetching pain points:', err);
      } finally {
        setIsLoadingPainPoints(false);
      }
    };

    fetchPainPoints();
  }, []);

  // Load current idea and set selected pain points
  useEffect(() => {
    if (ideaId) {
      fetchIdeaById(ideaId);
    }
  }, [ideaId, fetchIdeaById]);

  useEffect(() => {
    if (currentIdea?.linked_pain_points) {
      setSelectedPainPointIds(currentIdea.linked_pain_points);
    }
  }, [currentIdea]);

  const handleTogglePainPoint = (clusterId: string) => {
    setSelectedPainPointIds((prev) => {
      if (prev.includes(clusterId)) {
        return prev.filter((id) => id !== clusterId);
      } else {
        return [...prev, clusterId];
      }
    });
  };

  const handleSave = async () => {
    if (!ideaId) return;
    setIsSaving(true);
    setError(null);
    try {
      await linkPainPoints(ideaId, selectedPainPointIds);
      navigate(`/ideas/${ideaId}`);
    } catch (err: any) {
      setError(err.message || 'Failed to link pain points');
      console.error('Error linking pain points:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Filter pain points based on search query
  const filteredPainPoints = availablePainPoints.filter((pp) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      pp.problem_title.toLowerCase().includes(query) ||
      pp.problem_description.toLowerCase().includes(query)
    );
  });

  const selectedCount = selectedPainPointIds.length;
  const hasChanges =
    JSON.stringify([...selectedPainPointIds].sort()) !==
    JSON.stringify([...(currentIdea?.linked_pain_points || [])].sort());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Button
            variant="ghost"
            onClick={() => navigate(`/ideas/${ideaId}`)}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Idea
          </Button>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <LinkIcon className="h-8 w-8 text-primary" />
            Link Pain Points
          </h1>
          <p className="text-muted-foreground mt-2">
            Connect your idea to validated pain points from Module 1
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => navigate(`/ideas/${ideaId}`)}
            disabled={isSaving}
            className="glass border-border/50"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving || !hasChanges}
            className="bg-gradient-to-r from-accent to-primary text-white"
          >
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Current Idea Info */}
      {currentIdea && (
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="text-xl">{currentIdea.title}</CardTitle>
            <CardDescription className="line-clamp-2">
              {currentIdea.description}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Badge variant="outline">
                {selectedCount} pain point(s) selected
              </Badge>
              {hasChanges && (
                <Badge variant="default" className="bg-blue-500">
                  Unsaved changes
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <Card className="glass border-border/50">
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search pain points by title or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 glass border-border/50"
            />
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="glass border-border/50 border-red-500">
          <CardContent className="pt-6">
            <p className="text-red-500">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Pain Points List */}
      {isLoadingPainPoints ? (
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary mb-4" />
              <p className="text-muted-foreground">Loading pain points...</p>
            </div>
          </CardContent>
        </Card>
      ) : filteredPainPoints.length === 0 ? (
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <LinkIcon className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-xl font-semibold mb-2">
                {searchQuery ? 'No pain points found' : 'No pain points available'}
              </h3>
              <p className="text-muted-foreground mb-6">
                {searchQuery
                  ? 'Try adjusting your search query'
                  : 'Complete a problem discovery workflow in Module 1 to discover pain points'}
              </p>
              {!searchQuery && (
                <Button
                  onClick={() => navigate('/problem-discovery')}
                  className="bg-gradient-to-r from-accent to-primary text-white"
                >
                  Discover Problems
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">
            Showing {filteredPainPoints.length} of {availablePainPoints.length} pain point(s)
          </div>
          {filteredPainPoints.map((painPoint) => {
            const isSelected = selectedPainPointIds.includes(painPoint.cluster_id);
            const totalEngagement = painPoint.post_references.reduce(
              (sum, post) => sum + (post.score || 0) + (post.num_comments || 0),
              0
            );

            return (
              <Card
                key={painPoint.cluster_id}
                className={`glass border-border/50 cursor-pointer transition-all duration-300 ${
                  isSelected ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
                }`}
                onClick={() => handleTogglePainPoint(painPoint.cluster_id)}
              >
                <CardHeader>
                  <div className="flex items-start gap-4">
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => handleTogglePainPoint(painPoint.cluster_id)}
                      className="mt-1"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-2">
                        {painPoint.problem_title}
                      </CardTitle>
                      <CardDescription className="line-clamp-3">
                        {painPoint.problem_description}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <MessageSquare className="h-4 w-4" />
                      {painPoint.post_references.length} post(s)
                    </div>
                    <div className="flex items-center gap-1">
                      <ThumbsUp className="h-4 w-4" />
                      {totalEngagement} total engagement
                    </div>
                    {painPoint.post_references[0] && (
                      <div className="flex items-center gap-1">
                        <Badge variant="outline" className="text-xs">
                          r/{painPoint.post_references[0].subreddit}
                        </Badge>
                      </div>
                    )}
                  </div>
                  {painPoint.post_references.length > 0 && (
                    <div className="mt-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          window.open(painPoint.post_references[0].url, '_blank');
                        }}
                        className="text-xs"
                      >
                        <ExternalLink className="mr-2 h-3 w-3" />
                        View Sample Post
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Save Button (Bottom) */}
      {filteredPainPoints.length > 0 && (
        <Card className="glass border-border/50 sticky bottom-4">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">
                  {selectedCount} pain point(s) selected
                </p>
                {hasChanges && (
                  <p className="text-sm text-muted-foreground">
                    You have unsaved changes
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setSelectedPainPointIds(currentIdea?.linked_pain_points || [])}
                  disabled={!hasChanges || isSaving}
                  className="glass border-border/50"
                >
                  <Unlink className="mr-2 h-4 w-4" />
                  Reset
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={isSaving || !hasChanges}
                  size="lg"
                  className="bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.02] transition-all duration-300"
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="mr-2 h-5 w-5" />
                      Save Changes
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
