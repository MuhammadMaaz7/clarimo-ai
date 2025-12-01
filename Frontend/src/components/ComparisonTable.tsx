import React from 'react';
import {
  Idea,
  ValidationResult,
  ComparisonReport,
  MetricName,
  METRIC_METADATA,
  getScoreColor,
  formatScore,
} from '../types/validation';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Trophy, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ComparisonTableProps {
  comparisonReport: ComparisonReport;
  validationResults: Record<string, ValidationResult>;
  ideas: Idea[];
}

const ComparisonTable: React.FC<ComparisonTableProps> = ({
  comparisonReport,
  validationResults,
  ideas,
}) => {
  // Get all metric names from the first validation result
  const metricNames: MetricName[] = Object.keys(METRIC_METADATA) as MetricName[];

  // Helper to get score for a specific idea and metric
  const getScore = (ideaId: string, metric: MetricName): number | null => {
    const validation = validationResults[ideaId];
    if (!validation?.individual_scores) return null;
    return validation.individual_scores[metric]?.value ?? null;
  };

  // Helper to check if an idea is the winner for a metric
  const isWinner = (ideaId: string, metric: MetricName): boolean => {
    const idea = ideas.find((i) => i.id === ideaId);
    if (!idea?.latest_validation?.validation_id) return false;
    
    const winnerValidationId = comparisonReport.winners[metric];
    return idea.latest_validation.validation_id === winnerValidationId;
  };

  // Helper to get overall score
  const getOverallScore = (ideaId: string): number | null => {
    const validation = validationResults[ideaId];
    return validation?.overall_score ?? null;
  };

  // Helper to determine if overall winner
  const isOverallWinner = (ideaId: string): boolean => {
    const scores = ideas.map((idea) => getOverallScore(idea.id) ?? 0);
    const maxScore = Math.max(...scores);
    const currentScore = getOverallScore(ideaId);
    return currentScore === maxScore && currentScore !== null;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Side-by-Side Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b-2">
                <th className="text-left p-4 font-semibold bg-muted/50 sticky left-0 z-10">
                  Metric
                </th>
                {ideas.map((idea) => (
                  <th
                    key={idea.id}
                    className="text-center p-4 font-semibold bg-muted/50 min-w-[180px]"
                  >
                    <div className="space-y-1">
                      <div className="font-semibold text-sm line-clamp-2">
                        {idea.title}
                      </div>
                      {isOverallWinner(idea.id) && (
                        <Badge variant="default" className="bg-amber-500">
                          <Trophy className="h-3 w-3 mr-1" />
                          Top Choice
                        </Badge>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Overall Score Row */}
              <tr className="border-b bg-accent/30">
                <td className="p-4 font-semibold sticky left-0 bg-accent/30 z-10">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">🎯</span>
                    <span>Overall Score</span>
                  </div>
                </td>
                {ideas.map((idea) => {
                  const score = getOverallScore(idea.id);
                  const isWinner = isOverallWinner(idea.id);
                  return (
                    <td
                      key={idea.id}
                      className={`text-center p-4 ${
                        isWinner ? 'bg-amber-50 dark:bg-amber-950/20' : ''
                      }`}
                    >
                      <div className="flex flex-col items-center gap-1">
                        <span
                          className="text-2xl font-bold"
                          style={{ color: score ? getScoreColor(score) : '#999' }}
                        >
                          {formatScore(score)}
                        </span>
                        <span className="text-xs text-muted-foreground">/ 5.0</span>
                        {isWinner && (
                          <Trophy className="h-4 w-4 text-amber-500 mt-1" />
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>

              {/* Individual Metric Rows */}
              {metricNames.map((metric) => {
                const metricInfo = METRIC_METADATA[metric];
                
                return (
                  <tr key={metric} className="border-b hover:bg-accent/50 transition-colors">
                    <td className="p-4 sticky left-0 bg-background z-10">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{metricInfo.icon}</span>
                        <div>
                          <div className="font-medium">{metricInfo.displayName}</div>
                          <div className="text-xs text-muted-foreground line-clamp-1">
                            {metricInfo.description}
                          </div>
                        </div>
                      </div>
                    </td>
                    {ideas.map((idea) => {
                      const score = getScore(idea.id, metric);
                      const winner = isWinner(idea.id, metric);
                      
                      return (
                        <td
                          key={idea.id}
                          className={`text-center p-4 ${
                            winner ? 'bg-green-50 dark:bg-green-950/20' : ''
                          }`}
                        >
                          {score !== null ? (
                            <div className="flex flex-col items-center gap-1">
                              <span
                                className="text-xl font-semibold"
                                style={{ color: getScoreColor(score) }}
                              >
                                {score.toFixed(1)}
                              </span>
                              {winner && (
                                <Badge
                                  variant="outline"
                                  className="text-xs border-green-500 text-green-700 dark:text-green-400"
                                >
                                  <Trophy className="h-3 w-3 mr-1" />
                                  Best
                                </Badge>
                              )}
                            </div>
                          ) : (
                            <span className="text-muted-foreground">N/A</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Legend */}
        <div className="mt-6 p-4 bg-muted/50 rounded-lg">
          <h4 className="font-semibold mb-3 text-sm">Score Legend</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: getScoreColor(5) }}
              />
              <span>4.0-5.0: Excellent</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: getScoreColor(3.5) }}
              />
              <span>3.0-3.9: Moderate</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: getScoreColor(2) }}
              />
              <span>1.0-2.9: Weak</span>
            </div>
            <div className="flex items-center gap-2">
              <Trophy className="h-4 w-4 text-green-600" />
              <span>Highest in category</span>
            </div>
          </div>
        </div>

        {/* Comparison Insights */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          {ideas.map((idea) => {
            const validation = validationResults[idea.id];
            if (!validation?.individual_scores) return null;

            const scores = Object.entries(validation.individual_scores)
              .filter(([_, score]) => score?.value !== undefined)
              .map(([metric, score]) => ({
                metric: metric as MetricName,
                value: score.value,
              }));

            const avgScore = getOverallScore(idea.id) ?? 0;
            const strongMetrics = scores.filter((s) => s.value >= 4);
            const weakMetrics = scores.filter((s) => s.value <= 2);

            return (
              <Card key={idea.id} className="bg-accent/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm line-clamp-2">{idea.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                      <span className="font-medium">Strengths ({strongMetrics.length})</span>
                    </div>
                    {strongMetrics.length > 0 ? (
                      <ul className="text-xs text-muted-foreground space-y-1 ml-6">
                        {strongMetrics.slice(0, 3).map((s) => (
                          <li key={s.metric}>
                            {METRIC_METADATA[s.metric].displayName} ({s.value.toFixed(1)})
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-muted-foreground ml-6">None identified</p>
                    )}
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingDown className="h-4 w-4 text-red-600" />
                      <span className="font-medium">Weaknesses ({weakMetrics.length})</span>
                    </div>
                    {weakMetrics.length > 0 ? (
                      <ul className="text-xs text-muted-foreground space-y-1 ml-6">
                        {weakMetrics.slice(0, 3).map((s) => (
                          <li key={s.metric}>
                            {METRIC_METADATA[s.metric].displayName} ({s.value.toFixed(1)})
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-muted-foreground ml-6">None identified</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default ComparisonTable;
