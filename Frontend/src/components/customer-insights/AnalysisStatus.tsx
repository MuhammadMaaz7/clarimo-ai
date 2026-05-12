/**
 * Analysis Status Component
 * Shows real-time progress of customer insights analysis
 */

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { Loader2, CheckCircle2, Search, Users, Lightbulb, MessageSquare } from 'lucide-react';
import { customerInsightsApi } from '../../services/customerInsightsApi';

interface AnalysisStatusProps {
  analysisId: string;
  startupIdea: string;
  status: string;
  currentStage: string;
  progressPercentage: number;
  onComplete?: () => void;
}

export default function AnalysisStatus({
  analysisId,
  startupIdea,
  status: initialStatus,
  currentStage: initialStage,
  progressPercentage: initialProgress,
  onComplete,
}: AnalysisStatusProps) {
  const [status, setStatus] = useState(initialStatus);
  const [currentStage, setCurrentStage] = useState(initialStage);
  const [progressPercentage, setProgressPercentage] = useState(initialProgress);

  useEffect(() => {
    if (status === 'processing') {
      const interval = setInterval(async () => {
        try {
          const data = await customerInsightsApi.getStatus(analysisId);
          setStatus(data.status);
          setCurrentStage(data.current_stage);
          setProgressPercentage(data.progress_percentage);

          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(interval);
            if (data.status === 'completed' && onComplete) {
              onComplete();
            }
          }
        } catch (error) {
          console.error('Failed to fetch status:', error);
        }
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [analysisId, status, onComplete]);

  const getStageInfo = (stage: string) => {
    const stages: Record<string, { icon: any; label: string; description: string }> = {
      data_collection: {
        icon: Search,
        label: 'Collecting Data',
        description: 'Fetching discussions from Reddit and Product Hunt',
      },
      community_discovery: {
        icon: MessageSquare,
        label: 'Discovering Communities',
        description: 'Identifying active communities',
      },
      segmentation: {
        icon: Users,
        label: 'Segmenting Audience',
        description: 'Analyzing and grouping discussions',
      },
      insights_extraction: {
        icon: Lightbulb,
        label: 'Extracting Insights',
        description: 'Identifying pain points and features',
      },
      finalizing: {
        icon: CheckCircle2,
        label: 'Finalizing',
        description: 'Preparing results',
      },
    };

    return stages[stage] || {
      icon: Loader2,
      label: 'Processing',
      description: 'Analyzing your startup idea',
    };
  };

  const stageInfo = getStageInfo(currentStage);
  const StageIcon = stageInfo.icon;

  return (
    <Card className="glass border-border/50">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
              Analysis in Progress
            </CardTitle>
            <CardDescription className="mt-2">
              {startupIdea}
            </CardDescription>
          </div>
          <Badge variant="secondary">
            {progressPercentage}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <Progress value={progressPercentage} className="h-2" />
          <p className="text-sm text-muted-foreground text-center">
            Estimated time: 1-2 minutes
          </p>
        </div>

        {/* Current Stage */}
        <div className="flex items-start gap-4 p-4 rounded-lg bg-primary/5 border border-primary/20">
          <div className="rounded-lg bg-primary/10 p-2">
            <StageIcon className="h-6 w-6 text-primary" />
          </div>
          <div className="flex-1">
            <p className="font-semibold">{stageInfo.label}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {stageInfo.description}
            </p>
          </div>
        </div>

        {/* Stage Timeline */}
        <div className="space-y-3">
          <p className="text-sm font-medium">Pipeline Stages:</p>
          <div className="space-y-2">
            {[
              { key: 'data_collection', label: 'Data Collection', range: '0-50%' },
              { key: 'community_discovery', label: 'Community Discovery', range: '50-60%' },
              { key: 'segmentation', label: 'Audience Segmentation', range: '60-85%' },
              { key: 'insights_extraction', label: 'Insights Extraction', range: '85-95%' },
              { key: 'finalizing', label: 'Finalizing', range: '95-100%' },
            ].map((stage) => {
              const isActive = currentStage === stage.key;
              const isCompleted = progressPercentage > parseInt(stage.range.split('-')[1]);

              return (
                <div
                  key={stage.key}
                  className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
                    isActive
                      ? 'bg-primary/10 border border-primary/20'
                      : isCompleted
                      ? 'bg-success/5 border border-success/20'
                      : 'bg-muted/30'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="h-4 w-4 text-success" />
                  ) : isActive ? (
                    <Loader2 className="h-4 w-4 text-primary animate-spin" />
                  ) : (
                    <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/30" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm font-medium">{stage.label}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">{stage.range}</span>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
