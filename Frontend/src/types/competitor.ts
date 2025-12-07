/**
 * TypeScript types for Competitor Analysis Module
 */

// Analysis Status
export type AnalysisStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

// Product for analysis
export interface Product {
  id: string;
  user_id: string;
  product_name: string;
  product_description: string;
  key_features: string[];
  created_at: string;
  updated_at: string;
  latest_analysis?: {
    analysis_id: string;
    competitors_found: number;
    status: AnalysisStatus;
    created_at: string;
  };
}

// Product form data
export interface ProductFormData {
  productName: string;
  productDescription: string;
  keyFeatures: string[];
}

// Competitor information
export interface Competitor {
  name: string;
  description: string;
  source: 'app_store' | 'play_store' | 'github' | 'web';
  url?: string;
  rating?: number;
  rating_count?: number;
  price?: number;
  installs?: string;
  stars?: number;
  forks?: number;
  features?: string[];
  strengths?: string[];
  weaknesses?: string[];
  market_position?: 'leader' | 'challenger' | 'niche' | 'emerging';
}

// Competitive analysis result
export interface CompetitiveAnalysis {
  analysis_id: string;
  product_id: string;
  user_id: string;
  status: AnalysisStatus;
  competitors: Competitor[];
  market_insights: {
    total_competitors: number;
    market_saturation: 'low' | 'medium' | 'high';
    opportunity_score: number;
    key_trends: string[];
  };
  positioning_analysis: {
    your_strengths: string[];
    your_weaknesses: string[];
    opportunities: string[];
    threats: string[];
  };
  feature_comparison: {
    feature: string;
    your_product: boolean;
    competitors_with_feature: number;
    competitive_advantage: 'strong' | 'moderate' | 'weak';
  }[];
  recommendations: string[];
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

// Analysis history item
export interface AnalysisHistoryItem {
  analysis_id: string;
  product_id: string;
  competitors_found: number;
  opportunity_score: number;
  status: AnalysisStatus;
  created_at: string;
  completed_at: string | null;
}
