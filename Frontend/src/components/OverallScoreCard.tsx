/**
 * OverallScoreCard Component
 * 
 * Large, prominent display of the overall validation score with
 * visual indicator (color-coded) and score interpretation text.
 * 
 * Requirements: 11.2
 */

import { Card, CardContent } from './ui/card';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Award,
  AlertCircle,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { getScoreColor, getScoreLabel } from '../types/validation';

interface OverallScoreCardProps {
  score: number;
  previousScore?: number; // Optional: for showing improvement/decline
}

export default function OverallScoreCard({ score, previousScore }: OverallScoreCardProps) {
  const scoreColor = getScoreColor(score);
  const scoreLabel = getScoreLabel(score);
  
  // Calculate score change if previous score is provided
  const scoreDelta = previousScore !== undefined ? score - previousScore : null;
  const hasImproved = scoreDelta !== null && scoreDelta > 0;
  const hasDeclined = scoreDelta !== null && scoreDelta < 0;
  const isUnchanged = scoreDelta !== null && scoreDelta === 0;

  // Get interpretation based on score
  const getInterpretation = (score: number): string => {
    if (score >= 4.5) {
      return 'Outstanding! Your idea shows exceptional potential across all dimensions. This is a strong candidate for pursuit.';
    } else if (score >= 4.0) {
      return 'Excellent! Your idea demonstrates strong viability with solid fundamentals. Minor refinements could make it even stronger.';
    } else if (score >= 3.5) {
      return 'Good! Your idea has solid potential with some areas for improvement. Focus on addressing the weaknesses identified.';
    } else if (score >= 3.0) {
      return 'Moderate. Your idea has potential but requires significant work in several areas. Review the recommendations carefully.';
    } else if (score >= 2.0) {
      return 'Needs Work. Your idea faces substantial challenges. Consider pivoting or addressing critical weaknesses before proceeding.';
    } else {
      return 'High Risk. Your idea currently shows significant challenges across multiple dimensions. Major revisions are recommended.';
    }
  };

  // Get icon based on score
  const getScoreIcon = (score: number) => {
    if (score >= 4.5) return <Award className="h-12 w-12 text-white" />;
    if (score >= 4.0) return <CheckCircle2 className="h-12 w-12 text-white" />;
    if (score >= 3.0) return <AlertCircle className="h-12 w-12 text-white" />;
    return <XCircle className="h-12 w-12 text-white" />;
  };

  return (
    <Card className="glass border-border/50 overflow-hidden">
      <CardContent className="p-0">
        <div className="grid md:grid-cols-[300px_1fr] gap-0">
          {/* Score Display Section */}
          <div 
            className="p-8 flex flex-col items-center justify-center text-white relative overflow-hidden"
            style={{
              background: `linear-gradient(135deg, ${scoreColor} 0%, ${scoreColor}dd 100%)`,
            }}
          >
            {/* Background decoration */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white rounded-full -translate-y-16 translate-x-16" />
              <div className="absolute bottom-0 left-0 w-24 h-24 bg-white rounded-full translate-y-12 -translate-x-12" />
            </div>

            {/* Icon */}
            <div className="mb-4 relative z-10">
              {getScoreIcon(score)}
            </div>

            {/* Score Value */}
            <div className="text-center relative z-10">
              <div className="text-6xl font-bold mb-2">
                {score.toFixed(1)}
              </div>
              <div className="text-2xl font-semibold opacity-90 mb-1">
                / 5.0
              </div>
              <div className="text-lg font-medium opacity-80 uppercase tracking-wide">
                {scoreLabel}
              </div>
            </div>

            {/* Score Change Indicator */}
            {scoreDelta !== null && (
              <div className="mt-4 flex items-center gap-2 text-sm font-medium relative z-10">
                {hasImproved && (
                  <>
                    <TrendingUp className="h-4 w-4" />
                    <span>+{scoreDelta.toFixed(2)} from last validation</span>
                  </>
                )}
                {hasDeclined && (
                  <>
                    <TrendingDown className="h-4 w-4" />
                    <span>{scoreDelta.toFixed(2)} from last validation</span>
                  </>
                )}
                {isUnchanged && (
                  <>
                    <Minus className="h-4 w-4" />
                    <span>No change from last validation</span>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Interpretation Section */}
          <div className="p-8 flex flex-col justify-center">
            <h3 className="text-2xl font-bold mb-4">Overall Assessment</h3>
            <p className="text-muted-foreground text-lg leading-relaxed mb-6">
              {getInterpretation(score)}
            </p>

            {/* Score Breakdown Visual */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Score Range</span>
                <span className="font-medium">1.0 - 5.0</span>
              </div>
              <div className="relative h-3 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full overflow-hidden">
                {/* Score indicator */}
                <div 
                  className="absolute top-0 h-full w-1 bg-white shadow-lg"
                  style={{ left: `${((score - 1) / 4) * 100}%` }}
                >
                  <div className="absolute -top-6 left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-white" />
                </div>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Poor</span>
                <span>Moderate</span>
                <span>Excellent</span>
              </div>
            </div>

            {/* Additional Context */}
            <div className="mt-6 p-4 bg-card/50 rounded-lg border border-border/30">
              <p className="text-sm text-muted-foreground">
                <strong className="text-foreground">Note:</strong> This score represents the average 
                of all validation metrics. Review individual metric scores below for detailed insights 
                into specific areas of strength and improvement.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
