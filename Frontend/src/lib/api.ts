/**
 * API Utility with Token Expiration Handling
 * Automatically handles 401 errors and token expiration
 */

const API_BASE_URL = 'http://localhost:8000';

interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  [key: string]: any;
}

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

/**
 * Enhanced fetch with automatic token handling and expiration detection
 */
async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('auth_token');
  
  // Record API activity for session management
  try {
    const { getTokenManager } = await import('../services/TokenManager');
    const tokenManager = getTokenManager();
    tokenManager.recordApiActivity();
  } catch (error) {
    // Silently fail if TokenManager is not available
    console.debug('TokenManager not available for activity recording');
  }
  
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
    
    // Handle token expiration
    if (response.status === 401) {
      const isTokenExpired = response.headers.get('x-token-expired') === 'true';
      
      if (isTokenExpired || token) {
        // Clear expired token
        localStorage.removeItem('auth_token');
        
        // Dispatch custom event for components to listen to
        globalThis.dispatchEvent(new CustomEvent('auth:token-expired'));
        
        // Redirect to login after a short delay
        setTimeout(() => {
          globalThis.location.href = '/login';
        }, 100);
        
        throw new ApiError('Your session has expired. Please log in again.', 401, true);
      }
      
      throw new ApiError('Unauthorized access', 401, false);
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || errorData.message || `HTTP ${response.status}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    
    // Network or other errors
    console.error('API Request failed:', error);
    throw new ApiError('Network error. Please check your connection.', 0);
  }
}

/**
 * API Methods
 */
export const api = {
  // Auth endpoints
  auth: {
    login: (email: string, password: string) =>
      apiRequest<{ access_token: string; user: any }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    
    signup: (email: string, password: string, full_name: string) =>
      apiRequest<{ access_token: string; user: any }>('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password, full_name }),
      }),
    
    me: () => apiRequest<any>('/auth/me'),
    
    validateToken: () => apiRequest<{ valid: boolean; user: any }>('/auth/validate-token'),
    
    updateProfile: (data: { full_name: string; email: string }) =>
      apiRequest<{ id: string; email: string; full_name: string }>('/auth/profile', {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
  },

  // Problem discovery endpoints
  problems: {
    discover: (data: {
      problemDescription: string;
      domain?: string;
      region?: string;
      targetAudience?: string;
    }) =>
      apiRequest<ApiResponse>('/problems/discover', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    validateInput: (data: {
      problemDescription: string;
      domain?: string;
      region?: string;
      targetAudience?: string;
    }) =>
      apiRequest<{
        success: boolean;
        validation: {
          is_valid: boolean;
          reason: string;
          confidence?: number;
        };
        message: string;
      }>('/problems/validate-input', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    getResults: (requestId: string) =>
      apiRequest<ApiResponse>(`/problems/results/${requestId}`),
    
    getRequests: () =>
      apiRequest<any[]>('/problems/requests'),
    
    getRequestDetails: (requestId: string) =>
      apiRequest<any>(`/problems/requests/${requestId}`),
    
    deleteRequest: (requestId: string) =>
      apiRequest<{ success: boolean; message: string }>(`/problems/requests/${requestId}`, {
        method: 'DELETE',
      }),
  },

  // Processing status endpoints
  status: {
    getProcessingStatus: (inputId: string) =>
      apiRequest<{
        input_id: string;
        overall_status: string;
        progress_percentage: number;
        current_stage: string;
        message: string;
        description: string;
        animation: string;
        next_action: string;
        stages: Record<string, any>;
        estimated_time_remaining: string;
        can_view_results: boolean;
        pain_points_available?: boolean;
        pain_points_count?: number;
      }>(`/api/processing-status/${inputId}`),
    
    getAllProcessingStatus: () =>
      apiRequest<{
        processing_status: any[];
        total_inputs: number;
      }>('/api/processing-status/'),
  },

  // Clustering endpoints
  clustering: {
    clusterPosts: (data: {
      input_id: string;
      min_cluster_size?: number;
      create_visualization?: boolean;
    }) =>
      apiRequest<{
        success: boolean;
        message: string;
        total_posts: number;
        clusters_found: number;
        clustered_posts?: number;
        noise_posts?: number;
        clusters?: Record<string, any>;
        statistics?: Record<string, any>;
        output_files?: Record<string, string>;
        clusters_directory?: string;
      }>('/api/clustering/cluster', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    getClusterResults: (inputId: string) =>
      apiRequest<{
        success: boolean;
        input_id: string;
        clusters: Record<string, any>;
        statistics: Record<string, any>;
        clustering_metadata: Record<string, any>;
        config: Record<string, any>;
        files: Record<string, string>;
        directory: string;
      }>(`/api/clustering/results/${inputId}`),
    
    listClusterResults: () =>
      apiRequest<{
        success: boolean;
        cluster_results: any[];
        total_results: number;
      }>('/api/clustering/list'),
    
    deleteClusterResults: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        deleted_directory: string;
      }>(`/api/clustering/results/${inputId}`, {
        method: 'DELETE',
      }),
    
    triggerAutoClustering: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        input_id: string;
        status: string;
      }>(`/api/clustering/auto-cluster/${inputId}`, {
        method: 'POST',
      }),
  },

  // Embedding cache endpoints
  cache: {
    getStatistics: () =>
      apiRequest<{
        success: boolean;
        cache_statistics: {
          cache_exists: boolean;
          cached_embeddings: number;
          cache_size_mb: number;
          cache_directory?: string;
        };
        explanation: {
          purpose: string;
          scope: string;
          benefit: string;
        };
      }>('/api/embeddings/cache/stats'),
    
    clear: () =>
      apiRequest<{
        success: boolean;
        message: string;
        embeddings_removed: number;
        space_freed_mb: number;
      }>('/api/embeddings/cache/clear', {
        method: 'DELETE',
      }),
  },

  // Pain points endpoints
  painPoints: {
    extract: (data: {
      input_id: string;
      output_dir?: string;
    }) =>
      apiRequest<{
        success: boolean;
        message: string;
        total_clusters: number;
        processed: number;
        failed: number;
        individual_files?: string[];
        aggregated_file?: string;
        pain_points_count?: number;
      }>('/api/pain-points/extract', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    getResults: (inputId: string, includeDomains: boolean = false) =>
      apiRequest<{
        success: boolean;
        metadata: {
          total_clusters: number;
          analysis_timestamp: number;
          user_id: string;
          input_id: string;
        };
        pain_points: Array<{
          cluster_id: string;
          problem_title: string;
          problem_description: string;
          post_references: Array<{
            post_id: string;
            subreddit: string;
            created_utc: string;
            url: string;
            text: string;
            title?: string;
            score?: number;
            num_comments?: number;
          }>;
          analysis_timestamp: number;
          source: string;
        }>;
        total_pain_points: number;
        domains?: Record<string, any>;
      }>(`/api/pain-points/results/${inputId}${includeDomains ? '?include_domains=true' : ''}`),
    
    list: () =>
      apiRequest<{
        success: boolean;
        pain_points_results: Array<{
          input_id: string;
          total_pain_points: number;
          analysis_timestamp: number;
          total_clusters: number;
          file_path: string;
        }>;
        total_results: number;
      }>('/api/pain-points/list'),
    
    getByDomain: (inputId: string) =>
      apiRequest<{
        success: boolean;
        input_id: string;
        domains: Record<string, any[]>;
        total_domains: number;
        total_pain_points: number;
      }>(`/api/pain-points/domains/${inputId}`),
    
    delete: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        deleted_files: string[];
        files_deleted: number;
      }>(`/api/pain-points/results/${inputId}`, {
        method: 'DELETE',
      }),
    
    triggerAuto: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        input_id: string;
        status: string;
      }>(`/api/pain-points/trigger-auto/${inputId}`, {
        method: 'POST',
      }),
    
    getHistory: (limit: number = 50) =>
      apiRequest<{
        success: boolean;
        history: Array<{
          input_id: string;
          original_query: string;
          pain_points_count: number;
          total_clusters: number;
          analysis_timestamp: string;
          created_at: string;
        }>;
        total_items: number;
      }>(`/api/pain-points/history?limit=${limit}`),
    
    getStats: () =>
      apiRequest<{
        success: boolean;
        stats: {
          total_analyses: number;
          total_pain_points: number;
          total_clusters: number;
          latest_analysis: string | null;
        };
      }>('/api/pain-points/stats'),
    
    getAnalysisFromDB: (inputId: string) =>
      apiRequest<{
        success: boolean;
        analysis: any;
      }>(`/api/pain-points/analysis/${inputId}`),
  },
};

export { ApiError };
export default api;