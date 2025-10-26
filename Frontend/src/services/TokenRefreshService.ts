/**
 * TokenRefreshService - Handles token refresh operations with retry logic and error handling
 * 
 * Features:
 * - Exponential backoff retry strategy
 * - Concurrent request deduplication
 * - Error categorization and recovery
 * - Network error handling
 */

export interface RefreshResult {
  success: boolean;
  newToken?: string;
  error?: string;
  retryAfter?: number;
}

export interface RetryPolicy {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
}

export enum RefreshErrorType {
  NETWORK_ERROR = 'network_error',
  AUTH_ERROR = 'auth_error',
  SERVER_ERROR = 'server_error',
  VALIDATION_ERROR = 'validation_error',
  UNKNOWN_ERROR = 'unknown_error'
}

export class RefreshError extends Error {
  constructor(
    message: string,
    public type: RefreshErrorType,
    public status?: number,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = 'RefreshError';
  }
}

export class TokenRefreshService {
  private retryPolicy: RetryPolicy = {
    maxAttempts: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2
  };
  
  private _isRefreshing: boolean = false;
  private lastRefreshAttempt: Date | null = null;
  private pendingRefreshPromise: Promise<RefreshResult> | null = null;

  constructor(retryPolicy?: Partial<RetryPolicy>) {
    if (retryPolicy) {
      this.retryPolicy = { ...this.retryPolicy, ...retryPolicy };
    }
  }

  // Main token refresh method with deduplication
  async refreshToken(currentToken: string): Promise<RefreshResult> {
    // If a refresh is already in progress, return the existing promise
    if (this.pendingRefreshPromise) {
      console.log('Token refresh already in progress, waiting for result');
      return this.pendingRefreshPromise;
    }

    // Create new refresh promise
    this.pendingRefreshPromise = this.performRefresh(currentToken);
    
    try {
      const result = await this.pendingRefreshPromise;
      return result;
    } finally {
      // Clear the pending promise when done
      this.pendingRefreshPromise = null;
    }
  }

  // Validate token without refresh
  async validateToken(_token: string): Promise<boolean> {
    try {
      const { api } = await import('../lib/api');
      const result = await api.auth.validateToken();
      return result.valid;
    } catch (error) {
      console.error('Token validation failed:', error);
      return false;
    }
  }

  // Configuration methods
  setRefreshEndpoint(_url: string): void {
    // Currently not used as we use the existing validate-token endpoint
    // In future implementations, this could be used for dedicated refresh endpoints
  }

  setRetryPolicy(policy: RetryPolicy): void {
    this.retryPolicy = policy;
  }

  // Status methods
  isRefreshing(): boolean {
    return this._isRefreshing;
  }

  getLastRefreshAttempt(): Date | null {
    return this.lastRefreshAttempt;
  }

  // Private implementation methods
  private async performRefresh(currentToken: string): Promise<RefreshResult> {
    this._isRefreshing = true;
    this.lastRefreshAttempt = new Date();

    let lastError: RefreshError | null = null;

    for (let attempt = 1; attempt <= this.retryPolicy.maxAttempts; attempt++) {
      try {
        console.log(`Token refresh attempt ${attempt}/${this.retryPolicy.maxAttempts}`);
        
        const result = await this.attemptRefresh(currentToken);
        
        if (result.success) {
          console.log('Token refresh successful');
          this._isRefreshing = false;
          return result;
        } else {
          throw new RefreshError(
            result.error || 'Token refresh failed',
            RefreshErrorType.AUTH_ERROR,
            undefined,
            false
          );
        }
      } catch (error) {
        lastError = this.categorizeError(error);
        console.error(`Token refresh attempt ${attempt} failed:`, lastError.message);

        // Don't retry for non-retryable errors
        if (!lastError.retryable) {
          break;
        }

        // Don't retry on the last attempt
        if (attempt === this.retryPolicy.maxAttempts) {
          break;
        }

        // Wait before retrying
        const delay = this.calculateRetryDelay(attempt);
        console.log(`Waiting ${delay}ms before retry...`);
        await this.sleep(delay);
      }
    }

    this._isRefreshing = false;
    
    return {
      success: false,
      error: lastError?.message || 'Token refresh failed after all attempts',
      retryAfter: this.calculateRetryDelay(this.retryPolicy.maxAttempts)
    };
  }

