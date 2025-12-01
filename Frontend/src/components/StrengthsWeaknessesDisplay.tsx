/**
 * StrengthsWeaknessesDisplay Component
 * 
 * Side-by-side display of strengths and weaknesses with visual cards
 * showing metric names and scores.
 * 
 * Requirements: 11.3
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { 
  TrendingUp, 
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  Info
} from 'lucide-react';
import { IndividualScores, MetricName, getMetricInfo, formatScore } from '../types/validation';

interface StrengthsWeaknessesDisplayProps {
  strengths: string[]; // Metric names that are strengths
  weaknesses: string[]; // Metric names that are weaknesses
  individualScores: IndividualScores;
}

export default function StrengthsWeaknessesDisplay({
  strengths,
  weaknesses,
  individualScores,
}: StrengthsWeaknessesDisplayProps) {
  // Helper to get score for a metric name
  const getScoreForMetric = (metricName: string) => {
    const key = metricName as MetricName;
    return individualScores[key];
  };

  // Helper to render metric card
  const renderMetricCard = (metricName: string, isStrength: boolean) => {
    const score = getScoreForMetric(metricName);
    if (!score) return null;

    const metricInfo = getMetricInfo(metricName as MetricName);
    const bgColor = isStrength 
      ? 'bg-green-500/10 border-green-500/30' 
      : 'bg-red-500/10 border-red-500/30';
    const iconColor = isStrength ? 'text-green-500' : 'text-red-500';

    return (
      <div
        key={metricName}
        className={`p-4 rounded-lg border ${bgColor} transition-all hover:scale-[1.02] cursor-default`}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{metricInfo.icon}</span>
            <div>
              <h4 className="font-semibold text-sm">{metricInfo.displayName}</h4>
              <p className="text-xs text-muted-foreground line-clamp-1">
                {metricInfo.description}
              </p>
            </div>
          </div>
          {isStrength ? (
            <CheckCircle2 className={`h-5 w-5 ${iconColor} flex-shrink-0`} />
          ) : (
            <AlertTriangle className={`h-5 w-5 ${iconColor} flex-shrink-0`} />
          )}
        </div>
        <div className="flex items-center justify-between mt-3">
          <Badge 
            variant={isStrength ? "default" : "destructive"}
            className="text-sm font-bold"
          >
            {formatScore(score.value)} / 5.0
          </Badge>
          <span className="text-xs text-muted-foreground">
            {isStrength ? 'Strong Performance' : 'Needs Improvement'}
          </span>
        </div>
      </div>
    );
  };

  const hasStrengths = strengths.length > 0;
  const hasWeaknesses = weaknesses.length > 0;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      {/* Strengths Section */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <TrendingUp className="h-5 w-5" />
            Strengths
          </CardTitle>
          <CardDescription>
            {hasStrengths 
              ? `${strengths.length} area${strengths.length > 1 ? 's' : ''} where your idea excels`
              : 'No standout strengths identified (scores ≥ 4.0)'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          {hasStrengths ? (
            <div className="space-y-3">
              {strengths.map((metricName) => renderMetricCard(metricName, true))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Info className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">
                No metrics scored 4.0 or higher. Focus on improving your idea across all dimensions.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Weaknesses Section */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
            <TrendingDown className="h-5 w-5" />
            Weaknesses
          </CardTitle>
          <CardDescription>
            {hasWeaknesses 
              ? `${weaknesses.length} area${weaknesses.length > 1 ? 's' : ''} that need attention`
              : 'No critical weaknesses identified (all scores > 2.0)'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          {hasWeaknesses ? (
            <div className="space-y-3">
              {weaknesses.map((metricName) => renderMetricCard(metricName, false))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-3 opacity-50 text-green-500" />
              <p className="text-sm">
                Great! All metrics scored above 2.0. Continue refining to achieve even higher scores.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
