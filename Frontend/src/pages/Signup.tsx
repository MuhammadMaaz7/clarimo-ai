import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { unifiedToast } from '../lib/toast-utils';
import { z } from 'zod';
import { Checkbox } from '../components/ui/checkbox';
import { Lightbulb, Target, Users, ArrowRight } from 'lucide-react';

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
      navigate('/');
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
                Start Your
                <br />
                <span className="gradient-text">Startup Journey</span>
              </h2>
              <p className="text-lg text-muted-foreground">
                Join thousands of entrepreneurs turning ideas into successful ventures
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div className="flex items-start space-x-3 glass p-4 rounded-lg">
                <Target className="h-5 w-5 text-primary mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-foreground">Problem Discovery</h3>
                  <p className="text-sm text-muted-foreground">Identify real problems worth solving</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 glass p-4 rounded-lg">
                <Lightbulb className="h-5 w-5 text-accent mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-foreground">AI Validation</h3>
                  <p className="text-sm text-muted-foreground">Get instant feedback on your ideas</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 glass p-4 rounded-lg">
                <Users className="h-5 w-5 text-primary mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-foreground">Community Support</h3>
                  <p className="text-sm text-muted-foreground">Connect with fellow entrepreneurs</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Form */}
        <div className="w-1/2 bg-background/95 backdrop-blur-sm flex items-center justify-center p-12 xl:p-16">
          <div className="w-full max-w-md space-y-6">
            <div className="space-y-2 text-center">
              <h2 className="text-3xl font-bold text-foreground">Create Account</h2>
              <p className="text-muted-foreground">
                Already have an account?{' '}
                <Link to="/login" className="text-primary hover:text-accent transition-colors font-medium">
                  Log in
                </Link>
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="fullName" className="text-foreground">Full Name</Label>
                  <Input
                    id="fullName"
                    type="text"
                    placeholder="abcd"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                    className="bg-input border-border h-11 focus:border-primary transition-colors"
                  />
                </div>

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
                  <p className="text-xs text-muted-foreground">Must be at least 8 characters</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-foreground">Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="bg-input border-border h-11 focus:border-primary transition-colors"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="terms"
                  checked={termsAccepted}
                  onCheckedChange={(checked) => setTermsAccepted(checked as boolean)}
                />
                <label
                  htmlFor="terms"
                  className="text-sm text-muted-foreground leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  I agree to the{' '}
                  <span className="text-primary hover:underline cursor-pointer">
                    Terms & Conditions
                  </span>
                </label>
              </div>

              <Button
                type="submit"
                className="w-full gradient-primary hover:opacity-90 transition-opacity h-11 text-base font-medium glow-sm"
                disabled={loading}
              >
                {loading ? 'Creating account...' : 'Create Account'}
                {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  Secure Registration
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
                Start Your{' '}
                <span className="gradient-text">Startup Journey</span>
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground">
                Join thousands of entrepreneurs turning ideas into ventures
              </p>
            </div>
          </div>

          {/* Mobile Form */}
          <div className="glass p-6 sm:p-8 rounded-2xl border border-border/50 glow-sm">
            <div className="space-y-6">
              <div className="space-y-2 text-center">
                <h3 className="text-xl sm:text-2xl font-bold text-foreground">Create Account</h3>
                <p className="text-sm text-muted-foreground">
                  Already have an account?{' '}
                  <Link to="/login" className="text-primary hover:text-accent transition-colors font-medium">
                    Log in
                  </Link>
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label htmlFor="fullName-mobile" className="text-foreground">Full Name</Label>
                    <Input
                      id="fullName-mobile"
                      type="text"
                      placeholder="abcd"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      required
                      className="bg-input border-border h-11 focus:border-primary transition-colors"
                    />
                  </div>

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
                    <p className="text-xs text-muted-foreground">Must be at least 8 characters</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword-mobile" className="text-foreground">Confirm Password</Label>
                    <Input
                      id="confirmPassword-mobile"
                      type="password"
                      placeholder="Confirm your password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      className="bg-input border-border h-11 focus:border-primary transition-colors"
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="terms-mobile"
                    checked={termsAccepted}
                    onCheckedChange={(checked) => setTermsAccepted(checked as boolean)}
                  />
                  <label
                    htmlFor="terms-mobile"
                    className="text-sm text-muted-foreground leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    I agree to the{' '}
                    <span className="text-primary hover:underline cursor-pointer">
                      Terms & Conditions
                    </span>
                  </label>
                </div>

                <Button
                  type="submit"
                  className="w-full gradient-primary hover:opacity-90 transition-opacity h-11 text-base font-medium glow-sm"
                  disabled={loading}
                >
                  {loading ? 'Creating account...' : 'Create Account'}
                  {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
                </Button>
              </form>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border"></div>
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">
                    Secure Registration
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

export default Signup;
