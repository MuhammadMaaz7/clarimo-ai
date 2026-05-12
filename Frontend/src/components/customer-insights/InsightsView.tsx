/**
 * Insights View Component
 * Displays pain points, desired features, and recurring themes
 */

import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { AlertCircle, Sparkles, TrendingUp, Tag } from 'lucide-react';

interface InsightsViewProps {
  insights: {
    pain_points: string[];
    desired_features: string[];
    recurring_themes: string[];
    keywords: string[];
  };
}

export default function InsightsView({ insights }: InsightsViewProps) {
  return (
    <div className="space-y-6">
      {/* Pain Points */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Pain Points
          </CardTitle>
        </CardHeader>
        <CardContent>
          {insights.pain_points.length === 0 ? (
            <p className="text-muted-foreground text-sm">No pain points identified</p>
          ) : (
            <div className="space-y-2">
              {insights.pain_points.map((point, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg bg-destructive/5 border border-destructive/20"
                >
                  <span className="text-destructive font-semibold text-sm">
                    {index + 1}.
                  </span>
                  <p className="text-sm flex-1">{point}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Desired Features */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Desired Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          {insights.desired_features.length === 0 ? (
            <p className="text-muted-foreground text-sm">No feature requests identified</p>
          ) : (
            <div className="space-y-2">
              {insights.desired_features.map((feature, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20"
                >
                  <span className="text-primary font-semibold text-sm">
                    {index + 1}.
                  </span>
                  <p className="text-sm flex-1">{feature}</p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recurring Themes */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-success" />
            Recurring Themes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {insights.recurring_themes.length === 0 ? (
            <p className="text-muted-foreground text-sm">No recurring themes identified</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {insights.recurring_themes.map((theme, index) => (
                <Badge key={index} variant="secondary" className="text-sm">
                  {theme}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Keywords */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Tag className="h-5 w-5 text-muted-foreground" />
            Top Keywords
          </CardTitle>
        </CardHeader>
        <CardContent>
          {insights.keywords.length === 0 ? (
            <p className="text-muted-foreground text-sm">No keywords identified</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {insights.keywords.map((keyword, index) => (
                <Badge key={index} variant="outline" className="text-sm">
                  {keyword}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
