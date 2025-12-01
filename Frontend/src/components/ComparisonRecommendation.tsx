import React from 'react';
import { Idea, ComparisonReport } from '../types/validation';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import {
  Trophy,
  Lightbulb,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react';

interface ComparisonRecommendationProps {
  comparisonReport: ComparisonReport;
  ideas: Idea[];
}

const ComparisonRecommendation: React.FC<ComparisonRecommendationProps> = ({
  comparisonReport,
  ideas,
}) => {
  // Find the recommended idea (highest overall score)
  const getRecommendedIdea = (): Idea | null => {
    if (!comparisonReport.ideas || comparisonReport.ideas.length === 0) {
      return null;
    }

    // Get the idea with the highest overall score
    let maxScore = -1;
    let recommendedIdeaId: string | null = null;

    comparisonReport.ideas.forEach((ideaData: any) => {
      const score = ideaData.overall_score ?? 0;
      if (score > maxScore) {
        maxScore = score;
        recommendedIdeaId = ideaData.id;
      }
    });

    return ideas.find((idea) => idea.id === recommendedIdeaId) || null;
  };

  const recommendedIdea = getRecommendedIdea();

  // Count wins for each idea
  const getWinCounts = (): Record<string, number> => {
    const counts: Record<string, number> = {};
    
    ideas.forEach((idea) => {
      counts[idea.id] = 0;
    });

    Object.values(comparisonReport.winners).forEach((winnerValidationId) => {
      const winnerIdea = ideas.find(
        (idea) => idea.latest_validation?.validation_id === winnerValidationId
      );
      if (winnerIdea) {
        counts[winnerIdea.id] = (counts[winnerIdea.id] || 0) + 1;
      }
    });

    return counts;
  };

  const winCounts = getWinCounts();

  // Get key differentiators for recommended idea
  const getKeyDifferentiators = (): string[] => {
    if (!recommendedIdea) return [];

    const differentiators: string[] = [];
    
    Object.entries(comparisonReport.winners).forEach(([metric, winnerValidationId]) => {
      if (recommendedIdea.latest_validation?.validation_id === winnerValidationId) {
        differentiators.push(metric);
      }
    });

    return differentiators.slice(0, 5); // Top 5 differentiators
  };

  const keyDifferentiators = getKeyDifferentiators();

  // Generate next steps
  const getNextSteps = (): string[] => {
    if (!recommendedIdea) return [];

    const steps: string[] = [
      'Review the detailed validation report for deeper insights',
      'Validate assumptions with potential customers through interviews',
      'Create a minimum viable product (MVP) to test core features',
      'Develop a go-to-market strategy based on validation findings',
    ];

    // Add specific steps based on weak areas
    const recommendedIdeaData = comparisonReport.ideas.find(
      (i: any) => i.id === recommendedIdea.id
    );

    if (recommendedIdeaData) {
      const scores = recommendedIdeaData.individual_scores || {};
      
      if (scores.market_demand?.value < 3) {
        steps.push('Conduct additional market research to validate demand');
      }

    }

    return steps.slice(0, 6);
  };

  const nextSteps = getNextSteps();

  // Format metric name for display
  const formatMetricName = (metric: string): string => {
    return metric
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  if (!recommendedIdea) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-amber-500" />
          <p className="text-muted-foreground">
            Unable to generate recommendation. Please ensure all ideas have completed validations.
          </p>
        </CardContent>
      </Card>
    );
  }

  const recommendedIdeaScore =
    comparisonReport.ideas.find((i: any) => i.id === recommendedIdea.id)?.overall_score ?? 0;

  return (
    <Card className="border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-background">
      <CardHeader>
        <div className="flex items-center gap-3">
          <Trophy className="h-6 w-6 text-amber-500" />
          <CardTitle className="text-2xl">Our Recommendation</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Recommended Idea */}
        <div className="p-6 bg-background rounded-lg border-2 border-primary/30">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <Badge variant="default" className="mb-2 bg-amber-500">
                <Trophy className="h-3 w-3 mr-1" />
                Top Choice
              </Badge>
              <h3 className="text-2xl font-bold mb-2">{recommendedIdea.title}</h3>
              <p className="text-muted-foreground line-clamp-3">
                {recommendedIdea.description}
              </p>
            </div>
            <div className="text-right ml-4">
              <div className="text-4xl font-bold text-primary">
                {recommendedIdeaScore.toFixed(2)}
              </div>
              <div className="text-sm text-muted-foreground">Overall Score</div>
            </div>
          </div>

          {/* Win Count */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <span>
              Scored highest in {winCounts[recommendedIdea.id] || 0} out of{' '}
              {Object.keys(comparisonReport.winners).length} metrics
            </span>
          </div>
        </div>

        {/* Justification */}
        <div>
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-amber-500" />
            Why This Idea?
          </h4>
          <div className="space-y-2">
            {comparisonReport.overall_recommendation ? (
              <p className="text-muted-foreground leading-relaxed">
                {comparisonReport.overall_recommendation}
              </p>
            ) : (
              <p className="text-muted-foreground leading-relaxed">
                Based on our comprehensive analysis, this idea demonstrates the strongest overall
                validation across multiple dimensions. It shows the best balance of market
                opportunity, technical feasibility, and business viability among the compared
                options.
              </p>
            )}
          </div>
        </div>

        {/* Key Differentiators */}
        {keyDifferentiators.length > 0 && (
          <div>
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Key Strengths
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {keyDifferentiators.map((metric) => (
                <div
                  key={metric}
                  className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-900"
                >
                  <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm font-medium">{formatMetricName(metric)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Next Steps */}
        <div>
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <ArrowRight className="h-5 w-5 text-primary" />
            Recommended Next Steps
          </h4>
          <ol className="space-y-2">
            {nextSteps.map((step, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-sm font-semibold flex items-center justify-center">
                  {index + 1}
                </span>
                <span className="text-sm text-muted-foreground pt-0.5">{step}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4 border-t">
          <Button
            className="flex-1"
            onClick={() => (window.location.href = `/ideas/${recommendedIdea.id}`)}
          >
            View Full Details
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            onClick={() =>
              (window.location.href = `/ideas/${recommendedIdea.id}/validate`)
            }
          >
            Run New Validation
          </Button>
        </div>

        {/* Disclaimer */}
        <div className="text-xs text-muted-foreground text-center pt-4 border-t">
          <p>
            This recommendation is based on quantitative validation scores. Consider your personal
            goals, resources, and market timing when making your final decision.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default ComparisonRecommendation;
