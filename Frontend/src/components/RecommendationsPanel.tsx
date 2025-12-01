/**
 * RecommendationsPanel Component
 * 
 * Prioritized list of recommendations categorized by metric
 * in an actionable format.
 * 
 * Requirements: 11.4
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { 
  Lightbulb, 
  CheckSquare,
  AlertCircle,
  ArrowRight,
  Target
} from 'lucide-react';
import { useState } from 'react';

interface RecommendationsPanelProps {
  recommendations: string[];
  categorized?: boolean; // If true, recommendations should be in format "Category: Recommendation"
}

export default function RecommendationsPanel({
  recommendations,
  categorized = false,
}: RecommendationsPanelProps) {
  const [checkedItems, setCheckedItems] = useState<Set<number>>(new Set());

  // Toggle checkbox for a recommendation
  const toggleCheck = (index: number) => {
    const newChecked = new Set(checkedItems);
    if (newChecked.has(index)) {
      newChecked.delete(index);
    } else {
      newChecked.add(index);
    }
    setCheckedItems(newChecked);
  };

  // Parse recommendation to extract category if present
  const parseRecommendation = (rec: string): { category: string | null; text: string } => {
    if (!categorized) {
      return { category: null, text: rec };
    }

    // Check if recommendation starts with a category (e.g., "Problem Clarity: ...")
    const match = rec.match(/^([^:]+):\s*(.+)$/);
    if (match) {
      return { category: match[1].trim(), text: match[2].trim() };
    }
    return { category: null, text: rec };
  };

  // Get priority badge based on position (first few are critical)
  const getPriorityBadge = (index: number) => {
    if (index < 2) {
      return (
        <Badge variant="destructive" className="text-xs">
          Critical
        </Badge>
      );
    } else if (index < 4) {
      return (
        <Badge variant="default" className="text-xs bg-orange-500">
          High Priority
        </Badge>
      );
    } else {
      return (
        <Badge variant="outline" className="text-xs">
          Recommended
        </Badge>
      );
    }
  };

  // Get icon color based on priority
  const getIconColor = (index: number) => {
    if (index < 2) return 'text-red-500';
    if (index < 4) return 'text-orange-500';
    return 'text-blue-500';
  };

  if (!recommendations || recommendations.length === 0) {
    return (
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-primary" />
            Recommendations
          </CardTitle>
          <CardDescription>
            Actionable steps to improve your idea
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <CheckSquare className="h-12 w-12 mx-auto mb-3 opacity-50 text-green-500" />
            <p className="text-sm">
              Excellent! No critical recommendations at this time. Your idea is well-positioned.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass border-border/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-primary" />
          Critical Recommendations
        </CardTitle>
        <CardDescription>
          Prioritized action items to strengthen your idea ({recommendations.length} total)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Info Banner */}
        <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="text-blue-600 dark:text-blue-400 font-medium mb-1">
              Action Plan
            </p>
            <p className="text-muted-foreground">
              These recommendations are prioritized by impact. Start with critical items first, 
              then work through high-priority and recommended actions.
            </p>
          </div>
        </div>

        {/* Recommendations List */}
        <div className="space-y-4">
          {recommendations.map((recommendation, index) => {
            const { category, text } = parseRecommendation(recommendation);
            const isChecked = checkedItems.has(index);

            return (
              <div
                key={index}
                className={`group p-4 rounded-lg border transition-all ${
                  isChecked
                    ? 'bg-green-500/5 border-green-500/30 opacity-60'
                    : 'bg-card/50 border-border/30 hover:border-primary/50 hover:bg-card/80'
                }`}
              >
                <div className="flex items-start gap-3">
                  {/* Checkbox */}
                  <button
                    onClick={() => toggleCheck(index)}
                    className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-all mt-0.5 ${
                      isChecked
                        ? 'bg-green-500 border-green-500'
                        : 'border-border hover:border-primary'
                    }`}
                  >
                    {isChecked && (
                      <CheckSquare className="h-4 w-4 text-white" />
                    )}
                  </button>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Target className={`h-4 w-4 ${getIconColor(index)} flex-shrink-0`} />
                        {getPriorityBadge(index)}
                        {category && (
                          <Badge variant="outline" className="text-xs">
                            {category}
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-muted-foreground flex-shrink-0">
                        #{index + 1}
                      </span>
                    </div>
                    <p className={`text-sm leading-relaxed ${
                      isChecked ? 'line-through text-muted-foreground' : 'text-foreground'
                    }`}>
                      {text}
                    </p>
                  </div>

                  {/* Action Arrow */}
                  {!isChecked && (
                    <ArrowRight className="h-5 w-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5" />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Progress Indicator */}
        {checkedItems.size > 0 && (
          <div className="mt-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-green-600 dark:text-green-400">
                Progress
              </span>
              <span className="text-sm text-muted-foreground">
                {checkedItems.size} of {recommendations.length} completed
              </span>
            </div>
            <div className="w-full bg-border/30 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500"
                style={{ width: `${(checkedItems.size / recommendations.length) * 100}%` }}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
