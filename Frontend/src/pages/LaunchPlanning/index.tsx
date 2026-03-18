import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { 
  Rocket, 
  Calendar, 
  CheckCircle2, 
  AlertTriangle,
  Layout,
  PieChart,
  ListTodo,
  TrendingUp,
  Brain,
  Layers,
  Check,
  Target,
  Download
} from 'lucide-react';
import { api } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';

export default function LaunchPlanning() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('standalone');
  const [result, setResult] = useState<any>(null);
  
  // Form State
  const [formData, setFormData] = useState({
    idea_description: '',
    target_audience: '',
    product_stage: 'idea',
    estimated_budget: 5000,
    team_size: 1,
    target_market: '',
    expected_timeline_months: 6,
    problem_discovery_id: '',
    validation_id: '',
    competitor_analysis_id: ''
  });

  // Data for Integrated Mode
  const [history, setHistory] = useState({
    problems: [] as any[],
    validations: [] as any[],
    competitors: [] as any[],
    plans: [] as any[]
  });

  useEffect(() => {
    if (activeTab === 'integrated' || activeTab === 'history') {
      loadHistory();
    }
  }, [activeTab]);

  const loadHistory = async () => {
    try {
      const [problemHistory, ideaList, competitorHistory, planHistory] = await Promise.all([
        api.userInputs.getAll(),
        api.ideas.getAll(),
        api.competitorAnalyses.list(),
        user?.id ? api.launchPlanning.getHistory(user.id) : Promise.resolve([])
      ]);
      
      setHistory({
        problems: problemHistory || [],
        validations: ideaList.flatMap((i: any) => i.latest_validation ? [i.latest_validation] : []) || [],
        competitors: (competitorHistory as any)?.analyses || [],
        plans: planHistory || []
      });
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const handleSubmit = async () => {
    if (!formData.idea_description) {
      toast.error('Please provide an idea description');
      return;
    }

    setLoading(true);
    try {
      const response = await api.launchPlanning.createPlan({
        ...formData,
        user_id: user?.id
      });
      setResult(response);
      toast.success('Launch plan generated successfully!');
    } catch (error) {
      toast.error('Failed to generate launch plan');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return <LaunchPlanResult plan={result} onReset={() => setResult(null)} />;
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="space-y-8">
        <div className="flex items-center gap-4 mb-8">
            <div className="p-3 bg-primary/10 rounded-2xl">
                <Rocket className="h-8 w-8 text-primary" />
            </div>
            <div>
                <h1 className="text-4xl font-bold">Launch Planning Assistant</h1>
                <p className="text-muted-foreground">Transition from idea to execution with a structured plan</p>
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

          <TabsContent value="standalone">
            <Card className="glass">
              <CardHeader>
                <CardTitle>Direct Idea Input</CardTitle>
                <CardDescription>Enter your startup details manually to get a baseline plan</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-4 md:col-span-2">
                    <Label>Startup Idea & Description</Label>
                    <Textarea 
                      placeholder="Describe your startup idea in detail..." 
                      className="min-h-[120px] glass border-border/50 focus:border-primary transition-all duration-300"
                      value={formData.idea_description}
                      onChange={(e) => setFormData({...formData, idea_description: e.target.value})}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Product Stage</Label>
                    <Select value={formData.product_stage} onValueChange={(v) => setFormData({...formData, product_stage: v})}>
                      <SelectTrigger className="glass border-border/50 focus:border-primary transition-all duration-300">
                        <SelectValue placeholder="Select stage" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="idea">Idea / Concept</SelectItem>
                        <SelectItem value="prototype">Prototype / Design</SelectItem>
                        <SelectItem value="mvp">MVP Build</SelectItem>
                        <SelectItem value="beta">Beta / Soft Launch</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Estimated Budget ($)</Label>
                    <Input 
                      type="number" 
                      className="glass border-border/50 focus:border-primary transition-all duration-300"
                      value={formData.estimated_budget}
                      onChange={(e) => setFormData({...formData, estimated_budget: parseInt(e.target.value)})}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Team Size</Label>
                    <Input 
                      type="number" 
                      className="glass border-border/50 focus:border-primary transition-all duration-300"
                      value={formData.team_size}
                      onChange={(e) => setFormData({...formData, team_size: parseInt(e.target.value)})}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Timeline (Months)</Label>
                    <Input 
                      type="number" 
                      className="glass border-border/50 focus:border-primary transition-all duration-300"
                      value={formData.expected_timeline_months}
                      onChange={(e) => setFormData({...formData, expected_timeline_months: parseInt(e.target.value)})}
                    />
                  </div>
                </div>

                <Button 
                  className="w-full h-12 text-lg bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.01] transition-all duration-300 font-semibold shadow-lg" 
                  onClick={handleSubmit} 
                  disabled={loading}
                >
                  {loading ? 'Analyzing...' : 'Generate Launch Plan'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="integrated">
             <Card className="glass">
              <CardHeader>
                <CardTitle>Integrated AI Insights</CardTitle>
                <CardDescription>Leverage outputs from previous modules for a data-driven plan</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                 <div className="grid gap-6 md:grid-cols-1">
                    <div className="space-y-2">
                        <Label>1. Problem Discovery Output</Label>
                        <Select value={formData.problem_discovery_id} onValueChange={(v) => {
                            const p = history.problems.find(x => x.input_id === v);
                            setFormData({
                                ...formData, 
                                problem_discovery_id: v,
                                idea_description: p?.problem_description || formData.idea_description
                            });
                        }}>
                        <SelectTrigger className="glass border-border/50 focus:border-primary transition-all duration-300">
                            <SelectValue placeholder="Select previous discovery" />
                        </SelectTrigger>
                        <SelectContent>
                            {history.problems.map((p) => (
                                <SelectItem key={p.input_id} value={p.input_id}>{p.problem_description.substring(0, 50)}...</SelectItem>
                            ))}
                            {history.problems.length === 0 && <SelectItem value="none" disabled>No history found</SelectItem>}
                        </SelectContent>
                        </Select>
                        {formData.problem_discovery_id && (
                            <div className="mt-2 p-3 bg-secondary/20 rounded-lg text-xs border border-secondary/30">
                                <p className="font-bold mb-1">Preview Pain Points:</p>
                                <ul className="list-disc pl-4 space-y-1">
                                    {history.problems.find(p => p.input_id === formData.problem_discovery_id)?.extracted_pain_points?.slice(0, 3).map((pt: string, i: number) => (
                                        <li key={i}>{pt}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label>2. Idea Validation Result</Label>
                        <Select value={formData.validation_id} onValueChange={(v) => setFormData({...formData, validation_id: v})}>
                        <SelectTrigger className="glass border-border/50 focus:border-primary transition-all duration-300">
                            <SelectValue placeholder="Select validation report" />
                        </SelectTrigger>
                        <SelectContent>
                            {history.validations.map((v) => (
                                <SelectItem key={v.validation_id} value={v.validation_id}>Score: {v.overall_score} ({v.validation_id.substring(0,8)})</SelectItem>
                            ))}
                            {history.validations.length === 0 && <SelectItem value="none" disabled>No validations found</SelectItem>}
                        </SelectContent>
                        </Select>
                        {formData.validation_id && (
                            <div className="mt-2 p-3 bg-primary/5 rounded-lg text-xs border border-primary/20 flex justify-between items-center">
                                <span>Validation Score: <strong>{history.validations.find(v => v.validation_id === formData.validation_id)?.overall_score}/5</strong></span>
                                <Badge variant="outline" className="text-[10px]">Data Ready</Badge>
                            </div>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label>3. Competitor Analysis</Label>
                        <Select value={formData.competitor_analysis_id} onValueChange={(v) => setFormData({...formData, competitor_analysis_id: v})}>
                        <SelectTrigger className="glass border-border/50 focus:border-primary transition-all duration-300">
                            <SelectValue placeholder="Select analysis" />
                        </SelectTrigger>
                        <SelectContent>
                            {history.competitors.map((c) => (
                                <SelectItem key={c.analysis_id} value={c.analysis_id}>{c.analysis_id.substring(0, 8)} ({c.competitors_found} competitors)</SelectItem>
                            ))}
                            {history.competitors.length === 0 && <SelectItem value="none" disabled>No history found</SelectItem>}
                        </SelectContent>
                        </Select>
                        {formData.competitor_analysis_id && (
                            <div className="mt-2 p-3 bg-blue-500/5 rounded-lg text-xs border border-blue-500/20">
                                <p>Analyzed <strong>{history.competitors.find(c => c.analysis_id === formData.competitor_analysis_id)?.competitors_found}</strong> competitors in this niche.</p>
                            </div>
                        )}
                    </div>

                    <div className="space-y-4 pt-4 border-t border-border/50">
                        <Label>Verify Idea Description</Label>
                        <Textarea 
                        placeholder="Confirm or refine your idea for this plan..." 
                        className="glass border-border/50 focus:border-primary transition-all duration-300"
                        value={formData.idea_description}
                        onChange={(e) => setFormData({...formData, idea_description: e.target.value})}
                        />
                    </div>
                 </div>

                 <Button 
                   className="w-full h-12 text-lg bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.01] transition-all duration-300 font-semibold shadow-lg" 
                   onClick={handleSubmit} 
                   disabled={loading}
                 >
                  {loading ? 'Syncing Data & Processing...' : 'Generate Informed Plan'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history">
            <Card className="glass">
                <CardHeader>
                    <CardTitle>Launch Plan History</CardTitle>
                    <CardDescription>Review and download your previous strategic plans</CardDescription>
                </CardHeader>
                <CardContent>
                    {history.plans.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">
                            <Rocket className="h-12 w-12 mx-auto mb-4 opacity-20" />
                            <p>No launch plans found. Generate your first plan to see it here.</p>
                        </div>
                    ) : (
                        <div className="grid gap-4">
                            {history.plans.map((p: any) => (
                                <div key={p.plan_id} className="flex items-center justify-between p-4 rounded-xl border border-border/50 hover:border-primary/30 transition-all bg-accent/5 group">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                            {Math.round(p.readiness_score)}
                                        </div>
                                        <div>
                                            <div className="font-bold">{p.inputs.idea_description.substring(0, 40)}...</div>
                                            <div className="text-xs text-muted-foreground">{new Date(p.created_at).toLocaleDateString()} • {p.inputs.product_stage}</div>
                                        </div>
                                    </div>
                                    <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Button variant="ghost" size="sm" onClick={() => setResult(p)}>View Result</Button>
                                    </div>
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

function LaunchPlanResult({ plan, onReset }: { plan: any, onReset: () => void }) {
    const handleDownload = () => {
        const content = `
LAUNCH PLAN REPORT
Generated: ${new Date(plan.created_at).toLocaleString()}
--------------------------------------------------
EXECUTIVE SUMMARY
${plan.executive_summary}

READINESS SCORE: ${Math.round(plan.readiness_score)}/100
RECOMMENDATION: ${plan.launch_timing_recommendation}

BUDGET ALLOCATION:
${plan.budget_allocation.map((b: any) => `- ${b.category}: $${b.amount} (${b.percentage}%)`).join('\n')}

TIMELINE:
${plan.timeline.map((m: any) => `- ${m.title} (${m.duration_weeks} weeks): ${m.description}`).join('\n')}

CHECKLIST:
${plan.checklist.map((c: any) => `[ ] ${c.task} (${c.priority})`).join('\n')}

MARKET ANALYSIS:
${plan.market_saturation_analysis || 'N/A'}
        `;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Clarimo_Launch_Plan_${plan.plan_id.substring(0,8)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="container mx-auto px-4 py-8 max-w-6xl">
            <div className="flex justify-between items-center mb-8">
                <div>
                     <Badge variant="secondary" className="mb-2">Module 5: Launch Planning Output</Badge>
                     <h1 className="text-3xl font-bold">Your Custom Launch Strategy</h1>
                </div>
                <div className="flex gap-4">
                    <Button variant="outline" onClick={handleDownload} className="gap-2">
                        <Download className="h-4 w-4" /> Download Report
                    </Button>
                    <Button variant="outline" onClick={onReset}>Generate Another Plan</Button>
                </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
                {/* Score & Summary */}
                <Card className="lg:col-span-2 glass overflow-hidden relative">
                    <div className="absolute top-0 right-0 p-8 opacity-10">
                        <Rocket className="h-32 w-32" />
                    </div>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Brain className="h-5 w-5 text-primary" />
                            Executive Summary
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="flex items-center gap-6 p-4 bg-primary/5 rounded-xl border border-primary/10">
                            <div className="flex flex-col items-center">
                                <span className="text-4xl font-bold text-primary">{Math.round(plan.readiness_score)}</span>
                                <span className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground">Readiness</span>
                            </div>
                            <div className="h-10 w-[1px] bg-border" />
                            <p className="font-medium">{plan.launch_timing_recommendation}</p>
                        </div>
                        <p className="text-lg leading-relaxed">{plan.executive_summary}</p>
                        
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div className="space-y-3">
                                <h4 className="font-bold flex items-center gap-2">
                                    <AlertTriangle className="h-4 w-4 text-orange-500" /> Key Risks
                                </h4>
                                <ul className="space-y-2">
                                    {plan.risk_factors.map((risk: string, i: number) => (
                                        <li key={i} className="text-sm flex gap-2">
                                            <span className="text-orange-500">•</span> {risk}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <div className="space-y-3">
                                <h4 className="font-bold flex items-center gap-2">
                                    <TrendingUp className="h-4 w-4 text-green-500" /> Success Metrics
                                </h4>
                                <ul className="space-y-2">
                                    {plan.success_metrics.map((metric: string, i: number) => (
                                        <li key={i} className="text-sm flex gap-2">
                                            <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" /> {metric}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>

                        {plan.market_saturation_analysis && (
                            <div className="pt-6 border-t border-border/50">
                                <h4 className="font-bold flex items-center gap-2 mb-3">
                                    <Target className="h-4 w-4 text-blue-500" /> Market Saturation Analysis
                                </h4>
                                <div className="p-4 bg-blue-500/5 rounded-xl border border-blue-500/10 text-sm leading-relaxed italic">
                                    {plan.market_saturation_analysis}
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Budget */}
                <Card className="glass">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <PieChart className="h-5 w-5 text-primary" />
                            Budget Allocation
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {plan.budget_allocation.map((item: any, i: number) => (
                            <div key={i} className="space-y-1">
                                <div className="flex justify-between text-sm">
                                    <span className="font-medium">{item.category}</span>
                                    <span className="text-muted-foreground">${item.amount.toLocaleString()}</span>
                                </div>
                                <div className="h-2 w-full bg-accent rounded-full overflow-hidden">
                                    <div 
                                        className="h-full bg-primary" 
                                        style={{ width: `${item.percentage}%` }}
                                    />
                                </div>
                                <p className="text-[10px] text-muted-foreground">{item.description}</p>
                            </div>
                        ))}
                        <div className="pt-4 mt-4 border-t border-border flex justify-between items-center">
                            <span className="font-bold">Total Estimate</span>
                            <span className="text-xl font-bold text-primary">${plan.budget_allocation.reduce((a: number, b: any) => a + b.amount, 0).toLocaleString()}</span>
                        </div>
                    </CardContent>
                </Card>

                {/* Timeline */}
                <Card className="lg:col-span-2 glass">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Calendar className="h-5 w-5 text-primary" />
                            Launch Timeline
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="relative space-y-8 before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-primary before:via-border before:to-transparent">
                            {plan.timeline.map((milestone: any, i: number) => (
                                <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                    <div className="flex items-center justify-center w-10 h-10 rounded-full border border-primary bg-background text-primary shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 group-hover:bg-primary group-hover:text-white transition-all duration-300">
                                        {i + 1}
                                    </div>
                                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-border/50 bg-accent/50 group-hover:border-primary/30 transition-all duration-300">
                                        <div className="flex items-center justify-between space-x-2 mb-1">
                                            <div className="font-bold text-lg">{milestone.title}</div>
                                            <time className="font-mono text-sm text-primary">{milestone.duration_weeks} Weeks</time>
                                        </div>
                                        <div className="text-muted-foreground text-sm mb-4">{milestone.description}</div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                            {milestone.tasks.map((task: string, j: number) => (
                                                <div key={j} className="text-xs flex items-center gap-2 py-1 px-2 bg-background/50 rounded-md border border-border/30">
                                                    <Check className="h-3 w-3 text-green-500" /> {task}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Checklist */}
                <Card className="glass">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <ListTodo className="h-5 w-5 text-primary" />
                            Launch Checklist
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {plan.checklist.map((item: any, i: number) => (
                                <div key={i} className="flex gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors items-start">
                                    <div className="pt-1">
                                        <div className="h-5 w-5 rounded border-2 border-primary flex items-center justify-center text-primary">
                                            {/* Minimal checkbox style */}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <div className="text-sm font-medium leading-tight">{item.task}</div>
                                        <div className="flex gap-2">
                                            <Badge variant="outline" className="text-[9px] uppercase h-4 py-0 font-bold">{item.category}</Badge>
                                            <Badge className={`text-[9px] uppercase h-4 py-0 font-bold ${
                                                item.priority === 'high' ? 'bg-red-500' : 
                                                item.priority === 'medium' ? 'bg-orange-500' : 'bg-blue-500'
                                            }`}>
                                                {item.priority}
                                            </Badge>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
