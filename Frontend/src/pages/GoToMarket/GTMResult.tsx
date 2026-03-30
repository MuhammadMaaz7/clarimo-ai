/**
 * Module 6: GTM Strategy Result View
 * Displays channels, messaging guide, campaign roadmap, and insights.
 */

import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import {
  Megaphone, Target, MessageSquare, Calendar, TrendingUp,
  AlertTriangle, CheckCircle2, Download, Zap, Users,
  BarChart3, ArrowRight, Lightbulb, Radio
} from 'lucide-react';

// ── Priority / Category color maps ──────────────────────────────────────────

const PRIORITY_BADGE: Record<string, string> = {
  high: 'bg-red-500/15 text-red-400 border-red-500/30',
  medium: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
  low: 'bg-green-500/15 text-green-400 border-green-500/30',
};

const CATEGORY_BADGE: Record<string, string> = {
  paid: 'bg-purple-500/15 text-purple-400',
  organic: 'bg-green-500/15 text-green-400',
  community: 'bg-blue-500/15 text-blue-400',
  owned: 'bg-orange-500/15 text-orange-400',
  outbound: 'bg-pink-500/15 text-pink-400',
  partnership: 'bg-cyan-500/15 text-cyan-400',
};

// ── Main Component ───────────────────────────────────────────────────────────

