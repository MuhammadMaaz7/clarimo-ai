/**
 * MetricDetailModal Component
 * 
 * Detailed modal view for individual metrics with:
 * - Full justifications and evidence
 * - Drill-down capability
 * - Comprehensive metric analysis
 * 
 * Requirements: All metric requirements
 */

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogCancel,
} from './ui/alert-dialog';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { 
  X,
  CheckCircle2, 
  AlertCircle, 
  Info,
  TrendingUp,
  Lightbulb,
  FileText,
  BarChart3,
  ExternalLink
} from 'lucide-react';
import { Score, MetricName, getMetricInfo, getScoreColor, getScoreLabel } from '../types/validation';

interface MetricDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  metricName: MetricName;
  score: Score;
}

export default function MetricDetailModal({
  isOpen,
  onClose,
  metricName,
  score,
}: MetricDetailModalProps) {
  const metricInfo = getMetricInfo(metricName);
  const scoreColor = getScoreColor(score.value);
  const scoreLabel = getScoreLabel(score.value);

  // Determine score status icon
  const getScoreIcon = () => {
    if (score.value >= 4) return <CheckCircle2 className="h-6 w-6" style={{ color: scoreColor }} />;
    if (score.value >= 3) return <Info className="h-6 w-6" style={{ color: scoreColor }} />;
    return <AlertCircle className="h-6 w-6" style={{ color: scoreColor }} />;
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto glass">
        {/* Header */}
        <AlertDialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3 flex-1">
              <div className="text-4xl">{metricInfo.icon}</div>
              <div className="flex-1">
                <AlertDialogTitle className="text-2xl flex items-center gap-2">
                  {metricInfo.displayName}
                  {getScoreIcon()}
                </AlertDialogTitle>
                <AlertDialogDescription className="text-base mt-1">
                  {metricInfo.description}
                </AlertDialogDescription>
              </div>
            </div>
            
            <AlertDialogCancel asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <X className="h-4 w-4" />
              </Button>
            </AlertDialogCancel>
          </div>

          {/* Score Display */}
          <div className="flex items-center gap-6 mt-6 p-6 bg-muted/30 rounded-lg">
            <div className="flex items-baseline gap-2">
              <div 
                className="text-6xl font-bold"
                style={{ color: scoreColor }}
              >
                {score.value.toFixed(1)}
              </div>
              <div className="text-2xl text-muted-foreground">/5.0</div>
            </div>
            
            <div className="flex-1">
              <Badge 
                variant="outline" 
                className="border-current text-lg px-4 py-1"
                style={{ color: scoreColor, borderColor: scoreColor }}
              >
                {scoreLabel}
              </Badge>
              
              {/* Score Interpretation */}
              <p className="text-sm text-muted-foreground mt-2">
                {score.value >= 4.5 && "Outstanding performance in this metric"}
                {score.value >= 4 && score.value < 4.5 && "Strong performance with minor areas for improvement"}
                {score.value >= 3 && score.value < 4 && "Moderate performance with room for enhancement"}
                {score.value >= 2 && score.value < 3 && "Below average performance requiring attention"}
                {score.value < 2 && "Significant improvement needed in this area"}
              </p>
            </div>
          </div>
        </AlertDialogHeader>

        {/* Content Sections */}
        <div className="space-y-6 mt-6">
          {/* Justifications Section */}
          {score.justifications && score.justifications.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-primary" />
                Analysis & Justifications
              </h3>
              <div className="space-y-3">
                {score.justifications.map((justification, index) => (
                  <div 
                    key={index} 
                    className="flex gap-3 p-4 bg-muted/20 rounded-lg border border-border/50"
                  >
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-semibold mt-0.5">
                      {index + 1}
                    </div>
                    <p className="flex-1 text-muted-foreground">{justification}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evidence Section */}
          {score.evidence && Object.keys(score.evidence).length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Supporting Evidence
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(score.evidence).map(([key, value]) => (
                  <div 
                    key={key} 
                    className="p-4 bg-muted/20 rounded-lg border border-border/50"
                  >
                    <div className="text-xs text-muted-foreground uppercase tracking-wide mb-1">
                      {key.replace(/_/g, ' ')}
                    </div>
                    <div className="text-lg font-semibold">
                      {typeof value === 'number' 
                        ? value.toLocaleString() 
                        : typeof value === 'object'
                        ? JSON.stringify(value, null, 2)
                        : String(value)
                      }
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations Section */}
          {score.recommendations && score.recommendations.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-primary" />
                Recommendations for Improvement
              </h3>
              <div className="space-y-3">
                {score.recommendations.map((recommendation, index) => (
                  <div 
                    key={index} 
                    className="flex gap-3 p-4 bg-primary/5 rounded-lg border border-primary/20"
                  >
                    <TrendingUp className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                    <p className="flex-1 text-muted-foreground">{recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata Section */}
          {score.metadata && Object.keys(score.metadata).length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                Additional Information
              </h3>
              <div className="space-y-2">
                {Object.entries(score.metadata).map(([key, value]) => (
                  <div 
                    key={key} 
                    className="flex items-center justify-between p-3 bg-muted/20 rounded-lg text-sm"
                  >
                    <span className="text-muted-foreground font-medium capitalize">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <span className="font-mono text-xs">
                      {typeof value === 'object' 
                        ? JSON.stringify(value) 
                        : String(value)
                      }
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Help Text */}
          <div className="p-4 bg-muted/10 rounded-lg border border-border/30">
            <p className="text-sm text-muted-foreground">
              <strong>About this metric:</strong> {metricInfo.description}
              {score.value < 3 && (
                <span className="block mt-2">
                  This metric scored below average. Review the recommendations above to improve your score.
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex justify-end gap-2 mt-6 pt-6 border-t border-border/50">
          <AlertDialogCancel asChild>
            <Button variant="outline">Close</Button>
          </AlertDialogCancel>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}
