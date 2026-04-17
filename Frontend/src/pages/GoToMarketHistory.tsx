import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Target, History, Plus, Search, Calendar, BadgeCheck, DollarSign, Globe } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import { motion } from 'framer-motion';

export default function GoToMarketHistory() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [strategies, setStrategies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (user?.id) {
      loadHistory();
    }
  }, [user]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const result = await api.gtm.getHistory(user!.id);
      setStrategies(result);
    } catch (error: any) {
      console.error('Failed to load GTM history:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const filteredStrategies = strategies.filter((strategy) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    const desc = strategy.inputs?.startup_description?.toLowerCase() || '';
    return desc.includes(query);
  });

  if (loading) {
    return (
      <div className="container mx-auto px-6 py-12">
        <div className="flex flex-col items-center justify-center py-20 space-y-4 opacity-50">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
          <p className="text-sm">Fetching GTM archives...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-12 max-w-6xl">
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <h1 className="text-4xl font-black tracking-tight text-white flex items-center gap-4">
              <div className="p-3 bg-blue-500/10 rounded-2xl">
                <Target className="h-8 w-8 text-blue-500" />
              </div>
              GTM Archives
            </h1>
            <p className="text-muted-foreground text-lg">
              Historical Go-to-Market strategies and channel optimization logs.
            </p>
          </div>
          <Button
            onClick={() => navigate('/go-to-market')}
            size="lg"
            className="h-14 px-8 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/20 transition-all hover:scale-[1.02]"
          >
            <Plus className="mr-2 h-5 w-5" />
            New Strategy
          </Button>
        </div>

        {/* Filters */}
        {strategies.length > 0 && (
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search by startup description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-14 pl-12 bg-white/5 border-white/10 rounded-2xl focus:border-blue-500/50 transition-all text-lg"
            />
          </div>
        )}

        {/* Content */}
        {filteredStrategies.length === 0 ? (
          <Card className="bg-white/[0.02] border-white/5 border-dashed rounded-[2.5rem]">
            <CardContent className="py-24 text-center">
              <div className="max-w-md mx-auto space-y-6">
                <div className="p-6 bg-white/5 rounded-full w-fit mx-auto">
                  <History className="h-12 w-12 text-muted-foreground opacity-20" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-2xl font-bold text-white">No Strategies Found</h3>
                  <p className="text-muted-foreground">
                    {searchQuery 
                      ? "No archival records match your search criteria."
                      : "Your GTM vault is currently empty. Define your market entry strategy to see it here."}
                  </p>
                </div>
                {!searchQuery && (
                  <Button
                    onClick={() => navigate('/go-to-market')}
                    variant="outline"
                    className="h-12 border-white/10 hover:bg-white/5"
                  >
                    Build GTM Strategy
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {filteredStrategies.map((strategy, idx) => (
              <motion.div
                key={strategy.gtm_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                <Card 
                  className="bg-white/[0.02] border-white/5 hover:border-blue-500/30 hover:bg-white/[0.04] transition-all duration-300 rounded-[2rem] overflow-hidden group cursor-pointer"
                  onClick={() => navigate(`/go-to-market?id=${strategy.gtm_id}`)}
                >
                  <CardContent className="p-8">
                    <div className="flex flex-col lg:flex-row gap-8">
                      {/* Main Info */}
                      <div className="flex-1 space-y-6">
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <div className="flex items-center gap-3">
                                <span className="px-3 py-1 bg-blue-500/10 text-blue-400 text-[10px] font-black uppercase tracking-widest rounded-full border border-blue-500/20">
                                  {strategy.inputs?.business_model || 'Strategy'}
                                </span>
                                <span className="text-xs text-muted-foreground flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {formatDate(strategy.created_at)}
                                </span>
                            </div>
                            <h3 className="text-xl font-bold text-white group-hover:text-blue-400 transition-colors line-clamp-1 mt-3">
                              {strategy.inputs?.startup_description || 'Untitled GTM Strategy'}
                            </h3>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-white/5">
                           <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Budget</p>
                              <p className="text-sm font-bold text-white flex items-center gap-1">
                                <DollarSign className="h-3 w-3 text-green-500" />
                                {(strategy.inputs?.budget || 0).toLocaleString()}
                              </p>
                           </div>
                           <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Channels</p>
                              <p className="text-sm font-bold text-white flex items-center gap-1">
                                <Globe className="h-3 w-3 text-blue-400" />
                                {strategy.channel_recommendations?.length || 0} Recommended
                              </p>
                           </div>
                           <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Timeline</p>
                              <p className="text-sm font-bold text-white">
                                {strategy.inputs?.launch_date_weeks} Weeks
                              </p>
                           </div>
                           <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Focus</p>
                              <p className="text-sm font-bold text-white truncate">
                                {strategy.inputs?.target_audience}
                              </p>
                           </div>
                        </div>
                      </div>

                      {/* Messaging Sneak Peek */}
                      <div className="lg:w-1/3 p-6 bg-white/[0.03] rounded-3xl border border-white/5 space-y-3">
                         <div className="flex items-center gap-2 text-xs font-bold text-white/60">
                            <BadgeCheck className="h-3 w-3" />
                            CORE POSITIONING
                         </div>
                         <p className="text-sm text-muted-foreground leading-relaxed line-clamp-4 italic">
                            "{strategy.positioning_statement || strategy.messaging_guide?.elevator_pitch}"
                         </p>
                         <Button
                          variant="ghost"
                          className="w-full text-xs font-bold text-blue-400 hover:text-blue-300 hover:bg-blue-400/5 mt-2"
                         >
                            Deep Dive Strategy
                         </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