export default function GTMResult({ strategy, onReset }: { strategy: any; onReset: () => void }) {
  const handleDownload = () => {
    const lines = [
      'GO-TO-MARKET STRATEGY REPORT',
      `Generated: ${new Date(strategy.created_at).toLocaleString()}`,
      '='.repeat(60),
      '',
      'EXECUTIVE SUMMARY',
      strategy.executive_summary,
      '',
      'POSITIONING STATEMENT',
      strategy.positioning_statement,
      '',
      'TARGET SEGMENT ANALYSIS',
      strategy.target_segment_analysis,
      '',
      'COMPETITIVE DIFFERENTIATION',
      strategy.competitive_differentiation,
      '',
      'MESSAGING GUIDE',
      `Headline: ${strategy.messaging_guide?.headline}`,
      `Tagline: ${strategy.messaging_guide?.tagline}`,
      `Elevator Pitch: ${strategy.messaging_guide?.elevator_pitch}`,
      `Tone: ${strategy.messaging_guide?.tone}`,
      `CTA: ${strategy.messaging_guide?.call_to_action}`,
      '',
      'KEY MESSAGES',
      ...(strategy.messaging_guide?.key_messages || []).map((m: string) => `- ${m}`),
      '',
      'CHANNEL RECOMMENDATIONS',
      ...(strategy.channel_recommendations || []).map(
        (c: any) => `[${c.priority.toUpperCase()}] ${c.channel} (${c.category})\n  ${c.rationale}`
      ),
      '',
      'CAMPAIGN ROADMAP',
      ...(strategy.campaign_roadmap || []).map(
        (p: any) => `Phase: ${p.phase} (Weeks ${p.week_start}–${p.week_end})\n  ${p.objective}`
      ),
      '',
      'RISK FACTORS',
      ...(strategy.risk_factors || []).map((r: string) => `- ${r}`),
      '',
      'SUCCESS METRICS',
      ...(strategy.success_metrics || []).map((m: string) => `- ${m}`),
    ];

    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Clarimo_GTM_${strategy.gtm_id.substring(0, 8)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl space-y-6">
      {/* Top bar */}
      <div className="flex justify-between items-center">
        <div>
          <Badge variant="secondary" className="mb-2">Module 6: GTM Strategy Output</Badge>
          <h1 className="text-3xl font-bold">Your Go-to-Market Strategy</h1>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleDownload} className="gap-2">
            <Download className="h-4 w-4" /> Download
          </Button>
          <Button variant="outline" onClick={onReset}>New Strategy</Button>
        </div>
      </div>

      {/* Row 1: Summary + Positioning */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2 glass overflow-hidden relative">
          <div className="absolute top-0 right-0 p-8 opacity-5">
            <Megaphone className="h-40 w-40" />
          </div>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-primary" /> Executive Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <p className="text-lg leading-relaxed">{strategy.executive_summary}</p>

            <div className="p-4 bg-primary/5 rounded-xl border border-primary/10">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">
                Positioning Statement
              </p>
              <p className="italic text-sm leading-relaxed">{strategy.positioning_statement}</p>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-bold flex items-center gap-2 text-sm">
                  <Users className="h-4 w-4 text-blue-400" /> Target Segment
                </h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {strategy.target_segment_analysis}
                </p>
              </div>
              <div className="space-y-2">
                <h4 className="font-bold flex items-center gap-2 text-sm">
                  <Zap className="h-4 w-4 text-yellow-400" /> Differentiation
                </h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {strategy.competitive_differentiation}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Risks & Metrics */}
        <Card className="glass">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" /> Insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-3">
              <h4 className="font-bold flex items-center gap-2 text-sm">
                <AlertTriangle className="h-4 w-4 text-orange-400" /> Risk Factors
              </h4>
              <ul className="space-y-2">
                {(strategy.risk_factors || []).map((r: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2">
                    <span className="text-orange-400 shrink-0">•</span> {r}
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-3 pt-4 border-t border-border/50">
              <h4 className="font-bold flex items-center gap-2 text-sm">
                <TrendingUp className="h-4 w-4 text-green-400" /> Success Metrics
              </h4>
              <ul className="space-y-2">
                {(strategy.success_metrics || []).map((m: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-400 shrink-0 mt-0.5" /> {m}
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 2: Channel Recommendations */}
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Radio className="h-5 w-5 text-primary" /> Channel Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {(strategy.channel_recommendations || []).map((ch: any, i: number) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-border/50 bg-accent/30 hover:border-primary/30 transition-all space-y-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="font-bold text-sm leading-tight">{ch.channel}</span>
                  <Badge className={`text-[10px] shrink-0 ${PRIORITY_BADGE[ch.priority] || ''}`}>
                    {ch.priority}
                  </Badge>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <Badge className={`text-[10px] ${CATEGORY_BADGE[ch.category] || 'bg-muted text-muted-foreground'}`}>
                    {ch.category}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{ch.rationale}</p>
                <div className="text-xs space-y-1 pt-1 border-t border-border/30">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Reach</span>
                    <span className="font-medium">{ch.estimated_reach}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Cost</span>
                    <span className="font-medium">{ch.estimated_cost}</span>
                  </div>
                </div>
                <ul className="space-y-1 pt-1">
                  {(ch.tactics || []).map((t: string, j: number) => (
                    <li key={j} className="text-xs flex gap-2 text-muted-foreground">
                      <ArrowRight className="h-3 w-3 shrink-0 mt-0.5 text-primary" /> {t}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Row 3: Messaging Guide */}
      <MessagingGuideCard guide={strategy.messaging_guide} />

      {/* Row 4: Campaign Roadmap */}
      <CampaignRoadmapCard roadmap={strategy.campaign_roadmap} budget={strategy.inputs?.budget} />
    </div>
  );
}

// ── Messaging Guide Card ─────────────────────────────────────────────────────

function MessagingGuideCard({ guide }: { guide: any }) {
  if (!guide) return null;
  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-primary" /> Messaging Guide
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-6 md:grid-cols-2">
          {/* Left: Core copy */}
          <div className="space-y-4">
            <div className="p-4 bg-primary/5 rounded-xl border border-primary/10">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Headline</p>
              <p className="text-xl font-bold">{guide.headline}</p>
            </div>
            <div className="p-3 bg-accent/30 rounded-xl border border-border/30">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Tagline</p>
              <p className="font-medium italic">{guide.tagline}</p>
            </div>
            <div className="p-3 bg-accent/30 rounded-xl border border-border/30">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Elevator Pitch</p>
              <p className="text-sm leading-relaxed">{guide.elevator_pitch}</p>
            </div>
            <div className="flex items-center gap-3 p-3 bg-accent/20 rounded-xl border border-border/30">
              <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Tone:</span>
              <span className="text-sm font-medium">{guide.tone}</span>
            </div>
          </div>

          {/* Right: Messages, differentiators, pain points, CTA */}
          <div className="space-y-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Key Messages</p>
              <ul className="space-y-2">
                {(guide.key_messages || []).map((m: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2 p-2 bg-accent/20 rounded-lg">
                    <CheckCircle2 className="h-4 w-4 text-primary shrink-0 mt-0.5" /> {m}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Differentiators</p>
              <ul className="space-y-1">
                {(guide.differentiators || []).map((d: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2">
                    <Zap className="h-4 w-4 text-yellow-400 shrink-0 mt-0.5" /> {d}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Pain Points Addressed</p>
              <ul className="space-y-1">
                {(guide.pain_points_addressed || []).map((p: string, i: number) => (
                  <li key={i} className="text-sm flex gap-2">
                    <Target className="h-4 w-4 text-red-400 shrink-0 mt-0.5" /> {p}
                  </li>
                ))}
              </ul>
            </div>
            <div className="p-3 bg-gradient-to-r from-accent/30 to-primary/10 rounded-xl border border-primary/20">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Call to Action</p>
              <p className="font-bold text-primary">{guide.call_to_action}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Campaign Roadmap Card ────────────────────────────────────────────────────

function CampaignRoadmapCard({ roadmap, budget }: { roadmap: any[]; budget?: number }) {
  if (!roadmap?.length) return null;

  const phaseGradients = [
    'from-violet-500/20 to-purple-600/10 border-violet-500/30',
    'from-blue-500/20 to-cyan-600/10 border-blue-500/30',
    'from-orange-500/20 to-red-600/10 border-orange-500/30',
    'from-green-500/20 to-emerald-600/10 border-green-500/30',
  ];

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" /> Campaign Roadmap
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {roadmap.map((phase: any, i: number) => (
            <div
              key={i}
              className={`p-5 rounded-xl border bg-gradient-to-r ${phaseGradients[i % phaseGradients.length]} transition-all hover:scale-[1.005]`}
            >
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-background/50 flex items-center justify-center font-bold text-sm">
                    {i + 1}
                  </div>
                  <div>
                    <p className="font-bold">{phase.phase}</p>
                    <p className="text-xs text-muted-foreground">
                      Weeks {phase.week_start}–{phase.week_end}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  {budget && (
                    <Badge variant="outline" className="text-xs">
                      ${Math.round(budget * phase.budget_allocation_pct).toLocaleString()} budget
                    </Badge>
                  )}
                  <Badge variant="outline" className="text-xs">
                    {Math.round(phase.budget_allocation_pct * 100)}% of budget
                  </Badge>
                </div>
              </div>

              <p className="text-sm text-muted-foreground mb-4 leading-relaxed">{phase.objective}</p>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">Activities</p>
                  <ul className="space-y-1">
                    {(phase.activities || []).map((a: string, j: number) => (
                      <li key={j} className="text-xs flex gap-2 text-foreground/80">
                        <ArrowRight className="h-3 w-3 shrink-0 mt-0.5 text-primary" /> {a}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-2">KPIs to Track</p>
                  <ul className="space-y-1">
                    {(phase.kpis || []).map((k: string, j: number) => (
                      <li key={j} className="text-xs flex gap-2 text-foreground/80">
                        <BarChart3 className="h-3 w-3 shrink-0 mt-0.5 text-green-400" /> {k}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
