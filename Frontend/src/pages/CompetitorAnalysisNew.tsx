/**
 * New Competitor Analysis Page
 * Production-ready with clean UI and robust error handling
 */

import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Loader2, Plus, X, Target, ExternalLink } from 'lucide-react';
import api from '../lib/api';
import { unifiedToast } from '../lib/toast-utils';

interface AnalysisResult {
  success: boolean;
  analysis_id: string;
  execution_time: number;
  product: {
    name: string;
    description: string;
    features: string[];
    pricing?: string;
    target_audience?: string;
  };
  top_competitors: Array<{
    name: string;
    description: string;
    url: string;
    features: string[];
    pricing?: string;
    target_audience?: string;
    source: string;
    competitor_type?: 'direct' | 'indirect';
    similarity_score?: number;
    enriched?: boolean;
  }>;
  feature_matrix: {
    features: string[];
    products: Array<{
      name: string;
      is_user_product: boolean;
      feature_support: Record<string, boolean>;
    }>;
  };
  comparison: {
    pricing: {
      user_product: string;
      competitors: Array<{
        name: string;
        pricing: string;
      }>;
    };
    feature_count: {
      user_product: number;
      competitors: Array<{
        name: string;
        count: number;
      }>;
    };
    positioning: string;
  };
  gap_analysis: {
    opportunities: string[];
    unique_strengths: string[];
    areas_to_improve: string[];
    market_gaps: string[];
  };
  insights: {
    market_position: string;
    competitive_advantages: string[];
    differentiation_strategy: string;
    recommendations: string[];
  };
  market_insights?: {
    total_competitors: number;
    direct_competitors?: number;
    indirect_competitors?: number;
    market_saturation?: 'low' | 'medium' | 'high';
    opportunity_score?: number;
  };
  metadata: {
    total_competitors_analyzed: number;
    timestamp: string;
  };
}

