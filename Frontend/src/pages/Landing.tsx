import { motion, Variants } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ArrowRight, Target, BarChart2, CheckCircle2, Bot, Layers } from 'lucide-react';
import Hero3D from '../components/landing/Hero3D';
import { Button } from '../components/ui/button';
import PageTransition from '../components/PageTransition';

export default function Landing() {
  const { user } = useAuth();

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15, delayChildren: 0.2 },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1, 
      y: 0,
      transition: { duration: 0.6, ease: [0.25, 0.1, 0.25, 1.0] }
    },
  };

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
            <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center glow">
              <span className="text-white font-bold text-xl">C</span>
            </div>
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
        <section className="relative min-h-screen flex items-center justify-center pt-24 pb-12 w-full">
          <Hero3D />
          
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
                <span className="gradient-text drop-shadow-[0_0_20px_rgba(167,139,250,0.5)]">Build Smarter.</span>
              </h1>
              
              <p className="text-lg md:text-xl text-white/80 max-w-2xl mx-auto leading-relaxed drop-shadow-md font-medium">
                Clarimo AI is your intelligent co-founder. Discover real problems, validate ideas instantly, analyze competitors, and plan your go-to-market strategy—all in one place.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6">
                <Link to={user ? "/dashboard" : "/signup"}>
                  <Button size="lg" className="h-14 px-8 text-lg rounded-xl glow-accent bg-accent hover:bg-accent/90 text-white shadow-[0_0_40px_-5px_hsl(var(--accent))] transition-all duration-300 hover:scale-105 active:scale-95 border border-accent/50 group">
                    Accelerate Your Startup 
                    <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
                <a href="#features">
                  <Button variant="outline" size="lg" className="h-14 px-8 text-lg rounded-xl glass border-border text-white hover:bg-white/10 hover:text-white transition-all duration-300 backdrop-blur-md">
                    See How It Works
                  </Button>
                </a>
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
          
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-100px" }}
            className="container mx-auto px-4 relative z-10"
          >
            <motion.div variants={itemVariants} className="text-center mb-16 space-y-4">
              <h2 className="text-3xl md:text-5xl font-bold">The Complete <span className="text-primary glow-sm">Founder's Arsenal</span></h2>
              <p className="text-muted-foreground text-lg max-w-xl mx-auto">Everything you need from zero to one. Powered by advanced reasoning engines and real-time market data.</p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
              {/* Feature 1 */}
              <motion.div variants={itemVariants} className="col-span-1 md:col-span-2 bg-[#0d0d12] border border-white/5 backdrop-blur-xl rounded-3xl p-8 hover:border-primary/30 transition-all duration-500 overflow-hidden relative group hover:shadow-[0_0_30px_-5px_rgba(167,139,250,0.15)] hover:-translate-y-1">
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl group-hover:bg-primary/20 transition-all duration-700 -mr-20 -mt-20"></div>
                <Target className="w-12 h-12 text-primary mb-6 drop-shadow-md" />
                <h3 className="text-2xl font-bold mb-3">Problem Discovery</h3>
                <p className="text-muted-foreground leading-relaxed max-w-md">Find untapped niches and urgent pain points instantly. Analyze thousands of data signals to discover real problems worth solving before writing a single line of code.</p>
              </motion.div>
              
              {/* Feature 2 */}
              <motion.div variants={itemVariants} className="col-span-1 bg-[#0d0d12] border border-white/5 backdrop-blur-xl rounded-3xl p-8 hover:border-accent/30 transition-all duration-500 relative group overflow-hidden hover:shadow-[0_0_30px_-5px_rgba(216,180,254,0.15)] hover:-translate-y-1">
                 <div className="absolute bottom-0 left-0 w-40 h-40 bg-accent/10 rounded-full blur-2xl group-hover:bg-accent/20 transition-all duration-700"></div>
                <Bot className="w-12 h-12 text-accent mb-6 drop-shadow-md" />
                <h3 className="text-2xl font-bold mb-3">AI Validation</h3>
                <p className="text-muted-foreground leading-relaxed">Let AI criticize and objectively score your startup ideas based on market demand.</p>
              </motion.div>

              {/* Feature 3 */}
              <motion.div variants={itemVariants} className="col-span-1 bg-[#0d0d12] border border-white/5 backdrop-blur-xl rounded-3xl p-8 hover:border-[#3b82f6]/30 transition-all duration-500 relative group hover:shadow-[0_0_30px_-5px_rgba(59,130,246,0.15)] hover:-translate-y-1">
                <BarChart2 className="w-12 h-12 text-[#3b82f6] mb-6 drop-shadow-md" />
                <h3 className="text-2xl font-bold mb-3">Competitor Radar</h3>
                <p className="text-muted-foreground leading-relaxed">Deep-dive into competitors' offerings, sentiment, and feature gaps in seconds.</p>
              </motion.div>

              {/* Feature 4 */}
              <motion.div variants={itemVariants} className="col-span-1 md:col-span-2 bg-[#0d0d12] border border-white/5 backdrop-blur-xl rounded-3xl p-8 hover:border-primary/30 transition-all duration-500 relative group overflow-hidden hover:shadow-[0_0_30px_-5px_rgba(167,139,250,0.15)] hover:-translate-y-1">
                 <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-gradient-to-r from-primary/5 to-accent/5 blur-3xl"></div>
                <div className="relative z-10 flex flex-col md:flex-row items-center gap-8">
                  <div className="flex-1">
                    <Layers className="w-12 h-12 text-primary mb-6 drop-shadow-md" />
                    <h3 className="text-2xl font-bold mb-3">Go-to-Market Planner</h3>
                    <p className="text-muted-foreground leading-relaxed">Generate actionable growth loops, marketing angles, and MVP launch strategies tailored exactly to your product's strengths.</p>
                  </div>
                  <div className="w-full md:w-1/3 space-y-3">
                    {['Audience Personas', 'Feature Roadmap', 'Pricing Strategy'].map(item => (
                      <div key={item} className="flex items-center gap-3 bg-white/5 border border-white/10 px-4 py-3 rounded-xl transition-all hover:bg-white/10 hover:border-primary/40 group">
                        <CheckCircle2 className="text-primary w-5 h-5 group-hover:scale-110 transition-transform" />
                        <span className="text-sm font-medium">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
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
              {[
                { label: 'Faster Validation', value: '10x' },
                { label: 'Ideas Analyzed', value: '500+' },
                { label: 'Powered Insights', value: 'AI' }
              ].map((stat) => (
                <div key={stat.label} className="w-full text-center py-8 md:py-6 px-4 hover:bg-white/5 transition-colors duration-300 first:rounded-l-2xl last:rounded-r-2xl">
                  <div className="text-4xl lg:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 mb-2 drop-shadow-sm">{stat.value}</div>
                  <div className="text-sm text-primary tracking-[0.2em] uppercase font-bold">{stat.label}</div>
                </div>
              ))}
            </div>
          </motion.div>
        </section>

        {/* CTA Section */}
        <section className="py-24 relative overflow-hidden z-10 bg-background">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,hsl(var(--primary)/0.15),transparent_60%)] pointer-events-none" />
          
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
            className="container mx-auto px-4 relative z-10 text-center space-y-8"
          >
            <h2 className="text-4xl md:text-6xl font-extrabold max-w-3xl mx-auto text-white tracking-tight">
              Ready to stop guessing and start building?
            </h2>
            <p className="text-lg md:text-xl text-muted-foreground max-w-xl mx-auto">
              Join elite founders using Clarimo to turn vague concepts into validated, market-ready businesses perfectly adapted to current demands.
            </p>
            <motion.div 
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="pt-6 flex justify-center"
            >
              <Link to={user ? "/dashboard" : "/signup"}>
                <Button size="lg" className="h-14 px-10 text-lg rounded-full bg-white text-black hover:bg-gray-100 shadow-[0_0_30px_-5px_rgba(255,255,255,0.3)] transition-all duration-300">
                  Enter Clarimo AI
                </Button>
              </Link>
            </motion.div>
          </motion.div>
        </section>

        {/* Minimal Footer */}
        <footer className="border-t border-white/5 py-10 bg-[#020202] relative z-10">
          <div className="container mx-auto px-4 flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center gap-2 mb-4 md:mb-0 opacity-50 hover:opacity-100 transition-opacity">
              <div className="w-5 h-5 rounded bg-primary flex items-center justify-center">
                <span className="text-[#020202] font-bold text-[10px]">C</span>
              </div>
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
