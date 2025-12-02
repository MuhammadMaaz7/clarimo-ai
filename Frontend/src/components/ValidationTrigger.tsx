/**
 * ValidationTrigger Component
 * 
 * Provides a button to start validation with configuration options
 * and a confirmation dialog.
 * 
 * Requirements: 11.1
 */

import { PlayCircle } from 'lucide-react';
import { Button } from './ui/button';
import { useValidation } from '../contexts/ValidationContext';
import { ValidationConfig } from '../types/validation';
import { useToast } from '../hooks/use-toast';

interface ValidationTriggerProps {
  ideaId: string;
  ideaTitle: string;
  disabled?: boolean;
  onValidationStarted?: (validationId: string) => void;
  variant?: 'default' | 'outline' | 'secondary';
  size?: 'default' | 'sm' | 'lg';
}

export function ValidationTrigger({
  ideaId,
  ideaTitle,
  disabled = false,
  onValidationStarted,
  variant = 'default',
  size = 'default',
}: ValidationTriggerProps) {
  const { startValidation, validationLoading } = useValidation();
  const { toast } = useToast();
  
  // Default validation configuration
  const config: ValidationConfig = {
    includeWebSearch: true,
    includeCompetitiveAnalysis: true,
    maxCompetitorsToAnalyze: 10,
    useCachedResults: true,
  };

  const handleStartValidation = async () => {
    try {
      const result = await startValidation(ideaId, config);
      
      toast({
        title: 'Validation Started',
        description: `Validation for "${ideaTitle}" has been initiated. This may take a few minutes.`,
      });

      // Notify parent component
      if (onValidationStarted) {
        onValidationStarted(result.validation_id);
      }
    } catch (error: any) {
      toast({
        title: 'Validation Failed',
        description: error.message || 'Failed to start validation. Please try again.',
        variant: 'destructive',
      });
    }
  };

  return (
    <Button
      variant={variant}
      size={size}
      disabled={disabled || validationLoading}
      onClick={handleStartValidation}
    >
      <PlayCircle className="mr-2 h-4 w-4" />
      {validationLoading ? 'Validating...' : 'Start Validation'}
    </Button>
  );
}
