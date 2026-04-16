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
  Rocket
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useDashboardStats } from '../hooks/useDashboardStats';
import { PremiumCard } from '../components/ui/premium/PremiumCard';
import { PremiumButton } from '../components/ui/premium/PremiumButton';
import { motion } from 'framer-motion';

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

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className="responsive-container-dashboard">
      <div className="max-w-[1400px] mx-auto px-4 md:px-0">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-12"
      >
        {/* Welcome Header */}
        <motion.div variants={itemVariants} className="space-y-4">
          <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-white/80 to-white/50 bg-clip-text text-transparent">
            {getGreeting()}, {user?.full_name?.split(' ')[0] || 'there'}!
          </h1>
          <p className="text-xl text-muted-foreground/80 max-w-2xl leading-relaxed">
            Welcome back to Clarimo AI. Your startup intelligence is aggregated and ready for review.
          </p>
        </motion.div>

        {/* Stats Overview */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold tracking-tight">Ecosystem Progress</h2>
            <div className="h-px flex-1 bg-gradient-to-r from-white/10 to-transparent ml-8" />
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {/* Problem Discovery Stats */}
            <PremiumCard glow variant="default" className="relative group">
              <div className="flex items-center justify-between mb-8">
                <div className="p-3 bg-purple-500/10 rounded-2xl group-hover:bg-purple-500/20 transition-colors">
                  <BarChart3 className="h-6 w-6 text-purple-500 group-hover:scale-110 transition-transform" />
                </div>
                <PremiumButton
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/discovered-problems')}
                  className="text-xs group-hover:text-white"
                >
                  View All
                </PremiumButton>
              </div>
              <div className="space-y-2">
                <p className="text-4xl font-black">{loading ? '...' : stats?.problemDiscovery.total || 0}</p>
                <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Discoveries</p>
                <p className="text-xs text-muted-foreground/60">
                  {loading ? '...' : stats?.problemDiscovery.totalProblems || 0} pain points identified
                </p>
              </div>
            </PremiumCard>

            {/* Ideas Stats */}
            <PremiumCard glow variant="default" className="relative group">
              <div className="flex items-center justify-between mb-8">
                <div className="p-3 bg-blue-500/10 rounded-2xl group-hover:bg-blue-500/20 transition-colors">
                  <Lightbulb className="h-6 w-6 text-blue-500 group-hover:scale-110 transition-transform" />
                </div>
                <PremiumButton
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/ideas')}
                  className="text-xs group-hover:text-white"
                >
                  View All
                </PremiumButton>
              </div>
              <div className="space-y-2">
                <p className="text-4xl font-black">{loading ? '...' : stats?.ideas.total || 0}</p>
                <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Prototypes</p>
                <p className="text-xs text-muted-foreground/60">
                  {loading ? '...' : stats?.ideas.validated || 0} validated via AI
                </p>
              </div>
            </PremiumCard>

            {/* Competitor Analysis Stats */}
            <PremiumCard glow variant="default" className="relative group">
              <div className="flex items-center justify-between mb-8">
                <div className="p-3 bg-green-500/10 rounded-2xl group-hover:bg-green-500/20 transition-colors">
                  <Target className="h-6 w-6 text-green-500 group-hover:scale-110 transition-transform" />
                </div>
                <PremiumButton
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/competitor-analysis/history')}
                  className="text-xs group-hover:text-white"
                >
                  View All
                </PremiumButton>
              </div>
              <div className="space-y-2">
                <p className="text-4xl font-black">{loading ? '...' : stats?.competitorAnalysis.total || 0}</p>
                <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Market Scans</p>
                <p className="text-xs text-muted-foreground/60">
                  {loading ? '...' : stats?.competitorAnalysis.totalCompetitors || 0} competitors mapped
                </p>
              </div>
            </PremiumCard>

            {/* Launch Planning Stats */}
            <PremiumCard glow variant="default" className="relative group">
              <div className="flex items-center justify-between mb-8">
                <div className="p-3 bg-orange-500/10 rounded-2xl group-hover:bg-orange-500/20 transition-colors">
                  <Rocket className="h-6 w-6 text-orange-500 group-hover:scale-110 transition-transform" />
                </div>
                <PremiumButton
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/launch-planning')}
                  className="text-xs group-hover:text-white"
                >
                  Go
                </PremiumButton>
              </div>
              <div className="space-y-2">
                <p className="text-4xl font-black">{loading ? '...' : stats?.launchPlanning.total || 0}</p>
                <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">Go-To-Market</p>
                <p className="text-xs text-muted-foreground/60">
                   Active strategy roadmaps
                </p>
              </div>
            </PremiumCard>
          </div>
        </div>

        {/* Global Activity & Control Center */}
        <div className="grid gap-8 lg:grid-cols-5">
          {/* Recent Activity */}
          <PremiumCard variant="default" className="lg:col-span-3 h-full">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/5 rounded-lg">
                  <History className="h-5 w-5 text-white/60" />
                </div>
                <div>
                  <h3 className="text-xl font-bold">Intelligence Feed</h3>
                  <p className="text-xs text-muted-foreground">Latest algorithmic processing results</p>
                </div>
              </div>
              <div className="px-3 py-1 bg-white/5 rounded-full border border-white/10 text-[10px] font-bold uppercase tracking-widest text-white/40">
                Live Data
              </div>
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-4 opacity-50">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
                <p className="text-sm">Fetching activity...</p>
              </div>
            ) : recentActivity.length === 0 ? (
              <div className="text-center py-16 bg-white/[0.02] rounded-3xl border border-dashed border-white/10">
                <AlertCircle className="h-10 w-10 mx-auto text-muted-foreground mb-4 opacity-40" />
                <p className="text-lg font-semibold text-white/60">No Intelligence Logged</p>
                <p className="text-sm text-muted-foreground mt-1 px-8">Complete a market scan or idea validation to see real-time updates.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {recentActivity.map((activity, index) => (
                  <motion.div 
                    key={index} 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center gap-5 p-5 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/10 hover:bg-white/[0.04] transition-all group"
                  >
                    <div className={`p-3 rounded-xl ${
                      activity.type === 'problem' ? 'bg-purple-500/10' :
                      activity.type === 'idea' ? 'bg-blue-500/10' :
                      activity.type === 'launch' ? 'bg-orange-500/10' :
                      'bg-green-500/10'
                    }`}>
                      {activity.type === 'problem' && <BarChart3 className="h-5 w-5 text-purple-500" />}
                      {activity.type === 'idea' && <Lightbulb className="h-5 w-5 text-blue-500" />}
                      {activity.type === 'competitor' && <Target className="h-5 w-5 text-green-500" />}
                      {activity.type === 'launch' && <Rocket className="h-5 w-5 text-orange-500" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-base font-bold text-white/90">
                        {activity.type === 'problem' && 'Semantic Problem Analysis'}
                        {activity.type === 'idea' && 'AI Prototype Validation'}
                        {activity.type === 'competitor' && 'Competitor Landscape Map'}
                        {activity.type === 'launch' && 'Strategy Optimization'}
                      </p>
                      <p className="text-xs text-muted-foreground uppercase tracking-widest mt-1">
                        Processed {activity.count} {activity.count === 1 ? 'Entity' : 'Entities'} • {formatDate(activity.date)}
                      </p>
                    </div>
                    <PremiumButton
                      variant="outlined"
                      size="icon"
                      onClick={() => {
                        if (activity.type === 'problem') navigate('/discovered-problems');
                        if (activity.type === 'idea') navigate('/ideas');
                        if (activity.type === 'competitor') navigate('/competitor-analysis/history');
                        if (activity.type === 'launch') navigate('/launch-planning');
                      }}
                      className="opacity-0 group-hover:opacity-100 h-9 w-9 rounded-lg"
                    >
                      <ArrowRight className="h-4 w-4" />
                    </PremiumButton>
                  </motion.div>
                ))}
              </div>
            )}
          </PremiumCard>

          {/* Quick Links / Control Center */}
          <PremiumCard variant="default" className="lg:col-span-2 h-full flex flex-col">
            <div className="mb-8">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <TrendingUp className="h-5 w-5 text-primary" />
                </div>
                <h3 className="text-xl font-bold">Control Center</h3>
              </div>
              <p className="text-xs text-muted-foreground">Orchestrate your startup modules</p>
            </div>
            
            <div className="space-y-3 flex-1">
              {[
                { label: 'Problem Repository', icon: FileText, route: '/discovered-problems', count: stats?.problemDiscovery.total },
                { label: 'Invention Lab', icon: Lightbulb, route: '/ideas', count: stats?.ideas.total },
                { label: 'Market Intelligence', icon: Target, route: '/competitor-analysis/history', count: stats?.competitorAnalysis.total },
                { label: 'GTM Strategy', icon: Rocket, route: '/launch-planning', count: stats?.launchPlanning.total },
              ].map((link, idx) => (
                <PremiumButton
                  key={idx}
                  variant="outlined"
                  size="lg"
                  className="w-full justify-start border-white/5 hover:border-primary/20 hover:bg-primary/5 transition-all group py-6"
                  onClick={() => navigate(link.route)}
                >
                  <link.icon className="mr-4 h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                  <span className="font-semibold text-white/80 group-hover:text-white">{link.label}</span>
                  <span className="ml-auto text-[10px] font-black bg-white/5 px-2 py-1 rounded-md text-white/40 group-hover:text-primary group-hover:bg-primary/10 transition-all uppercase tracking-tighter">
                    {link.count || 0}
                  </span>
                </PremiumButton>
              ))}
            </div>

            <PremiumCard variant="accent" hover={false} className="mt-8 p-4 border-dashed">
              <div className="flex items-center gap-4">
                 <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center">
                    <Activity className="h-5 w-5 text-primary" />
                 </div>
                 <div>
                    <p className="text-[10px] uppercase tracking-widest text-white/40 font-bold">Total Network Actions</p>
                    <p className="text-2xl font-black text-white">{totalActions}</p>
                 </div>
              </div>
            </PremiumCard>
          </PremiumCard>
        </div>
      </motion.div>
    </div>
  </div>
  );
}
