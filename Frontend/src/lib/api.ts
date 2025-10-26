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
      }>(`/api/processing-status/${inputId}`),
    
    getAllProcessingStatus: () =>
      apiRequest<{
        processing_status: any[];
        total_inputs: number;
      }>('/api/processing-status/'),
  },
};

export { ApiError };
export default api;