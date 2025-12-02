/**
 * ValidationReportView Component
 * 
 * Main dashboard for displaying validation report with overall score,
 * executive summary, strengths, weaknesses, and recommendations.
 * 
 * Requirements: 11.1, 11.2, 11.3, 11.4
 */

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  FileText, 
  Download, 
  Share2, 
  TrendingUp,
  Lightbulb,
  Calendar,
  BarChart3,
  Target,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Eye,
  Award
} from 'lucide-react';
import { ValidationReport } from '../types/validation';
import OverallScoreCard from './OverallScoreCard';
import StrengthsWeaknessesDisplay from './StrengthsWeaknessesDisplay';
import RecommendationsPanel from './RecommendationsPanel';
import MetricScoreCard from './MetricScoreCard';

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
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedSummary, setExpandedSummary] = useState(false);

  // Calculate metrics data for visualization
  const metricsData = [
    { name: 'Problem Clarity', value: report.problem_clarity?.value || 0, key: 'problem_clarity' },
    { name: 'Market Demand', value: report.market_demand?.value || 0, key: 'market_demand' },
    { name: 'Solution Fit', value: report.solution_fit?.value || 0, key: 'solution_fit' },
    { name: 'Differentiation', value: report.differentiation?.value || 0, key: 'differentiation' },
  ];

  const maxScore = 5;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header Section with Gradient Background */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-primary/10 via-accent/10 to-background p-6 border border-border/50">
        <div className="absolute inset-0 bg-grid-white/10 [mask-image:radial-gradient(white,transparent_85%)]" />
        
        <div className="relative z-10 flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-primary/20">
                <Award className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                  Validation Report
                </h1>
                <p className="text-muted-foreground mt-1">
                  Comprehensive analysis for "{report.idea_title}"
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4 mt-4 text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="h-4 w-4" />
                <span>
                  {new Date(report.validation_date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </span>
              </div>
              <Badge variant="outline" className="gap-1">
                <Eye className="h-3 w-3" />
                ID: {report.validation_id.slice(0, 8)}
              </Badge>
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
                className="glass border-border/50 hover:bg-primary/10"
              >
                <Download className="mr-2 h-4 w-4" />
                JSON
              </Button>
            )}
            {onExportPdf && (
              <Button
                variant="outline"
                size="sm"
                onClick={onExportPdf}
                disabled={isExporting}
                className="glass border-border/50 hover:bg-primary/10"
              >
                <Download className="mr-2 h-4 w-4" />
                PDF
              </Button>
            )}
            {onShare && (
              <Button
                variant="default"
                size="sm"
                onClick={onShare}
                disabled={isExporting}
                className="gap-2"
              >
                <Share2 className="h-4 w-4" />
                Share
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Overall Score Card - Prominent Display */}
      <OverallScoreCard score={report.overall_score} />

      {/* Tabbed Navigation for Better Organization */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-grid">
          <TabsTrigger value="overview" className="gap-2">
            <Sparkles className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="metrics" className="gap-2">
            <BarChart3 className="h-4 w-4" />
            Metrics
          </TabsTrigger>
          <TabsTrigger value="analysis" className="gap-2">
            <Target className="h-4 w-4" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="actions" className="gap-2">
            <TrendingUp className="h-4 w-4" />
            Actions
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          {/* Executive Summary with Expand/Collapse */}
          {report.executive_summary && (
            <Card className="glass border-border/50 hover:border-primary/30 transition-all">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-primary" />
                    Executive Summary
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setExpandedSummary(!expandedSummary)}
                    className="gap-2"
                  >
                    {expandedSummary ? (
                      <>
                        <ChevronUp className="h-4 w-4" />
                        Collapse
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4" />
                        Expand
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <p className={`text-muted-foreground whitespace-pre-wrap leading-relaxed transition-all ${
                  expandedSummary ? '' : 'line-clamp-3'
                }`}>
                  {report.executive_summary}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Quick Metrics Overview - Visual Bar Chart */}
          <Card className="glass border-border/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                Metrics at a Glance
              </CardTitle>
              <CardDescription>
                Visual comparison of all validation metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {metricsData.map((metric) => (
                  <div key={metric.key} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{metric.name}</span>
                      <span className="text-muted-foreground">
                        {metric.value.toFixed(1)} / {maxScore}
                      </span>
                    </div>
                    <div className="relative h-3 bg-muted/30 rounded-full overflow-hidden">
                      <div
                        className="absolute inset-y-0 left-0 bg-primary rounded-full transition-all duration-1000 ease-out"
                        style={{ width: `${(metric.value / maxScore) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

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
        </TabsContent>

        {/* Metrics Tab - Detailed Metric Cards */}
        <TabsContent value="metrics" className="space-y-6 mt-6">
          <div className="grid gap-6">
            {report.problem_clarity && (
              <MetricScoreCard
                metricName="problem_clarity"
                score={report.problem_clarity}
              />
            )}
            {report.market_demand && (
              <MetricScoreCard
                metricName="market_demand"
                score={report.market_demand}
              />
            )}
            {report.solution_fit && (
              <MetricScoreCard
                metricName="solution_fit"
                score={report.solution_fit}
              />
            )}
            {report.differentiation && (
              <MetricScoreCard
                metricName="differentiation"
                score={report.differentiation}
              />
            )}
          </div>
        </TabsContent>

        {/* Analysis Tab - Detailed Analysis */}
        <TabsContent value="analysis" className="space-y-6 mt-6">
          {report.detailed_analysis && (
            <Card className="glass border-border/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary" />
                  Detailed Analysis
                </CardTitle>
                <CardDescription>
                  In-depth examination of your idea's validation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p className="text-muted-foreground whitespace-pre-wrap leading-relaxed">
                    {typeof report.detailed_analysis === 'string' 
                      ? report.detailed_analysis 
                      : JSON.stringify(report.detailed_analysis, null, 2)
                    }
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Strengths and Weaknesses in Analysis Tab */}
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
        </TabsContent>

        {/* Actions Tab - Recommendations and Next Steps */}
        <TabsContent value="actions" className="space-y-6 mt-6">
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
                <ol className="space-y-4">
                  {report.next_steps.map((step, index) => (
                    <li key={index} className="flex gap-4 group">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent text-white flex items-center justify-center text-sm font-bold shadow-lg">
                        {index + 1}
                      </div>
                      <div className="flex-1 pt-1">
                        <p className="text-foreground leading-relaxed group-hover:text-primary transition-colors">
                          {step}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Report Metadata Footer */}
      <Card className="glass border-border/50 bg-card/30">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-sm text-muted-foreground">
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
