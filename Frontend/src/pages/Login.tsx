import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { unifiedToast } from '../lib/toast-utils';
import { z } from 'zod';
import { ArrowRight, Lock } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import { motion } from 'framer-motion';

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const validated = loginSchema.parse({ email, password });
      await login(validated.email, validated.password);
      unifiedToast.success({
        description: 'You have successfully logged in.',
      });
      navigate('/dashboard');
    } catch (error) {
      if (error instanceof z.ZodError) {
        unifiedToast.error({
          title: 'Validation Error',
          description: error.issues[0].message,
        });
      } else {
        unifiedToast.error({
          description: error instanceof Error ? error.message : 'Login failed',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-screen w-full relative flex items-center justify-center bg-[#050508] overflow-hidden selection:bg-primary/30">
        
        {/* Animated Background Effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.15),transparent_50%)] animate-pulse-slow pointer-events-none" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.14] pointer-events-none mix-blend-overlay"></div>

        {/* Absolute Header link to go back */}
        <Link to="/" className="absolute top-8 left-8 z-50 flex items-center gap-2 group p-2 hover:bg-white/5 rounded-lg transition-colors">
          <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-white transition-colors rotate-180" />
          <span className="text-sm font-medium text-muted-foreground group-hover:text-white transition-colors">Back to Home</span>
        </Link>
        
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-md p-8 md:p-10 z-10 mx-4 glass border-white/10 rounded-[2rem] shadow-2xl bg-black/40 backdrop-blur-2xl"
        >
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center mb-6 shadow-[0_0_30px_-5px_hsl(var(--primary))]">
              <Lock className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">Welcome back</h1>
            <p className="text-sm text-muted-foreground text-center">
              Login to access your personalized intelligence dashboard.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-4">
              <div className="space-y-2">
                 <Label htmlFor="email" className="text-xs font-bold uppercase tracking-wider text-muted-foreground ml-1">Email</Label>
                 <Input
                   id="email"
                   type="email"
                   placeholder="founder@startup.com"
                   value={email}
                   onChange={(e) => setEmail(e.target.value)}
                   required
                   className="bg-white/5 border-white/10 h-12 rounded-xl focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all px-4 placeholder:text-muted-foreground/50 text-white"
                 />
              </div>

              <div className="space-y-2">
                 <Label htmlFor="password" className="text-xs font-bold uppercase tracking-wider text-muted-foreground ml-1">Password</Label>
                 <Input
                   id="password"
                   type="password"
                   placeholder="••••••••"
                   value={password}
                   onChange={(e) => setPassword(e.target.value)}
                   required
                   className="bg-white/5 border-white/10 h-12 rounded-xl focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all px-4 placeholder:text-muted-foreground/50 text-white tracking-widest"
                 />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-white hover:bg-white/90 text-black h-12 text-base font-semibold rounded-xl shadow-[0_0_20px_-5px_rgba(255,255,255,0.4)] transition-all active:scale-[0.98] mt-4 disabled:opacity-50"
              disabled={loading}
            >
              {loading ? 'Authenticating...' : 'Enter Dashboard'}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-white/5 flex flex-col items-center space-y-4">
            <p className="text-sm text-muted-foreground">
              Don't have an account yet?{' '}
              <Link to="/signup" className="text-white hover:text-primary transition-colors font-semibold">
                Sign up
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </PageTransition>
  );
};

export default Login;
