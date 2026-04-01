import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { unifiedToast } from '../lib/toast-utils';
import { z } from 'zod';
import { Checkbox } from '../components/ui/checkbox';
import { ArrowRight, UserPlus } from 'lucide-react';
import PageTransition from '../components/PageTransition';
import { motion } from 'framer-motion';

const signupSchema = z.object({
  fullName: z.string().trim().min(2, { message: 'Name must be at least 2 characters' }).max(100, { message: 'Name must be less than 100 characters' }),
  email: z.string().trim().email({ message: 'Invalid email address' }).max(255, { message: 'Email must be less than 255 characters' }),
  password: z.string().min(8, { message: 'Password must be at least 8 characters' }).max(100, { message: 'Password must be less than 100 characters' }),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

const Signup = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!termsAccepted) {
      unifiedToast.error({
        title: 'Terms Required',
        description: 'Please accept the terms and conditions',
      });
      return;
    }

    setLoading(true);

    try {
      const validated = signupSchema.parse({ fullName, email, password, confirmPassword });
      await signup(validated.email, validated.password, validated.fullName);
      unifiedToast.success({
        description: 'Your account has been created successfully.',
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
          description: error instanceof Error ? error.message : 'Signup failed',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageTransition>
      <div className="min-h-screen w-full relative flex items-center justify-center bg-[#050508] overflow-hidden selection:bg-accent/30">
        
        {/* Animated Background Effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-[radial-gradient(ellipse_at_center,hsl(var(--accent)/0.15),transparent_50%)] animate-pulse-slow pointer-events-none" />
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
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-accent to-primary flex items-center justify-center mb-6 shadow-[0_0_30px_-5px_hsl(var(--accent))]">
              <UserPlus className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">Create Account</h1>
            <p className="text-sm text-muted-foreground text-center">
              Join elite founders turning concepts into robust market reality.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-3">
              <div className="space-y-1.5">
                 <Label htmlFor="fullName" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground ml-1">Full Name</Label>
                 <Input
                   id="fullName"
                   type="text"
                   placeholder="Steve Jobs"
                   value={fullName}
                   onChange={(e) => setFullName(e.target.value)}
                   required
                   className="bg-white/5 border-white/10 h-11 rounded-xl focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all px-4 placeholder:text-muted-foreground/50 text-white"
                 />
              </div>

              <div className="space-y-1.5">
                 <Label htmlFor="email" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground ml-1">Email</Label>
                 <Input
                   id="email"
                   type="email"
                   placeholder="founder@startup.com"
                   value={email}
                   onChange={(e) => setEmail(e.target.value)}
                   required
                   className="bg-white/5 border-white/10 h-11 rounded-xl focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all px-4 placeholder:text-muted-foreground/50 text-white"
                 />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                   <Label htmlFor="password" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground ml-1">Password</Label>
                   <Input
                     id="password"
                     type="password"
                     placeholder="••••••••"
                     value={password}
                     onChange={(e) => setPassword(e.target.value)}
                     required
                     className="bg-white/5 border-white/10 h-11 rounded-xl focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all px-4 placeholder:text-muted-foreground/50 text-white tracking-widest"
                   />
                </div>
                
                <div className="space-y-1.5">
                   <Label htmlFor="confirmPassword" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground ml-1">Confirm</Label>
                   <Input
                     id="confirmPassword"
                     type="password"
                     placeholder="••••••••"
                     value={confirmPassword}
                     onChange={(e) => setConfirmPassword(e.target.value)}
                     required
                     className="bg-white/5 border-white/10 h-11 rounded-xl focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all px-4 placeholder:text-muted-foreground/50 text-white tracking-widest"
                   />
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2 pt-2 pb-1">
              <Checkbox
                id="terms"
                checked={termsAccepted}
                onCheckedChange={(checked) => setTermsAccepted(checked as boolean)}
                className="border-white/20 data-[state=checked]:bg-accent"
              />
              <label
                htmlFor="terms"
                className="text-xs text-muted-foreground leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                I agree to the{' '}
                <span className="text-white hover:text-accent font-medium cursor-pointer transition-colors">
                  Terms & Conditions
                </span>
              </label>
            </div>

            <Button
              type="submit"
              className="w-full bg-white hover:bg-white/90 text-black h-12 text-base font-semibold rounded-xl shadow-[0_0_20px_-5px_rgba(255,255,255,0.4)] transition-all active:scale-[0.98] mt-2 disabled:opacity-50"
              disabled={loading}
            >
              {loading ? 'Accelerating...' : 'Join Platform'}
            </Button>
          </form>

          <div className="mt-8 pt-6 border-t border-white/5 flex flex-col items-center space-y-4">
            <p className="text-sm text-muted-foreground">
              Already a user?{' '}
              <Link to="/login" className="text-white hover:text-accent transition-colors font-semibold">
                Sign in
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </PageTransition>
  );
};

export default Signup;
