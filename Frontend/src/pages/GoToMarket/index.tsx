/**
 * Module 6: Go-to-Market Strategy Generator
 * Input form with standalone and integrated modes.
 * Results view with channels, messaging guide, and campaign roadmap.
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Label } from '../../components/ui/label';
import { Megaphone, Layers, Layout, Calendar } from 'lucide-react';
import { api } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import GTMResult from './GTMResult';

export default function GoToMarket() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('standalone');
  const [result, setResult] = useState<any>(null);

  const [formData, setFormData] = useState({
    startup_description: '',
    target_audience: '',
    unique_value_proposition: '',
    business_model: 'saas',
    budget: 5000,
    launch_date_weeks: 12,
    problem_discovery_id: '',
    validation_id: '',
    competitor_analysis_id: '',
    launch_plan_id: '',
  });

  const [history, setHistory] = useState({
    problems: [] as any[],
    validations: [] as any[],
    competitors: [] as any[],
    plans: [] as any[],
    gtmHistory: [] as any[],
  });

  useEffect(() => {
    if (activeTab === 'integrated' || activeTab === 'history') {
      loadHistory();
    }
  }, [activeTab]);

  const loadHistory = async () => {
    try {
      const [problemHistory, ideaList, competitorHistory, planHistory, gtmHist] = await Promise.all([
        api.userInputs.getAll(),
        api.ideas.getAll(),
        api.competitorAnalyses.list(),
        user?.id ? api.launchPlanning.getHistory(user.id) : Promise.resolve([]),
        user?.id ? api.gtm.getHistory(user.id) : Promise.resolve([]),
      ]);
      setHistory({
        problems: problemHistory || [],
        validations: ideaList.flatMap((i: any) => i.latest_validation ? [i.latest_validation] : []),
        competitors: (competitorHistory as any)?.analyses || [],
        plans: planHistory || [],
        gtmHistory: gtmHist || [],
      });
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleSubmit = async () => {
    if (!formData.startup_description || !formData.target_audience) {
      toast.error('Please fill in the startup description and target audience.');
      return;
    }
    setLoading(true);
    try {
      const response = await api.gtm.createStrategy({ ...formData, user_id: user?.id });
      setResult(response);
      toast.success('GTM strategy generated successfully!');
    } catch (err) {
      toast.error('Failed to generate GTM strategy. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return <GTMResult strategy={result} onReset={() => setResult(null)} />;
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <div className="p-3 bg-primary/10 rounded-2xl">
            <Megaphone className="h-8 w-8 text-primary" />
          </div>
          <div>
            <h1 className="text-4xl font-bold">Go-to-Market Strategy</h1>
            <p className="text-muted-foreground">
              Generate a data-driven GTM plan with channel recommendations, messaging, and campaign roadmap
            </p>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8 glass">
            <TabsTrigger value="standalone" className="gap-2">
              <Layout className="h-4 w-4" /> Standalone
            </TabsTrigger>
            <TabsTrigger value="integrated" className="gap-2">
              <Layers className="h-4 w-4" /> Integrated
            </TabsTrigger>
            <TabsTrigger value="history" className="gap-2">
              <Calendar className="h-4 w-4" /> History
            </TabsTrigger>
          </TabsList>

          {/* ── Standalone Tab ── */}
          <TabsContent value="standalone">
            <Card className="glass">
              <CardHeader>
                <CardTitle>Direct Input</CardTitle>
                <CardDescription>Enter your startup details to generate a GTM strategy from scratch</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <StandaloneForm formData={formData} setFormData={setFormData} />
                <Button
                  className="w-full h-12 text-lg bg-gradient-to-r from-accent to-primary text-white glow hover:scale-[1.01] transition-all duration-300 font-semibold shadow-lg"
                  onClick={handleSubmit}
                  disabled={loading}
                >
                  {loading ? 'Generating Strategy...' : 'Generate GTM Strategy'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── Integrated Tab ── */}
          <TabsContent value="integrated">
            <Card className="glass">
              <CardHeader>
                <CardTitle>Integrated AI Insights</CardTitle>
                <CardDescription>Pull data from previous modules for a richer, context-aware GTM plan</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <IntegratedForm formData={formData} setFormData={setFormData} history={history} />
                <Button
                  className="w-full h-12 text-lg bg-gradient-to-r from-accent to-primary text-white glow hover:scale-[1.01] transition-all duration-300 font-semibold shadow-lg"
                  onClick={handleSubmit}
                  disabled={loading}
                >
                  {loading ? 'Syncing & Generating...' : 'Generate Informed GTM Strategy'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── History Tab ── */}
          <TabsContent value="history">
            <Card className="glass">
              <CardHeader>
                <CardTitle>GTM Strategy History</CardTitle>
                <CardDescription>Review your previously generated strategies</CardDescription>
              </CardHeader>
              <CardContent>
                {history.gtmHistory.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <Megaphone className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>No GTM strategies yet. Generate your first one above.</p>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {history.gtmHistory.map((s: any) => (
                      <div
                        key={s.gtm_id}
                        className="flex items-center justify-between p-4 rounded-xl border border-border/50 hover:border-primary/30 transition-all bg-accent/5 group"
                      >
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                            <Megaphone className="h-5 w-5" />
                          </div>
                          <div>
                            <div className="font-bold">
                              {s.inputs?.startup_description?.substring(0, 45)}...
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {new Date(s.created_at).toLocaleDateString()} • {s.inputs?.business_model}
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => setResult(s)}
                        >
                          View
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// ── Standalone Form ──────────────────────────────────────────────────────────

function StandaloneForm({ formData, setFormData }: { formData: any; setFormData: any }) {
  const update = (key: string, value: any) => setFormData((p: any) => ({ ...p, [key]: value }));

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="space-y-2 md:col-span-2">
        <Label>Startup Description *</Label>
        <Textarea
          placeholder="Describe your startup, what it does, and the problem it solves..."
          className="min-h-[110px] glass border-border/50 focus:border-primary transition-all"
          value={formData.startup_description}
          onChange={(e) => update('startup_description', e.target.value)}
        />
      </div>

      <div className="space-y-2 md:col-span-2">
        <Label>Target Audience *</Label>
        <Input
          placeholder="e.g. Early-stage SaaS founders with 1-10 employees"
          className="glass border-border/50 focus:border-primary transition-all"
          value={formData.target_audience}
          onChange={(e) => update('target_audience', e.target.value)}
        />
      </div>

      <div className="space-y-2 md:col-span-2">
        <Label>Unique Value Proposition</Label>
        <Input
          placeholder="What makes you different from existing solutions?"
          className="glass border-border/50 focus:border-primary transition-all"
          value={formData.unique_value_proposition}
          onChange={(e) => update('unique_value_proposition', e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label>Business Model</Label>
        <Select value={formData.business_model} onValueChange={(v) => update('business_model', v)}>
          <SelectTrigger className="glass border-border/50 focus:border-primary transition-all">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="saas">SaaS</SelectItem>
            <SelectItem value="b2b">B2B</SelectItem>
            <SelectItem value="b2c">B2C</SelectItem>
            <SelectItem value="b2b2c">B2B2C</SelectItem>
            <SelectItem value="ecommerce">E-Commerce</SelectItem>
            <SelectItem value="marketplace">Marketplace</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Marketing Budget ($)</Label>
        <Input
          type="number"
          className="glass border-border/50 focus:border-primary transition-all"
          value={formData.budget}
          onChange={(e) => update('budget', parseFloat(e.target.value) || 0)}
        />
      </div>

      <div className="space-y-2">
        <Label>Weeks Until Launch</Label>
        <Input
          type="number"
          className="glass border-border/50 focus:border-primary transition-all"
          value={formData.launch_date_weeks}
          onChange={(e) => update('launch_date_weeks', parseInt(e.target.value) || 12)}
        />
      </div>
    </div>
  );
}

// ── Integrated Form ──────────────────────────────────────────────────────────

function IntegratedForm({
  formData, setFormData, history
}: { formData: any; setFormData: any; history: any }) {
  const update = (key: string, value: any) => setFormData((p: any) => ({ ...p, [key]: value }));

  return (
    <div className="space-y-6">
      {/* Previous module selectors */}
      <div className="space-y-2">
        <Label>1. Problem Discovery Output</Label>
        <Select
          value={formData.problem_discovery_id}
          onValueChange={(v) => {
            const p = history.problems.find((x: any) => x.input_id === v);
            update('problem_discovery_id', v);
            if (p) update('startup_description', p.problem_description || formData.startup_description);
          }}
        >
          <SelectTrigger className="glass border-border/50 focus:border-primary transition-all">
            <SelectValue placeholder="Select a discovery session" />
          </SelectTrigger>
          <SelectContent>
            {history.problems.map((p: any) => (
              <SelectItem key={p.input_id} value={p.input_id}>
                {p.problem_description?.substring(0, 55)}...
              </SelectItem>
            ))}
            {history.problems.length === 0 && (
              <SelectItem value="none" disabled>No history found</SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>2. Idea Validation Result</Label>
        <Select value={formData.validation_id} onValueChange={(v) => update('validation_id', v)}>
          <SelectTrigger className="glass border-border/50 focus:border-primary transition-all">
            <SelectValue placeholder="Select a validation report" />
          </SelectTrigger>
          <SelectContent>
            {history.validations.map((v: any) => (
              <SelectItem key={v.validation_id} value={v.validation_id}>
                Score: {v.overall_score} ({v.validation_id.substring(0, 8)})
              </SelectItem>
            ))}
            {history.validations.length === 0 && (
              <SelectItem value="none" disabled>No validations found</SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>3. Competitor Analysis</Label>
        <Select value={formData.competitor_analysis_id} onValueChange={(v) => update('competitor_analysis_id', v)}>
          <SelectTrigger className="glass border-border/50 focus:border-primary transition-all">
            <SelectValue placeholder="Select an analysis" />
          </SelectTrigger>
          <SelectContent>
            {history.competitors.map((c: any) => (
              <SelectItem key={c.analysis_id} value={c.analysis_id}>
                {c.analysis_id.substring(0, 8)} ({c.competitors_found} competitors)
              </SelectItem>
            ))}
            {history.competitors.length === 0 && (
              <SelectItem value="none" disabled>No analyses found</SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>4. Launch Plan</Label>
        <Select value={formData.launch_plan_id} onValueChange={(v) => update('launch_plan_id', v)}>
          <SelectTrigger className="glass border-border/50 focus:border-primary transition-all">
            <SelectValue placeholder="Select a launch plan" />
          </SelectTrigger>
          <SelectContent>
            {history.plans.map((p: any) => (
              <SelectItem key={p.plan_id} value={p.plan_id}>
                {p.inputs?.idea_description?.substring(0, 45)}... (Score: {Math.round(p.readiness_score)})
              </SelectItem>
            ))}
            {history.plans.length === 0 && (
              <SelectItem value="none" disabled>No plans found</SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="pt-4 border-t border-border/50 space-y-4">
        <StandaloneForm formData={formData} setFormData={setFormData} />
      </div>
    </div>
  );
}
