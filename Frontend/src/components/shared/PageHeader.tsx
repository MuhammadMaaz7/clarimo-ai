/**
 * Unified Page Header Component
 * Consistent page headers across the application
 */

import { ArrowLeft, LucideIcon } from 'lucide-react';
import { Button } from '../ui/button';
import { useNavigate } from 'react-router-dom';

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  backTo?: string;
  backLabel?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  icon: Icon,
  backTo,
  backLabel = 'Back',
  actions,
  className,
}: PageHeaderProps) {
  const navigate = useNavigate();

  return (
    <div className={`space-y-4 ${className || ''}`}>
      {backTo && (
        <Button
          variant="ghost"
          onClick={() => navigate(backTo)}
          className="mb-2"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          {backLabel}
        </Button>
      )}
      
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <div className="flex items-center gap-3">
            {Icon && (
              <div className="rounded-lg bg-primary/10 p-2">
                <Icon className="h-6 w-6 text-primary" />
              </div>
            )}
            <h1 className="text-3xl font-bold tracking-tight gradient-text">
              {title}
            </h1>
          </div>
          {description && (
            <p className="text-muted-foreground max-w-2xl">
              {description}
            </p>
          )}
        </div>
        
        {actions && (
          <div className="flex items-center gap-2">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
}

export default PageHeader;
