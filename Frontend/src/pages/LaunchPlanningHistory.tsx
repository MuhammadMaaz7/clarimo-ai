import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Rocket, History, Plus, Search, Calendar, Target, DollarSign } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import api from '../lib/api';
import { motion } from 'framer-motion';

export default function LaunchPlanningHistory() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [plans, setPlans] = useState<any[]>([]);
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
      const result = await api.launchPlanning.getHistory(user!.id);
      setPlans(result);
    } catch (error: any) {
      console.error('Failed to load launch planning history:', error);
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

  const filteredPlans = plans.filter((plan) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    const desc = plan.inputs?.idea_description?.toLowerCase() || '';
    return desc.includes(query);
  });

  if (loading) {
    return (
      <div className="container mx-auto px-6 py-12">
        <div className="flex flex-col items-center justify-center py-20 space-y-4 opacity-50">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
          <p className="text-sm">Retrieving launch records...</p>
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
              <div className="p-3 bg-orange-500/10 rounded-2xl">
                <Rocket className="h-8 w-8 text-orange-500" />
              </div>
              Launch History
            </h1>
            <p className="text-muted-foreground text-lg">
              Review and iterate on your previously generated launch roadmaps.
            </p>
          </div>
          <Button
            onClick={() => navigate('/launch-planning')}
            size="lg"
            className="h-14 px-8 bg-orange-500 hover:bg-orange-600 text-white font-bold rounded-2xl shadow-lg shadow-orange-500/20 transition-all hover:scale-[1.02]"
          >
            <Plus className="mr-2 h-5 w-5" />
            New Launch Plan
          </Button>
        </div>

        {/* Filters */}
        {plans.length > 0 && (
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search by idea description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-14 pl-12 bg-white/5 border-white/10 rounded-2xl focus:border-orange-500/50 transition-all text-lg"
            />
          </div>
        )}

        {/* Content */}
        {filteredPlans.length === 0 ? (
          <Card className="bg-white/[0.02] border-white/5 border-dashed rounded-[2.5rem]">
            <CardContent className="py-24 text-center">
              <div className="max-w-md mx-auto space-y-6">
                <div className="p-6 bg-white/5 rounded-full w-fit mx-auto">
                  <History className="h-12 w-12 text-muted-foreground opacity-20" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-2xl font-bold text-white">No Launch Plans Found</h3>
                  <p className="text-muted-foreground">
                    {searchQuery 
                      ? "We couldn't find any plans matching your search criteria."
                      : "You haven't generated any launch plans yet. Start planning your startup journey today."}
                  </p>
                </div>
                {!searchQuery && (
                  <Button
                    onClick={() => navigate('/launch-planning')}
                    variant="outline"
                    className="h-12 border-white/10 hover:bg-white/5"
                  >
                    Generate First Plan
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6">
            {filteredPlans.map((plan, idx) => (
              <motion.div
                key={plan.plan_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                <Card 
                  className="bg-white/[0.02] border-white/5 hover:border-orange-500/30 hover:bg-white/[0.04] transition-all duration-300 rounded-[2rem] overflow-hidden group cursor-pointer"
                  onClick={() => navigate(`/launch-planning?id=${plan.plan_id}`)}
                >
                  <CardContent className="p-8">
                    <div className="flex flex-col lg:flex-row gap-8">
                      {/* Visual Indicator */}
                      <div className="flex-1 space-y-6">
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <div className="flex items-center gap-3">
                                <span className="px-3 py-1 bg-orange-500/10 text-orange-400 text-[10px] font-black uppercase tracking-widest rounded-full border border-orange-500/20">
                                  {plan.product_stage || plan.inputs?.product_stage}
                                </span>
                                <span className="text-xs text-muted-foreground flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {formatDate(plan.created_at)}
                                </span>
                            </div>
                            <h3 className="text-xl font-bold text-white group-hover:text-orange-400 transition-colors line-clamp-1 mt-3">
                              {plan.inputs?.idea_description || 'Untitled Launch Plan'}
                            </h3>
                          </div>
                          <div className="text-right">
                             <div className="text-3xl font-black text-white">{plan.readiness_score}%</div>
                             <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-tighter">Readiness</div>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-white/5">
                           <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Budget</p>
                              <p className="text-sm font-bold text-white flex items-center gap-1">
                                <DollarSign className="h-3 w-3 text-green-500" />
                                {(plan.inputs?.estimated_budget || 0).toLocaleString()}
                              </p>
                           </div>
                           <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Timeline</p>
                              <p className="text-sm font-bold text-white">
                                {plan.inputs?.expected_timeline_months} Months
                              </p>
                           </div>
                           <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Team</p>
                              <p className="text-sm font-bold text-white">
                                {plan.inputs?.team_size} Members
                              </p>
                           </div>
                           <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Tasks</p>
                              <p className="text-sm font-bold text-white">
                                {plan.checklist?.length || 0} Actions
                              </p>
                           </div>
                        </div>
                      </div>

                      {/* Summary Section */}
                      <div className="lg:w-1/3 p-6 bg-white/[0.03] rounded-3xl border border-white/5 space-y-3">
                         <div className="flex items-center gap-2 text-xs font-bold text-white/60">
                            <Target className="h-3 w-3" />
                            EXECUTIVE SUMMARY
                         </div>
                         <p className="text-sm text-muted-foreground leading-relaxed line-clamp-4">
                            {plan.executive_summary}
                         </p>
                         <Button
                          variant="ghost"
                          className="w-full text-xs font-bold text-orange-400 hover:text-orange-300 hover:bg-orange-400/5 mt-2"
                         >
                            View Full Roadmap
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
