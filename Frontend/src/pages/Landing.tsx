import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowRight, Target, BarChart2, CheckCircle2, Bot, Users, Rocket, TrendingUp } from 'lucide-react';
import Beams from '../components/landing/Beams';
import ShinyText from '../components/landing/ShinyText';
import SpotlightCard from '../components/landing/SpotlightCard';
import Counter from '../components/landing/Counter';
import AnimatedButton from '../components/landing/AnimatedButton';
import FadeContent from '../components/landing/FadeContent';
import AnimatedContent from '../components/landing/AnimatedContent';
import { Button } from '../components/ui/button';
import PageTransition from '../components/PageTransition';

export default function Landing() {
  const { user } = useAuth();

  return (
    <PageTransition>
      <div className="min-h-screen bg-background text-foreground overflow-x-hidden selection:bg-primary/30">
        {/* Absolute Header */}
        <motion.header 
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 glass border-b-0 backdrop-blur-md bg-background/40"
        >
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="Clarimo AI" className="w-8 h-8 rounded-lg" />
            <span className="font-bold text-xl tracking-tight">Clarimo AI</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm font-medium hover:text-primary transition-colors text-muted-foreground hover:text-foreground">
              Log in
            </Link>
            <Link to={user ? "/dashboard" : "/signup"}>
              <Button size="sm" className="glow-sm font-semibold tracking-wide bg-gradient-primary hover:opacity-90 transition-opacity">
                {user ? "Dashboard" : "Get Started"} <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </div>
        </motion.header>

        {/* Hero Section */}
        <section className="relative min-h-screen flex items-center justify-center pt-24 pb-12 w-full overflow-hidden">
          {/* Beams Background */}
          <div className="absolute inset-0 w-full h-full">
            <Beams
              beamWidth={1.5}
              beamHeight={18}
              beamNumber={15}
              lightColor="#a78bfa"
              speed={1.5}
              noiseIntensity={1.5}
              scale={0.15}
              rotation={0}
            />
          </div>
          
          <div className="relative z-10 container mx-auto px-4 text-center mt-[-10vh]">
            <motion.div
              initial={{ opacity: 0, y: 40, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
              className="max-w-4xl mx-auto space-y-8"
            >
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass border border-primary/30 text-primary mb-4 text-sm font-medium tracking-wide shadow-[0_0_15px_-3px_hsl(var(--primary)_/_0.4)]"
              >
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                </span>
                The Ultimate AI-Driven Startup Engine
              </motion.div>
              
              <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white drop-shadow-xl">
                Launch Faster.<br />
                <ShinyText
                  text="Build Smarter."
                  speed={3}
                  className="text-5xl md:text-7xl font-extrabold tracking-tight"
                  color="#a78bfa"
                  shineColor="#ffffff"
                  spread={90}
                  direction="left"
                  delay={0.5}
                />
              </h1>
              
              <p className="text-lg md:text-xl text-white/80 max-w-2xl mx-auto leading-relaxed drop-shadow-md font-medium">
                Clarimo AI is your intelligent co-founder. Discover real problems, validate ideas instantly, analyze competitors, and plan your go-to-market strategy all in one place.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6">
                <Link to={user ? "/dashboard" : "/signup"}>
                  <AnimatedButton variant="primary" size="lg">
                    Accelerate Your Startup
                    {/* <ArrowRight className="w-5 h-5" /> */}
                  </AnimatedButton>
                </Link>
                <AnimatedButton variant="secondary" size="lg" href="#features" smoothScroll={true}>
                  See How It Works
                </AnimatedButton>
              </div>
            </motion.div>
          </div>
          
          {/* Scroll indicator */}
          <motion.div 
            animate={{ y: [0, 10, 0] }}
            transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
            className="absolute bottom-10 left-1/2 -translate-x-1/2 text-white/50 z-10"
          >
            <div className="w-[1px] h-16 bg-gradient-to-b from-primary to-transparent mx-auto mb-2" />
          </motion.div>
        </section>

        {/* Features Grid / Bento Layout */}
        <section id="features" className="py-24 relative z-10 bg-background overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.05),transparent_70%)] pointer-events-none" />
          
          <div className="container mx-auto px-4 relative z-10">
            <FadeContent blur={true} duration={800} delay={100} threshold={0.2}>
              <div className="text-center mb-16 space-y-4">
                <h2 className="text-3xl md:text-5xl font-bold">The Complete <span className="text-primary glow-sm">Founder's Arsenal</span></h2>
                <p className="text-muted-foreground text-lg max-w-xl mx-auto">Everything you need from zero to one. Powered by advanced reasoning engines and real-time market data.</p>
              </div>
            </FadeContent>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
              {/* Feature 1 - Problem Discovery */}
              <AnimatedContent distance={60} direction="vertical" duration={0.7} delay={0.1} threshold={0.15}>
                <SpotlightCard 
                  className="bg-[#0d0d12] border border-white/5 backdrop-blur-xl p-8 h-full"
                  spotlightColor="rgba(167, 139, 250, 0.25)"
                  spotlightSize={350}
                >
                  <div className="relative">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-3xl"></div>
                    <Target className="w-12 h-12 text-primary mb-6 drop-shadow-md relative z-10" />
                    <h3 className="text-2xl font-bold mb-3 relative z-10">Problem Discovery</h3>
                    <p className="text-muted-foreground leading-relaxed relative z-10">Find untapped niches and urgent pain points instantly. Analyze thousands of data signals to discover real problems worth solving.</p>
                  </div>
                </SpotlightCard>
              </AnimatedContent>
              
              {/* Feature 2 - Idea Validation */}
              <AnimatedContent distance={60} direction="vertical" duration={0.7} delay={0.2} threshold={0.15}>
                <SpotlightCard 
                  className="bg-[#0d0d12] border border-white/5 backdrop-blur-xl p-8 h-full"
                  spotlightColor="rgba(216, 180, 254, 0.25)"
                  spotlightSize={350}
                >
                  <div className="relative">
                    <div className="absolute bottom-0 left-0 w-32 h-32 bg-accent/10 rounded-full blur-3xl"></div>
                    <Bot className="w-12 h-12 text-accent mb-6 drop-shadow-md relative z-10" />
                    <h3 className="text-2xl font-bold mb-3 relative z-10">Idea Validation</h3>
                    <p className="text-muted-foreground leading-relaxed relative z-10">Let AI criticize and objectively score your startup ideas based on market demand, feasibility, and competitive landscape.</p>
                  </div>
                </SpotlightCard>
              </AnimatedContent>

              {/* Feature 3 - Competitor Analysis */}
              <AnimatedContent distance={60} direction="vertical" duration={0.7} delay={0.3} threshold={0.15}>
                <SpotlightCard 
                  className="bg-[#0d0d12] border border-white/5 backdrop-blur-xl p-8 h-full"
                  spotlightColor="rgba(59, 130, 246, 0.25)"
                  spotlightSize={350}
                >
                  <div className="relative">
                    <BarChart2 className="w-12 h-12 text-[#3b82f6] mb-6 drop-shadow-md relative z-10" />
                    <h3 className="text-2xl font-bold mb-3 relative z-10">Competitor Intelligence</h3>
                    <p className="text-muted-foreground leading-relaxed relative z-10">Deep-dive into competitors' offerings, sentiment, and feature gaps in seconds with AI-powered analysis.</p>
                  </div>
                </SpotlightCard>
              </AnimatedContent>

              {/* Feature 4 - Customer Insights */}
              <AnimatedContent distance={60} direction="vertical" duration={0.7} delay={0.1} threshold={0.15}>
                <SpotlightCard 
                  className="bg-[#0d0d12] border border-white/5 backdrop-blur-xl p-8 h-full"
                  spotlightColor="rgba(6, 182, 212, 0.25)"
                  spotlightSize={350}
                >
                  <div className="relative">
                    <Users className="w-12 h-12 text-cyan-500 mb-6 drop-shadow-md relative z-10" />
                    <h3 className="text-2xl font-bold mb-3 relative z-10">Customer Insights</h3>
                    <p className="text-muted-foreground leading-relaxed relative z-10">Discover your ideal customers, their behaviors, and preferences through AI-driven audience segmentation.</p>
                  </div>
                </SpotlightCard>
              </AnimatedContent>

              {/* Feature 5 - Launch Planning */}
              <AnimatedContent distance={60} direction="vertical" duration={0.7} delay={0.2} threshold={0.15}>
                <SpotlightCard 
                  className="bg-[#0d0d12] border border-white/5 backdrop-blur-xl p-8 h-full"
                  spotlightColor="rgba(251, 146, 60, 0.25)"
                  spotlightSize={350}
                >
                  <div className="relative">
                    <Rocket className="w-12 h-12 text-orange-500 mb-6 drop-shadow-md relative z-10" />
                    <h3 className="text-2xl font-bold mb-3 relative z-10">Launch Planning</h3>
                    <p className="text-muted-foreground leading-relaxed relative z-10">Create comprehensive launch strategies with timelines, milestones, and actionable steps for your product.</p>
                  </div>
                </SpotlightCard>
              </AnimatedContent>

              {/* Feature 6 - GTM Strategy */}
              <AnimatedContent distance={60} direction="vertical" duration={0.7} delay={0.3} threshold={0.15}>
                <SpotlightCard 
                  className="bg-[#0d0d12] border border-white/5 backdrop-blur-xl p-8 h-full"
                  spotlightColor="rgba(167, 139, 250, 0.25)"
                  spotlightSize={350}
                >
                  <div className="relative">
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-gradient-to-r from-primary/5 to-accent/5 blur-3xl"></div>
                    <TrendingUp className="w-12 h-12 text-primary mb-6 drop-shadow-md relative z-10" />
                    <h3 className="text-2xl font-bold mb-3 relative z-10">GTM Strategy</h3>
                    <p className="text-muted-foreground leading-relaxed relative z-10">Generate growth loops, marketing angles, and MVP strategies tailored to your product's unique strengths.</p>
                  </div>
                </SpotlightCard>
              </AnimatedContent>
            </div>
          </div>
        </section>

        {/* Minimal High-End Stats */}
        <section className="py-16 border-y border-white/5 bg-[#050508] relative z-10">
          <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-100 contrast-150 mix-blend-overlay"></div>
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="container mx-auto px-4 relative z-10"
          >
            <div className="flex flex-col md:flex-row items-center justify-evenly divide-y md:divide-y-0 md:divide-x divide-white/10 w-full max-w-5xl mx-auto rounded-3xl border border-white/5 glass p-2 shadow-2xl">
              <div className="w-full text-center py-8 md:py-6 px-4 hover:bg-white/5 transition-colors duration-300 first:rounded-l-2xl last:rounded-r-2xl">
                <div className="text-4xl lg:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 mb-2 drop-shadow-sm">
                  <Counter value={10} suffix="x" />
                </div>
                <div className="text-sm text-primary tracking-[0.2em] uppercase font-bold">Faster Validation</div>
              </div>
              <div className="w-full text-center py-8 md:py-6 px-4 hover:bg-white/5 transition-colors duration-300 first:rounded-l-2xl last:rounded-r-2xl">
                <div className="text-4xl lg:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 mb-2 drop-shadow-sm">
                  <Counter value={500} suffix="+" />
                </div>
                <div className="text-sm text-primary tracking-[0.2em] uppercase font-bold">Ideas Analyzed</div>
              </div>
              <div className="w-full text-center py-8 md:py-6 px-4 hover:bg-white/5 transition-colors duration-300 first:rounded-l-2xl last:rounded-r-2xl">
                <div className="text-4xl lg:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 mb-2 drop-shadow-sm">
                  <Counter value={100} suffix="%" />
                </div>
                <div className="text-sm text-primary tracking-[0.2em] uppercase font-bold">AI Powered</div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* CTA Section */}
        <section className="py-24 relative overflow-hidden z-10 bg-background">
          {/* Subtle background gradient */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(var(--primary)/0.1),transparent_70%)] pointer-events-none" />
          
          <FadeContent blur={true} duration={800} delay={100} threshold={0.2}>
            <div className="container mx-auto px-4 relative z-10 text-center">
              <div className="max-w-3xl mx-auto space-y-8">
                {/* Heading */}
                <h2 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-tight">
                  Ready to stop guessing<br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-primary">
                    and start building?
                  </span>
                </h2>

                {/* Description */}
                <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                  Join elite founders using Clarimo to turn vague concepts into validated, market-ready businesses.
                </p>

                {/* CTA Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
                  <Link to={user ? "/dashboard" : "/signup"}>
                    <AnimatedButton variant="primary" size="lg">
                      Enter Clarimo AI
                      {/* <ArrowRight className="w-5 h-5" /> */}
                    </AnimatedButton>
                  </Link>
                  <AnimatedButton variant="secondary" size="lg" href="#features" smoothScroll={true}>
                    Learn More
                  </AnimatedButton>
                </div>

                {/* Trust indicators
                <div className="flex flex-wrap items-center justify-center gap-6 pt-6 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary" />
                    <span>No credit card required</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary" />
                    <span>Free to start</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-primary" />
                    <span>Cancel anytime</span>
                  </div>
                </div> */}
              </div>
            </div>
          </FadeContent>
        </section>

        {/* Minimal Footer */}
        <footer className="border-t border-white/5 py-10 bg-[#020202] relative z-10">
          <div className="container mx-auto px-4 flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center gap-2 mb-4 md:mb-0 opacity-50 hover:opacity-100 transition-opacity">
              <img src="/logo.png" alt="Clarimo AI" className="w-5 h-5 rounded" />
              <span className="font-semibold text-sm">Clarimo AI &copy; 2026</span>
            </div>
            <div className="flex gap-8 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <Link to="#" className="hover:text-white transition-colors hover:glow-sm py-2">Privacy</Link>
              <Link to="#" className="hover:text-white transition-colors hover:glow-sm py-2">Terms</Link>
              <Link to="#" className="hover:text-white transition-colors hover:glow-sm py-2">Contact</Link>
            </div>
          </div>
        </footer>
      </div>
    </PageTransition>
  );
}
