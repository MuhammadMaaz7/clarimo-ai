import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDiscoveredProblems } from '../hooks/useDiscoveredProblems';
import { PremiumCard } from '../components/ui/premium/PremiumCard';
import { PremiumButton } from '../components/ui/premium/PremiumButton';
import { Input } from '../components/ui/input';
import { 
  BarChart3, 
  History, 
  Calendar, 
  ExternalLink, 
  AlertCircle, 
  Trash2, 
  Search, 
  Plus, 
  Layers
} from 'lucide-react';
import ConfirmationModal from '../components/ConfirmationModal';
import { motion, AnimatePresence } from 'framer-motion';

const DiscoveredProblems = () => {
  const navigate = useNavigate();
  const {
      filteredHistory,
      history,
      stats,
      isLoading,
      isDeleting,
      searchQuery,
      setSearchQuery,
      deleteAnalysis
  } = useDiscoveredProblems();

  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    inputId: string;
    query: string;
  }>({ isOpen: false, inputId: '', query: '' });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const openDeleteConfirmation = (inputId: string, query: string) => {
    setConfirmModal({ isOpen: true, inputId, query });
  };

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, y: 0, 
      transition: { duration: 0.6, staggerChildren: 0.1 } 
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.98 },
    visible: { opacity: 1, scale: 1 }
  };

  return (
    <div className="container mx-auto px-6 py-10 max-w-7xl relative overflow-hidden">
        {/* Animated Background Orbs */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[100px] -mr-64 -mt-64 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[300px] h-[300px] bg-accent/5 rounded-full blur-[80px] -ml-32 -mb-32 pointer-events-none" />

      <motion.div initial="hidden" animate="visible" variants={containerVariants} className="space-y-10 relative z-10">
        {/* Intelligence Header */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <div className="p-4 rounded-3xl bg-primary/10 border border-primary/20 backdrop-blur-xl">
               <Layers className="h-10 w-10 text-primary" />
            </div>
            <div>
              <h1 className="text-4xl font-black tracking-tight text-white capitalize">Problem Archives</h1>
              <p className="text-muted-foreground mt-1 max-w-md">Access intelligence gathered from global digital communities and pain-point signals.</p>
            </div>
          </div>
          <PremiumButton
            onClick={() => navigate('/problem-discovery')}
            className="h-14 px-8 rounded-2xl shadow-primary/20 hover:scale-105"
          >
            <Plus className="mr-3 h-5 w-5" /> Initiate New Discovery
          </PremiumButton>
        </div>

        {/* Global Analytics Overview */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
                { label: 'Analyses Run', val: stats.total_analyses, icon: BarChart3, color: 'text-blue-400', bg: 'bg-blue-400/5' },
                { label: 'Total Conflicts', val: stats.total_pain_points, icon: AlertCircle, color: 'text-green-400', bg: 'bg-green-400/5' },
                { label: 'Macro Themes', val: stats.total_clusters, icon: History, color: 'text-purple-400', bg: 'bg-purple-400/5' },
                { label: 'Last Intel Sync', val: stats.latest_analysis ? formatDate(stats.latest_analysis).split(',')[0] : 'Never', icon: Calendar, color: 'text-orange-400', bg: 'bg-orange-400/5' }
            ].map((stat, i) => (
                <PremiumCard key={i} variant="glass" className="p-6">
                   <div className="flex items-center gap-4">
                      <div className={`p-4 rounded-2xl ${stat.bg} ${stat.color} border border-white/5`}>
                         <stat.icon className="h-6 w-6" />
                      </div>
                      <div>
                         <p className="text-2xl font-black tracking-tight text-white">{stat.val}</p>
                         <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{stat.label}</p>
                      </div>
                   </div>
                </PremiumCard>
            ))}
          </div>
        )}

        {/* Neural Search Command */}
        {history.length > 0 && (
          <PremiumCard variant="glass" className="relative group">
            <div className="absolute inset-0 bg-primary/[0.02] opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative flex items-center gap-4">
                <Search className="h-5 w-5 text-primary/60 ml-4" />
                <Input
                  placeholder="Query semantic archives..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-transparent border-none focus-visible:ring-0 text-lg h-14 w-full placeholder:text-white/20"
                />
            </div>
          </PremiumCard>
        )}

        {/* Result Matrix */}
        <div className="space-y-6">
          <AnimatePresence mode="popLayout">
            {filteredHistory.length === 0 ? (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center py-20">
                     <PremiumCard variant="glass" className="max-w-md text-center p-12 space-y-6 border-dashed border-white/10">
                        <div className="p-6 rounded-full bg-white/5 w-fit mx-auto">
                            <Bot className="h-10 w-10 text-muted-foreground" />
                        </div>
                        <div className="space-y-2">
                           <h3 className="text-xl font-bold text-white">Archives Empty</h3>
                           <p className="text-muted-foreground">The system contains no logs for your current search parameters. Initiate a discovery probe to populate the matrix.</p>
                        </div>
                        <PremiumButton variant="outlined" onClick={() => setSearchQuery('')}>Clear Neural Filter</PremiumButton>
                     </PremiumCard>
                </motion.div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {filteredHistory.map((item) => (
                    <motion.div 
                        key={item.input_id} 
                        variants={itemVariants} 
                        layout
                        whileHover={{ y: -5 }}
                        className="group"
                    >
                        <PremiumCard 
                            variant="glass" 
                            className="h-full hover:border-primary/40 transition-all duration-500 overflow-hidden"
                            onClick={() => navigate(`/analysis/${item.input_id}`)}
                        >
                            <div className="flex flex-col h-full justify-between gap-6">
                                <div className="space-y-4">
                                    <div className="flex items-start justify-between">
                                        <div className="bg-white/5 border border-white/10 px-3 py-1 rounded-full text-[10px] font-black tracking-widest text-primary/80 uppercase">Entry #{item.input_id.slice(0, 5)}</div>
                                        <div className="text-[10px] font-medium text-muted-foreground">{formatDate(item.created_at)}</div>
                                    </div>
                                    <h3 className="text-2xl font-bold text-white leading-snug group-hover:text-primary transition-colors">"{item.original_query}"</h3>
                                    
                                    <div className="grid grid-cols-2 gap-3 pt-2">
                                        <div className="bg-[#050505] p-4 rounded-2xl border border-white/5">
                                            <p className="text-2xl font-black text-white">{item.pain_points_count}</p>
                                            <p className="text-[10px] uppercase font-black tracking-widest text-muted-foreground">Signals</p>
                                        </div>
                                        <div className="bg-[#050505] p-4 rounded-2xl border border-white/5">
                                            <p className="text-2xl font-black text-white">{item.total_clusters}</p>
                                            <p className="text-[10px] uppercase font-black tracking-widest text-muted-foreground">Macro Themes</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-3 pt-4 border-t border-white/5">
                                    <PremiumButton variant="primary" className="flex-1 h-12 rounded-xl text-xs font-black uppercase tracking-widest">
                                        Open Intel <ExternalLink className="ml-2 h-4 w-4" />
                                    </PremiumButton>
                                    <PremiumButton 
                                        variant="outlined" 
                                        className="w-12 h-12 p-0 rounded-xl border-red-500/20 group-hover:border-red-500/50 text-red-400 hover:bg-red-500/10 transition-all"
                                        loading={isDeleting}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            openDeleteConfirmation(item.input_id, item.original_query);
                                        }}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </PremiumButton>
                                </div>
                            </div>
                        </PremiumCard>
                    </motion.div>
                    ))}
                </div>
            )}
          </AnimatePresence>
        </div>

        {/* Global Footer Insight */}
        {!isLoading && filteredHistory.length > 0 && (
          <div className="py-10 border-t border-white/5 flex items-center justify-center gap-4 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
             <div className="h-1 w-12 bg-white/5 rounded-full" />
             Displaying {filteredHistory.length} of {history.length} archives
             <div className="h-1 w-12 bg-white/5 rounded-full" />
          </div>
        )}
      </motion.div>

      {/* Confirmation Protocols */}
      <ConfirmationModal
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal(p => ({ ...p, isOpen: false }))}
        onConfirm={() => {
            deleteAnalysis(confirmModal.inputId);
            setConfirmModal(p => ({ ...p, isOpen: false }));
        }}
        title="Protocol Termination?"
        message={`Are you sure you want to permanently erase the archive entry for "${confirmModal.query}"? This action is irreversible.`}
        confirmText="Erase Archive"
        cancelText="Abort"
        variant="danger"
      />
    </div>
  );
};

// Internal minimal assets
const Bot = ({ className }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
);

export default DiscoveredProblems;