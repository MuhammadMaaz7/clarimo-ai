import { Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';

interface LoadingSpinnerProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

const LoadingSpinner = ({ className, size = 'md' }: LoadingSpinnerProps) => {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="relative">
        <Loader2 className={cn('animate-spin text-primary glow', sizeMap[size], className)} />
        <div className="absolute inset-0 blur-xl bg-primary/20 animate-pulse" />
      </div>
    </div>
  );
};

export default LoadingSpinner;
