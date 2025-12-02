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
  FileText
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

  // Format evidence value for display
  const formatEvidenceValue = (value: any): React.ReactNode => {
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    if (typeof value === 'object' && value !== null) {
      // Handle external data with detailed breakdown
      if (value.total_products_found !== undefined) {
        const hn = value.hackernews_products || 0;
        const gh = value.github_repos || 0;
        const appStore = value.app_store_apps || 0;
        const playStore = value.play_store_apps || 0;
        
        return (
          <div className="space-y-1">
            <div className="font-bold">{value.total_products_found} Total Products</div>
            <div className="text-sm space-y-0.5">
              {hn > 0 && <div>• HackerNews: {hn}</div>}
              {gh > 0 && <div>• GitHub: {gh}</div>}
              {appStore > 0 && <div>• App Store: {appStore}</div>}
              {playStore > 0 && <div>• Play Store: {playStore}</div>}
            </div>
          </div>
        );
      }
      // Handle app store data separately
      if (value.app_store || value.play_store) {
        const appStoreCount = value.app_store?.apps?.length || 0;
        const playStoreCount = value.play_store?.apps?.length || 0;
        return (
          <div className="space-y-1">
            <div>App Store: {appStoreCount} apps</div>
            <div>Play Store: {playStoreCount} apps</div>
            <div className="text-xs text-muted-foreground">
              Total: {appStoreCount + playStoreCount} competitors
            </div>
          </div>
        );
      }
      // Format other objects
      const entries = Object.entries(value);
      if (entries.length <= 5) {
        return (
          <div className="space-y-1 text-sm">
            {entries.map(([k, v]) => (
              <div key={k}>{k}: {String(v)}</div>
            ))}
          </div>
        );
      }
      return `${entries.length} items`;
    }
    return String(value);
  };

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

          {/* Evidence Section - Only show user-friendly data */}
          {score.evidence && Object.keys(score.evidence).length > 0 && (() => {
            // Filter out technical metadata
            const technicalKeys = ['model', 'llm', 'api', 'version', 'timestamp', 'processing_time', 'tokens', 'confidence_threshold', 'engine', 'provider'];
            const filteredEvidence = Object.entries(score.evidence).filter(([key]) => 
              !technicalKeys.some(tech => key.toLowerCase().includes(tech))
            );
            
            if (filteredEvidence.length === 0) return null;
            
            return (
              <div className="space-y-3">
                <h3 className="font-semibold text-lg flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary" />
                  Market Evidence
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {filteredEvidence.map(([key, value]) => (
                    <div 
                      key={key} 
                      className="p-4 bg-muted/20 rounded-lg border border-border/50"
                    >
                      <div className="text-xs text-muted-foreground uppercase tracking-wide mb-2">
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div className="text-base font-semibold">
                        {formatEvidenceValue(value)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}

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
