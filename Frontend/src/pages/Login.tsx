import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useToast } from '../hooks/use-toast';
import { z } from 'zod';
import { Sparkles, TrendingUp, ArrowRight } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().trim().email({ message: 'Invalid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' }),
});

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const validated = loginSchema.parse({ email, password });
      await login(validated.email, validated.password);
      toast({
        title: 'Success',
        description: 'You have successfully logged in.',
      });
      navigate('/');
    } catch (error) {
      if (error instanceof z.ZodError) {
        toast({
          title: 'Validation Error',
          description: error.issues[0].message,
          variant: 'destructive',
        });
      } else {
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Login failed',
          variant: 'destructive',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative bg-gradient-to-br from-accent/20 via-primary/10 to-background overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,hsl(var(--accent))_0%,transparent_50%)] opacity-20" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_70%,hsl(var(--primary))_0%,transparent_50%)] opacity-20" />

      {/* Desktop Layout */}
      <div className="hidden lg:flex min-h-screen">
        {/* Left Side - Branding */}
        <div className="relative w-1/2 flex items-center justify-center p-12 xl:p-16">
          <div className="relative z-10 max-w-lg space-y-8 text-left">
            <div className="space-y-6">
              <div className="flex items-center space-x-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl overflow-hidden glow-sm">
                  <img src="/logo.png" alt="Clarimo AI" className="h-full w-full object-cover" />
                </div>
                <h1 className="text-3xl font-bold gradient-text">Clarimo AI</h1>
              </div>
              <h2 className="text-4xl xl:text-5xl font-bold text-foreground leading-tight">
                Transform Ideas,
                <br />
                <span className="gradient-text">Launch Startups</span>
              </h2>
              <p className="text-lg text-muted-foreground">
                Accelerate your startup journey with AI-powered insights and validation
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div className="flex items-start space-x-3 glass p-4 rounded-lg">
                <Sparkles className="h-5 w-5 text-accent mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-foreground">AI-Powered Analysis</h3>
                  <p className="text-sm text-muted-foreground">Validate ideas with intelligent market research</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 glass p-4 rounded-lg">
                <TrendingUp className="h-5 w-5 text-primary mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-foreground">Growth Strategies</h3>
                  <p className="text-sm text-muted-foreground">Get personalized roadmaps to success</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Form */}
        <div className="w-1/2 bg-background/95 backdrop-blur-sm flex items-center justify-center p-12 xl:p-16">
          <div className="w-full max-w-md space-y-8">
            <div className="space-y-2 text-center">
              <h2 className="text-3xl font-bold text-foreground">Welcome Back</h2>
              <p className="text-muted-foreground">
                New to Clarimo?{' '}
                <Link to="/signup" className="text-primary hover:text-accent transition-colors font-medium">
                  Create an account
                </Link>
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-foreground">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="bg-input border-border h-11 focus:border-primary transition-colors"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-foreground">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="bg-input border-border h-11 focus:border-primary transition-colors"
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full gradient-primary hover:opacity-90 transition-opacity h-11 text-base font-medium glow-sm"
                disabled={loading}
              >
                {loading ? 'Signing in...' : 'Sign In'}
                {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  Secure Authentication
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile/Tablet Layout */}
      <div className="lg:hidden min-h-screen flex flex-col items-center justify-center p-6 sm:p-8">
        <div className="relative z-10 w-full max-w-md space-y-8">
          {/* Mobile Header */}
          <div className="text-center space-y-6">
            <div className="flex items-center justify-center space-x-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl overflow-hidden glow-sm">
                <img src="/logo.png" alt="Clarimo AI" className="h-full w-full object-cover" />
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold gradient-text">Clarimo AI</h1>
            </div>
            <div className="space-y-3">
              <h2 className="text-2xl sm:text-3xl font-bold text-foreground">
                Transform Ideas,{' '}
                <span className="gradient-text">Launch Startups</span>
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground">
                Accelerate your startup journey with AI-powered insights
              </p>
            </div>
          </div>

          {/* Mobile Form */}
          <div className="glass p-6 sm:p-8 rounded-2xl border border-border/50 glow-sm">
            <div className="space-y-6">
              <div className="space-y-2 text-center">
                <h3 className="text-xl sm:text-2xl font-bold text-foreground">Welcome Back</h3>
                <p className="text-sm text-muted-foreground">
                  New to Clarimo?{' '}
                  <Link to="/signup" className="text-primary hover:text-accent transition-colors font-medium">
                    Create an account
                  </Link>
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email-mobile" className="text-foreground">Email</Label>
                    <Input
                      id="email-mobile"
                      type="email"
                      placeholder="your@email.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="bg-input border-border h-11 focus:border-primary transition-colors"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password-mobile" className="text-foreground">Password</Label>
                    <Input
                      id="password-mobile"
                      type="password"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="bg-input border-border h-11 focus:border-primary transition-colors"
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full gradient-primary hover:opacity-90 transition-opacity h-11 text-base font-medium glow-sm"
                  disabled={loading}
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                  {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
                </Button>
              </form>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border"></div>
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">
                    Secure Authentication
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
