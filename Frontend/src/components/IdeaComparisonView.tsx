import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { Idea, ValidationResult, ComparisonReport } from '../types/validation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, TrendingUp, AlertCircle } from 'lucide-react';
import ComparisonTable from './ComparisonTable';
import ComparisonRecommendation from './ComparisonRecommendation';

interface IdeaComparisonViewProps {
  ideas?: Idea[];
  preSelectedIdeaIds?: string[];
}

const IdeaComparisonView: React.FC<IdeaComparisonViewProps> = ({
  ideas: propIdeas,
  preSelectedIdeaIds = [],
}) => {
  const [ideas, setIdeas] = useState<Idea[]>(propIdeas || []);
  const [selectedIdeaIds, setSelectedIdeaIds] = useState<string[]>(preSelectedIdeaIds);
  const [validationResults, setValidationResults] = useState<Record<string, ValidationResult>>({});
  const [comparisonReport, setComparisonReport] = useState<ComparisonReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingIdeas, setLoadingIdeas] = useState(!propIdeas);
  const [error, setError] = useState<string | null>(null);

  // Load ideas if not provided
  useEffect(() => {
    if (!propIdeas) {
      loadIdeas();
    }
  }, [propIdeas]);

  // Load validation results for selected ideas
  useEffect(() => {
    if (selectedIdeaIds.length > 0) {
      loadValidationResults();
    }
  }, [selectedIdeaIds]);

  const loadIdeas = async () => {
    try {
      setLoadingIdeas(true);
      setError(null);
      const fetchedIdeas = await api.ideas.getAll({
        sortBy: 'updated_at',
        sortOrder: 'desc',
      });
      
      // Filter ideas that have at least one validation
      const ideasWithValidations = fetchedIdeas.filter(
        (idea) => idea.latest_validation && idea.latest_validation.status === 'completed'
      );
      
      setIdeas(ideasWithValidations);
    } catch (err: any) {
      setError(err.message || 'Failed to load ideas');
    } finally {
      setLoadingIdeas(false);
    }
  };

  const loadValidationResults = async () => {
    try {
      setError(null);
      const results: Record<string, ValidationResult> = {};
      
      for (const ideaId of selectedIdeaIds) {
        const idea = ideas.find((i) => i.id === ideaId);
        if (idea?.latest_validation?.validation_id) {
          const validation = await api.validations.getResult(
            idea.latest_validation.validation_id
          );
          results[ideaId] = validation;
        }
      }
      
      setValidationResults(results);
    } catch (err: any) {
      setError(err.message || 'Failed to load validation results');
    }
  };

  const handleIdeaSelection = (ideaId: string, checked: boolean) => {
    if (checked) {
      if (selectedIdeaIds.length >= 5) {
        setError('You can compare up to 5 ideas at a time');
        return;
      }
      setSelectedIdeaIds([...selectedIdeaIds, ideaId]);
    } else {
      setSelectedIdeaIds(selectedIdeaIds.filter((id) => id !== ideaId));
    }
  };

  const handleCompare = async () => {
    if (selectedIdeaIds.length < 2) {
      setError('Please select at least 2 ideas to compare');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Get validation IDs for selected ideas
      const validationIds = selectedIdeaIds
        .map((ideaId) => {
          const idea = ideas.find((i) => i.id === ideaId);
          return idea?.latest_validation?.validation_id;
        })
        .filter((id): id is string => !!id);

      if (validationIds.length !== selectedIdeaIds.length) {
        setError('Some selected ideas do not have completed validations');
        return;
      }

      // Fetch comparison report
      const report = await api.validations.compare(validationIds);
      setComparisonReport(report);
    } catch (err: any) {
      setError(err.message || 'Failed to generate comparison');
    } finally {
      setLoading(false);
    }
  };

  const handleClearSelection = () => {
    setSelectedIdeaIds([]);
    setComparisonReport(null);
    setValidationResults({});
  };

  if (loadingIdeas) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-3 text-lg">Loading ideas...</span>
      </div>
    );
  }

  if (ideas.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <AlertCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-lg font-semibold mb-2">No Ideas to Compare</h3>
          <p className="text-muted-foreground mb-4">
            You need at least 2 validated ideas to use the comparison feature.
          </p>
          <Button onClick={() => (window.location.href = '/ideas/new')}>
            Create Your First Idea
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Compare Ideas</h1>
        <p className="text-muted-foreground">
          Select 2-5 ideas to compare their validation scores side-by-side
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Idea Selection */}
      {!comparisonReport && (
        <Card>
          <CardHeader>
            <CardTitle>Select Ideas to Compare</CardTitle>
            <CardDescription>
              Choose 2-5 ideas with completed validations ({selectedIdeaIds.length} selected)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {ideas.map((idea) => (
                <div
                  key={idea.id}
                  className="flex items-start space-x-3 p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <Checkbox
                    id={`idea-${idea.id}`}
                    checked={selectedIdeaIds.includes(idea.id)}
                    onCheckedChange={(checked) =>
                      handleIdeaSelection(idea.id, checked as boolean)
                    }
                    disabled={
                      !selectedIdeaIds.includes(idea.id) && selectedIdeaIds.length >= 5
                    }
                  />
                  <div className="flex-1">
                    <label
                      htmlFor={`idea-${idea.id}`}
                      className="font-medium cursor-pointer"
                    >
                      {idea.title}
                    </label>
                    <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                      {idea.description}
                    </p>
                    {idea.latest_validation && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-muted-foreground">
                          Overall Score:
                        </span>
                        <span
                          className={`text-sm font-semibold ${
                            idea.latest_validation.overall_score >= 4
                              ? 'text-green-600'
                              : idea.latest_validation.overall_score >= 3
                              ? 'text-amber-600'
                              : 'text-red-600'
                          }`}
                        >
                          {idea.latest_validation.overall_score.toFixed(2)}/5.0
                        </span>
                        <span className="text-xs text-muted-foreground">
                          • Validated{' '}
                          {new Date(idea.latest_validation.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3 mt-6">
              <Button
                onClick={handleCompare}
                disabled={selectedIdeaIds.length < 2 || loading}
                className="flex-1"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Comparing...
                  </>
                ) : (
                  <>
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Compare Selected Ideas
                  </>
                )}
              </Button>
              {selectedIdeaIds.length > 0 && (
                <Button variant="outline" onClick={handleClearSelection}>
                  Clear Selection
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Comparison Results */}
      {comparisonReport && (
        <div className="space-y-6">
          {/* Action Buttons */}
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Comparison Results</h2>
            <Button variant="outline" onClick={handleClearSelection}>
              New Comparison
            </Button>
          </div>

          {/* Comparison Table */}
          <ComparisonTable
            comparisonReport={comparisonReport}
            validationResults={validationResults}
            ideas={ideas.filter((idea) => selectedIdeaIds.includes(idea.id))}
          />

          {/* Overall Recommendation */}
          <ComparisonRecommendation
            comparisonReport={comparisonReport}
            ideas={ideas.filter((idea) => selectedIdeaIds.includes(idea.id))}
          />
        </div>
      )}
    </div>
  );
};

export default IdeaComparisonView;
