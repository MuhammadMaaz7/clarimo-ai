/**
 * TypeScript types for Idea Validation Module
 */

// Validation Status
export type ValidationStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

// Score for individual metrics
export interface Score {
  value: number; // 1-5
  justifications: string[];
  evidence?: Record<string, any>;
  recommendations: string[];
  metadata?: Record<string, any>;
  error?: boolean; // Indicates if this metric failed to evaluate
  error_message?: string; // Error message if evaluation failed
}

// Idea model
export interface Idea {
  id: string;
  user_id: string;
  title: string;
  description: string;
  problem_statement: string;
  solution_description: string;
  target_market: string;
  business_model?: string;
  team_capabilities?: string;
  created_at: string;
  updated_at: string;
  latest_validation?: {
    validation_id: string;
    overall_score: number;
    status: ValidationStatus;
    created_at: string;
  };
}

// Idea creation/update data
export interface IdeaFormData {
  title: string;
  description: string;
  problemStatement: string;
  solutionDescription: string;
  targetMarket: string;
  businessModel?: string;
  teamCapabilities?: string;
}

// Validation configuration
export interface ValidationConfig {
  includeWebSearch?: boolean;
  includeCompetitiveAnalysis?: boolean;
  maxCompetitorsToAnalyze?: number;
  useCachedResults?: boolean;
}

// Validation result
export interface ValidationResult {
  validation_id: string;
  idea_id: string;
  user_id: string;
  status: ValidationStatus;
  overall_score: number | null;
  individual_scores: IndividualScores | null;
  report_data: ReportData | null;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

// Individual metric scores (simplified to 4 core metrics)
export interface IndividualScores {
  problem_clarity?: Score;
  market_demand?: Score;
  solution_fit?: Score;
  differentiation?: Score;
}

// Report data
export interface ReportData {
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  validation_date: string;
}

// Validation report (comprehensive)
export interface ValidationReport {
  validation_id: string;
  idea_id: string;
  idea_title: string;
  overall_score: number;
  validation_date: string;
  
  // Individual scores (4 core metrics)
  problem_clarity?: Score;
  market_demand?: Score;
  solution_fit?: Score;
  differentiation?: Score;
  
  // Aggregated insights
  strengths: string[];
  weaknesses: string[];
  critical_recommendations: string[];
  
  // Visualizations
  radar_chart_data: Record<string, number>;
  score_distribution: Record<string, number>;
  
  // Detailed sections
  executive_summary?: string;
  detailed_analysis?: Record<string, any>;
  next_steps: string[];
}

// Validation status response
export interface ValidationStatusResponse {
  validation_id: string;
  status: ValidationStatus;
  progress: number;
  current_stage: string;
  estimated_completion: string | null;
}

// Validation history item
export interface ValidationHistoryItem {
  validation_id: string;
  idea_id: string;
  overall_score: number;
  status: ValidationStatus;
  created_at: string;
  completed_at: string | null;
}

// Comparison report
export interface ComparisonReport {
  comparison_id: string;
  validation_ids: string[];
  ideas: Array<Record<string, any>>;
  metric_comparison: Record<string, number[]>;
  winners: Record<string, string>;
  overall_recommendation: string | null;
  created_at: string;
}

// Version comparison
export interface VersionComparison {
  idea_id: string;
  validation_1_id: string;
  validation_2_id: string;
  validation_1_date: string;
  validation_2_date: string;
  score_deltas: Record<string, number>;
  improved_metrics: string[];
  declined_metrics: string[];
  unchanged_metrics: string[];
  overall_score_delta: number;
}

// Share link
export interface ShareLink {
  share_id: string;
  validation_id: string;
  share_url: string;
  privacy_level: 'public' | 'private' | 'password_protected';
  created_at: string;
  expires_at: string | null;
  is_active: boolean;
  access_count?: number;
}

// Metric names
export type MetricName =
  | 'problem_clarity'
  | 'market_demand'
  | 'solution_fit'
  | 'differentiation';

// Metric display information
export interface MetricInfo {
  name: MetricName;
  displayName: string;
  description: string;
  icon: string;
  color: string;
}

// Metric metadata (simplified to 4 core metrics)
export const METRIC_METADATA: Record<MetricName, Omit<MetricInfo, 'name'>> = {
  problem_clarity: {
    displayName: 'Problem Clarity',
    description: 'How clearly the idea defines the problem it solves',
    icon: '○',
    color: 'hsl(var(--primary))', // theme primary
  },
  market_demand: {
    displayName: 'Market Demand',
    description: 'Evidence of market interest and demand for the solution',
    icon: '△',
    color: 'hsl(var(--primary))', // theme primary
  },
  solution_fit: {
    displayName: 'Solution Fit',
    description: 'How well the solution addresses the identified problem',
    icon: '□',
    color: 'hsl(var(--primary))', // theme primary
  },
  differentiation: {
    displayName: 'Differentiation',
    description: 'Uniqueness and competitive advantage of the idea',
    icon: '◇',
    color: 'hsl(var(--primary))', // theme primary
  },
};

// Helper function to get metric info
export function getMetricInfo(metricName: MetricName): MetricInfo {
  return {
    name: metricName,
    ...METRIC_METADATA[metricName],
  };
}

// Helper function to get score color (subtle theme colors)
export function getScoreColor(score: number): string {
  if (score >= 4) return 'hsl(var(--primary))'; // theme primary for good
  if (score >= 3) return 'hsl(var(--muted-foreground))'; // muted for moderate
  return 'hsl(var(--destructive))'; // destructive for poor
}

// Helper function to get score label
export function getScoreLabel(score: number): string {
  if (score >= 4.5) return 'Excellent';
  if (score >= 4) return 'Strong';
  if (score >= 3) return 'Moderate';
  if (score >= 2) return 'Weak';
  return 'Poor';
}

// Helper function to format score
export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'N/A';
  return score.toFixed(2);
}
