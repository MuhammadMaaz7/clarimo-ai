import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { ValidationHistoryItem } from '../types/validation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import LoadingSpinner from './LoadingSpinner';
import { AlertCircle, Calendar, TrendingUp, TrendingDown, Minus, CheckCircle, Clock, XCircle } from 'lucide-react';

interface ValidationHistoryViewProps {
  ideaId: string;
  ideaTitle?: string;
  onCompareVersions?: (validationId1: string, validationId2: string) => void;
}

const ValidationHistoryView: React.FC<ValidationHistoryViewProps> = ({
  ideaId,
  ideaTitle,
  onCompareVersions,
}) => {
  const navigate = useNavigate();
  const [history, setHistory] = useState<ValidationHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);

  useEffect(() => {
    loadHistory();
  }, [ideaId]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.validations.getHistory(ideaId);
      setHistory(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load validation history');
      console.error('Error loading validation history:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVersionSelect = (validationId: string) => {
    setSelectedVersions((prev) => {
      if (prev.includes(validationId)) {
        return prev.filter((id) => id !== validationId);
      } else if (prev.length < 2) {
        return [...prev, validationId];
      } else {
        // Replace the first selected version
        return [prev[1], validationId];
      }
    });
  };

  const handleCompareVersions = () => {
    if (selectedVersions.length === 2 && onCompareVersions) {
      onCompareVersions(selectedVersions[0], selectedVersions[1]);
    }
  };

  const handleViewValidation = (validationId: string) => {
    navigate(`/ideas/${ideaId}/validate?validation_id=${validationId}`);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <Clock className="h-5 w-5 text-blue-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      completed: 'default',
      in_progress: 'secondary',
      failed: 'destructive',
      pending: 'outline',
    };

    return (
      <Badge variant={variants[status] || 'outline'}>
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  const getScoreColor = (score: number) => {
    if (score >= 4) return 'text-green-600';
    if (score >= 3) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreTrend = (currentScore: number, previousScore: number | null) => {
    if (previousScore === null) return null;
    
    const delta = currentScore - previousScore;
    if (Math.abs(delta) < 0.1) {
      return <Minus className="h-4 w-4 text-gray-500 inline ml-2" />;
    } else if (delta > 0) {
      return (
        <span className="text-green-600 text-sm ml-2">
          <TrendingUp className="h-4 w-4 inline" /> +{delta.toFixed(2)}
        </span>
      );
    } else {
      return (
        <span className="text-red-600 text-sm ml-2">
          <TrendingDown className="h-4 w-4 inline" /> {delta.toFixed(2)}
        </span>
      );
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
          <Button onClick={loadHistory} variant="outline" className="mt-4">
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (history.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No validation history yet</p>
            <p className="text-sm text-gray-500 mt-2">
              Run a validation to see it appear here
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Validation History</CardTitle>
          <CardDescription>
            {ideaTitle && <span className="font-medium">{ideaTitle}</span>}
            {history.length > 0 && (
              <span className="text-sm text-gray-500 ml-2">
                ({history.length} validation{history.length !== 1 ? 's' : ''})
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {selectedVersions.length === 2 && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-blue-600" />
                  <span className="text-sm font-medium text-blue-900">
                    2 versions selected for comparison
                  </span>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={handleCompareVersions}
                    size="sm"
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    Compare Versions
                  </Button>
                  <Button
                    onClick={() => setSelectedVersions([])}
                    size="sm"
                    variant="outline"
                  >
                    Clear Selection
                  </Button>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            {history.map((item, index) => {
              const previousScore = index < history.length - 1 ? history[index + 1].overall_score : null;
              const isSelected = selectedVersions.includes(item.validation_id);

              return (
                <Card
                  key={item.validation_id}
                  className={`transition-all ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : 'hover:shadow-md'
                  }`}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          {getStatusIcon(item.status)}
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900">
                                Version {history.length - index}
                              </span>
                              {getStatusBadge(item.status)}
                              {index === 0 && (
                                <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
                                  Latest
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                              <Calendar className="h-4 w-4" />
                              {formatDate(item.created_at)}
                            </div>
                          </div>
                        </div>

                        {item.status === 'completed' && (
                          <div className="mt-3 flex items-center">
                            <span className="text-sm text-gray-600 mr-2">Overall Score:</span>
                            <span className={`text-2xl font-bold ${getScoreColor(item.overall_score)}`}>
                              {item.overall_score.toFixed(2)}
                            </span>
                            <span className="text-gray-500 text-sm ml-1">/5.0</span>
                            {getScoreTrend(item.overall_score, previousScore)}
                          </div>
                        )}

                        {item.status === 'failed' && (
                          <div className="mt-3 text-sm text-red-600">
                            Validation failed. Please try again.
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col gap-2 ml-4">
                        {item.status === 'completed' && (
                          <>
                            <Button
                              onClick={() => handleViewValidation(item.validation_id)}
                              size="sm"
                              variant="outline"
                            >
                              View Report
                            </Button>
                            <Button
                              onClick={() => handleVersionSelect(item.validation_id)}
                              size="sm"
                              variant={isSelected ? 'default' : 'outline'}
                              disabled={selectedVersions.length === 2 && !isSelected}
                            >
                              {isSelected ? 'Selected' : 'Select to Compare'}
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {history.length > 1 && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <div className="text-blue-600 mt-1">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-blue-900">Compare Versions</p>
                <p className="text-sm text-blue-700 mt-1">
                  Select any two completed validations to see how your idea has evolved over time.
                  You'll see which metrics improved, declined, or stayed the same.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ValidationHistoryView;
