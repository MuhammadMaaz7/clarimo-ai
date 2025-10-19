import { useState } from 'react';
import ProblemForm, { FormData } from '../components/ProblemForm';
import ProblemCard from '../components/ProblemCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { Sparkles } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface Problem {
  id: number;
  title: string;
  description: string;
  subreddit: string;
  score: number;
}

const ProblemDiscovery = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [problems, setProblems] = useState<Problem[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const { user } = useAuth();

  // Mock data for demonstration
  const mockProblems: Problem[] = [
    {
      id: 1,
      title: 'Small businesses struggle with managing customer relationships',
      description: 'Many small businesses lack affordable CRM solutions that are easy to use and integrate with their existing tools. They often resort to spreadsheets which become unwieldy.',
      subreddit: 'smallbusiness',
      score: 247,
    },
    {
      id: 2,
      title: 'Remote teams face coordination challenges',
      description: 'With the rise of remote work, teams struggle to maintain effective communication and coordination across different time zones and tools.',
      subreddit: 'remotework',
      score: 189,
    },
    {
      id: 3,
      title: 'Freelancers waste time on invoicing and payments',
      description: 'Independent contractors spend countless hours creating invoices, tracking payments, and following up with clients instead of doing billable work.',
      subreddit: 'freelance',
      score: 156,
    },
    {
      id: 4,
      title: 'Students need better tools for collaborative learning',
      description: 'Current education platforms lack features that promote peer-to-peer learning and make group projects more manageable.',
      subreddit: 'education',
      score: 134,
    },
    {
      id: 5,
      title: 'Content creators struggle with managing multiple platforms',
      description: 'Creators waste time posting the same content across multiple social media platforms and struggle to analyze their performance holistically.',
      subreddit: 'contentcreation',
      score: 112,
    },
  ];

  const handleSubmit = async (data: FormData) => {
    setIsLoading(true);
    setHasSearched(true);
    
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch('http://localhost:8000/problems/discover', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success && result.data?.problems) {
        // Transform the API response to match our Problem interface
        const transformedProblems = result.data.problems.map((problem: any) => ({
          id: problem.id,
          title: problem.title,
          description: problem.description,
          subreddit: problem.source,
          score: problem.score
        }));
        
        setProblems(transformedProblems);
      } else {
        console.error('API response format error:', result);
        // Fallback to mock data if API response is unexpected
        setProblems(mockProblems);
      }
    } catch (error) {
      console.error('Error calling problem discovery API:', error);
      // Fallback to mock data on error
      setProblems(mockProblems);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="responsive-spacing-md pb-8">
      {/* Hero Section */}
      <div className="glass border-border/50 rounded-2xl p-8 md:p-12 text-center glow-sm bg-white/5 backdrop-blur-xl">
        <div className="mb-6 flex justify-center">
          <div className="rounded-2xl bg-gradient-to-br from-accent to-primary p-4 glow-sm shadow-lg">
            <Sparkles className="h-10 w-10 text-white" />
          </div>
        </div>
        <h1 className="mb-4 text-3xl md:text-5xl font-bold text-white animate-in fade-in slide-in-from-bottom-4 duration-700">
          Welcome back, {user?.full_name?.split(' ')[0]}!
        </h1>
        <p className="mx-auto max-w-2xl text-base md:text-lg text-muted-foreground leading-relaxed animate-in fade-in slide-in-from-bottom-4 duration-700 delay-150">
          Uncover real problems from online communities and identify opportunities worth pursuing
        </p>
      </div>

      {/* Form */}
      <ProblemForm onSubmit={handleSubmit} isLoading={isLoading} />

      {/* Results */}
      {isLoading && <LoadingSpinner size="lg" />}

      {!isLoading && problems.length > 0 && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <h2 className="text-2xl md:text-3xl font-bold">Discovered Problems</h2>
            <span className="text-sm md:text-base text-muted-foreground bg-accent/10 px-4 py-2 rounded-full border border-accent/20">
              {problems.length} problems found
            </span>
          </div>
          <div className="responsive-grid-cards">
            {problems.map((problem, index) => (
              <ProblemCard key={problem.id} {...problem} index={index} />
            ))}
          </div>
        </div>
      )}

      {!isLoading && hasSearched && problems.length === 0 && (
        <div className="glass rounded-2xl border-dashed border-2 border-border/50 p-16 text-center">
          <p className="text-muted-foreground text-lg">
            No problems found. Try adjusting your search criteria.
          </p>
        </div>
      )}
    </div>
  );
};

export default ProblemDiscovery;
