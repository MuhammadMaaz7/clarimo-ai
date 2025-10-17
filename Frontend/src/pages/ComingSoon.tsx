import { useLocation } from 'react-router-dom';
import { Rocket } from 'lucide-react';

const moduleNames: Record<string, string> = {
  '/idea-validation': 'Idea Validation',
  '/competitor-analysis': 'Competitor Analysis',
  '/customer-finding': 'Customer Finding',
  '/launch-planning': 'Launch Planning',
  '/go-to-market': 'Go-to-Market Strategy',
};

const ComingSoon = () => {
  const location = useLocation();
  const moduleName = moduleNames[location.pathname] || 'This Module';

  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center">
      <div className="text-center">
        <div className="mb-6 flex justify-center">
          <div className="rounded-full bg-gradient-to-br from-accent/20 to-primary/20 p-6 backdrop-blur-sm border border-accent/30 glow-sm">
            <Rocket className="h-16 w-16 text-accent" />
          </div>
        </div>
        <h1 className="mb-3 text-4xl font-bold text-white">{moduleName}</h1>
        <p className="text-xl text-muted-foreground">Coming Soon</p>
        <p className="mt-4 max-w-md text-sm text-muted-foreground">
          We're working hard to bring you this feature. Check back soon!
        </p>
      </div>
    </div>
  );
};

export default ComingSoon;
