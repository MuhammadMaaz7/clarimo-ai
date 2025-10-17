import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { MessageSquare, TrendingUp } from 'lucide-react';

interface ProblemCardProps {
  title: string;
  description: string;
  subreddit: string;
  score: number;
  index: number;
}

const ProblemCard = ({ title, description, subreddit, score, index }: ProblemCardProps) => {
  return (
    <Card className="opacity-0 animate-in fade-in slide-in-from-bottom-4 glass glass-hover hover:glow-sm hover:-translate-y-2 transition-all duration-500 group" style={{ animationDelay: `${index * 0.1}s`, animationFillMode: 'forwards' }}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg font-semibold leading-tight group-hover:text-primary transition-colors">{title}</CardTitle>
          <Badge variant="secondary" className="shrink-0 bg-primary/10 text-primary border-primary/20 group-hover:bg-primary group-hover:text-white transition-all duration-300">
            <TrendingUp className="mr-1 h-3 w-3" />
            {score}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-4 leading-relaxed">{description}</p>
        <div className="flex items-center text-xs text-muted-foreground group-hover:text-primary transition-colors">
          <MessageSquare className="mr-1.5 h-3.5 w-3.5" />
          <span className="font-medium">r/{subreddit}</span>
        </div>
      </CardContent>
    </Card>
  );
};

export default ProblemCard;
