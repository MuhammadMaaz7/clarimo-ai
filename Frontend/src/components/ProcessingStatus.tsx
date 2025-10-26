import { Sparkles, Clock, CheckCircle, Target, AlertCircle } from 'lucide-react';

interface ProcessingStatusProps {
  status: {
    input_id: string;
    overall_status: string;
    progress_percentage: number;
    current_stage: string;
    message: string;
    description: string;
    animation: string;
    next_action: string;
    estimated_time_remaining: string;
    can_view_results: boolean;
  };
}

const ProcessingStatus = ({ status }: ProcessingStatusProps) => {
  const getStageIcon = (stage: string) => {
    switch (stage) {
      case 'keyword_generation':
        return <Sparkles className="h-8 w-8 text-white" />;
      case 'reddit_fetch':
        return <Clock className="h-8 w-8 text-white" />;
      case 'embedding_generation':
        return <Sparkles className="h-8 w-8 text-white animate-spin" />;
      case 'semantic_filtering':
        return <Target className="h-8 w-8 text-white" />;
      case 'completed':
        return <CheckCircle className="h-8 w-8 text-white" />;
      default:
        return <AlertCircle className="h-8 w-8 text-white" />;
    }
  };

  const getAnimationClass = (animation: string) => {
    switch (animation) {
      case 'startup':
        return 'animate-pulse';
      case 'searching':
        return 'animate-bounce';
      case 'thinking':
        return 'animate-spin';
      case 'filtering':
        return 'animate-pulse';
      case 'celebration':
        return 'animate-bounce';
      default:
        return 'animate-pulse';
    }
  };

  const stages = [
    { key: 'keyword_generation', icon: '🔑', label: 'Keywords' },
    { key: 'reddit_fetch', icon: '📡', label: 'Fetch Posts' },
    { key: 'embedding_generation', icon: '🧠', label: 'AI Analysis' },
    { key: 'semantic_filtering', icon: '🎯', label: 'Filter Results' }
  ];

  const getStageStatus = (stageKey: string) => {
    const stageOrder = ['keyword_generation', 'reddit_fetch', 'embedding_generation', 'semantic_filtering'];
    const currentIndex = stageOrder.indexOf(status.current_stage);
    const stageIndex = stageOrder.indexOf(stageKey);
    
    if (stageIndex < currentIndex) return 'completed';
    if (stageIndex === currentIndex) return 'in_progress';
    return 'pending';
  };

  return (
    <div className="glass rounded-2xl border-border/50 p-8 text-center glow-sm bg-white/5 backdrop-blur-xl">
      <div className="mb-6 flex justify-center">
        <div className={`rounded-2xl bg-gradient-to-br from-accent to-primary p-4 glow-sm shadow-lg ${getAnimationClass(status.animation)}`}>
          {getStageIcon(status.current_stage)}
        </div>
      </div>
      
      <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
        {status.message}
      </h2>
      
      <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
        {status.description}
      </p>
      
      {/* Progress Bar */}
      <div className="w-full bg-border/30 rounded-full h-3 mb-4 overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-1000 ease-out rounded-full glow-sm"
          style={{ width: `${status.progress_percentage}%` }}
        />
      </div>
      
      <div className="flex justify-between text-sm text-muted-foreground mb-6">
        <span>{status.progress_percentage}% Complete</span>
        <span>ETA: {status.estimated_time_remaining}</span>
      </div>
      
      {/* Stage Indicators */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
        {stages.map((stage) => {
          const stageStatus = getStageStatus(stage.key);
          const isActive = status.current_stage === stage.key;
          const isCompleted = stageStatus === 'completed';
          
          return (
            <div 
              key={stage.key}
              className={`p-3 rounded-xl border transition-all duration-300 ${
                isActive 
                  ? 'border-primary bg-primary/10 glow-sm' 
                  : isCompleted 
                    ? 'border-green-500/50 bg-green-500/10' 
                    : 'border-border/30 bg-card/20'
              }`}
            >
              <div className="text-2xl mb-1">{stage.icon}</div>
              <div className="text-xs font-medium">{stage.label}</div>
              {isActive && (
                <div className="text-xs text-primary mt-1">Processing...</div>
              )}
              {isCompleted && (
                <div className="text-xs text-green-400 mt-1">✓ Done</div>
              )}
            </div>
          );
        })}
      </div>
      
      <p className="text-sm text-muted-foreground mt-6">
        {status.next_action}
      </p>
      
      {status.overall_status === 'completed' && (
        <div className="mt-4 p-4 bg-green-500/10 border border-green-500/30 rounded-xl">
          <CheckCircle className="h-6 w-6 text-green-400 mx-auto mb-2" />
          <p className="text-green-400 font-medium">Processing Complete!</p>
          <p className="text-sm text-muted-foreground mt-1">Your results are ready to view.</p>
        </div>
      )}
    </div>
  );
};

export default ProcessingStatus;