export default function CompetitorAnalysisNew() {
  const [searchParams] = useSearchParams();
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [resultsTab, setResultsTab] = useState('competitors');
  
  // Form state
  const [productName, setProductName] = useState('');
  const [description, setDescription] = useState('');
  const [features, setFeatures] = useState<string[]>(['']);
  const [pricing, setPricing] = useState('');
  const [targetAudience, setTargetAudience] = useState('');

  // Load analysis if ID provided
  useEffect(() => {
    const analysisId = searchParams.get('id');
    if (analysisId) {
      loadAnalysis(analysisId);
    }
  }, [searchParams]);

  const loadAnalysis = async (analysisId: string) => {
    try {
      setIsAnalyzing(true);
      const result = await api.competitorAnalyses.getById(analysisId);
      setAnalysisResult(result);
    } catch (error: any) {
      unifiedToast.error({ description: 'Failed to load analysis' });
      console.error(error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const addFeature = () => {
    setFeatures([...features, '']);
  };

  const removeFeature = (index: number) => {
    setFeatures(features.filter((_, i) => i !== index));
  };

  const updateFeature = (index: number, value: string) => {
    const newFeatures = [...features];
    newFeatures[index] = value;
    setFeatures(newFeatures);
  };

  const handleAnalyze = async () => {
    // Validation
    if (!productName.trim()) {
      unifiedToast.error({ description: 'Please enter a product name' });
      return;
    }
    if (!description.trim()) {
      unifiedToast.error({ description: 'Please enter a product description' });
      return;
    }

    const validFeatures = features.filter(f => f.trim());
    if (validFeatures.length === 0) {
      unifiedToast.error({ description: 'Please add at least one feature' });
      return;
    }

    setIsAnalyzing(true);

    try {
      const result = await api.competitorAnalyses.analyze({
        name: productName.trim(),
        description: description.trim(),
        features: validFeatures,
        pricing: pricing.trim() || undefined,
        target_audience: targetAudience.trim() || undefined,
      });

      setAnalysisResult(result);
      unifiedToast.success({ description: 'Analysis complete!' });
    } catch (error: any) {
      console.error('Analysis failed:', error);
      unifiedToast.error({ description: error.message || 'Analysis failed. Please try again.' });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Show results with tabs if analysis is complete
  if (analysisResult) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-gradient-to-br from-accent to-primary p-2">
                <Target className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">{analysisResult.product.name}</h1>
                <p className="text-sm text-muted-foreground">
                  Analysis completed in {analysisResult.execution_time.toFixed(1)}s • {analysisResult.metadata.total_competitors_analyzed} competitors analyzed
                </p>
              </div>
            </div>
            {!searchParams.get('id') && (
              <Button onClick={() => setAnalysisResult(null)} variant="outline">
                <Plus className="mr-2 h-4 w-4" />
                New Analysis
              </Button>
            )}
          </div>

          {/* Results Tabs */}
          <Tabs value={resultsTab} onValueChange={setResultsTab} className="w-full">
            <TabsList className="grid w-full max-w-3xl grid-cols-4">
              <TabsTrigger value="product">Product Info</TabsTrigger>
              <TabsTrigger value="competitors">Competitors ({analysisResult.top_competitors.length})</TabsTrigger>
              <TabsTrigger value="comparison">Feature Comparison</TabsTrigger>
              <TabsTrigger value="analysis">Market Analysis</TabsTrigger>
            </TabsList>

            {/* Product Info Tab */}
            <TabsContent value="product" className="mt-6">
              <Card className="glass border-border/50">
                <CardHeader>
                  <CardTitle>Your Product Information</CardTitle>
                  <CardDescription>The inputs you provided for this analysis</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Product Name</h3>
                    <p className="text-lg font-semibold">{analysisResult.product.name}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Description</h3>
                    <p className="text-foreground whitespace-pre-wrap">{analysisResult.product.description}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Features</h3>
                    <ul className="list-disc list-inside space-y-1">
                      {analysisResult.product.features.map((feature: string, idx: number) => (
                        <li key={idx} className="text-foreground">{feature}</li>
                      ))}
                    </ul>
                  </div>
                  
                  {analysisResult.product.pricing && (
                    <div>
                      <h3 className="text-sm font-medium text-muted-foreground mb-2">Pricing</h3>
                      <p className="text-foreground">{analysisResult.product.pricing}</p>
                    </div>
                  )}
                  
                  {analysisResult.product.target_audience && (
                    <div>
                      <h3 className="text-sm font-medium text-muted-foreground mb-2">Target Audience</h3>
                      <p className="text-foreground">{analysisResult.product.target_audience}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Competitors Tab */}
            <TabsContent value="competitors" className="mt-6 space-y-4">
              {analysisResult.top_competitors.length === 0 ? (
                <Card className="glass border-border/50">
                  <CardContent className="pt-6 text-center text-muted-foreground">
                    No competitors found. This might be a very niche market or the search needs refinement.
                  </CardContent>
                </Card>
              ) : (
                <>
                  {/* Classification Summary */}
                  {analysisResult.market_insights?.direct_competitors !== undefined && (
                    <Card className="glass border-border/50 bg-gradient-to-r from-primary/5 to-secondary/5">
                      <CardHeader>
                        <CardTitle className="text-lg">Competitor Classification</CardTitle>
                        <CardDescription>Competitors categorized by similarity to your product</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid gap-4 md:grid-cols-3">
                          <div className="p-4 rounded-lg bg-background/50 border border-border">
                            <div className="text-2xl font-bold mb-1">{analysisResult.market_insights.total_competitors}</div>
                            <div className="text-sm text-muted-foreground">Total Competitors</div>
                          </div>
                          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                            <div className="text-2xl font-bold text-red-600 mb-1">{analysisResult.market_insights.direct_competitors}</div>
                            <div className="text-sm text-muted-foreground">Direct Competitors</div>
                          </div>
                          <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                            <div className="text-2xl font-bold text-yellow-600 mb-1">{analysisResult.market_insights.indirect_competitors}</div>
                            <div className="text-sm text-muted-foreground">Indirect Competitors</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Filter Buttons */}
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        const directComps = analysisResult.top_competitors.filter(c => c.competitor_type === 'direct');
                        if (directComps.length > 0) {
                          // Scroll to first direct competitor
                          document.getElementById('competitor-0')?.scrollIntoView({ behavior: 'smooth' });
                        }
                      }}
                    >
                      <span className="w-2 h-2 rounded-full bg-red-500 mr-2"></span>
                      Direct Only
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        const indirectComps = analysisResult.top_competitors.filter(c => c.competitor_type === 'indirect');
                        if (indirectComps.length > 0) {
                          // Scroll to first indirect competitor
                          const firstIndirectIndex = analysisResult.top_competitors.findIndex(c => c.competitor_type === 'indirect');
                          document.getElementById(`competitor-${firstIndirectIndex}`)?.scrollIntoView({ behavior: 'smooth' });
                        }
                      }}
                    >
                      <span className="w-2 h-2 rounded-full bg-yellow-500 mr-2"></span>
                      Indirect Only
                    </Button>
                  </div>

                  {/* Competitors List */}
                  {
                analysisResult.top_competitors.map((competitor, index) => (
                  <Card 
                    key={index} 
                    id={`competitor-${index}`}
                    className="glass border-border/50 hover:border-primary/30 transition-colors"
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-lg">{competitor.name}</h3>
                            {competitor.url && (
                              <a
                                href={competitor.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:text-primary/80"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </a>
                            )}
                            {competitor.competitor_type && (
                              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                competitor.competitor_type === 'direct' 
                                  ? 'bg-red-500/20 text-red-600 border border-red-500/30' 
                                  : 'bg-yellow-500/20 text-yellow-600 border border-yellow-500/30'
                              }`}>
                                {competitor.competitor_type === 'direct' ? 'Direct' : 'Indirect'}
                              </span>
                            )}

                          </div>
                          <p className="text-xs text-muted-foreground">Source: {competitor.source}</p>
                        </div>
                        {competitor.pricing && (
                          <div className="text-right bg-secondary px-3 py-1 rounded">
                            <div className="text-sm font-medium">{competitor.pricing}</div>
                          </div>
                        )}
                      </div>
                      
                      <p className="text-sm mb-3 text-muted-foreground">{competitor.description}</p>
                      
                      {competitor.features && competitor.features.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-border/50">
                          <p className="text-xs font-medium mb-2 text-muted-foreground">Key Features:</p>
                          <div className="flex flex-wrap gap-2">
                            {competitor.features.slice(0, 6).map((feature, idx) => (
                              <span
                                key={idx}
                                className="text-xs bg-accent/50 px-2 py-1 rounded"
                              >
                                {feature}
                              </span>
                            ))}
                            {competitor.features.length > 6 && (
                              <span className="text-xs text-muted-foreground px-2 py-1">
                                +{competitor.features.length - 6} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
                </>
              )}
            </TabsContent>

            {/* Feature Comparison Tab */}
            <TabsContent value="comparison" className="mt-6 space-y-4">
              {analysisResult.feature_matrix.features.length === 0 || 
               analysisResult.feature_matrix.products.length <= 1 ? (
                <Card className="glass border-border/50">
                  <CardContent className="pt-6">
                    <div className="text-center text-muted-foreground space-y-2">
                      <p className="font-medium">Limited Feature Data Available</p>
                      <p className="text-sm">
                        We couldn't extract detailed feature information from competitors. 
                        This is common for products without public feature lists.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <>
                  <Card className="glass border-border/50">
                    <CardHeader>
                      <CardTitle>Feature Comparison Matrix</CardTitle>
                      <CardDescription>
                        Comparing {analysisResult.feature_matrix.products.length} products across {analysisResult.feature_matrix.features.length} features
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse">
                          <thead>
                            <tr className="border-b-2 border-border">
                              <th className="text-left p-3 font-semibold sticky left-0 bg-background">Feature</th>
                              {analysisResult.feature_matrix.products.map((product, idx) => (
                                <th key={idx} className="text-center p-3 font-semibold min-w-[120px]">
                                  <div className="flex flex-col items-center gap-1">
                                    <span className={product.is_user_product ? 'text-primary font-bold' : ''}>
                                      {product.name}
                                    </span>
                                    {product.is_user_product && (
                                      <span className="text-xs bg-primary/20 px-2 py-0.5 rounded">Your Product</span>
                                    )}
                                  </div>
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {analysisResult.feature_matrix.features.map((feature, idx) => (
                              <tr key={idx} className="border-b border-border/50 hover:bg-accent/5 transition-colors">
                                <td className="p-3 text-sm font-medium sticky left-0 bg-background">{feature}</td>
                                {analysisResult.feature_matrix.products.map((product, pIdx) => (
                                  <td key={pIdx} className="text-center p-3">
                                    {product.feature_support[feature] ? (
                                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-500/20 text-green-600 font-bold">✓</span>
                                    ) : (
                                      <span className="text-muted-foreground/30 text-lg">—</span>
                                    )}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Pricing Comparison */}
                  {analysisResult.comparison.pricing.competitors.length > 0 && (
                    <Card className="glass border-border/50">
                      <CardHeader>
                        <CardTitle>Pricing Comparison</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                          <div className="p-4 rounded-lg bg-primary/10 border-2 border-primary/30">
                            <div className="text-xs font-medium text-muted-foreground mb-1">Your Product</div>
                            <div className="text-xl font-bold text-primary">
                              {analysisResult.comparison.pricing.user_product}
                            </div>
                          </div>
                          {analysisResult.comparison.pricing.competitors.map((comp, idx) => (
                            <div key={idx} className="p-4 rounded-lg bg-secondary border border-border">
                              <div className="text-xs font-medium text-muted-foreground mb-1">{comp.name}</div>
                              <div className="text-xl font-bold">{comp.pricing}</div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              )}
            </TabsContent>

            {/* Market Analysis Tab */}
            <TabsContent value="analysis" className="mt-6 space-y-4">
              {/* Market Position */}
              <Card className="glass border-border/50">
                <CardHeader>
                  <CardTitle>Market Position</CardTitle>
                  <CardDescription>Honest assessment of where you stand</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed">{analysisResult.insights.market_position}</p>
                </CardContent>
              </Card>

              {/* Two Column Layout */}
              <div className="grid gap-4 md:grid-cols-2">
                {/* What You're Up Against */}
                {analysisResult.gap_analysis.areas_to_improve && 
                 analysisResult.gap_analysis.areas_to_improve.length > 0 && (
                  <Card className="glass border-border/50">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-orange-600">
                        <Target className="h-5 w-5" />
                        Challenges
                      </CardTitle>
                      <CardDescription>What you're up against</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {analysisResult.gap_analysis.areas_to_improve.map((area, index) => (
                          <li key={index} className="text-sm flex items-start gap-2">
                            <span className="text-orange-500 mt-0.5">▸</span>
                            <span>{area}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* Opportunities */}
                {analysisResult.gap_analysis.opportunities && 
                 analysisResult.gap_analysis.opportunities.length > 0 && (
                  <Card className="glass border-border/50">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-green-600">
                        <Target className="h-5 w-5" />
                        Opportunities
                      </CardTitle>
                      <CardDescription>Where you could win</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {analysisResult.gap_analysis.opportunities.map((opp, index) => (
                          <li key={index} className="text-sm flex items-start gap-2">
                            <span className="text-green-500 mt-0.5">▸</span>
                            <span>{opp}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}
              </div>

              {/* Strategy & Recommendations */}
              <Card className="glass border-border/50">
                <CardHeader>
                  <CardTitle>Recommendations</CardTitle>
                  <CardDescription>What to focus on</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {analysisResult.insights.differentiation_strategy && (
                    <div>
                      <h3 className="font-semibold mb-2 text-sm">Differentiation Strategy</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {analysisResult.insights.differentiation_strategy}
                      </p>
                    </div>
                  )}
                  
                  {analysisResult.insights.recommendations && 
                   analysisResult.insights.recommendations.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-2 text-sm">Action Items</h3>
                      <ul className="space-y-2">
                        {analysisResult.insights.recommendations.map((rec, index) => (
                          <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-primary mt-0.5 font-bold">→</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
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

  // Show input form if no results
  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center space-y-2 mb-8">
          <h1 className="text-3xl font-bold">Competitor Analysis</h1>
          <p className="text-muted-foreground">
            Discover competitors and identify market opportunities
          </p>
        </div>

        {/* Form */}
        <Card className="glass border-border/50">
          <CardContent className="pt-6 space-y-6">
            {/* Product Name */}
            <div className="space-y-2">
              <Label htmlFor="productName" className="text-base">Product Name *</Label>
              <Input
                id="productName"
                placeholder="e.g., TaskMaster Pro"
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                disabled={isAnalyzing}
                className="glass border-border/50 focus:border-primary transition-all duration-300"
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-base">Description *</Label>
              <Textarea
                id="description"
                placeholder="Describe what your product does and who it's for..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={isAnalyzing}
                rows={4}
                className="resize-none glass border-border/50 focus:border-primary transition-all duration-300"
              />
            </div>

            {/* Features */}
            <div className="space-y-2">
              <Label className="text-base">Key Features *</Label>
              <div className="space-y-2">
                {features.map((feature, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      placeholder={`Feature ${index + 1}`}
                      value={feature}
                      onChange={(e) => updateFeature(index, e.target.value)}
                      disabled={isAnalyzing}
                      className="glass border-border/50 focus:border-primary transition-all duration-300"
                    />
                    {features.length > 1 && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeFeature(index)}
                        disabled={isAnalyzing}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addFeature}
                  disabled={isAnalyzing}
                  className="glass border-border/50 hover:border-primary transition-all duration-300"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Feature
                </Button>
              </div>
            </div>

            {/* Optional Fields Section */}
            <div className="space-y-4 pt-4 border-t border-border/50">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                Optional Information
              </h3>

              {/* Pricing (Optional) */}
              <div className="space-y-2">
                <Label htmlFor="pricing">Pricing (Optional)</Label>
                <Input
                  id="pricing"
                  placeholder="e.g., $9/month or Free"
                  value={pricing}
                  onChange={(e) => setPricing(e.target.value)}
                  disabled={isAnalyzing}
                  className="glass border-border/50 focus:border-primary transition-all duration-300"
                />
                <p className="text-xs text-muted-foreground">
                  Your pricing model or plan
                </p>
              </div>

              {/* Target Audience (Optional) */}
              <div className="space-y-2">
                <Label htmlFor="targetAudience">Target Audience (Optional)</Label>
                <Input
                  id="targetAudience"
                  placeholder="e.g., Small businesses, Developers"
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  disabled={isAnalyzing}
                  className="glass border-border/50 focus:border-primary transition-all duration-300"
                />
                <p className="text-xs text-muted-foreground">
                  Who your product is designed for
                </p>
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="button"
              size="lg"
              className="w-full bg-gradient-to-r from-accent to-primary text-white glow hover:glow-sm hover:scale-[1.02] transition-all duration-300 font-semibold text-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              onClick={handleAnalyze}
              disabled={isAnalyzing}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Analyzing... (60-90s)
                </>
              ) : (
                <>
                  <Target className="mr-2 h-5 w-5" />
                  Analyze Competitors
                </>
              )}
            </Button>

            {isAnalyzing && (
              <div className="text-center space-y-1">
                <p className="text-sm text-muted-foreground">
                  Discovering competitors from multiple sources...
                </p>
                <p className="text-xs text-muted-foreground">
                  This may take 60-90 seconds
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
