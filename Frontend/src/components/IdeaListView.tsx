import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { Badge } from './ui/badge';
import {
  Lightbulb,
  Plus,
  Search,
  Filter,

  Eye,
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
} from 'lucide-react';
import { Idea } from '../types/validation';
import { useValidation } from '../contexts/ValidationContext';
import { formatScore, getScoreColor, getScoreLabel } from '../types/validation';

export default function IdeaListView() {
  const navigate = useNavigate();
  const { ideas, ideasLoading, ideasError, fetchIdeas } = useValidation();

  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchIdeas();
  }, [fetchIdeas]);

  // Filter and sort ideas
  const filteredAndSortedIdeas = ideas
    .filter((idea) => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        idea.title.toLowerCase().includes(query) ||
        idea.description.toLowerCase().includes(query) ||
        idea.problem_statement.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => {
      let aValue: any;
      let bValue: any;

      if (sortBy === 'created_at') {
        aValue = new Date(a.created_at).getTime();
        bValue = new Date(b.created_at).getTime();
      } else if (sortBy === 'title') {
        aValue = a.title.toLowerCase();
        bValue = b.title.toLowerCase();
      } else if (sortBy === 'overall_score') {
        aValue = a.latest_validation?.overall_score || 0;
        bValue = b.latest_validation?.overall_score || 0;
      } else {
        return 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const getStatusBadge = (idea: Idea) => {
    if (!idea.latest_validation) {
      return (
        <Badge variant="outline" className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          Not Validated
        </Badge>
      );
    }

    const status = idea.latest_validation.status;
    if (status === 'completed') {
      return (
        <Badge variant="default" className="flex items-center gap-1 bg-green-500">
          <CheckCircle2 className="h-3 w-3" />
          Validated
        </Badge>
      );
    } else if (status === 'in_progress' || status === 'pending') {
      return (
        <Badge variant="default" className="flex items-center gap-1 bg-blue-500">
          <Loader2 className="h-3 w-3 animate-spin" />
          In Progress
        </Badge>
      );
    } else if (status === 'failed') {
      return (
        <Badge variant="destructive" className="flex items-center gap-1">
          <XCircle className="h-3 w-3" />
          Failed
        </Badge>
      );
    }
  };

  const getScoreBadge = (score: number) => {
    const color = getScoreColor(score);
    const label = getScoreLabel(score);
    return (
      <div className="flex items-center gap-2">
        <div
          className="text-2xl font-bold"
          style={{ color }}
        >
          {formatScore(score)}
        </div>
        <div className="text-sm text-muted-foreground">{label}</div>
      </div>
    );
  };

  if (ideasError) {
    return (
      <Card className="glass border-border/50">
        <CardContent className="pt-6">
          <div className="text-center text-red-500">
            <XCircle className="h-12 w-12 mx-auto mb-4" />
            <p className="text-lg font-semibold">Error loading ideas</p>
            <p className="text-sm text-muted-foreground mt-2">{ideasError}</p>
            <Button onClick={fetchIdeas} className="mt-4">
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Lightbulb className="h-8 w-8 text-primary" />
            My Ideas
          </h1>
          <p className="text-muted-foreground mt-2">
            Manage and validate your startup ideas
          </p>
        </div>
        <Button
          onClick={() => navigate('/ideas/new')}
          size="lg"
          className="bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.02] transition-all duration-300"
        >
          <Plus className="mr-2 h-5 w-5" />
          New Idea
        </Button>
      </div>

      {/* Search and Filters */}
      <Card className="glass border-border/50">
        <CardContent className="pt-6">
          <div className="space-y-4">
            {/* Search Bar */}
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search ideas by title, description, or problem..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 glass border-border/50"
                />
              </div>
              <Button
                variant="outline"
                onClick={() => setShowFilters(!showFilters)}
                className="glass border-border/50"
              >
                <Filter className="mr-2 h-4 w-4" />
                Filters
              </Button>
            </div>

            {/* Filters */}
            {showFilters && (
              <div className="grid gap-4 sm:grid-cols-2 pt-4 border-t border-border/50">
                <div className="space-y-2">
                  <Label>Sort By</Label>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="glass border-border/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="created_at">Date Created</SelectItem>
                      <SelectItem value="title">Title</SelectItem>
                      <SelectItem value="overall_score">Validation Score</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Sort Order</Label>
                  <Select
                    value={sortOrder}
                    onValueChange={(value) => setSortOrder(value as 'asc' | 'desc')}
                  >
                    <SelectTrigger className="glass border-border/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="desc">Descending</SelectItem>
                      <SelectItem value="asc">Ascending</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Ideas List */}
      {ideasLoading ? (
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary mb-4" />
              <p className="text-muted-foreground">Loading your ideas...</p>
            </div>
          </CardContent>
        </Card>
      ) : filteredAndSortedIdeas.length === 0 ? (
        <Card className="glass border-border/50">
          <CardContent className="pt-6">
            <div className="text-center py-12">
              <Lightbulb className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-xl font-semibold mb-2">
                {searchQuery ? 'No ideas found' : 'No ideas yet'}
              </h3>
              <p className="text-muted-foreground mb-6">
                {searchQuery
                  ? 'Try adjusting your search query'
                  : 'Start by submitting your first startup idea for validation'}
              </p>
              {!searchQuery && (
                <Button
                  onClick={() => navigate('/ideas/new')}
                  className="bg-gradient-to-r from-accent to-primary text-white"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Submit Your First Idea
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {filteredAndSortedIdeas.map((idea) => (
            <Card
              key={idea.id}
              className="glass border-border/50 hover:border-primary/50 transition-all duration-300 cursor-pointer"
              onClick={() => navigate(`/ideas/${idea.id}`)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-xl mb-2">{idea.title}</CardTitle>
                    <CardDescription className="line-clamp-2">
                      {idea.description}
                    </CardDescription>
                  </div>
                  <div className="ml-4">{getStatusBadge(idea)}</div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">
                      Target Market: {idea.target_market}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Created: {new Date(idea.created_at).toLocaleDateString()}
                    </p>
                    {idea.linked_pain_points.length > 0 && (
                      <p className="text-xs text-muted-foreground">
                        {idea.linked_pain_points.length} pain point(s) linked
                      </p>
                    )}
                  </div>
                  {idea.latest_validation?.overall_score && (
                    <div className="text-right">
                      {getScoreBadge(idea.latest_validation.overall_score)}
                    </div>
                  )}
                </div>
                <div className="mt-4 flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="glass border-border/50"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/ideas/${idea.id}`);
                    }}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    View Details
                  </Button>
                  {idea.latest_validation?.validation_id && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="glass border-border/50"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/ideas/${idea.id}/validate`);
                      }}
                    >
                      View Validation
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Results Count */}
      {!ideasLoading && filteredAndSortedIdeas.length > 0 && (
        <div className="text-center text-sm text-muted-foreground">
          Showing {filteredAndSortedIdeas.length} of {ideas.length} idea(s)
        </div>
      )}
    </div>
  );
}
