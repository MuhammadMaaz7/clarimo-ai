/**
 * Customer Insights Page
 * Form-first design matching other modules
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Users, Search, Loader2 } from 'lucide-react';
import { customerInsightsApi } from '../services/customerInsightsApi';
import { unifiedToast } from '../lib/toast-utils';

export default function CustomerInsights() {
  const navigate = useNavigate();
  const [startupIdea, setStartupIdea] = useState('');
  const [targetMarket, setTargetMarket] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!startupIdea.trim()) {
      unifiedToast.error({
        description: 'Please enter your startup idea',
      });
      return;
    }

    try {
      setIsSubmitting(true);
      const result = await customerInsightsApi.startAnalysis({
        startupIdea: startupIdea.trim(),
        targetMarket: targetMarket.trim() || undefined,
      });

      unifiedToast.success({
        description: 'Analysis started! This will take 1-2 minutes.',
      });

      // Navigate to analysis detail page
      navigate(`/customer-insights/${result.analysis_id}`);
    } catch (error: any) {
      unifiedToast.error({
        title: 'Failed to Start Analysis',
        description: error.message || 'Please try again later.',
      });
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center space-y-2 mb-8">
          <h1 className="text-3xl font-bold">Customer Insights</h1>
          <p className="text-muted-foreground">
            Discover where your target audience is active and understand their pain points
          </p>
        </div>

        {/* Form */}
        <Card className="glass border-border/50">
          <CardContent className="pt-6 space-y-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Startup Idea */}
              <div className="space-y-2">
                <Label htmlFor="startupIdea" className="text-base">
                  Startup Idea <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="startupIdea"
                  placeholder="e.g., AI-powered meal planning app for busy professionals who want to eat healthy but don't have time to plan meals"
                  value={startupIdea}
                  onChange={(e) => setStartupIdea(e.target.value)}
                  rows={4}
                  required
                  maxLength={500}
                  disabled={isSubmitting}
                  className="resize-none glass border-border/50 focus:border-primary transition-all duration-300"
                />
                <p className="text-xs text-muted-foreground">
                  {startupIdea.length}/500 characters • Describe your product and what problem it solves
                </p>
              </div>

              {/* Target Market (Optional) */}
              <div className="space-y-2">
                <Label htmlFor="targetMarket" className="text-base">
                  Target Market (Optional)
                </Label>
                <Input
                  id="targetMarket"
                  placeholder="e.g., Working professionals aged 25-45, Health-conscious millennials"
                  value={targetMarket}
                  onChange={(e) => setTargetMarket(e.target.value)}
                  maxLength={200}
                  disabled={isSubmitting}
                  className="glass border-border/50 focus:border-primary transition-all duration-300"
                />
                <p className="text-xs text-muted-foreground">
                  Who is your ideal customer? (helps refine the analysis)
                </p>
              </div>

              {/* Submit Button */}
              <Button
                type="submit"
                size="lg"
                className="w-full bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.02] transition-all duration-300 font-semibold text-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Starting Analysis... (1-2 min)
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-5 w-5" />
                    Discover Your Customers
                  </>
                )}
              </Button>

              {isSubmitting && (
                <div className="text-center space-y-1">
                  <p className="text-sm text-muted-foreground">
                    Analyzing communities and audience segments...
                  </p>
                  <p className="text-xs text-muted-foreground">
                    This may take 1-2 minutes
                  </p>
                </div>
              )}
            </form>
          </CardContent>
        </Card>

        {/* Info Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-primary/10 p-2">
                  <Users className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Community Discovery</h3>
                  <p className="text-sm text-muted-foreground">
                    Find active Reddit communities and Product Hunt discussions
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-accent/10 p-2">
                  <Search className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Audience Segmentation</h3>
                  <p className="text-sm text-muted-foreground">
                    Identify distinct customer groups and their characteristics
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass border-border/50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-secondary/10 p-2">
                  <Users className="h-5 w-5 text-secondary" />
                </div>
                <div>
                  <h3 className="font-semibold mb-1">Pain Point Analysis</h3>
                  <p className="text-sm text-muted-foreground">
                    Understand what problems your audience is trying to solve
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
