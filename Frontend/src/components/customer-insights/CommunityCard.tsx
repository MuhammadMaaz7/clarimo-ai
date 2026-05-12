/**
 * Community Card Component
 * Displays information about a discovered community
 */

import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { MessageSquare, TrendingUp, ExternalLink } from 'lucide-react';

interface CommunityCardProps {
  community: {
    name: string;
    source: string;
    discussion_count: number;
    engagement_score: number;
    url: string | null;
    description: string | null;
  };
}

export default function CommunityCard({ community }: CommunityCardProps) {
  const getSourceBadge = (source: string) => {
    const colors: Record<string, string> = {
      reddit: 'bg-orange-500/10 text-orange-500 hover:bg-orange-500/20',
      producthunt: 'bg-red-500/10 text-red-500 hover:bg-red-500/20',
    };

    return (
      <Badge variant="outline" className={colors[source] || ''}>
        {source === 'reddit' ? 'Reddit' : 'Product Hunt'}
      </Badge>
    );
  };

  const getEngagementColor = (score: number) => {
    if (score >= 7) return 'text-success';
    if (score >= 4) return 'text-primary';
    return 'text-muted-foreground';
  };

  return (
    <Card className="glass border-border/50 hover:border-primary/50 transition-all">
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            {community.name}
          </CardTitle>
          {getSourceBadge(community.source)}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {community.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {community.description}
            </p>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MessageSquare className="h-4 w-4" />
                <span>Discussions</span>
              </div>
              <p className="text-2xl font-bold">{community.discussion_count}</p>
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                <span>Engagement</span>
              </div>
              <p className={`text-2xl font-bold ${getEngagementColor(community.engagement_score)}`}>
                {community.engagement_score.toFixed(1)}
              </p>
            </div>
          </div>

          {community.url && (
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => window.open(community.url!, '_blank')}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              Visit Community
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
