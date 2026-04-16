/**
 * Competitor Analysis Page
 * Unified Standalone Experience
 */

import { useState } from 'react';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Plus, X, Target, ExternalLink, Info } from 'lucide-react';
import { useCompetitorAnalysis } from '../hooks/useCompetitorAnalysis';
import { PremiumCard } from '../components/ui/premium/PremiumCard';
import { PremiumButton } from '../components/ui/premium/PremiumButton';
import { motion, AnimatePresence } from 'framer-motion';
import { ModuleHeader } from '../components/ui/ModuleHeader';

export default function CompetitorAnalysis() {
  const [resultsTab, setResultsTab] = useState('competitors');
  
  const {
    analysisResult,
    isAnalyzing,
    productName,
    setProductName,
    description,
    setDescription,
    features,
    addFeature,
    removeFeature,
    updateFeature,
    pricing,
    setPricing,
    targetAudience,
    setTargetAudience,
    startAnalysis,
    reset,
  } = useCompetitorAnalysis();

  const handleAnalyze = async () => {
    if (!productName.trim() || !description.trim() || features.filter(f => f.trim()).length === 0) {
      return;
    }
    await startAnalysis();
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  // Show Results View
  if (analysisResult) {
    return (
      <div className="responsive-container-dashboard">
        <motion.div 
          initial="hidden" 
          animate="visible" 
          variants={containerVariants}
          className="max-w-6xl mx-auto space-y-8"
        >
          <ModuleHeader
            icon={Target}
            title="Competitor Analysis"
            description="Decode market dominance and identify strategic gaps with AI-powered competitor intelligence."
            actions={
              <PremiumButton onClick={reset} variant="outlined">
                <Plus className="mr-2 h-4 w-4" />
                New Analysis
              </PremiumButton>
            }
          />

          {/* Results Tabs */}
          <Tabs value={resultsTab} onValueChange={setResultsTab} className="w-full">
            <TabsList className="grid w-full max-w-3xl grid-cols-4 bg-white/5 border border-white/10 p-1 rounded-2xl">
              <TabsTrigger value="product" className="rounded-xl data-[state=active]:bg-white/10 data-[state=active]:text-white">Product Info</TabsTrigger>
              <TabsTrigger value="competitors" className="rounded-xl data-[state=active]:bg-white/10 data-[state=active]:text-white">Competitors</TabsTrigger>
              <TabsTrigger value="comparison" className="rounded-xl data-[state=active]:bg-white/10 data-[state=active]:text-white">Feature Matrix</TabsTrigger>
              <TabsTrigger value="analysis" className="rounded-xl data-[state=active]:bg-white/10 data-[state=active]:text-white">Strategy</TabsTrigger>
            </TabsList>

            {/* Product Info Tab */}
            <TabsContent value="product" className="mt-8">
              <PremiumCard variant="default">
                <div className="space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-2">
                       <h3 className="text-xs font-bold uppercase tracking-widest text-primary">Core Proposition</h3>
                       <p className="text-2xl font-bold">{analysisResult.product.name}</p>
                       <p className="text-muted-foreground leading-relaxed mt-2">{analysisResult.product.description}</p>
                    </div>
                    <div className="space-y-2">
                       <h3 className="text-xs font-bold uppercase tracking-widest text-primary">Strategic Features</h3>
                        <div className="flex flex-wrap gap-2 pt-2">
                          {analysisResult.product.features.map((feature: string, idx: number) => (
                            <span key={idx} className="px-3 py-1 bg-white/5 rounded-full text-sm border border-white/10">{feature}</span>
                          ))}
                        </div>
                    </div>
                  </div>
                  
                  <div className="h-px bg-white/5 w-full" />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8 opacity-80">
                    <div>
                       <h3 className="text-xs font-bold uppercase tracking-widest text-white/40 mb-1">Target Audience</h3>
                       <p className="text-base font-semibold">{analysisResult.product.target_audience || 'Not Specified'}</p>
                    </div>
                    <div>
                       <h3 className="text-xs font-bold uppercase tracking-widest text-white/40 mb-1">Pricing Model</h3>
                       <p className="text-base font-semibold">{analysisResult.product.pricing || 'Not Specified'}</p>
                    </div>
                  </div>
                </div>
              </PremiumCard>
            </TabsContent>

            {/* Competitors Tab */}
            <TabsContent value="competitors" className="mt-8 space-y-6">
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {analysisResult.top_competitors.map((competitor, index) => (
                  <PremiumCard key={index} glow className="group flex flex-col h-full">
                    <div className="flex-1 space-y-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-bold text-xl truncate pr-2">{competitor.name}</h3>
                            {competitor.competitor_type && (
                              <span className={`text-[10px] uppercase font-black px-2 py-0.5 rounded ${
                                competitor.competitor_type === 'direct' 
                                  ? 'bg-red-500/10 text-red-500 border border-red-500/20' 
                                  : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                              }`}>
                                {competitor.competitor_type}
                              </span>
                            )}
                          </div>
                        </div>
                        {competitor.url && (
                          <PremiumButton variant="ghost" size="icon" className="h-8 w-8" onClick={() => window.open(competitor.url, '_blank')}>
                            <ExternalLink className="h-4 w-4" />
                          </PremiumButton>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground/80 line-clamp-3 leading-relaxed">
                        {competitor.description}
                      </p>
                    </div>
                    {competitor.pricing && (
                      <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between">
                         <span className="text-[10px] uppercase tracking-tighter text-white/30 font-bold">Estimated Cost</span>
                         <span className="text-xs font-black text-primary">{competitor.pricing}</span>
                      </div>
                    )}
                  </PremiumCard>
                ))}
              </div>
            </TabsContent>

            {/* Comparison Tab */}
            <TabsContent value="comparison" className="mt-8">
               <PremiumCard variant="default" className="overflow-hidden p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="bg-white/5">
                          <th className="text-left p-6 font-bold text-sm uppercase tracking-widest text-white/40 sticky left-0 bg-[#0c0c0c] z-20 w-64">Competitive Vector</th>
                          {analysisResult.feature_matrix.products.map((product, idx) => (
                            <th key={idx} className="p-6 font-extrabold text-lg min-w-[200px] border-l border-white/5">
                                <span className={product.is_user_product ? 'text-primary' : 'text-white'}>
                                  {product.name}
                                </span>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {analysisResult.feature_matrix.features.map((feature, idx) => (
                          <tr key={idx} className="hover:bg-white/[0.02]">
                            <td className="p-6 text-sm font-semibold sticky left-0 bg-[#0c0c0c] z-10 border-r border-white/5">{feature}</td>
                            {analysisResult.feature_matrix.products.map((product, pIdx) => (
                              <td key={pIdx} className="p-6 text-center border-l border-white/5">
                                {product.feature_support[feature] ? (
                                  <div className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-green-500/10 text-green-500">
                                    <Plus className="h-4 w-4" />
                                  </div>
                                ) : (
                                  <span className="text-white/10">—</span>
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
               </PremiumCard>
            </TabsContent>

            {/* Analysis Tab */}
            <TabsContent value="analysis" className="mt-8 grid gap-8 md:grid-cols-2">
               <PremiumCard variant="default" className="md:col-span-2">
                 <div className="flex items-center gap-3 mb-6">
                    <Info className="h-5 w-5 text-primary" />
                    <h3 className="text-xl font-bold">Strategic Market Positioning</h3>
                 </div>
                 <p className="text-lg text-muted-foreground/90 italic">
                   "{analysisResult.insights.market_position}"
                 </p>
               </PremiumCard>
               {/* Simplified Gap Analysis */}
               <PremiumCard variant="glass" className="border-orange-500/10">
                 <h3 className="text-sm font-bold uppercase tracking-widest text-orange-500 mb-6">Structural Vulnerabilities</h3>
                 <ul className="space-y-4">
                    {analysisResult.gap_analysis.areas_to_improve.map((area, index) => (
                      <li key={index} className="flex gap-4 p-3 rounded-xl bg-orange-500/5 text-sm">
                        <span className="text-orange-500 font-black">!</span>
                        <span className="text-white/80">{area}</span>
                      </li>
                    ))}
                 </ul>
               </PremiumCard>

               <PremiumCard variant="glass" className="border-green-500/10">
                 <h3 className="text-sm font-bold uppercase tracking-widest text-green-500 mb-6">Strategic Windows</h3>
                 <ul className="space-y-4">
                    {analysisResult.gap_analysis.opportunities.map((opp, index) => (
                      <li key={index} className="flex gap-4 p-3 rounded-xl bg-green-500/5 text-sm">
                        <span className="text-green-500 font-black">+</span>
                        <span className="text-white/80">{opp}</span>
                      </li>
                    ))}
                 </ul>
               </PremiumCard>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    );
  }

  // Show Input Form
  return (
    <div className="responsive-container-dashboard">
      <div className="max-w-5xl mx-auto space-y-8">
        <ModuleHeader
          icon={Target}
          title="Competitor Analysis"
          description="Deploy an algorithmic scan to map your competitive ecosystem and identify structural vulnerabilities."
        />

        <PremiumCard variant="default">
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4">
              <div className="space-y-1.5">
                <Label className="brand-label">Asset Name</Label>
                <Input
                  placeholder="e.g., TaskMaster Pro"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  disabled={isAnalyzing}
                  className="brand-input"
                />
              </div>

              <div className="space-y-1.5">
                <Label className="brand-label">Proposition Description</Label>
                <Textarea
                  placeholder="Describe the core mechanism and target user..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={isAnalyzing}
                  className="brand-textarea min-h-[80px]"
                />
              </div>
            </div>

            <div className="space-y-3">
              <Label className="brand-label">Feature Vectors</Label>
              <div className="grid grid-cols-1 gap-2">
                <AnimatePresence>
                  {features.map((feature, index) => (
                    <motion.div key={index} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="flex gap-2">
                      <Input
                        placeholder={`Strategic Feature 0${index + 1}`}
                        value={feature}
                        onChange={(e) => updateFeature(index, e.target.value)}
                        disabled={isAnalyzing}
                        className="brand-input flex-1"
                      />
                      {features.length > 1 && (
                        <PremiumButton
                          variant="ghost"
                          size="icon"
                          onClick={() => removeFeature(index)}
                          disabled={isAnalyzing}
                          className="h-10 w-10 text-white/20 hover:text-red-500"
                        >
                          <X className="h-4 w-4" />
                        </PremiumButton>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>
                <PremiumButton variant="ghost" size="sm" onClick={addFeature} disabled={isAnalyzing} className="w-fit p-0 h-auto text-primary">
                  <Plus className="h-4 w-4 mr-2" />
                  Scale Analysis Vector
                </PremiumButton>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
               <div className="space-y-1.5">
                  <Label className="brand-label">Pricing Strategy</Label>
                  <Input placeholder="$19/mo" value={pricing} onChange={(e) => setPricing(e.target.value)} disabled={isAnalyzing} className="brand-input" />
               </div>
               <div className="space-y-1.5">
                  <Label className="brand-label">Market Demographics</Label>
                  <Input placeholder="e.g., Solo-Founders" value={targetAudience} onChange={(e) => setTargetAudience(e.target.value)} disabled={isAnalyzing} className="brand-input" />
               </div>
            </div>

            <PremiumButton
              size="lg"
              className="w-full h-14 text-lg font-bold"
              variant="accent"
              onClick={handleAnalyze}
              loading={isAnalyzing}
            >
               {isAnalyzing ? 'Mapping Landscapes...' : 'Deploy Intel Scan'}
            </PremiumButton>
          </div>
        </PremiumCard>
      </div>
    </div>
  );
}
