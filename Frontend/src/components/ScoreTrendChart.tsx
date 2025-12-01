/**
 * ScoreTrendChart Component
 * 
 * Displays score changes over time across multiple validation versions.
 * Shows trends for each metric with visual indicators for improvements and declines.
 * 
 * Requirements: 13.2, 13.3
 */

import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { METRIC_METADATA, MetricName, ValidationHistoryItem } from '@/types/validation';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ScoreTrendChartProps {
  validationHistory: ValidationHistoryItem[];
  metricScores: Record<string, Record<string, number>>; // validation_id -> metric -> score
  className?: string;
  selectedMetrics?: MetricName[];
  showLegend?: boolean;
  maxScore?: number;
}

interface ChartDataPoint {
  date: string;
  validationId: string;
  formattedDate: string;
  [key: string]: string | number; // Dynamic metric scores
}

interface MetricTrend {
  metric: MetricName;
  displayName: string;
  color: string;
  trend: 'up' | 'down' | 'stable';
  change: number;
}

export const ScoreTrendChart: React.FC<ScoreTrendChartProps> = ({
  validationHistory,
  metricScores,
  className = '',
  selectedMetrics,
  showLegend = true,
  maxScore = 5,
}) => {
  // Get all available metrics from the data
  const allMetrics = Array.from(
    new Set(
      Object.values(metricScores).flatMap(scores => Object.keys(scores))
    )
  ) as MetricName[];

  // Use selected metrics or all metrics
  const metricsToShow = selectedMetrics || allMetrics;

  // State for toggling metrics
  const [visibleMetrics, setVisibleMetrics] = useState<Set<MetricName>>(
    new Set(metricsToShow)
  );

  // Transform data for chart
  const chartData: ChartDataPoint[] = validationHistory
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .map(validation => {
      const dataPoint: ChartDataPoint = {
        date: validation.created_at,
        validationId: validation.validation_id,
        formattedDate: formatDate(validation.created_at),
      };

      // Add scores for each metric
      const scores = metricScores[validation.validation_id] || {};
      metricsToShow.forEach(metric => {
        dataPoint[metric] = scores[metric] || 0;
      });

      return dataPoint;
    });

  // Calculate trends for each metric
  const metricTrends: MetricTrend[] = metricsToShow.map(metric => {
    const metricKey = metric as MetricName;
    const metadata = METRIC_METADATA[metricKey];
    
    // Get first and last scores
    const firstScore = chartData[0]?.[metric] as number || 0;
    const lastScore = chartData[chartData.length - 1]?.[metric] as number || 0;
    const change = lastScore - firstScore;
    
    let trend: 'up' | 'down' | 'stable' = 'stable';
    if (change > 0.1) trend = 'up';
    else if (change < -0.1) trend = 'down';

    return {
      metric: metricKey,
      displayName: metadata?.displayName || metric,
      color: metadata?.color || '#3B82F6',
      trend,
      change,
    };
  });

  // Format date for display
  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  // Toggle metric visibility
  const toggleMetric = (metric: MetricName) => {
    setVisibleMetrics(prev => {
      const newSet = new Set(prev);
      if (newSet.has(metric)) {
        newSet.delete(metric);
      } else {
        newSet.add(metric);
      }
      return newSet;
    });
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
          <p className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {label}
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4 text-sm">
              <span style={{ color: entry.color }}>{entry.name}:</span>
              <span className="font-bold" style={{ color: entry.color }}>
                {entry.value.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  // Custom legend
  const CustomLegend = () => (
    <div className="flex flex-wrap gap-3 justify-center mt-4">
      {metricTrends.map(({ metric, displayName, color, trend, change }) => {
        const isVisible = visibleMetrics.has(metric);
        
        return (
          <button
            key={metric}
            onClick={() => toggleMetric(metric)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all ${
              isVisible
                ? 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
                : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 opacity-50'
            }`}
          >
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: isVisible ? color : '#9ca3af' }}
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {displayName}
            </span>
            {trend === 'up' && (
              <TrendingUp className="w-4 h-4 text-green-500" />
            )}
            {trend === 'down' && (
              <TrendingDown className="w-4 h-4 text-red-500" />
            )}
            {trend === 'stable' && (
              <Minus className="w-4 h-4 text-gray-400" />
            )}
            <span
              className={`text-xs font-semibold ${
                trend === 'up'
                  ? 'text-green-600'
                  : trend === 'down'
                  ? 'text-red-600'
                  : 'text-gray-500'
              }`}
            >
              {change > 0 ? '+' : ''}{change.toFixed(2)}
            </span>
          </button>
        );
      })}
    </div>
  );

  if (chartData.length === 0) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <p className="text-gray-500 dark:text-gray-400">No validation history available</p>
      </div>
    );
  }

  if (chartData.length === 1) {
    return (
      <div className={`flex flex-col items-center justify-center h-96 ${className}`}>
        <p className="text-gray-500 dark:text-gray-400 mb-2">
          Only one validation available
        </p>
        <p className="text-sm text-gray-400 dark:text-gray-500">
          Run more validations to see trends over time
        </p>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="formattedDate"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            stroke="#d1d5db"
          />
          <YAxis
            domain={[0, maxScore]}
            tick={{ fill: '#6b7280', fontSize: 12 }}
            stroke="#d1d5db"
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Reference line at average score */}
          <ReferenceLine
            y={maxScore / 2}
            stroke="#9ca3af"
            strokeDasharray="5 5"
            label={{ value: 'Average', fill: '#6b7280', fontSize: 11 }}
          />

          {/* Lines for each metric */}
          {metricTrends.map(({ metric, displayName, color }) => (
            visibleMetrics.has(metric) && (
              <Line
                key={metric}
                type="monotone"
                dataKey={metric}
                name={displayName}
                stroke={color}
                strokeWidth={2}
                dot={{ fill: color, r: 4 }}
                activeDot={{ r: 6 }}
                animationDuration={500}
              />
            )
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Custom legend with trend indicators */}
      {showLegend && <CustomLegend />}
    </div>
  );
};

export default ScoreTrendChart;
