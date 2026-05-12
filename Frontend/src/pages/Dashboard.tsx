import { useNavigate } from 'react-router-dom';
import {
  Lightbulb,
  Target,
  TrendingUp,
  ArrowRight,
  BarChart3,
  FileText,
  History,
  AlertCircle,
  Activity,
  Rocket,
  Globe,
  Users
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useDashboardStats } from '../hooks/useDashboardStats';
import { PremiumCard } from '../components/ui/premium/PremiumCard';
import { PremiumButton } from '../components/ui/premium/PremiumButton';
import { motion } from 'framer-motion';
import FadeContent from '../components/landing/FadeContent';
import AnimatedContent from '../components/landing/AnimatedContent';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { stats, loading, recentActivity, totalActions } = useDashboardStats();

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  return (
    <div className="responsive-container-dashboard min-h-screen">
      <div className="max-w-[1400px] mx-auto px-4 md:px-0">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-12 py-8"
      >
        {/* Welcome Header with Enhanced Design */}
        <FadeContent blur={true} duration={600} delay={0}>
          <div className="relative">
            {/* Decorative gradient orb */}
            <div className="absolute -top-20 -left-20 w-64 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
            <div className="relative space-y-4">
              {/* <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 mb-4">
                <Sparkles className="w-4 h-4 text-primary" />
                <span className="text-sm font-semibold text-primary">Dashboard Overview</span>
              </div> */}
              <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-white via-primary/90 to-accent/80 bg-clip-text text-transparent">
                {getGreeting()}, {user?.full_name?.split(' ')[0] || 'there'}!
              </h1>
              <p className="text-xl text-muted-foreground/80 max-w-2xl leading-relaxed">
                Your startup intelligence hub. Track progress, analyze insights, and accelerate your journey from idea to market.
              </p>
            </div>
          </div>
        </FadeContent>

        {/* Stats Overview with Enhanced Cards */}
        <div className="space-y-6">
          <FadeContent blur={false} duration={600} delay={100}>
            <div className="flex items-center gap-4">
              <h2 className="text-2xl font-bold tracking-tight">Ecosystem Progress</h2>
              <div className="h-px flex-1 bg-gradient-to-r from-primary/30 via-accent/20 to-transparent" />
            </div>
          </FadeContent>
          
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {/* Problem Discovery Stats */}
            <AnimatedContent distance={40} direction="vertical" duration={0.6} delay={0.1}>
              <PremiumCard glow variant="default" className="relative group overflow-hidden h-full">
                <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition-all duration-500" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-8">
                    <div className="p-3 bg-purple-500/10 rounded-2xl group-hover:bg-purple-500/15 transition-all duration-300">
                      <BarChart3 className="h-6 w-6 text-purple-400" />
                    </div>
                    <PremiumButton
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate('/discovered-problems')}
                      className="text-xs hover:text-white transition-all"
                    >
                      View All
                    </PremiumButton>
                  </div>
                  <div className="space-y-2">
                    <p className="text-4xl font-black text-white">
                      {loading ? '...' : stats?.problemDiscovery.total || 0}
                    </p>
                    <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Discoveries</p>
                    <p className="text-xs text-muted-foreground/60">
                      {loading ? '...' : stats?.problemDiscovery.totalProblems || 0} pain points identified
                    </p>
                  </div>
                </div>
              </PremiumCard>
            </AnimatedContent>

            {/* Ideas Stats */}
            <AnimatedContent distance={40} direction="vertical" duration={0.6} delay={0.2}>
              <PremiumCard glow variant="default" className="relative group overflow-hidden h-full">
                <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-all duration-500" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-8">
                    <div className="p-3 bg-blue-500/10 rounded-2xl group-hover:bg-blue-500/15 transition-all duration-300">
                      <Lightbulb className="h-6 w-6 text-blue-400" />
                    </div>
                    <PremiumButton
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate('/ideas')}
                      className="text-xs hover:text-white transition-all"
                    >
                      View All
                    </PremiumButton>
                  </div>
                  <div className="space-y-2">
                    <p className="text-4xl font-black text-white">
                      {loading ? '...' : stats?.ideas.total || 0}
                    </p>
                    <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Prototypes</p>
                    <p className="text-xs text-muted-foreground/60">
                      {loading ? '...' : stats?.ideas.validated || 0} validated via AI
                    </p>
                  </div>
                </div>
              </PremiumCard>
            </AnimatedContent>

            {/* Competitor Analysis Stats */}
            <AnimatedContent distance={40} direction="vertical" duration={0.6} delay={0.3}>
              <PremiumCard glow variant="default" className="relative group overflow-hidden h-full">
                <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/5 rounded-full blur-2xl group-hover:bg-green-500/10 transition-all duration-500" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-8">
                    <div className="p-3 bg-green-500/10 rounded-2xl group-hover:bg-green-500/15 transition-all duration-300">
                      <Target className="h-6 w-6 text-green-400" />
                    </div>
                    <PremiumButton
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate('/competitor-analysis/history')}
                      className="text-xs hover:text-white transition-all"
                    >
                      View All
                    </PremiumButton>
                  </div>
                  <div className="space-y-2">
                    <p className="text-4xl font-black text-white">
                      {loading ? '...' : stats?.competitorAnalysis.total || 0}
                    </p>
                    <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Market Scans</p>
                    <p className="text-xs text-muted-foreground/60">
                      {loading ? '...' : stats?.competitorAnalysis.totalCompetitors || 0} competitors mapped
                    </p>
                  </div>
                </div>
              </PremiumCard>
            </AnimatedContent>

            {/* Launch Planning Stats */}
            <AnimatedContent distance={40} direction="vertical" duration={0.6} delay={0.4}>
              <PremiumCard glow variant="default" className="relative group overflow-hidden h-full">
                <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/5 rounded-full blur-2xl group-hover:bg-orange-500/10 transition-all duration-500" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-8">
                    <div className="p-3 bg-orange-500/10 rounded-2xl group-hover:bg-orange-500/15 transition-all duration-300">
                      <Rocket className="h-6 w-6 text-orange-400" />
                    </div>
                    <div className="flex gap-2">
                      <PremiumButton
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate('/launch-planning/history')}
                        className="text-xs hover:text-white transition-all"
                      >
                        History
                      </PremiumButton>
                      <PremiumButton
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate('/launch-planning')}
                        className="text-xs hover:text-white bg-orange-500/10 transition-all"
                      >
                        Go
                      </PremiumButton>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-4xl font-black text-white">
                      {loading ? '...' : stats?.launchPlanning.total || 0}
                    </p>
                    <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Launch Plans</p>
                    <p className="text-[10px] text-muted-foreground/60 line-clamp-1">
                      {loading ? '...' : stats?.launchPlanning.latestTitle || 'Strategic roadmaps'}
                    </p>
                  </div>
                </div>
              </PremiumCard>
            </AnimatedContent>

            {/* GTM Stats */}
            <AnimatedContent distance={40} direction="vertical" duration={0.6} delay={0.5}>
              <PremiumCard glow variant="default" className="relative group overflow-hidden h-full">
                <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition-all duration-500" />
                <div className="relative">
                  <div className="flex items-center justify-between mb-8">
                    <div className="p-3 bg-cyan-500/10 rounded-2xl group-hover:bg-cyan-500/15 transition-all duration-300">
                      <TrendingUp className="h-6 w-6 text-cyan-400" />
                    </div>
                    <div className="flex gap-2">
                      <PremiumButton
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate('/go-to-market/history')}
                        className="text-xs hover:text-white transition-all"
                      >
                        History
                      </PremiumButton>
                      <PremiumButton
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate('/go-to-market')}
                        className="text-xs hover:text-white bg-cyan-500/10 transition-all"
                      >
                        Go
                      </PremiumButton>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-4xl font-black text-white">
                      {loading ? '...' : stats?.gtm.total || 0}
                    </p>
                    <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">GTM Strategy</p>
                    <p className="text-[10px] text-muted-foreground/60 line-clamp-1">
                      {loading ? '...' : stats?.gtm.latestTitle || 'Market entry vault'}
                    </p>
                  </div>
                </div>
              </PremiumCard>
            </AnimatedContent>
          </div>
        </div>

        {/* Global Activity & Control Center with Enhanced Design */}
        <div className="grid gap-8 lg:grid-cols-5">
          {/* Recent Activity */}
          <AnimatedContent distance={40} direction="vertical" duration={0.7} delay={0.2} className="lg:col-span-3">
            <PremiumCard variant="default" className="h-full">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-xl">
                    <History className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">Intelligence Feed</h3>
                    <p className="text-xs text-muted-foreground">Latest algorithmic processing results</p>
                  </div>
                </div>
                <div className="px-3 py-1 bg-primary/10 rounded-full border border-primary/20 text-[10px] font-bold uppercase tracking-widest text-primary">
                  Live Data
                </div>
              </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-4">
                <div className="relative">
                  <div className="animate-spin rounded-full h-12 w-12 border-2 border-primary border-t-transparent" />
                  <div className="absolute inset-0 rounded-full bg-primary/20 blur-xl animate-pulse" />
                </div>
                <p className="text-sm text-muted-foreground">Fetching activity...</p>
              </div>
            ) : recentActivity.length === 0 ? (
              <div className="text-center py-16 bg-gradient-to-br from-white/[0.02] to-primary/[0.02] rounded-3xl border border-dashed border-white/10">
                <div className="relative inline-block mb-4">
                  <AlertCircle className="h-12 w-12 text-muted-foreground opacity-40" />
                  <div className="absolute inset-0 bg-primary/20 blur-2xl" />
                </div>
                <p className="text-lg font-semibold text-white/60">No Intelligence Logged</p>
                <p className="text-sm text-muted-foreground mt-2 px-8 max-w-md mx-auto">
                  Complete a market scan or idea validation to see real-time updates in your feed.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {recentActivity.map((activity, index) => (
                  <motion.div 
                    key={index} 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1, duration: 0.5 }}
                    className="flex items-center gap-5 p-5 rounded-2xl bg-gradient-to-br from-white/[0.02] to-white/[0.01] border border-white/5 hover:border-primary/20 hover:bg-white/[0.04] transition-all duration-300 group cursor-pointer"
                    onClick={() => {
                      if (activity.type === 'problem') navigate('/discovered-problems');
                      if (activity.type === 'idea') navigate('/ideas');
                      if (activity.type === 'competitor') navigate('/competitor-analysis/history');
                      if (activity.type === 'launch') navigate('/launch-planning/history');
                      if (activity.type === 'gtm') navigate('/go-to-market/history');
                    }}
                  >
                    <div className={`p-3 rounded-xl transition-all duration-300 group-hover:scale-110 ${
                      activity.type === 'problem' ? 'bg-purple-500/10 group-hover:bg-purple-500/20' :
                      activity.type === 'idea' ? 'bg-blue-500/10 group-hover:bg-blue-500/20' :
                      activity.type === 'launch' ? 'bg-orange-500/10 group-hover:bg-orange-500/20' :
                      activity.type === 'gtm' ? 'bg-cyan-500/10 group-hover:bg-cyan-500/20' :
                      'bg-green-500/10 group-hover:bg-green-500/20'
                    }`}>
                      {activity.type === 'problem' && <BarChart3 className="h-5 w-5 text-purple-500" />}
                      {activity.type === 'idea' && <Lightbulb className="h-5 w-5 text-blue-500" />}
                      {activity.type === 'competitor' && <Target className="h-5 w-5 text-green-500" />}
                      {activity.type === 'launch' && <Rocket className="h-5 w-5 text-orange-500" />}
                      {activity.type === 'gtm' && <TrendingUp className="h-5 w-5 text-cyan-500" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-base font-bold text-white/90 group-hover:text-white transition-colors">
                        {activity.type === 'problem' && 'Semantic Problem Analysis'}
                        {activity.type === 'idea' && 'AI Prototype Validation'}
                        {activity.type === 'competitor' && 'Competitor Landscape Map'}
                        {activity.type === 'launch' && 'Launch Prep & Roadmap'}
                        {activity.type === 'gtm' && 'Market Entry Strategy'}
                      </p>
                      <p className="text-xs text-muted-foreground uppercase tracking-widest mt-1">
                        Processed {activity.count} {activity.count === 1 ? 'Entity' : 'Entities'} • {formatDate(activity.date)}
                      </p>
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-all duration-300">
                      <ArrowRight className="h-5 w-5 text-primary" />
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
            </PremiumCard>
          </AnimatedContent>

          {/* Quick Links / Control Center */}
          <AnimatedContent distance={40} direction="vertical" duration={0.7} delay={0.3} className="lg:col-span-2">
            <PremiumCard variant="default" className="h-full flex flex-col">
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-primary/10 rounded-xl">
                    <TrendingUp className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="text-xl font-bold">Control Center</h3>
                </div>
                <p className="text-xs text-muted-foreground">Orchestrate your startup modules</p>
              </div>
              
              <div className="space-y-3 flex-1">
                {[
                  { label: 'Problem Repository', icon: FileText, route: '/discovered-problems', count: stats?.problemDiscovery.total, color: 'purple' },
                  { label: 'Invention Lab', icon: Lightbulb, route: '/ideas', count: stats?.ideas.total, color: 'blue' },
                  { label: 'Market Intelligence', icon: Target, route: '/competitor-analysis/history', count: stats?.competitorAnalysis.total, color: 'green' },
                  { label: 'Customer Insights', icon: Users, route: '/customer-insights/history', count: 0, color: 'cyan' },
                  { label: 'Launch Roadmaps', icon: Rocket, route: '/launch-planning/history', count: stats?.launchPlanning.total, color: 'orange' },
                  { label: 'GTM Strategy', icon: Globe, route: '/go-to-market/history', count: stats?.gtm.total, color: 'cyan' },
                ].map((link, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + idx * 0.1, duration: 0.5 }}
                  >
                    <PremiumButton
                      variant="outlined"
                      size="lg"
                      className="w-full justify-start border-white/5 hover:border-primary/20 hover:bg-primary/5 transition-all group py-6"
                      onClick={() => navigate(link.route)}
                    >
                      <link.icon className="mr-4 h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                      <span className="font-semibold text-white/80 group-hover:text-white transition-colors">{link.label}</span>
                      <span className="ml-auto text-[10px] font-black bg-white/5 px-2.5 py-1 rounded-md text-white/40 group-hover:text-primary group-hover:bg-primary/10 transition-all uppercase tracking-tighter">
                        {link.count || 0}
                      </span>
                    </PremiumButton>
                  </motion.div>
                ))}
              </div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.2, duration: 0.5 }}
              >
                <PremiumCard variant="accent" hover={false} className="mt-8 p-5 border-dashed">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center">
                      <Activity className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Total Network Actions</p>
                      <p className="text-3xl font-black text-white">{totalActions}</p>
                    </div>
                  </div>
                </PremiumCard>
              </motion.div>
            </PremiumCard>
          </AnimatedContent>
        </div>
      </motion.div>
    </div>
  </div>
  );
}
