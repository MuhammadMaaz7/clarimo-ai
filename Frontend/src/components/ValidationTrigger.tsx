/**
 * ValidationTrigger Component
 * 
 * Provides a button to start validation with configuration options
 * and a confirmation dialog.
 * 
 * Requirements: 11.1
 */

import { useState } from 'react';
import { PlayCircle, Settings } from 'lucide-react';
import { Button } from './ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from './ui/alert-dialog';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './ui/card';
import { Checkbox } from './ui/checkbox';
import { Label } from './ui/label';
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
  showConfigOptions?: boolean;
}

export function ValidationTrigger({
  ideaId,
  ideaTitle,
  disabled = false,
  onValidationStarted,
  variant = 'default',
  size = 'default',
  showConfigOptions = true,
}: ValidationTriggerProps) {
  const { startValidation, validationLoading } = useValidation();
  const { toast } = useToast();
  
  // Validation configuration state
  const [config, setConfig] = useState<ValidationConfig>({
    includeWebSearch: true,
    includeCompetitiveAnalysis: true,
    maxCompetitorsToAnalyze: 10,
    useCachedResults: true,
  });

  // Dialog state
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);

  const handleStartValidation = async () => {
    try {
      const result = await startValidation(ideaId, config);
      
      toast({
        title: 'Validation Started',
        description: `Validation for "${ideaTitle}" has been initiated. This may take a few minutes.`,
      });

      // Close dialog
      setIsDialogOpen(false);

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

  const handleConfigChange = (key: keyof ValidationConfig, value: any) => {
    setConfig((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  return (
    <AlertDialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant={variant}
          size={size}
          disabled={disabled || validationLoading}
        >
          <PlayCircle className="mr-2 h-4 w-4" />
          {validationLoading ? 'Validating...' : 'Start Validation'}
        </Button>
      </AlertDialogTrigger>

      <AlertDialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <AlertDialogHeader>
          <AlertDialogTitle>Start Idea Validation</AlertDialogTitle>
          <AlertDialogDescription>
            You are about to validate "{ideaTitle}". This process will analyze your idea
            across multiple dimensions including market demand, technical feasibility,
            and competitive positioning.
          </AlertDialogDescription>
        </AlertDialogHeader>

        {showConfigOptions && (
          <div className="space-y-4 py-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Validation Configuration
                </CardTitle>
                <CardDescription>
                  Customize how the validation is performed
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Basic Options */}
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="includeWebSearch"
                      checked={config.includeWebSearch}
                      onCheckedChange={(checked) =>
                        handleConfigChange('includeWebSearch', checked)
                      }
                    />
                    <Label
                      htmlFor="includeWebSearch"
                      className="text-sm font-normal cursor-pointer"
                    >
                      Include web search for market demand analysis
                    </Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="includeCompetitiveAnalysis"
                      checked={config.includeCompetitiveAnalysis}
                      onCheckedChange={(checked) =>
                        handleConfigChange('includeCompetitiveAnalysis', checked)
                      }
                    />
                    <Label
                      htmlFor="includeCompetitiveAnalysis"
                      className="text-sm font-normal cursor-pointer"
                    >
                      Include competitive analysis (searches for existing solutions)
                    </Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="useCachedResults"
                      checked={config.useCachedResults}
                      onCheckedChange={(checked) =>
                        handleConfigChange('useCachedResults', checked)
                      }
                    />
                    <Label
                      htmlFor="useCachedResults"
                      className="text-sm font-normal cursor-pointer"
                    >
                      Use cached results when available (faster validation)
                    </Label>
                  </div>
                </div>

                {/* Advanced Options Toggle */}
                <div className="pt-2 border-t">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                    className="text-xs"
                  >
                    {showAdvancedOptions ? 'Hide' : 'Show'} Advanced Options
                  </Button>
                </div>

                {/* Advanced Options */}
                {showAdvancedOptions && (
                  <div className="space-y-3 pt-2">
                    <div className="space-y-2">
                      <Label htmlFor="maxCompetitors" className="text-sm">
                        Maximum competitors to analyze
                      </Label>
                      <div className="flex items-center gap-2">
                        <input
                          id="maxCompetitors"
                          type="number"
                          min="1"
                          max="20"
                          value={config.maxCompetitorsToAnalyze}
                          onChange={(e) =>
                            handleConfigChange(
                              'maxCompetitorsToAnalyze',
                              parseInt(e.target.value) || 10
                            )
                          }
                          className="w-20 px-3 py-2 border rounded-md text-sm"
                          disabled={!config.includeCompetitiveAnalysis}
                        />
                        <span className="text-xs text-muted-foreground">
                          (1-20 competitors)
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Estimated Time */}
            <div className="bg-muted/50 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="text-2xl">⏱️</div>
                <div>
                  <p className="text-sm font-medium">Estimated Time</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {config.includeWebSearch && config.includeCompetitiveAnalysis
                      ? '3-5 minutes'
                      : config.includeWebSearch || config.includeCompetitiveAnalysis
                      ? '2-3 minutes'
                      : '1-2 minutes'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    You can navigate away and return later. We'll notify you when it's complete.
                  </p>
                </div>
              </div>
            </div>

            {/* What will be analyzed */}
            <div className="bg-muted/50 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="text-2xl">📊</div>
                <div>
                  <p className="text-sm font-medium mb-2">What will be analyzed</p>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    <li>• Problem clarity and definition</li>
                    <li>• Market demand and interest signals</li>
                    <li>• Solution-problem fit</li>
                    <li>• Technical feasibility</li>
                    <li>• Market size estimation</li>
                    <li>• Monetization potential</li>
                    <li>• Risk assessment</li>
                    {config.includeCompetitiveAnalysis && (
                      <li>• Competitive differentiation</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel disabled={validationLoading}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleStartValidation}
            disabled={validationLoading}
          >
            {validationLoading ? 'Starting...' : 'Start Validation'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
