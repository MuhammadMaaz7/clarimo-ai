import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { VersionComparison, MetricName, METRIC_METADATA } from '../types/validation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import LoadingSpinner from './LoadingSpinner';
import ScoreDeltaDisplay from './ScoreDeltaDisplay';
import { AlertCircle, Calendar, TrendingUp, TrendingDown, ArrowLeft, Info } from 'lucide-react';

interface VersionComparisonViewProps {
  validationId1: string;
  validationId2: string;
  onBack?: () => void;
}

const VersionComparisonView: React.FC<VersionComparisonViewProps> = ({
  validationId1,
  validationId2,
  onBack,
}) => {
  const [comparison, setComparison] = useState<VersionComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadComparison();
  }, [validationId1, validationId2]);

  const loadComparison = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.validations.compareVersions(validationId1, validationId2);
      setComparison(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load version comparison');
      console.error('Error loading version comparison:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getMetricDisplayName = (metricKey: string): string => {
    const metricName = metricKey as MetricName;
    return METRIC_METADATA[metricName]?.displayName || metricKey;
  };

  const getMetricIcon = (metricKey: string): string => {
    const metricName = metricKey as MetricName;
    return METRIC_METADATA[metricName]?.icon || '📊';
  };

  const getCategoryBadge = (metrics: string[], label: string, variant: 'default' | 'secondary' | 'destructive') => {
    if (metrics.length === 0) return null;

    return (
      <div className="mb-4">
        <Badge variant={variant} className="mb-2">
          {label} ({metrics.length})
        </Badge>
        <div className="flex flex-wrap gap-2 mt-2">
          {metrics.map((metric) => (
            <div
              key={metric}
              className="px-3 py-1 bg-white border rounded-md text-sm flex items-center gap-2"
            >
              <span>{getMetricIcon(metric)}</span>
              <span>{getMetricDisplayName(metric)}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={loadComparison} variant="outline">
              Try Again
            </Button>
            {onBack && (
              <Button onClick={onBack} variant="outline">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to History
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!comparison) {
    return null;
  }

  const hasChanges =
    comparison.improved_metrics.length > 0 ||
    comparison.declined_metrics.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Version Comparison</CardTitle>
              <CardDescription>
                Comparing two validation versions to track improvements
              </CardDescription>
            </div>
            {onBack && (
              <Button onClick={onBack} variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to History
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-500">Earlier Version</div>
              <div className="flex items-center gap-2 text-gray-700">
                <Calendar className="h-4 w-4" />
                {formatDate(comparison.validation_1_date)}
              </div>
            </div>
            <div className="space-y-2">
              <div className="text-sm font-medium text-gray-500">Later Version</div>
              <div className="flex items-center gap-2 text-gray-700">
                <Calendar className="h-4 w-4" />
                {formatDate(comparison.validation_2_date)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Overall Score Change */}
      <Card className={
        comparison.overall_score_delta > 0
          ? 'border-green-200 bg-green-50'
          : comparison.overall_score_delta < 0
          ? 'border-red-200 bg-red-50'
          : 'border-gray-200 bg-gray-50'
      }>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {comparison.overall_score_delta > 0 ? (
              <TrendingUp className="h-6 w-6 text-green-600" />
            ) : comparison.overall_score_delta < 0 ? (
              <TrendingDown className="h-6 w-6 text-red-600" />
            ) : (
              <div className="h-6 w-6 text-gray-600">—</div>
            )}
            Overall Score Change
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScoreDeltaDisplay
            delta={comparison.overall_score_delta}
            size="large"
            showLabel={true}
          />
          {comparison.overall_score_delta > 0 && (
            <p className="text-sm text-green-700 mt-2">
              Your idea validation has improved! Keep refining based on the recommendations.
            </p>
          )}
          {comparison.overall_score_delta < 0 && (
            <p className="text-sm text-red-700 mt-2">
              Some metrics have declined. Review the detailed changes below to identify areas for improvement.
            </p>
          )}
          {comparison.overall_score_delta === 0 && (
            <p className="text-sm text-gray-700 mt-2">
              The overall score remained the same, but individual metrics may have changed.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Metric Changes Summary */}
      {hasChanges && (
        <Card>
          <CardHeader>
            <CardTitle>Metric Changes Summary</CardTitle>
            <CardDescription>
              Overview of which metrics improved, declined, or stayed the same
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {getCategoryBadge(
              comparison.improved_metrics,
              'Improved',
              'default'
            )}
            {getCategoryBadge(
              comparison.declined_metrics,
              'Declined',
              'destructive'
            )}
            {getCategoryBadge(
              comparison.unchanged_metrics,
              'Unchanged',
              'secondary'
            )}
          </CardContent>
        </Card>
      )}

      {/* Detailed Score Deltas */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Score Changes</CardTitle>
          <CardDescription>
            Score changes for each validation metric
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(comparison.score_deltas).map(([metricKey, delta]) => {
              const isImproved = comparison.improved_metrics.includes(metricKey);
              const isDeclined = comparison.declined_metrics.includes(metricKey);
              const isUnchanged = comparison.unchanged_metrics.includes(metricKey);

              return (
                <div
                  key={metricKey}
                  className={`p-4 rounded-lg border ${
                    isImproved
                      ? 'bg-green-50 border-green-200'
                      : isDeclined
                      ? 'bg-red-50 border-red-200'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{getMetricIcon(metricKey)}</span>
                      <div>
                        <div className="font-medium text-gray-900">
                          {getMetricDisplayName(metricKey)}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          {isImproved && (
                            <Badge variant="default" className="bg-green-600">
                              Improved
                            </Badge>
                          )}
                          {isDeclined && (
                            <Badge variant="destructive">
                              Declined
                            </Badge>
                          )}
                          {isUnchanged && (
                            <Badge variant="secondary">
                              Unchanged
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <ScoreDeltaDisplay delta={delta} size="medium" />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Insights and Recommendations */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 mt-1" />
            <div>
              <p className="text-sm font-medium text-blue-900">Insights</p>
              <div className="text-sm text-blue-700 mt-2 space-y-2">
                {comparison.improved_metrics.length > 0 && (
                  <p>
                    ✅ <strong>{comparison.improved_metrics.length}</strong> metric
                    {comparison.improved_metrics.length !== 1 ? 's' : ''} improved since the last validation.
                    Great progress!
                  </p>
                )}
                {comparison.declined_metrics.length > 0 && (
                  <p>
                    ⚠️ <strong>{comparison.declined_metrics.length}</strong> metric
                    {comparison.declined_metrics.length !== 1 ? 's' : ''} declined.
                    Review the recommendations for these areas.
                  </p>
                )}
                {comparison.unchanged_metrics.length > 0 && (
                  <p>
                    ℹ️ <strong>{comparison.unchanged_metrics.length}</strong> metric
                    {comparison.unchanged_metrics.length !== 1 ? 's' : ''} remained stable.
                  </p>
                )}
                {comparison.overall_score_delta > 0.5 && (
                  <p className="font-medium">
                    🎉 Significant improvement! Your overall score increased by{' '}
                    {comparison.overall_score_delta.toFixed(2)} points.
                  </p>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VersionComparisonView;
