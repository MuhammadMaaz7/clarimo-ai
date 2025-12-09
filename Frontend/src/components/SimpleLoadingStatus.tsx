/**
 * Simple Loading Status Component
 * Shows loading state with rotating messages or validation errors
 * Uses unified design system
 */

import { useEffect, useState } from 'react';
import { Loader2, AlertTriangle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

interface SimpleLoadingStatusProps {
  isValidationError?: boolean;
  validationMessage?: string;
  onRetry?: () => void;
}

const SimpleLoadingStatus = ({ isValidationError, validationMessage, onRetry }: SimpleLoadingStatusProps) => {
  const [currentMessage, setCurrentMessage] = useState(0);
  
  const loadingMessages = [
    "Analyzing your input...",
    "Searching relevant discussions...",
    "Processing community data...",
    "Identifying key insights...",
    "Generating results..."
  ];

  useEffect(() => {
    if (isValidationError) return;
    
    const interval = setInterval(() => {
      setCurrentMessage((prev) => (prev + 1) % loadingMessages.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [isValidationError]);

  if (isValidationError) {
    return (
      <Card className="glass border-destructive/50">
        <CardContent className="pt-12 pb-12">
          <div className="flex flex-col items-center justify-center text-center space-y-4">
            <div className="rounded-full bg-destructive/10 p-6">
              <AlertTriangle className="h-12 w-12 text-destructive" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-destructive">
                Input Validation Failed
              </h3>
              <p className="text-muted-foreground max-w-md">
                {validationMessage || "Please provide a valid business or technical problem description."}
              </p>
            </div>
            {onRetry && (
              <Button onClick={onRetry} variant="outline" className="mt-4">
                Try Again
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass border-border/50">
      <CardContent className="pt-12 pb-12">
        <div className="flex flex-col items-center justify-center text-center space-y-6">
          <div className="rounded-full bg-primary/10 p-6 glow-sm">
            <Loader2 className="h-12 w-12 text-primary animate-spin" />
          </div>
          
          <div className="space-y-2">
            <h3 className="text-xl font-semibold transition-all duration-500">
              {loadingMessages[currentMessage]}
            </h3>
            <p className="text-muted-foreground">
              Please wait while we analyze your request and gather insights.
            </p>
          </div>
          
          <div className="w-full max-w-md">
            <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
              <div className="h-full gradient-primary rounded-full animate-pulse" 
                   style={{ width: '60%' }} />
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              This may take a few minutes...
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SimpleLoadingStatus;