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
  Trash2, 
  Search, 
  Plus, 
  Layers,
  Activity,
  Zap
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
      transition: { duration: 0.6, staggerChildren: 0.05 } 
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-6 py-20">
        <div className="flex flex-col items-center justify-center space-y-4 opacity-50">
          <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary border-t-transparent" />
          <p className="text-sm font-bold tracking-widest uppercase">Synchronizing Archives...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-12 max-w-6xl">
       <motion.div initial="hidden" animate="visible" variants={containerVariants} className="space-y-10">
        
        {/* Header - Unified Style */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-4xl font-black tracking-tight text-white flex items-center gap-4">
              <div className="p-3 bg-primary/10 rounded-2xl">
                <Layers className="h-8 w-8 text-primary" />
              </div>
              Problem discovery History
            </h1>
            <p className="text-muted-foreground text-lg">
              Historical intelligence gathered from global digital communities and pain-point signals.
            </p>
          </div>
          <PremiumButton
            onClick={() => navigate('/problem-discovery')}
            className="h-14 px-8 rounded-2xl shadow-primary/20 hover:scale-[1.02]"
          >
            <Plus className="mr-2 h-5 w-5" />
            New Discovery Probe
          </PremiumButton>
        </div>

        {/* Filters - Unified Style */}
        {history.length > 0 && (
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search semantic archives by query..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-14 pl-12 bg-white/5 border-white/10 rounded-2xl focus:border-primary/50 transition-all text-lg"
            />
          </div>
        )}

        {/* Stats Grid - Unified Style */}
        {stats && !searchQuery && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
                { label: 'Analyses', val: stats.total_analyses, icon: BarChart3, color: 'text-blue-400', bg: 'bg-blue-400/5' },
                { label: 'Signals', val: stats.total_pain_points, icon: Zap, color: 'text-green-400', bg: 'bg-green-400/5' },
                { label: 'Themes', val: stats.total_clusters, icon: History, color: 'text-purple-400', bg: 'bg-purple-400/5' },
                { label: 'Last Sync', val: stats.latest_analysis ? new Date(stats.latest_analysis).toLocaleDateString() : 'Never', icon: Activity, color: 'text-orange-400', bg: 'bg-orange-400/5' }
            ].map((stat, i) => (
                <div key={i} className="p-4 rounded-3xl bg-white/[0.02] border border-white/5 flex items-center gap-3">
                   <div className={`p-2 rounded-xl ${stat.bg} ${stat.color}`}>
                      <stat.icon className="h-4 w-4" />
                   </div>
                   <div>
                      <p className="text-lg font-black text-white leading-none">{stat.val}</p>
                      <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground mt-1">{stat.label}</p>
                   </div>
                </div>
            ))}
          </div>
        )}

        {/* Content - Unified List Layout */}
        <AnimatePresence mode="popLayout">
          {filteredHistory.length === 0 ? (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <PremiumCard variant="glass" className="py-24 text-center border-dashed border-white/10">
                <div className="max-w-md mx-auto space-y-6">
                  <div className="p-6 bg-white/5 rounded-full w-fit mx-auto">
                    <History className="h-12 w-12 text-muted-foreground opacity-20" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-2xl font-bold text-white">Archives Empty</h3>
                    <p className="text-muted-foreground">
                      {searchQuery 
                        ? "We couldn't find any probe results matching your search criteria."
                        : "You haven't initiated any problem discovery probes yet."}
                    </p>
                  </div>
                  {!searchQuery && (
                    <PremiumButton
                      onClick={() => navigate('/problem-discovery')}
                      variant="outlined"
                      className="h-12 border-white/10 hover:bg-white/5"
                    >
                      Start First Probe
                    </PremiumButton>
                  )}
                </div>
              </PremiumCard>
            </motion.div>
          ) : (
            <div className="grid gap-6">
              {filteredHistory.map((item) => (
                <motion.div
                  key={item.input_id}
                  variants={itemVariants}
                  layout
                >
                  <CardWrapper 
                    onClick={() => navigate(`/analysis/${item.input_id}`)}
                  >
                    <div className="flex flex-col lg:flex-row gap-8">
                       {/* Main Info */}
                       <div className="flex-1 space-y-6">
                         <div className="flex items-start justify-between">
                            <div className="space-y-1">
                               <div className="flex items-center gap-3">
                                  <span className="px-3 py-1 bg-primary/10 text-primary text-[10px] font-black uppercase tracking-widest rounded-full border border-primary/20">
                                    Probe #{item.input_id.slice(0, 8)}
                                  </span>
                                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                                    <Calendar className="h-3 w-3" />
                                    {formatDate(item.created_at)}
                                  </span>
                               </div>
                               <h3 className="text-2xl font-bold text-white group-hover:text-primary transition-colors line-clamp-2 mt-3 leading-tight">
                                 "{item.original_query}"
                               </h3>
                            </div>
                         </div>

                         <div className="grid grid-cols-2 md:grid-cols-3 gap-6 pt-6 border-t border-white/5">
                            <div className="space-y-1">
                               <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Pain Signals</p>
                               <p className="text-2xl font-black text-white flex items-center gap-2">
                                 <Zap className="h-5 w-5 text-green-400" />
                                 {item.pain_points_count}
                               </p>
                            </div>
                            <div className="space-y-1">
                               <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Macro Themes</p>
                               <p className="text-2xl font-black text-white flex items-center gap-2">
                                 <Layers className="h-5 w-5 text-purple-400" />
                                 {item.total_clusters}
                               </p>
                            </div>
                            <div className="space-y-1 hidden md:block">
                               <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Status</p>
                               <p className="text-sm font-bold text-blue-400 flex items-center gap-2">
                                 <Activity className="h-4 w-4" />
                                 Analysis Finalized
                               </p>
                            </div>
                         </div>
                       </div>

                       {/* Action Section */}
                       <div className="lg:w-1/3 flex flex-col gap-3">
                          <PremiumButton 
                            className="w-full h-full min-h-[100px] flex flex-col items-center justify-center gap-2"
                            onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/analysis/${item.input_id}`);
                            }}
                          >
                             <ExternalLink className="h-6 w-6" />
                             <span className="text-xs font-black uppercase tracking-widest">Deep Dive Intel</span>
                          </PremiumButton>
                          <div className="flex gap-3">
                             <PremiumButton 
                                variant="outlined" 
                                className="flex-1 h-12 border-white/5 hover:border-red-500/50 hover:bg-red-500/10 text-red-400/60 hover:text-red-400 transition-all"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    openDeleteConfirmation(item.input_id, item.original_query);
                                }}
                             >
                                <Trash2 className="h-4 w-4 mr-2" />
                                <span className="text-[10px] font-black uppercase tracking-widest">Erase</span>
                             </PremiumButton>
                          </div>
                       </div>
                    </div>
                  </CardWrapper>
                </motion.div>
              ))}
            </div>
          )}
        </AnimatePresence>
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

// Internal sub-component for unified card style
const CardWrapper = ({ children, onClick }: { children: React.ReactNode; onClick: () => void }) => (
  <div 
    onClick={onClick}
    className="bg-white/[0.02] border border-white/5 hover:border-primary/40 hover:bg-white/[0.04] transition-all duration-300 rounded-[2.5rem] overflow-hidden group cursor-pointer p-8 md:p-10"
  >
    {children}
  </div>
);

export default DiscoveredProblems;