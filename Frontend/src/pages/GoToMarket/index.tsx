/**
 * Module 6: Go-to-Market Strategy Generator
 * Premium Dark UI — brand purple palette.
 */

import { useState } from 'react';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Megaphone } from 'lucide-react';
import { api } from '../../lib/api';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import GTMResult from './GTMResult';
import { PremiumCard } from '../../components/ui/premium/PremiumCard';
import { PremiumButton } from '../../components/ui/premium/PremiumButton';
import { ModuleHeader } from '../../components/ui/ModuleHeader';

export default function GoToMarket() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [formData, setFormData] = useState({
    startup_description: '',
    target_audience: '',
    unique_value_proposition: '',
    business_model: 'saas',
    budget: 5000,
    launch_date_weeks: 12,
  });

  const handleSubmit = async () => {
    if (!formData.startup_description || !formData.target_audience) {
      toast.error('Please fill in the startup description and target audience.');
      return;
    }
    setLoading(true);
    try {
      const response = await api.gtm.createStrategy({ ...formData, user_id: user?.id });
      setResult(response);
      toast.success('GTM strategy generated!');
    } catch (err) {
      toast.error('Failed to generate GTM strategy. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (result) return <GTMResult strategy={result} onReset={() => setResult(null)} />;

  const upd = (key: string, value: any) => setFormData((p) => ({ ...p, [key]: value }));

  return (
    <div className="responsive-container-dashboard">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <ModuleHeader
          icon={Megaphone}
          title="Go-to-Market Strategy"
          description="Generate a data-driven GTM plan with channel recommendations, messaging, and campaign roadmap. High-velocity execution starts here."
          iconBgClassName="bg-green-500/10 border-green-500/20 shadow-green-500/5"
          iconClassName="text-green-400"
        />

        <PremiumCard variant="default">
          <div className="grid gap-5 md:grid-cols-2">
            <div className="md:col-span-2 space-y-1.5">
              <label className="brand-label">Startup Description *</label>
              <Textarea 
                className="brand-textarea min-h-[90px]" 
                placeholder="Describe your startup, the problem it solves, and your core offering..." 
                value={formData.startup_description} 
                onChange={(e) => upd('startup_description', e.target.value)} 
                disabled={loading} 
              />
            </div>
            <div className="md:col-span-2 space-y-1.5">
              <label className="brand-label">Target Audience *</label>
              <Input 
                className="brand-input" 
                placeholder="e.g. Early-stage SaaS founders with 1–10 employees" 
                value={formData.target_audience} 
                onChange={(e) => upd('target_audience', e.target.value)} 
                disabled={loading} 
              />
            </div>
            <div className="md:col-span-2 space-y-1.5">
              <label className="brand-label">Unique Value Proposition</label>
              <Input 
                className="brand-input" 
                placeholder="What makes you different from existing solutions?" 
                value={formData.unique_value_proposition} 
                onChange={(e) => upd('unique_value_proposition', e.target.value)} 
                disabled={loading} 
              />
            </div>
            <div className="space-y-1.5">
              <label className="brand-label">Business Model</label>
              <Select value={formData.business_model} onValueChange={(v) => upd('business_model', v)} disabled={loading}>
                <SelectTrigger className="brand-input"><SelectValue /></SelectTrigger>
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
            <div className="space-y-1.5">
              <label className="brand-label">Marketing Budget ($)</label>
              <Input 
                type="number" 
                className="brand-input" 
                value={formData.budget} 
                onChange={(e) => upd('budget', parseFloat(e.target.value) || 0)} 
                disabled={loading} 
              />
            </div>
            <div className="space-y-1.5">
              <label className="brand-label">Weeks Until Launch</label>
              <Input 
                type="number" 
                className="brand-input" 
                value={formData.launch_date_weeks} 
                onChange={(e) => upd('launch_date_weeks', parseInt(e.target.value) || 12)} 
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
              {loading ? 'Generating Strategy...' : 'Generate GTM Strategy'}
            </PremiumButton>
          </div>
        </PremiumCard>
      </div>
    </div>
  );
}
