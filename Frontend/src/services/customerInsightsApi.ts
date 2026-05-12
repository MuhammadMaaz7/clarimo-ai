/**
 * Customer Insights API Service
 * Handles all API calls for the Customer Insights module
 */

const API_BASE_URL = 'http://localhost:8000/api';

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public isTokenExpired: boolean = false
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('auth_token');

  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (response.status === 401) {
      localStorage.removeItem('auth_token');
      globalThis.dispatchEvent(new CustomEvent('auth:token-expired'));
      setTimeout(() => {
        globalThis.location.href = '/login';
      }, 100);
      throw new ApiError('Your session has expired. Please log in again.', 401, true);
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      let errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
      
      if (response.status === 500) {
        errorMessage = 'An error occurred while processing your request. Please try again.';
      } else if (response.status === 503) {
        errorMessage = 'Service temporarily unavailable. Please try again in a moment.';
      }
      
      throw new ApiError(errorMessage, response.status);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError(
        'Unable to connect to the server. Please check your internet connection.',
        0
      );
    }
    
    throw new ApiError('An unexpected error occurred. Please try again.', 0);
  }
}

export const customerInsightsApi = {
  // Start a new analysis
  startAnalysis: (data: {
    startupIdea: string;
    targetMarket?: string;
  }) =>
    apiRequest<{
      success: boolean;
      analysis_id: string;
      message: string;
      status: string;
    }>('/customer-insights/analyze', {
      method: 'POST',
      body: JSON.stringify({
        startup_idea: data.startupIdea,
        target_market: data.targetMarket,
      }),
    }),

  // Get analysis status
  getStatus: (analysisId: string) =>
    apiRequest<{
      analysis_id: string;
      status: string;
      current_stage: string;
      progress_percentage: number;
      message: string;
      created_at: string;
      estimated_completion: string | null;
    }>(`/customer-insights/status/${analysisId}`),

  // Get complete analysis results
  getAnalysis: (analysisId: string) =>
    apiRequest<{
      analysis_id: string;
      startup_idea: string;
      target_market: string | null;
      status: string;
      current_stage: string;
      progress_percentage: number;
      created_at: string;
      completed_at: string | null;
      execution_time: number | null;
      total_discussions: number;
      communities: Array<{
        name: string;
        source: string;
        discussion_count: number;
        engagement_score: number;
        url: string | null;
        description: string | null;
      }>;
      segments: Array<{
        segment_id: string;
        segment_name: string;
        summary: string;
        pain_points: string[];
        interests: string[];
        discussion_count: number;
      }>;
      insights: {
        pain_points: string[];
        desired_features: string[];
        recurring_themes: string[];
        keywords: string[];
      };
      error_message: string | null;
    }>(`/customer-insights/analysis/${analysisId}`),

  // Get analysis history
  getHistory: () =>
    apiRequest<Array<{
      analysis_id: string;
      startup_idea: string;
      status: string;
      created_at: string;
      completed_at: string | null;
      communities_found: number;
      segments_found: number;
    }>>('/customer-insights/history'),

  // Delete analysis
  deleteAnalysis: (analysisId: string) =>
    apiRequest<{
      success: boolean;
      message: string;
      analysis_id: string;
    }>(`/customer-insights/analysis/${analysisId}`, {
      method: 'DELETE',
    }),

  // Get communities for an analysis
  getCommunities: (analysisId: string) =>
    apiRequest<{
      analysis_id: string;
      communities: Array<{
        name: string;
        source: string;
        discussion_count: number;
        engagement_score: number;
        url: string | null;
        description: string | null;
      }>;
      total_communities: number;
    }>(`/customer-insights/communities/${analysisId}`),

  // Get top communities
  getTopCommunities: (analysisId: string, limit: number = 10) =>
    apiRequest<{
      analysis_id: string;
      top_communities: Array<{
        name: string;
        source: string;
        discussion_count: number;
        engagement_score: number;
        url: string | null;
        description: string | null;
      }>;
      total_communities: number;
    }>(`/customer-insights/communities/${analysisId}/top?limit=${limit}`),

  // Get segments for an analysis
  getSegments: (analysisId: string) =>
    apiRequest<{
      analysis_id: string;
      segments: Array<{
        segment_id: string;
        segment_name: string;
        summary: string;
        pain_points: string[];
        interests: string[];
        discussion_count: number;
      }>;
      total_segments: number;
    }>(`/customer-insights/segments/${analysisId}`),

  // Get segment details
  getSegmentDetails: (segmentId: string) =>
    apiRequest<{
      segment_id: string;
      segment_name: string;
      summary: string;
      pain_points: string[];
      interests: string[];
      discussion_count: number;
      cluster_id: number | null;
      created_at: string;
    }>(`/customer-insights/segments/segment/${segmentId}`),
};

export default customerInsightsApi;
