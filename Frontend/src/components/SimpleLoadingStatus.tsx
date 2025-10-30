import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

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
    }, 3000); // Change message every 3 seconds

    return () => clearInterval(interval);
  }, [isValidationError]);

  if (isValidationError) {
    return (
      <div className="glass rounded-2xl border-red-500/30 p-8 text-center bg-red-500/10 backdrop-blur-xl">
        <div className="mb-6 flex justify-center">
          <div className="rounded-2xl bg-red-500 p-4 shadow-lg">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        </div>
        
        <h2 className="text-2xl font-bold text-red-400 mb-4">
          Input Validation Failed
        </h2>
        
        <p className="text-red-200 mb-6 max-w-2xl mx-auto">
          {validationMessage || "Please provide a valid business or technical problem description."}
        </p>
        
        <button 
          onClick={onRetry}
          className="px-6 py-3 bg-gradient-to-r from-primary to-accent text-white font-medium rounded-lg hover:opacity-90 transition-opacity"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="glass rounded-2xl border-border/50 p-8 text-center bg-white/5 backdrop-blur-xl">
      <div className="mb-6 flex justify-center">
        <div className="rounded-2xl bg-gradient-to-br from-accent to-primary p-4 shadow-lg">
          <Loader2 className="h-8 w-8 text-white animate-spin" />
        </div>
      </div>
      
      <h2 className="text-2xl font-bold text-white mb-4 transition-all duration-500">
        {loadingMessages[currentMessage]}
      </h2>
      
      <p className="text-muted-foreground mb-6">
        Please wait while we analyze your request and gather insights.
      </p>
      
      <div className="w-full bg-border/30 rounded-full h-2 overflow-hidden">
        <div className="h-full bg-gradient-to-r from-primary to-accent rounded-full animate-pulse" 
             style={{ width: '60%' }} />
      </div>
      
      <div className="mt-4 text-sm text-muted-foreground">
        This may take a few minutes...
      </div>
    </div>
  );
};

export default SimpleLoadingStatus;