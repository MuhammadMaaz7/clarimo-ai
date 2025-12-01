/**
 * ScoreDistributionChart Component
 * 
 * Displays validation scores as a bar chart with color-coding based on score ranges.
 * Provides a clear visual representation of metric performance.
 * 
 * Requirements: 11.5
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
  LabelList,
} from 'recharts';
import { METRIC_METADATA, MetricName, getScoreColor, getScoreLabel } from '@/types/validation';

interface ScoreDistributionChartProps {
  scores: Record<string, number>;
  className?: string;
  showLegend?: boolean;
  maxScore?: number;
  orientation?: 'horizontal' | 'vertical';
}

interface ChartDataPoint {
  metric: string;
  displayName: string;
  shortName: string;
  score: number;
  color: string;
  label: string;
}

export const ScoreDistributionChart: React.FC<ScoreDistributionChartProps> = ({
  scores,
  className = '',
  showLegend = false,
  maxScore = 5,
  orientation = 'vertical',
}) => {
  // Transform scores into chart data format
  const chartData: ChartDataPoint[] = Object.entries(scores).map(([key, value]) => {
    const metricKey = key as MetricName;
    const metadata = METRIC_METADATA[metricKey];
    
    return {
      metric: key,
      displayName: metadata?.displayName || key,
      shortName: getShortName(metadata?.displayName || key),
      score: value,
      color: getScoreColor(value),
      label: getScoreLabel(value),
    };
  });

  // Sort by score descending
  chartData.sort((a, b) => b.score - a.score);

  // Helper function to create short names for better display
  function getShortName(displayName: string): string {
    const words = displayName.split(' ');
    if (words.length === 1) return displayName;
    if (words.length === 2) return words.map(w => w.substring(0, 6)).join(' ');
    return words.map(w => w[0]).join('');
  }

  // Custom tooltip component
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
          <p className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
            {data.displayName}
          </p>
          <p className="text-sm" style={{ color: data.color }}>
            Score: <span className="font-bold">{data.score.toFixed(2)}</span> / {maxScore}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            {data.label}
          </p>
        </div>
      );
    }
    return null;
  };

  // Custom label for bars
  const CustomLabel = (props: any) => {
    const { x, y, width, height, value } = props;
    
    if (orientation === 'horizontal') {
      return (
        <text
          x={x + width + 5}
          y={y + height / 2}
          fill="#374151"
          textAnchor="start"
          dominantBaseline="middle"
          className="text-sm font-semibold"
        >
          {value.toFixed(2)}
        </text>
      );
    } else {
      return (
        <text
          x={x + width / 2}
          y={y - 5}
          fill="#374151"
          textAnchor="middle"
          dominantBaseline="hanging"
          className="text-sm font-semibold"
        >
          {value.toFixed(2)}
        </text>
      );
    }
  };

  if (chartData.length === 0) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <p className="text-gray-500 dark:text-gray-400">No data available</p>
      </div>
    );
  }

  if (orientation === 'horizontal') {
    return (
      <div className={`w-full ${className}`}>
        <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 50)}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 20, right: 60, bottom: 20, left: 120 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              type="number"
              domain={[0, maxScore]}
              tick={{ fill: '#6b7280', fontSize: 12 }}
              stroke="#d1d5db"
            />
            <YAxis
              type="category"
              dataKey="displayName"
              tick={{ fill: '#374151', fontSize: 12 }}
              stroke="#d1d5db"
              width={110}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
            {showLegend && <Legend />}
            <Bar dataKey="score" radius={[0, 8, 8, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
              <LabelList content={<CustomLabel />} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={chartData}
          margin={{ top: 30, right: 30, bottom: 80, left: 40 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="shortName"
            tick={{ fill: '#374151', fontSize: 11 }}
            stroke="#d1d5db"
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            domain={[0, maxScore]}
            tick={{ fill: '#6b7280', fontSize: 12 }}
            stroke="#d1d5db"
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }} />
          {showLegend && <Legend />}
          <Bar dataKey="score" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
            <LabelList content={<CustomLabel />} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ScoreDistributionChart;
