/**
 * Module 5: Launch Planning Assistant — Brand Purple Edition
 * Simplified Standalone Experience
 */

import { useState } from 'react';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import {
  Rocket, Calendar, CheckCircle2, AlertTriangle,
  PieChart, ListTodo, TrendingUp, Brain,
  Check, Target, Download, Loader2
} from 'lucide-react';
import { api } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { PremiumCard } from '../../components/ui/premium/PremiumCard';
import { PremiumButton } from '../../components/ui/premium/PremiumButton';
import { motion } from 'framer-motion';
import { ModuleHeader } from '../../components/ui/ModuleHeader';

export default function LaunchPlanning() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [formData, setFormData] = useState({
    idea_description: '',
    target_audience: '',
    product_stage: 'idea',
    estimated_budget: 5000,
    team_size: 1,
    target_market: '',
    expected_timeline_months: 6,
  });

  const handleSubmit = async () => {
    if (!formData.idea_description) { 
      toast.error('Please provide an idea description.'); 
      return; 
    }
    setLoading(true);
    try {
      const response = await api.launchPlanning.createPlan({ ...formData, user_id: user?.id });
      setResult(response);
      toast.success('Launch plan generated!');
    } catch (err) {
      toast.error('Failed to generate launch plan. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (result) return <LaunchPlanResult plan={result} onReset={() => setResult(null)} />;

  const f = (key: string, value: any) => setFormData((p) => ({ ...p, [key]: value }));

  return (
    <div className="responsive-container-dashboard">
      <div className="max-w-5xl mx-auto space-y-8">
        <ModuleHeader
          icon={Rocket}
          title="Launch Planning"
          description="Transition from idea to execution with a structured AI-powered plan. Define your roadmap, milestones, and resource allocation."
          iconBgClassName="bg-orange-500/10 border-orange-500/20 shadow-orange-500/5"
          iconClassName="text-orange-400"
        />

        <PremiumCard variant="default">
          <div className="grid gap-5 md:grid-cols-2">
            <div className="md:col-span-2 space-y-1.5">
              <label className="brand-label">Startup Idea & Description *</label>
              <Textarea 
                className="brand-textarea min-h-[90px]" 
                placeholder="Describe your startup idea in detail..." 
                value={formData.idea_description} 
                onChange={(e) => f('idea_description', e.target.value)} 
                disabled={loading} 
              />
            </div>
            <div className="space-y-1.5">
              <label className="brand-label">Product Stage</label>
              <Select value={formData.product_stage} onValueChange={(v) => f('product_stage', v)} disabled={loading}>
                <SelectTrigger className="brand-input"><SelectValue placeholder="Select stage" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="idea">Idea / Concept</SelectItem>
                  <SelectItem value="prototype">Prototype / Design</SelectItem>
                  <SelectItem value="mvp">MVP Build</SelectItem>
                  <SelectItem value="beta">Beta / Soft Launch</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="brand-label">Target Market</label>
              <Input 
                className="brand-input" 
                placeholder="e.g. US SaaS market" 
                value={formData.target_market} 
                onChange={(e) => f('target_market', e.target.value)} 
                disabled={loading} 
              />
            </div>
            <div className="space-y-1.5">
              <label className="brand-label">Estimated Budget ($)</label>
              <Input 
                type="number" 
                className="brand-input" 
                value={formData.estimated_budget} 
                onChange={(e) => f('estimated_budget', parseInt(e.target.value))} 
                disabled={loading} 
              />
            </div>
            <div className="space-y-1.5">
              <label className="brand-label">Team Size</label>
              <Input 
                type="number" 
                className="brand-input" 
                value={formData.team_size} 
                onChange={(e) => f('team_size', parseInt(e.target.value))} 
                disabled={loading} 
              />
            </div>
            <div className="md:col-span-2 space-y-1.5">
              <label className="brand-label">Timeline (Months)</label>
              <Input 
                type="number" 
                className="brand-input" 
                value={formData.expected_timeline_months} 
                onChange={(e) => f('expected_timeline_months', parseInt(e.target.value))} 
                disabled={loading} 
              />
            </div>
          </div>

          <div className="mt-6">
            <PremiumButton 
              size="lg" 
              variant="accent" 
              className="w-full h-12 text-lg font-bold" 
              onClick={handleSubmit} 
              loading={loading}
            >
              {loading ? 'Processing...' : 'Generate Launch Plan'}
            </PremiumButton>
          </div>
        </PremiumCard>
      </div>
    </div>
  );
}

// ── Result View ───────────────────────────────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } }
};
const itemVariants = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } };

function LaunchPlanResult({ plan, onReset }: { plan: any; onReset: () => void }) {
  const handleDownload = () => {
    const c = [
      'LAUNCH PLAN REPORT', `Generated: ${new Date(plan.created_at).toLocaleString()}`, '='.repeat(60),
      '', 'EXECUTIVE SUMMARY', plan.executive_summary,
      '', `READINESS SCORE: ${Math.round(plan.readiness_score)}/100`,
      `RECOMMENDATION: ${plan.launch_timing_recommendation}`,
      '', 'BUDGET ALLOCATION:', ...plan.budget_allocation.map((b: any) => `- ${b.category}: $${b.amount} (${b.percentage}%)`),
      '', 'TIMELINE:', ...plan.timeline.map((m: any) => `- ${m.title} (${m.duration_weeks} weeks): ${m.description}`),
      '', 'CHECKLIST:', ...plan.checklist.map((c: any) => `[ ] ${c.task} (${c.priority})`),
    ].join('\n');
    const blob = new Blob([c], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `Clarimo_Launch_Plan_${plan.plan_id?.substring(0, 8)}.txt`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  const score = Math.round(plan.readiness_score);
  const scoreColor = score >= 70 ? 'text-green-400' : score >= 45 ? 'text-yellow-400' : 'text-red-400';
  const scoreBg = score >= 70 ? 'bg-green-500/10 border-green-500/20' : score >= 45 ? 'bg-yellow-500/10 border-yellow-500/20' : 'bg-red-500/10 border-red-500/20';

  return (
    <div className="responsive-container-dashboard">
      <motion.div initial="hidden" animate="visible" variants={containerVariants} className="max-w-6xl mx-auto space-y-6">

        {/* Header */}
        <motion.div variants={itemVariants} className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="p-4 rounded-3xl bg-orange-500/10 border border-orange-500/20">
              <Rocket className="h-9 w-9 text-orange-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight text-white">Launch Strategy</h1>
              <p className="text-sm text-fuchsia-200/40 mt-1">Generated {new Date(plan.created_at).toLocaleDateString()}</p>
            </div>
          </div>
          <div className="flex gap-3">
            <PremiumButton variant="outlined" onClick={handleDownload} className="gap-2"><Download className="h-4 w-4" /> Download</PremiumButton>
            <PremiumButton variant="ghost" onClick={onReset}>Generate Another</PremiumButton>
          </div>
        </motion.div>

        {/* Summary + Budget */}
        <motion.div variants={itemVariants} className="grid gap-6 lg:grid-cols-3">
          <PremiumCard variant="default" className="lg:col-span-2 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-[0.03]"><Rocket className="h-48 w-48" /></div>
            <div className="relative space-y-6">
              <div className="flex items-center gap-2"><Brain className="h-5 w-5 text-primary" /><h2 className="text-lg font-bold">Executive Summary</h2></div>
              <div className={`flex items-center gap-5 p-4 rounded-2xl border ${scoreBg}`}>
                <div className="text-center">
                  <span className={`text-5xl font-black ${scoreColor}`}>{score}</span>
                  <p className="text-[10px] font-black uppercase tracking-widest text-fuchsia-200/30 mt-0.5">Readiness</p>
                </div>
                <div className="h-12 w-px bg-[#442754]/60" />
                <p className="text-sm font-semibold text-white/80">{plan.launch_timing_recommendation}</p>
              </div>
              <p className="text-base leading-relaxed text-white/80">{plan.executive_summary}</p>
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <h4 className="font-bold flex items-center gap-2 text-sm"><AlertTriangle className="h-4 w-4 text-orange-400" /> Key Risks</h4>
                  <ul className="space-y-2">
                    {plan.risk_factors.map((risk: string, i: number) => (
                      <li key={i} className="text-sm flex gap-2 text-muted-foreground"><span className="text-orange-400 shrink-0 font-black">!</span>{risk}</li>
                    ))}
                  </ul>
                </div>
                <div className="space-y-3">
                  <h4 className="font-bold flex items-center gap-2 text-sm"><TrendingUp className="h-4 w-4 text-green-400" /> Success Metrics</h4>
                  <ul className="space-y-2">
                    {plan.success_metrics.map((m: string, i: number) => (
                      <li key={i} className="text-sm flex gap-2 text-muted-foreground"><CheckCircle2 className="h-4 w-4 text-green-400 shrink-0 mt-0.5" />{m}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </PremiumCard>

          <PremiumCard variant="default">
            <div className="flex items-center gap-2 mb-6"><PieChart className="h-5 w-5 text-primary" /><h2 className="text-lg font-bold">Budget Allocation</h2></div>
            <div className="space-y-4">
              {plan.budget_allocation.map((item: any, i: number) => (
                <div key={i} className="space-y-1.5">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold text-fuchsia-100/80">{item.category}</span>
                    <span className="text-muted-foreground">${item.amount.toLocaleString()}</span>
                  </div>
                  <div className="h-1.5 w-full bg-[#211c37] rounded-full overflow-hidden border border-[#442754]/30">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${item.percentage}%` }}
                      transition={{ duration: 0.8, delay: i * 0.1, ease: 'easeOut' }}
                      className="h-full gradient-primary rounded-full"
                    />
                  </div>
                </div>
              ))}
              <div className="pt-4 mt-2 border-t border-[#442754]/50 flex justify-between items-center">
                <span className="text-sm font-bold text-fuchsia-100/60">Total</span>
                <span className="text-xl font-black text-primary">${plan.budget_allocation.reduce((a: number, b: any) => a + b.amount, 0).toLocaleString()}</span>
              </div>
            </div>
          </PremiumCard>
        </motion.div>

        {/* Timeline */}
        <motion.div variants={itemVariants}>
          <PremiumCard variant="default">
            <div className="flex items-center gap-2 mb-8"><Calendar className="h-5 w-5 text-primary" /><h2 className="text-lg font-bold">Launch Timeline</h2></div>
            <div className="relative space-y-8 before:absolute before:inset-0 before:ml-5 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-primary before:via-[#442754] before:to-transparent">
              {plan.timeline.map((milestone: any, i: number) => (
                <div key={i} className="relative flex items-start gap-5 group">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 text-primary font-black text-sm z-10">{i + 1}</div>
                  <div className="flex-1 p-5 rounded-2xl border border-[#442754]/60 bg-[#211c37]/40 hover:border-primary/25 transition-all">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-white">{milestone.title}</span>
                      <span className="text-xs font-black text-primary bg-primary/10 px-2 py-1 rounded-lg border border-primary/20">{milestone.duration_weeks} Weeks</span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-4 leading-relaxed">{milestone.description}</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {milestone.tasks.map((task: string, j: number) => (
                        <div key={j} className="text-xs flex items-center gap-2 py-1.5 px-3 bg-[#211c37]/80 rounded-lg border border-[#442754]/40 text-fuchsia-100/60">
                          <Check className="h-3 w-3 text-green-400 shrink-0" /> {task}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </PremiumCard>
        </motion.div>

        {/* Checklist */}
        <motion.div variants={itemVariants}>
          <PremiumCard variant="default">
            <div className="flex items-center gap-2 mb-6"><ListTodo className="h-5 w-5 text-primary" /><h2 className="text-lg font-bold">Launch Checklist</h2></div>
            <div className="space-y-2">
              {plan.checklist.map((item: any, i: number) => {
                const pc = item.priority === 'high' ? 'text-red-400 border-red-500/20 bg-red-500/5'
                  : item.priority === 'medium' ? 'text-yellow-400 border-yellow-500/20 bg-yellow-500/5'
                  : 'text-blue-400 border-blue-500/20 bg-blue-500/5';
                return (
                  <div key={i} className="flex gap-3 p-4 rounded-2xl border border-[#442754]/50 bg-[#211c37]/40 items-start group">
                    <div className="h-5 w-5 mt-0.5 shrink-0 rounded border-2 border-primary/30 group-hover:border-primary transition-colors" />
                    <div className="flex-1 space-y-1.5">
                      <p className="text-sm font-medium text-fuchsia-100/80">{item.task}</p>
                      <div className="flex gap-2">
                        <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded border border-[#442754]/40 text-fuchsia-200/30">{item.category}</span>
                        <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded border ${pc}`}>{item.priority}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </PremiumCard>
        </motion.div>
      </motion.div>
    </div>
  );
}