  private async attemptRefresh(currentToken: string): Promise<RefreshResult> {
    try {
      // Import API to avoid circular dependencies
      const { api } = await import('../lib/api');
      
      // Use the existing validate-token endpoint
      // In a real implementation, this would be a dedicated refresh endpoint
      const response = await api.auth.validateToken();
      
      if (response.valid) {
        return {
          success: true,
          newToken: currentToken // Token is still valid
        };
      } else {
        return {
          success: false,
          error: 'Token validation failed'
        };
      }
    } catch (error) {
      throw this.categorizeError(error);
    }
  }

  private categorizeError(error: any): RefreshError {
    // Handle API errors from our custom ApiError class
    if (error.name === 'ApiError') {
      if (error.status === 401 || error.status === 403) {
        return new RefreshError(
          'Authentication failed - token is invalid',
          RefreshErrorType.AUTH_ERROR,
          error.status,
          false // Don't retry auth errors
        );
      } else if (error.status >= 500) {
        return new RefreshError(
          'Server error during token refresh',
          RefreshErrorType.SERVER_ERROR,
          error.status,
          true // Retry server errors
        );
      } else if (error.status === 0) {
        return new RefreshError(
          'Network error during token refresh',
          RefreshErrorType.NETWORK_ERROR,
          error.status,
          true // Retry network errors
        );
      }
    }

    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return new RefreshError(
        'Network connection failed',
        RefreshErrorType.NETWORK_ERROR,
        undefined,
        true
      );
    }

    // Handle timeout errors
    if (error.name === 'AbortError' || error.message.includes('timeout')) {
      return new RefreshError(
        'Request timeout',
        RefreshErrorType.NETWORK_ERROR,
        undefined,
        true
      );
    }

    // Default to unknown error
    return new RefreshError(
      error.message || 'Unknown error during token refresh',
      RefreshErrorType.UNKNOWN_ERROR,
      undefined,
      true
    );
  }

  private calculateRetryDelay(attempt: number): number {
    const delay = this.retryPolicy.baseDelay * Math.pow(this.retryPolicy.backoffMultiplier, attempt - 1);
    return Math.min(delay, this.retryPolicy.maxDelay);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Method to handle refresh with custom retry logic for specific scenarios
  async refreshTokenWithCustomRetry(
    currentToken: string,
    customRetryPolicy?: Partial<RetryPolicy>
  ): Promise<RefreshResult> {
    const originalPolicy = { ...this.retryPolicy };
    
    if (customRetryPolicy) {
      this.retryPolicy = { ...this.retryPolicy, ...customRetryPolicy };
    }
    
    try {
      return await this.refreshToken(currentToken);
    } finally {
      this.retryPolicy = originalPolicy;
    }
  }

  // Method to check if we should attempt refresh based on error history
  shouldAttemptRefresh(): boolean {
    if (!this.lastRefreshAttempt) {
      return true;
    }

    // Don't attempt refresh if the last attempt was very recent (within 30 seconds)
    const timeSinceLastAttempt = Date.now() - this.lastRefreshAttempt.getTime();
    const minRetryInterval = 30 * 1000; // 30 seconds

    return timeSinceLastAttempt >= minRetryInterval;
  }

  // Method to reset refresh state (useful for testing or manual reset)
  reset(): void {
    this._isRefreshing = false;
    this.lastRefreshAttempt = null;
    this.pendingRefreshPromise = null;
  }

  // Method to get refresh statistics
  getRefreshStats(): {
    isRefreshing: boolean;
    lastAttempt: Date | null;
    retryPolicy: RetryPolicy;
  } {
    return {
      isRefreshing: this._isRefreshing,
      lastAttempt: this.lastRefreshAttempt,
      retryPolicy: { ...this.retryPolicy }
    };
  }
}

// Singleton instance
let tokenRefreshServiceInstance: TokenRefreshService | null = null;

export const getTokenRefreshService = (): TokenRefreshService => {
  if (!tokenRefreshServiceInstance) {
    tokenRefreshServiceInstance = new TokenRefreshService();
  }
  return tokenRefreshServiceInstance;
};

export const initializeTokenRefreshService = (retryPolicy?: Partial<RetryPolicy>): TokenRefreshService => {
  tokenRefreshServiceInstance = new TokenRefreshService(retryPolicy);
  return tokenRefreshServiceInstance;
};