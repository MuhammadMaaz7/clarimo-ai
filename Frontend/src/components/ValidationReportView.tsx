/**
 * ValidationReportView Component
 * 
 * Main dashboard for displaying validation report with overall score,
 * executive summary, strengths, weaknesses, and recommendations.
 * 
 * Requirements: 11.1, 11.2, 11.3, 11.4
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { 
  FileText, 
  Download, 
  Share2, 
  TrendingUp, 
  TrendingDown,
  AlertCircle,
  CheckCircle2,
  Lightbulb,
  Calendar
} from 'lucide-react';
import { ValidationReport } from '../types/validation';
import OverallScoreCard from './OverallScoreCard';
import StrengthsWeaknessesDisplay from './StrengthsWeaknessesDisplay';
import RecommendationsPanel from './RecommendationsPanel';

interface ValidationReportViewProps {
  report: ValidationReport;
  onExportJson?: () => void;
  onExportPdf?: () => void;
  onShare?: () => void;
  isExporting?: boolean;
}

export default function ValidationReportView({
  report,
  onExportJson,
  onExportPdf,
  onShare,
  isExporting = false,
}: ValidationReportViewProps) {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <FileText className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Validation Report</h1>
          </div>
          <p className="text-muted-foreground">
            Comprehensive analysis for "{report.idea_title}"
          </p>
          <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <span>
              Validated on {new Date(report.validation_date).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </span>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex gap-2">
          {onExportJson && (
            <Button
              variant="outline"
              size="sm"
              onClick={onExportJson}
              disabled={isExporting}
              className="glass border-border/50"
            >
              <Download className="mr-2 h-4 w-4" />
              Export JSON
            </Button>
          )}
          {onExportPdf && (
            <Button
              variant="outline"
              size="sm"
              onClick={onExportPdf}
              disabled={isExporting}
              className="glass border-border/50"
            >
              <Download className="mr-2 h-4 w-4" />
              Export PDF
            </Button>
          )}
          {onShare && (
            <Button
              variant="outline"
              size="sm"
              onClick={onShare}
              disabled={isExporting}
              className="glass border-border/50"
            >
              <Share2 className="mr-2 h-4 w-4" />
              Share
            </Button>
          )}
        </div>
      </div>

      {/* Overall Score Card - Prominent Display */}
      <OverallScoreCard score={report.overall_score} />

      {/* Executive Summary */}
      {report.executive_summary && (
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-primary" />
              Executive Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground whitespace-pre-wrap leading-relaxed">
              {report.executive_summary}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Strengths and Weaknesses */}
      <StrengthsWeaknessesDisplay
        strengths={report.strengths}
        weaknesses={report.weaknesses}
        individualScores={{
          problem_clarity: report.problem_clarity,
          market_demand: report.market_demand,
          solution_fit: report.solution_fit,
          differentiation: report.differentiation,
        }}
      />

      {/* Critical Recommendations */}
      <RecommendationsPanel recommendations={report.critical_recommendations} />

      {/* Next Steps */}
      {report.next_steps && report.next_steps.length > 0 && (
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Next Steps
            </CardTitle>
            <CardDescription>
              Recommended actions to move forward with your idea
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-3">
              {report.next_steps.map((step, index) => (
                <li key={index} className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-semibold">
                    {index + 1}
                  </div>
                  <p className="text-muted-foreground flex-1 pt-0.5">{step}</p>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}

      {/* Report Metadata */}
      <Card className="glass border-border/50 bg-card/30">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span>Validation ID: {report.validation_id}</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              <span>
                Generated: {new Date(report.validation_date).toLocaleString()}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
