/**
 * API Utility with Token Expiration Handling
 * Automatically handles 401 errors and token expiration
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

  // User Input endpoints - CORRECTED
  userInputs: {
    create: (data: {
      problemDescription: string;
      domain?: string;
      region?: string;
      targetAudience?: string;
    }) =>
      apiRequest<{
        success: boolean;
        input_id: string;
        message: string;
        created_at: string;
      }>('/user-inputs/', {
        method: 'POST',
        body: JSON.stringify({
          problem_description: data.problemDescription,
          domain: data.domain,
          region: data.region,
          target_audience: data.targetAudience,
        }),
      }),
    
    getAll: () =>
      apiRequest<Array<{
        _id: string;
        user_id: string;
        input_id: string;
        problem_description: string;
        status: string;
        current_stage: string;
        created_at: string;
        updated_at: string;
      }>>('/user-inputs/'),
    
    getById: (inputId: string) =>
      apiRequest<any>(`/user-inputs/${inputId}`),
    
    delete: (inputId: string) =>
      apiRequest<{ success: boolean; message: string }>(`/user-inputs/${inputId}`, {
        method: 'DELETE',
      }),
    
    deleteAnalysis: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        deleted_records: string[];
        errors: string[];
        records_deleted: number;
        errors_count: number;
      }>(`/user-input/${inputId}/analysis`, {
        method: 'DELETE',
      }),
    
    deleteComplete: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        deleted_components: string[];
        errors: string[];
        components_deleted: number;
        errors_count: number;
      }>(`/user-inputs/${inputId}/complete`, {
        method: 'DELETE',
      }),
  },

  // Problem discovery endpoints - CORRECTED
  problems: {
    discover: (data: {
      problemDescription: string;
      domain?: string;
      region?: string;
      targetAudience?: string;
    }) =>
      apiRequest<{
        success: boolean;
        input_id: string;
        message: string;
        created_at: string;
      }>('/user-input/', {  // ✅ FIXED: Changed from '/problems/discover' to '/user-input/'
        method: 'POST',
        body: JSON.stringify({
          problem_description: data.problemDescription,
          domain: data.domain,
          region: data.region,
          target_audience: data.targetAudience,
        }),
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
      }>('/user-input/validate', {  // You might need to create this endpoint
        method: 'POST',
        body: JSON.stringify({
          problem_description: data.problemDescription,
          domain: data.domain,
          region: data.region,
          target_audience: data.targetAudience,
        }),
      }),
  },

  // Processing status endpoints - CORRECTED
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
      }>(`/processing-status/${inputId}`),  // ✅ Fixed: removed /api prefix
    
    getAllProcessingStatus: () =>
      apiRequest<{
        processing_status: any[];
        total_inputs: number;
      }>('/processing-status/'),  // ✅ Fixed: removed /api prefix
  },

  // Keyword Generation endpoints - ADDED
  keywords: {
    generate: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        keywords_data?: {
          domain_anchors: string[];
          problem_phrases: string[];
          potential_subreddits: string[];
        };
        output_file?: string;
      }>(`/keywords/generate/${inputId}`, {
        method: 'POST',
      }),
    
    getResults: (inputId: string) =>
      apiRequest<{
        success: boolean;
        keywords_data: any;
        file_path: string;
      }>(`/keywords/results/${inputId}`),
  },

  // Reddit Fetching endpoints - ADDED
  reddit: {
    fetchPosts: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        total_posts: number;
        by_query: Array<{
          query: string;
          domain_anchors_used: string[];
          problem_phrases_used: string[];
          posts: any[];
          n_posts: number;
        }>;
        by_subreddit: Array<{
          subreddit: string;
          meta: any;
          posts: any[];
          extracted_count: number;
        }>;
        output_file?: string;
      }>(`/reddit/fetch/${inputId}`, {
        method: 'POST',
      }),
    
    getResults: (inputId: string) =>
      apiRequest<any>(`/reddit/results/${inputId}`),
  },

  // Embedding endpoints - ADDED
  embeddings: {
    generate: (inputId: string, useGpu: boolean = false, batchSize: number = 32) =>
      apiRequest<{
        success: boolean;
        message: string;
        documents_processed: number;
        output_directory: string;
        files_created: string[];
      }>(`/embeddings/generate/${inputId}?use_gpu=${useGpu}&batch_size=${batchSize}`, {
        method: 'POST',
      }),
    
    getDetails: (inputId: string) =>
      apiRequest<{
        input_id: string;
        embeddings_dir: string;
        metadata: any;
        files: Array<{
          name: string;
          path: string;
          size_bytes: number;
          created_at: number;
        }>;
        total_files: number;
      }>(`/embeddings/${inputId}`),
    
    list: () =>
      apiRequest<{
        embeddings: Array<{
          input_id: string;
          document_count: number;
          created_date: string;
          directory_path: string;
          files: Record<string, string>;
        }>;
        total_embeddings: number;
      }>('/embeddings/'),
    
    delete: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
      }>(`/embeddings/${inputId}`, {
        method: 'DELETE',
      }),
  },

  // Semantic Filtering endpoints - ADDED
  semanticFiltering: {
    filter: (inputId: string, data: {
      query: string;
      domain?: string;
      top_k?: number;
      similarity_threshold?: number;
    }) =>
      apiRequest<{
        success: boolean;
        message: string;
        total_documents: number;
        filtered_documents: number;
        similarity_threshold: number;
        similarity_stats: {
          min_similarity: number;
          max_similarity: number;
          avg_similarity: number;
        };
        output_files: {
          filtered_posts: string;
          filtered_csv?: string;
          filtering_config: string;
        };
        filtered_posts_directory: string;
        query_used: string;
        no_results: boolean;
        clustering_triggered: boolean;
      }>(`/semantic-filtering/filter/${inputId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    
    getResults: (inputId: string) =>
      apiRequest<{
        success: boolean;
        input_id: string;
        filtered_posts: any[];
        filtering_config: any;
        files: Record<string, string>;
        directory: string;
      }>(`/semantic-filtering/${inputId}`),
    
    list: () =>
      apiRequest<{
        filtered_results: Array<{
          input_id: string;
          filtered_count: number;
          total_documents: number;
          query_used: string;
          similarity_threshold: number;
          created_date: string;
          similarity_stats: {
            min_similarity: number;
            max_similarity: number;
            avg_similarity: number;
          };
          files: Record<string, string>;
          directory: string;
        }>;
        total_results: number;
      }>('/semantic-filtering/'),
    
    delete: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        files_deleted: string[];
      }>(`/semantic-filtering/${inputId}`, {
        method: 'DELETE',
      }),
  },

  // Clustering endpoints - CORRECTED
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
        pain_points_extraction_success?: boolean;
      }>('/clustering/cluster', {  // ✅ Fixed: removed /api prefix
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
      }>(`/clustering/results/${inputId}`),  // ✅ Fixed: removed /api prefix
    
    listClusterResults: () =>
      apiRequest<{
        success: boolean;
        cluster_results: any[];
        total_results: number;
      }>('/clustering/list'),  // ✅ Fixed: removed /api prefix
    
    deleteClusterResults: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        deleted_directory: string;
      }>(`/clustering/results/${inputId}`, {  // ✅ Fixed: removed /api prefix
        method: 'DELETE',
      }),
    
    triggerAutoClustering: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        input_id: string;
        status: string;
      }>(`/clustering/auto-cluster/${inputId}`, {  // ✅ Fixed: removed /api prefix
        method: 'POST',
      }),
  },

  // Embedding cache endpoints - CORRECTED
  cache: {
    getStatistics: () =>
      apiRequest<{
        success: boolean;
        cache_statistics: {
          cache_exists: boolean;
          optimized_cache?: any;
          cache_directory?: string;
          cache_type?: string;
          error?: string;
        };
        explanation: {
          purpose: string;
          scope: string;
          benefit: string;
          tiers: Record<string, string>;
        };
      }>('/embeddings/cache/stats'),  // ✅ Fixed: corrected endpoint
    
    clear: (cacheType: string = 'all') =>
      apiRequest<{
        success: boolean;
        message: string;
        embeddings_removed: number;
        space_freed_mb: number;
      }>(`/embeddings/cache/clear?cache_type=${cacheType}`, {  // ✅ Fixed: corrected endpoint
        method: 'DELETE',
      }),
  },

  // Pain points endpoints - CORRECTED
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
        completed_at?: number;
        success_rate?: number;
      }>('/pain-points/extract', {  // ✅ Fixed: removed /api prefix
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
          error?: boolean;
          error_message?: string;
        }>;
        total_pain_points: number;
        domains?: Record<string, any>;
      }>(`/pain-points/results/${inputId}?include_domains=${includeDomains}`),  // ✅ Fixed: removed /api prefix
    
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
      }>('/pain-points/list'),  // ✅ Fixed: removed /api prefix
    
    getByDomain: (inputId: string) =>
      apiRequest<{
        success: boolean;
        input_id: string;
        domains: Record<string, any[]>;
        total_domains: number;
        total_pain_points: number;
      }>(`/pain-points/domains/${inputId}`),  // ✅ Fixed: removed /api prefix
    
    delete: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        deleted_files: string[];
        files_deleted: number;
      }>(`/pain-points/results/${inputId}`, {  // ✅ Fixed: removed /api prefix
        method: 'DELETE',
      }),
    
    triggerAuto: (inputId: string) =>
      apiRequest<{
        success: boolean;
        message: string;
        input_id: string;
        status: string;
      }>(`/pain-points/trigger-auto/${inputId}`, {  // ✅ Fixed: removed /api prefix
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
      }>(`/pain-points/history?limit=${limit}`),  // ✅ Fixed: removed /api prefix
    
    getStats: () =>
      apiRequest<{
        success: boolean;
        stats: {
          total_analyses: number;
          total_pain_points: number;
          total_clusters: number;
          latest_analysis: string | null;
        };
      }>('/pain-points/stats'),  // ✅ Fixed: removed /api prefix
    
    getAnalysisFromDB: (inputId: string) =>
      apiRequest<{
        success: boolean;
        analysis: any;
      }>(`/pain-points/analysis/${inputId}`),  // ✅ Fixed: removed /api prefix
  },
};

export { ApiError };
export default api;