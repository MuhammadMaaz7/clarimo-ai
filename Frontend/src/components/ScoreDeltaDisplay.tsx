import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ScoreDeltaDisplayProps {
  delta: number;
  size?: 'small' | 'medium' | 'large';
  showLabel?: boolean;
  className?: string;
}

const ScoreDeltaDisplay: React.FC<ScoreDeltaDisplayProps> = ({
  delta,
  size = 'medium',
  showLabel = false,
  className = '',
}) => {
  // Determine if the change is significant (threshold: 0.05)
  const isSignificant = Math.abs(delta) >= 0.05;
  const isImproved = delta > 0;
  const isDeclined = delta < 0;
  const isUnchanged = !isSignificant;

  // Size configurations
  const sizeConfig = {
    small: {
      iconSize: 'h-4 w-4',
      textSize: 'text-sm',
      labelSize: 'text-xs',
    },
    medium: {
      iconSize: 'h-5 w-5',
      textSize: 'text-lg',
      labelSize: 'text-sm',
    },
    large: {
      iconSize: 'h-8 w-8',
      textSize: 'text-3xl',
      labelSize: 'text-base',
    },
  };

  const config = sizeConfig[size];

  // Color configurations
  const getColorClasses = () => {
    if (isUnchanged) {
      return {
        text: 'text-gray-600',
        bg: 'bg-gray-100',
        border: 'border-gray-300',
      };
    } else if (isImproved) {
      return {
        text: 'text-green-600',
        bg: 'bg-green-100',
        border: 'border-green-300',
      };
    } else {
      return {
        text: 'text-red-600',
        bg: 'bg-red-100',
        border: 'border-red-300',
      };
    }
  };

  const colors = getColorClasses();

  // Format delta value
  const formatDelta = (value: number): string => {
    const absValue = Math.abs(value);
    if (absValue < 0.01) return '0.00';
    return absValue.toFixed(2);
  };

  // Get label text
  const getLabel = (): string => {
    if (isUnchanged) return 'No Change';
    if (isImproved) return 'Improved';
    return 'Declined';
  };

  // Get icon
  const getIcon = () => {
    if (isUnchanged) {
      return <Minus className={`${config.iconSize} ${colors.text}`} />;
    } else if (isImproved) {
      return <TrendingUp className={`${config.iconSize} ${colors.text}`} />;
    } else {
      return <TrendingDown className={`${config.iconSize} ${colors.text}`} />;
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${colors.bg} ${colors.border}`}
      >
        {getIcon()}
        <div className="flex flex-col">
          <span className={`font-bold ${colors.text} ${config.textSize}`}>
            {isImproved && '+'}
            {isDeclined && '-'}
            {formatDelta(delta)}
          </span>
          {showLabel && (
            <span className={`${colors.text} ${config.labelSize} font-medium`}>
              {getLabel()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScoreDeltaDisplay;
