/**
 * MetricScoreCard Component
 * 
 * Reusable component for displaying any validation metric with:
 * - Score value with visual indicator
 * - Justifications list
 * - Recommendations list
 * - Evidence display
 * 
 * Requirements: 2.5, 3.5, 4.5, 5.5, 6.4, 7.4, 8.4, 9.5, 10.4
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { 
  CheckCircle2, 
  AlertCircle, 
  Info,
  ChevronRight,
  TrendingUp,
  Lightbulb,
  FileText
} from 'lucide-react';
import { Score, MetricName, getMetricInfo, getScoreColor, getScoreLabel } from '../types/validation';

interface MetricScoreCardProps {
  metricName: MetricName;
  score: Score;
  onViewDetails?: () => void;
  compact?: boolean;
  className?: string;
}

export default function MetricScoreCard({
  metricName,
  score,
  onViewDetails,
  compact = false,
  className = '',
}: MetricScoreCardProps) {
  const metricInfo = getMetricInfo(metricName);
  const scoreColor = getScoreColor(score.value);
  const scoreLabel = getScoreLabel(score.value);

  // Determine score status icon
  const getScoreIcon = () => {
    if (score.value >= 4) return <CheckCircle2 className="h-5 w-5" style={{ color: scoreColor }} />;
    if (score.value >= 3) return <Info className="h-5 w-5" style={{ color: scoreColor }} />;
    return <AlertCircle className="h-5 w-5" style={{ color: scoreColor }} />;
  };

  // Compact view for grid layouts
  if (compact) {
    return (
      <Card 
        className={`glass border-border/50 hover:border-primary/50 transition-all cursor-pointer ${className}`}
        onClick={onViewDetails}
      >
        <CardContent className="pt-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="text-2xl">{metricInfo.icon}</div>
              <div>
                <h3 className="font-semibold text-sm">{metricInfo.displayName}</h3>
                <p className="text-xs text-muted-foreground line-clamp-1">
                  {metricInfo.description}
                </p>
              </div>
            </div>
          </div>
          
          {/* Score Display */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div 
                className="text-3xl font-bold"
                style={{ color: scoreColor }}
              >
                {score.value.toFixed(1)}
              </div>
              <div className="text-sm text-muted-foreground">/5.0</div>
            </div>
            <Badge 
              variant="outline" 
              className="border-current"
              style={{ color: scoreColor, borderColor: scoreColor }}
            >
              {scoreLabel}
            </Badge>
          </div>

          {/* Quick Stats */}
          <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
            <span>{score.justifications.length} justifications</span>
            <span>{score.recommendations.length} recommendations</span>
          </div>

          {onViewDetails && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="w-full mt-3 text-xs"
            >
              View Details
              <ChevronRight className="ml-1 h-3 w-3" />
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  // Full view with all details
  return (
    <Card className={`glass border-border/50 ${className}`}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">{metricInfo.icon}</div>
            <div>
              <CardTitle className="flex items-center gap-2">
                {metricInfo.displayName}
                {getScoreIcon()}
              </CardTitle>
              <CardDescription>{metricInfo.description}</CardDescription>
            </div>
          </div>
          
          {/* Score Badge */}
          <div className="flex flex-col items-end gap-2">
            <div 
              className="text-4xl font-bold"
              style={{ color: scoreColor }}
            >
              {score.value.toFixed(1)}
            </div>
            <Badge 
              variant="outline" 
              className="border-current"
              style={{ color: scoreColor, borderColor: scoreColor }}
            >
              {scoreLabel}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Justifications */}
        {score.justifications && score.justifications.length > 0 && (
          <div>
            <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              Justifications
            </h4>
            <ul className="space-y-2">
              {score.justifications.map((justification, index) => (
                <li 
                  key={index} 
                  className="flex gap-2 text-sm text-muted-foreground"
                >
                  <span className="text-primary mt-1">•</span>
                  <span className="flex-1">{justification}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Evidence */}
        {score.evidence && Object.keys(score.evidence).length > 0 && (
          <div>
            <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              Evidence
            </h4>
            <div className="space-y-2">
              {Object.entries(score.evidence).map(([key, value]) => (
                <div 
                  key={key} 
                  className="flex items-center justify-between text-sm bg-muted/30 rounded-lg p-3"
                >
                  <span className="text-muted-foreground capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="font-medium">
                    {typeof value === 'number' 
                      ? value.toLocaleString() 
                      : typeof value === 'object'
                      ? JSON.stringify(value)
                      : String(value)
                    }
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {score.recommendations && score.recommendations.length > 0 && (
          <div>
            <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-primary" />
              Recommendations
            </h4>
            <ul className="space-y-2">
              {score.recommendations.map((recommendation, index) => (
                <li 
                  key={index} 
                  className="flex gap-2 text-sm"
                >
                  <TrendingUp className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                  <span className="flex-1 text-muted-foreground">{recommendation}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Metadata (if any) */}
        {score.metadata && Object.keys(score.metadata).length > 0 && (
          <div className="pt-4 border-t border-border/50">
            <details className="text-xs text-muted-foreground">
              <summary className="cursor-pointer hover:text-foreground transition-colors">
                Additional Information
              </summary>
              <div className="mt-2 space-y-1 pl-4">
                {Object.entries(score.metadata).map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <span className="font-medium">{key}:</span>
                    <span>{String(value)}</span>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}

        {/* View Details Button */}
        {onViewDetails && (
          <Button 
            variant="outline" 
            className="w-full"
            onClick={onViewDetails}
          >
            View Detailed Analysis
            <ChevronRight className="ml-2 h-4 w-4" />
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
