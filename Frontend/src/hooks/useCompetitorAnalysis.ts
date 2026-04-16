import { useState, useCallback, useEffect } from 'react';
import { api } from '../lib/api';
import { useSearchParams } from 'react-router-dom';
import { useAsyncAction } from './useAsyncAction';

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

export function useCompetitorAnalysis() {
  const [searchParams] = useSearchParams();
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  
  // Form state
  const [productName, setProductName] = useState('');
  const [description, setDescription] = useState('');
  const [features, setFeatures] = useState<string[]>(['']);
  const [pricing, setPricing] = useState('');
  const [targetAudience, setTargetAudience] = useState('');

  const { execute, loading } = useAsyncAction<AnalysisResult>();

  const loadAnalysis = useCallback(async (id: string) => {
    const result = await execute(() => api.competitorAnalyses.getById(id));
    if (result) setAnalysisResult(result);
  }, [execute]);

  useEffect(() => {
    const analysisId = searchParams.get('id');
    if (analysisId) {
      loadAnalysis(analysisId);
    }
  }, [searchParams, loadAnalysis]);

  const addFeature = () => setFeatures(prev => [...prev, '']);
  const removeFeature = (index: number) => setFeatures(prev => prev.filter((_, i) => i !== index));
  const updateFeature = (index: number, value: string) => {
    const newFeatures = [...features];
    newFeatures[index] = value;
    setFeatures(newFeatures);
  };

  const startAnalysis = async () => {
    const validFeatures = features.filter(f => f.trim());
    
    const result = await execute(() => api.competitorAnalyses.analyze({
      name: productName.trim(),
      description: description.trim(),
      features: validFeatures,
      pricing: pricing.trim() || undefined,
      target_audience: targetAudience.trim() || undefined,
    }));

    if (result) setAnalysisResult(result);
  };

  const reset = () => setAnalysisResult(null);

  return {
    analysisResult,
    isAnalyzing: loading,
    productName,
    setProductName,
    description,
    setDescription,
    features,
    setFeatures,
    addFeature,
    removeFeature,
    updateFeature,
    pricing,
    setPricing,
    targetAudience,
    setTargetAudience,
    startAnalysis,
    reset,
  };
}
