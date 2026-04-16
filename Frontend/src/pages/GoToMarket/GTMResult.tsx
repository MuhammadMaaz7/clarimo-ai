/**
 * Module 6: GTM Strategy Result View — Brand Purple Edition
 */

import {
  Megaphone, Target, MessageSquare, Calendar, TrendingUp,
  AlertTriangle, CheckCircle2, Download, Zap, Users,
  BarChart3, ArrowRight, Lightbulb, Radio
} from 'lucide-react';
import { PremiumCard } from '../../components/ui/premium/PremiumCard';
import { PremiumButton } from '../../components/ui/premium/PremiumButton';
import { motion } from 'framer-motion';

// ── Brand surface tokens
const surf = {
  card: 'bg-[#2d2048]/60 border-[#442754]/70',
  deep: 'bg-[#211c37]/60 border-[#442754]/50',
  elevated: 'bg-[#442754]/20 border-[#442754]/60',
};

const PRIORITY_BADGE: Record<string, string> = {
  high: 'bg-red-500/10 text-red-400 border-red-500/20',
  medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  low: 'bg-green-500/10 text-green-400 border-green-500/20',
};

const CATEGORY_BADGE: Record<string, string> = {
  paid: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  organic: 'bg-green-500/10 text-green-400 border-green-500/20',
  community: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  owned: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  outbound: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
  partnership: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

export default function GTMResult({ strategy, onReset }: { strategy: any; onReset: () => void }) {
  const handleDownload = () => {
    const lines = [
      'GO-TO-MARKET STRATEGY REPORT',
      `Generated: ${new Date(strategy.created_at).toLocaleString()}`,
      '='.repeat(60),
      '', 'EXECUTIVE SUMMARY', strategy.executive_summary,
      '', 'POSITIONING STATEMENT', strategy.positioning_statement,
      '', 'TARGET SEGMENT ANALYSIS', strategy.target_segment_analysis,
      '', 'COMPETITIVE DIFFERENTIATION', strategy.competitive_differentiation,
      '', 'MESSAGING GUIDE',
      `Headline: ${strategy.messaging_guide?.headline}`,
      `Tagline: ${strategy.messaging_guide?.tagline}`,
      `Elevator Pitch: ${strategy.messaging_guide?.elevator_pitch}`,
      `Tone: ${strategy.messaging_guide?.tone}`,
      `CTA: ${strategy.messaging_guide?.call_to_action}`,
      '', 'KEY MESSAGES',
      ...(strategy.messaging_guide?.key_messages || []).map((m: string) => `- ${m}`),
      '', 'CHANNEL RECOMMENDATIONS',
      ...(strategy.channel_recommendations || []).map(
        (c: any) => `[${c.priority.toUpperCase()}] ${c.channel} (${c.category})\n  ${c.rationale}`
      ),
      '', 'RISK FACTORS',
      ...(strategy.risk_factors || []).map((r: string) => `- ${r}`),
      '', 'SUCCESS METRICS',
      ...(strategy.success_metrics || []).map((m: string) => `- ${m}`),
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Clarimo_GTM_${strategy.gtm_id?.substring(0, 8)}.txt`;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  return (
    <div className="responsive-container-dashboard">
      <motion.div initial="hidden" animate="visible" variants={containerVariants} className="space-y-6">

        {/* Header */}
        <motion.div variants={itemVariants} className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="p-4 rounded-3xl bg-green-500/10 border border-green-500/20">
              <Megaphone className="h-9 w-9 text-green-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight text-white">Go-to-Market Strategy</h1>
              <p className="text-sm text-fuchsia-200/40 mt-1">Generated {new Date(strategy.created_at).toLocaleDateString()}</p>
            </div>
          </div>
          <div className="flex gap-3">
            <PremiumButton variant="outlined" onClick={handleDownload} className="gap-2">
              <Download className="h-4 w-4" /> Download Report
            </PremiumButton>
            <PremiumButton variant="ghost" onClick={onReset}>New Strategy</PremiumButton>
          </div>
        </motion.div>

        {/* Executive Summary + Insights */}
        <motion.div variants={itemVariants} className="grid gap-6 lg:grid-cols-3">
          <PremiumCard variant="default" className="lg:col-span-2 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-[0.03]"><Megaphone className="h-48 w-48" /></div>
            <div className="relative space-y-6">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold">Executive Summary</h2>
              </div>
              <p className="text-base leading-relaxed text-white/80">{strategy.executive_summary}</p>

              <div className="p-4 bg-[#211c37]/80 rounded-2xl border border-primary/20">
                <p className="text-[10px] font-black uppercase tracking-widest text-primary mb-2">Positioning Statement</p>
                <p className="italic text-sm leading-relaxed text-fuchsia-100/70">{strategy.positioning_statement}</p>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <h4 className="font-bold flex items-center gap-2 text-sm text-fuchsia-100/70"><Users className="h-4 w-4 text-blue-400" /> Target Segment</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">{strategy.target_segment_analysis}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-bold flex items-center gap-2 text-sm text-fuchsia-100/70"><Zap className="h-4 w-4 text-yellow-400" /> Differentiation</h4>
                  <p className="text-sm text-muted-foreground leading-relaxed">{strategy.competitive_differentiation}</p>
                </div>
              </div>
            </div>
          </PremiumCard>

          <PremiumCard variant="default">
            <div className="flex items-center gap-2 mb-6"><BarChart3 className="h-5 w-5 text-primary" /><h2 className="text-lg font-bold">Insights</h2></div>
            <div className="space-y-5">
              <div className="space-y-3">
                <h4 className="font-bold flex items-center gap-2 text-sm"><AlertTriangle className="h-4 w-4 text-orange-400" /> Risk Factors</h4>
                <ul className="space-y-2">
                  {(strategy.risk_factors || []).map((r: string, i: number) => (
                    <li key={i} className="text-sm flex gap-2 text-muted-foreground">
                      <span className="text-orange-400 shrink-0 font-black">!</span> {r}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="h-px bg-[#442754]/50" />
              <div className="space-y-3">
                <h4 className="font-bold flex items-center gap-2 text-sm"><TrendingUp className="h-4 w-4 text-green-400" /> Success Metrics</h4>
                <ul className="space-y-2">
                  {(strategy.success_metrics || []).map((m: string, i: number) => (
                    <li key={i} className="text-sm flex gap-2 text-muted-foreground">
                      <CheckCircle2 className="h-4 w-4 text-green-400 shrink-0 mt-0.5" /> {m}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </PremiumCard>
        </motion.div>

        {/* Channel Recommendations */}
        <motion.div variants={itemVariants}>
          <PremiumCard variant="default">
            <div className="flex items-center gap-2 mb-6"><Radio className="h-5 w-5 text-primary" /><h2 className="text-lg font-bold">Channel Recommendations</h2></div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {(strategy.channel_recommendations || []).map((ch: any, i: number) => (
                <div key={i} className={`p-4 rounded-2xl border ${surf.deep} hover:border-primary/30 hover:bg-[#2d2048]/50 transition-all space-y-3`}>
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-bold text-sm">{ch.channel}</span>
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded border ${PRIORITY_BADGE[ch.priority] || 'bg-muted/20 text-muted-foreground border-border'}`}>{ch.priority}</span>
                  </div>
                  <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded border ${CATEGORY_BADGE[ch.category] || 'bg-muted/20 text-muted-foreground border-border'}`}>{ch.category}</span>
                  <p className="text-xs text-muted-foreground leading-relaxed">{ch.rationale}</p>
                  <div className={`text-xs space-y-1 pt-2 border-t border-[#442754]/40`}>
                    <div className="flex justify-between"><span className="text-fuchsia-200/30">Reach</span><span className="font-medium text-fuchsia-100/70">{ch.estimated_reach}</span></div>
                    <div className="flex justify-between"><span className="text-fuchsia-200/30">Cost</span><span className="font-medium text-fuchsia-100/70">{ch.estimated_cost}</span></div>
                  </div>
                  <ul className="space-y-1">
                    {(ch.tactics || []).map((t: string, j: number) => (
                      <li key={j} className="text-xs flex gap-1.5 text-muted-foreground">
                        <ArrowRight className="h-3 w-3 shrink-0 mt-0.5 text-primary" /> {t}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </PremiumCard>
        </motion.div>

        {/* Messaging Guide */}
        <motion.div variants={itemVariants}>
          <MessagingGuideCard guide={strategy.messaging_guide} />
        </motion.div>

        {/* Campaign Roadmap */}
        <motion.div variants={itemVariants}>
          <CampaignRoadmapCard roadmap={strategy.campaign_roadmap} budget={strategy.inputs?.budget} />
        </motion.div>
      </motion.div>
    </div>
  );
}

// ── Messaging Guide ──────────────────────────────────────────────────────────

function MessagingGuideCard({ guide }: { guide: any }) {
  if (!guide) return null;
  return (
    <PremiumCard variant="default">
      <div className="flex items-center gap-2 mb-6"><MessageSquare className="h-5 w-5 text-primary" /><h2 className="text-lg font-bold">Messaging Guide</h2></div>
      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-4">
          <div className="p-4 bg-[#211c37]/80 rounded-2xl border border-primary/20">
            <p className="text-[10px] font-black uppercase tracking-widest text-primary mb-2">Headline</p>
            <p className="text-xl font-bold text-white">{guide.headline}</p>
          </div>
          <div className={`p-4 rounded-2xl border ${surf.deep}`}>
            <p className="text-[10px] font-black uppercase tracking-widest text-fuchsia-200/40 mb-2">Tagline</p>
            <p className="font-medium italic text-fuchsia-100/80">{guide.tagline}</p>
          </div>
          <div className={`p-4 rounded-2xl border ${surf.deep}`}>
            <p className="text-[10px] font-black uppercase tracking-widest text-fuchsia-200/40 mb-2">Elevator Pitch</p>
            <p className="text-sm leading-relaxed text-fuchsia-100/70">{guide.elevator_pitch}</p>
          </div>
          <div className={`flex items-center gap-3 p-3 rounded-2xl border ${surf.deep}`}>
            <span className="text-[10px] font-black uppercase tracking-widest text-fuchsia-200/40">Tone:</span>
            <span className="text-sm font-semibold text-fuchsia-100/80">{guide.tone}</span>
          </div>
        </div>
        <div className="space-y-4">
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-fuchsia-200/40 mb-3">Key Messages</p>
            <ul className="space-y-2">
              {(guide.key_messages || []).map((m: string, i: number) => (
                <li key={i} className={`text-sm flex gap-2 p-3 rounded-xl border ${surf.deep}`}>
                  <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" /><span className="text-fuchsia-100/70">{m}</span>
                </li>
              ))}
            </ul>
          </div>
          {guide.differentiators?.length > 0 && (
            <div>
              <p className="text-[10px] font-black uppercase tracking-widest text-fuchsia-200/40 mb-3">Differentiators</p>
              <ul className="space-y-1.5">
                {guide.differentiators.map((d: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2 text-muted-foreground">
                    <Zap className="h-4 w-4 text-yellow-400 shrink-0 mt-0.5" /> {d}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="p-4 bg-[#211c37]/80 rounded-2xl border border-primary/30">
            <p className="text-[10px] font-black uppercase tracking-widest text-primary mb-1">Call to Action</p>
            <p className="font-bold text-primary">{guide.call_to_action}</p>
          </div>
        </div>
      </div>
    </PremiumCard>
  );
}

// ── Campaign Roadmap ─────────────────────────────────────────────────────────

const PHASE_COLORS = [
  { bg: 'bg-violet-500/10', border: 'border-violet-500/20', text: 'text-violet-300', dot: 'bg-violet-500/20' },
  { bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-300', dot: 'bg-blue-500/20' },
  { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-300', dot: 'bg-orange-500/20' },
  { bg: 'bg-green-500/10', border: 'border-green-500/20', text: 'text-green-300', dot: 'bg-green-500/20' },
];

function CampaignRoadmapCard({ roadmap, budget }: { roadmap: any[]; budget?: number }) {
  if (!roadmap?.length) return null;
  return (
    <PremiumCard variant="default">
      <div className="flex items-center gap-2 mb-6"><Calendar className="h-5 w-5 text-primary" /><h2 className="text-lg font-bold">Campaign Roadmap</h2></div>
      <div className="space-y-4">
        {roadmap.map((phase: any, i: number) => {
          const color = PHASE_COLORS[i % PHASE_COLORS.length];
          return (
            <div key={i} className={`p-5 rounded-2xl border ${color.border} ${color.bg} transition-all`}>
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div className={`h-9 w-9 rounded-xl ${color.dot} flex items-center justify-center font-black text-sm ${color.text} border ${color.border}`}>{i + 1}</div>
                  <div>
                    <p className={`font-bold ${color.text}`}>{phase.phase}</p>
                    <p className="text-xs text-fuchsia-200/40">Weeks {phase.week_start}–{phase.week_end}</p>
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {budget && <span className={`text-[10px] font-black px-2 py-1 rounded-lg border ${color.border} ${color.text}`}>${Math.round(budget * phase.budget_allocation_pct).toLocaleString()}</span>}
                  <span className="text-[10px] font-black px-2 py-1 rounded-lg border border-[#442754]/60 text-fuchsia-200/40">{Math.round(phase.budget_allocation_pct * 100)}% of budget</span>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mb-4 leading-relaxed">{phase.objective}</p>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-fuchsia-200/30 mb-2">Activities</p>
                  <ul className="space-y-1">
                    {(phase.activities || []).map((a: string, j: number) => (
                      <li key={j} className="text-xs flex gap-2 text-muted-foreground"><ArrowRight className="h-3 w-3 shrink-0 mt-0.5 text-primary" />{a}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-widest text-fuchsia-200/30 mb-2">KPIs</p>
                  <ul className="space-y-1">
                    {(phase.kpis || []).map((k: string, j: number) => (
                      <li key={j} className="text-xs flex gap-2 text-muted-foreground"><BarChart3 className="h-3 w-3 shrink-0 mt-0.5 text-green-400" />{k}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </PremiumCard>
  );
}
