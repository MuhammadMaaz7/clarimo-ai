/**
 * TokenManager - Core component for intelligent token and session management
 * 
 * Handles:
 * - Activity-based token refresh
 * - Background task protection
 * - Session state management
 * - Event coordination
 */

import { ActivityDetector, getActivityDetector } from './ActivityDetector';

export enum SessionState {
  ACTIVE = 'active',
  IDLE = 'idle',
  PROCESSING = 'processing',
  WARNING = 'warning',
  EXPIRED = 'expired'
}

export enum ActivityType {
  MOUSE_MOVE = 'mouse_move',
  MOUSE_CLICK = 'mouse_click',
  KEYBOARD = 'keyboard',
  API_CALL = 'api_call',
  TAB_FOCUS = 'tab_focus'
}

export interface SessionConfig {
  tokenRefreshWindow: number; // minutes before expiration to start refresh
  idleTimeout: number; // minutes of inactivity before warning
  warningDuration: number; // minutes to show warning before logout
  activityThrottleMs: number;
  maxRefreshAttempts: number;
  refreshRetryDelay: number;
  enableTaskProtection: boolean;
  taskProtectionGracePeriod: number;
}

export interface BackgroundTask {
  id: string;
  type: string;
  startTime: Date;
  estimatedDuration?: number;
  description: string;
}

type EventCallback = (...args: any[]) => void;

export class TokenManager {
  private sessionState: SessionState = SessionState.ACTIVE;
  private lastActivity: Date = new Date();
  private backgroundTasks: Map<string, BackgroundTask> = new Map();
  private eventListeners: Map<string, EventCallback[]> = new Map();
  private refreshTimer: number | null = null;
  private idleTimer: number | null = null;
  private warningTimer: number | null = null;
  private isRefreshing: boolean = false;
  private activityDetector: ActivityDetector;
  
  private config: SessionConfig = {
    tokenRefreshWindow: 5, // 5 minutes before expiration
    idleTimeout: 30, // 30 minutes of inactivity
    warningDuration: 2, // 2 minutes warning
    activityThrottleMs: 1000,
    maxRefreshAttempts: 3,
    refreshRetryDelay: 1000,
    enableTaskProtection: true,
    taskProtectionGracePeriod: 5
  };

  constructor(config?: Partial<SessionConfig>) {
    if (config) {
      this.config = { ...this.config, ...config };
    }
    
    // Initialize activity detector
    this.activityDetector = getActivityDetector();
    this.setupActivityDetection();
    
    this.initializeTimers();
    this.loadSessionState();
  }

  // Core token operations
  async refreshToken(): Promise<boolean> {
    if (this.isRefreshing) {
      console.log('Token refresh already in progress');
      return false;
    }

    this.isRefreshing = true;
    
    try {
      const currentToken = this.getStoredToken();
      if (!currentToken) {
        console.log('No token found for refresh');
        return false;
      }

      // Import API dynamically to avoid circular dependencies
      const { api } = await import('../lib/api');
      
      // Use the existing validateToken endpoint as refresh mechanism
      const result = await api.auth.validateToken();
      
      if (result.valid) {
        this.emit('tokenRefreshed', currentToken);
        this.recordActivity(); // Reset activity timer on successful refresh
        console.log('Token refresh successful');
        return true;
      } else {
        console.log('Token validation failed during refresh');
        return false;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.emit('tokenExpired');
      return false;
    } finally {
      this.isRefreshing = false;
    }
  }

  async validateToken(): Promise<boolean> {
    try {
      const token = this.getStoredToken();
      if (!token) return false;

      const { api } = await import('../lib/api');
      const result = await api.auth.validateToken();
      return result.valid;
    } catch (error) {
      console.error('Token validation failed:', error);
      return false;
    }
  }

  clearToken(): void {
    localStorage.removeItem('auth_token');
    this.setSessionState(SessionState.EXPIRED);
    this.clearTimers();
    this.emit('tokenExpired');
  }

  // Session state management
  getSessionState(): SessionState {
    return this.sessionState;
  }

  setSessionState(state: SessionState): void {
    const previousState = this.sessionState;
    this.sessionState = state;
    
    console.log(`Session state changed: ${previousState} -> ${state}`);
    
    // Handle state transitions
    switch (state) {
      case SessionState.ACTIVE:
        this.startIdleTimer();
        break;
      case SessionState.IDLE:
        this.clearTimers();
        break;
      case SessionState.PROCESSING:
        this.clearIdleTimer();
        this.startRefreshTimer();
        break;
      case SessionState.WARNING:
        this.startWarningTimer();
        break;
      case SessionState.EXPIRED:
        this.clearTimers();
        break;
    }
    
    this.saveSessionState();
    this.emit('sessionStateChanged', state, previousState);
  }

  // Activity monitoring
  recordActivity(): void {
    this.lastActivity = new Date();
    
    // If we're in idle or warning state, return to active
    if (this.sessionState === SessionState.IDLE || this.sessionState === SessionState.WARNING) {
      this.setSessionState(SessionState.ACTIVE);
    }
    
    // Reset idle timer if not in processing mode
    if (this.sessionState !== SessionState.PROCESSING) {
      this.startIdleTimer();
    }
    
    // Check if we need to refresh token
    this.checkTokenRefreshNeeded();
    
    this.saveSessionState();
  }

  getLastActivity(): Date {
    return this.lastActivity;
  }

  // Background task management
  registerBackgroundTask(taskId: string, taskType: string, description: string = ''): void {
    const task: BackgroundTask = {
      id: taskId,
      type: taskType,
      startTime: new Date(),
      description
    };
    
    this.backgroundTasks.set(taskId, task);
    
    // Switch to processing mode if this is the first task
    if (this.backgroundTasks.size === 1) {
      this.setSessionState(SessionState.PROCESSING);
    }
    
    console.log(`Background task registered: ${taskId} (${taskType})`);
    this.emit('taskStarted', task);
    this.saveSessionState();
  }

  unregisterBackgroundTask(taskId: string): void {
    const task = this.backgroundTasks.get(taskId);
    if (task) {
      this.backgroundTasks.delete(taskId);
      console.log(`Background task completed: ${taskId}`);
      this.emit('taskCompleted', taskId);
      
      // If no more tasks, return to normal mode
      if (this.backgroundTasks.size === 0) {
        this.setSessionState(SessionState.ACTIVE);
        this.emit('allTasksCompleted');
      }
      
      this.saveSessionState();
    }
  }

  hasActiveBackgroundTasks(): boolean {
    return this.backgroundTasks.size > 0;
  }

  getActiveBackgroundTasks(): BackgroundTask[] {
    return Array.from(this.backgroundTasks.values());
  }

  // Event system
  on(event: string, callback: EventCallback): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(callback);
  }

  off(event: string, callback: EventCallback): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  private emit(event: string, ...args: any[]): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(...args);
        } catch (error) {
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  // Convenience methods for common events
  onTokenExpired(callback: () => void): void {
    this.on('tokenExpired', callback);
  }

  onTokenRefreshed(callback: (token: string) => void): void {
    this.on('tokenRefreshed', callback);
  }

  onSessionWarning(callback: (timeRemaining: number) => void): void {
    this.on('sessionWarning', callback);
  }

  onSessionStateChanged(callback: (newState: SessionState, oldState: SessionState) => void): void {
    this.on('sessionStateChanged', callback);
  }

  // Private helper methods
  private initializeTimers(): void {
    this.startIdleTimer();
    this.startRefreshTimer();
  }

  private startIdleTimer(): void {
    this.clearIdleTimer();
    
    // Don't start idle timer if we have background tasks
    if (this.hasActiveBackgroundTasks()) {
      return;
    }
    
    const idleTimeoutMs = this.config.idleTimeout * 60 * 1000;
    this.idleTimer = window.setTimeout(() => {
      if (!this.hasActiveBackgroundTasks()) {
        this.setSessionState(SessionState.WARNING);
        this.emit('sessionWarning', this.config.warningDuration);
      }
    }, idleTimeoutMs);
  }

  private clearIdleTimer(): void {
    if (this.idleTimer) {
      clearTimeout(this.idleTimer);
      this.idleTimer = null;
    }
  }

  private startWarningTimer(): void {
    this.clearWarningTimer();
    
    const warningTimeoutMs = this.config.warningDuration * 60 * 1000;
    this.warningTimer = window.setTimeout(() => {
      // Force logout if user didn't respond to warning
      this.clearToken();
    }, warningTimeoutMs);
  }

  private clearWarningTimer(): void {
    if (this.warningTimer) {
      clearTimeout(this.warningTimer);
      this.warningTimer = null;
    }
  }

  private startRefreshTimer(): void {
    this.clearRefreshTimer();
    
    const token = this.getStoredToken();
    if (!token) return;
    
    const tokenExpiration = this.getTokenExpiration();
    if (!tokenExpiration) return;
    
    const refreshWindowMs = this.config.tokenRefreshWindow * 60 * 1000;
    const timeUntilRefresh = tokenExpiration.getTime() - Date.now() - refreshWindowMs;
    
    if (timeUntilRefresh > 0) {
      this.refreshTimer = window.setTimeout(() => {
        this.checkTokenRefreshNeeded();
      }, timeUntilRefresh);
    } else {
      // Token is already in refresh window
      this.checkTokenRefreshNeeded();
    }
  }

  private clearRefreshTimer(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  private clearTimers(): void {
    this.clearIdleTimer();
    this.clearWarningTimer();
    this.clearRefreshTimer();
  }

  private async checkTokenRefreshNeeded(): Promise<void> {
    const tokenExpiration = this.getTokenExpiration();
    if (!tokenExpiration) return;
    
    const refreshWindowMs = this.config.tokenRefreshWindow * 60 * 1000;
    const timeUntilExpiration = tokenExpiration.getTime() - Date.now();
    
    // Refresh if we're in the refresh window and either:
    // 1. User is active (recent activity)
    // 2. Background tasks are running
    const shouldRefresh = timeUntilExpiration <= refreshWindowMs && (
      this.isRecentActivity() || this.hasActiveBackgroundTasks()
    );
    
    if (shouldRefresh) {
      const success = await this.refreshToken();
      if (success) {
        // Schedule next refresh check
        this.startRefreshTimer();
      }
    }
  }

  private isRecentActivity(): boolean {
    const activityThresholdMs = 5 * 60 * 1000; // 5 minutes
    return Date.now() - this.lastActivity.getTime() < activityThresholdMs;
  }

  private getStoredToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  private getTokenExpiration(): Date | null {
    // For now, assume tokens expire in 30 minutes from issue
    // In a real implementation, this would decode the JWT or use stored expiration
    const token = this.getStoredToken();
    if (!token) return null;
    
    // Simple heuristic: assume token was issued recently if no stored expiration
    const storedExpiration = localStorage.getItem('auth_token_expires_at');
    if (storedExpiration) {
      return new Date(storedExpiration);
    }
    
    // Default: assume 30 minutes from now (this should be improved)
    return new Date(Date.now() + 30 * 60 * 1000);
  }

  private saveSessionState(): void {
    const sessionData = {
      sessionState: this.sessionState,
      lastActivity: this.lastActivity.toISOString(),
      activeTasks: Array.from(this.backgroundTasks.values()).map(task => ({
        ...task,
        startTime: task.startTime.toISOString()
      }))
    };
    
    localStorage.setItem('session_state', JSON.stringify(sessionData));
  }

  private loadSessionState(): void {
    try {
      const stored = localStorage.getItem('session_state');
      if (stored) {
        const sessionData = JSON.parse(stored);
        
        this.lastActivity = new Date(sessionData.lastActivity);
        
        // Restore background tasks
        if (sessionData.activeTasks) {
          sessionData.activeTasks.forEach((task: any) => {
            this.backgroundTasks.set(task.id, {
              ...task,
              startTime: new Date(task.startTime)
            });
          });
        }
        
        // Determine appropriate session state
        if (this.hasActiveBackgroundTasks()) {
          this.setSessionState(SessionState.PROCESSING);
        } else {
          this.setSessionState(SessionState.ACTIVE);
        }
      }
    } catch (error) {
      console.error('Failed to load session state:', error);
      this.setSessionState(SessionState.ACTIVE);
    }
  }

  // Public method to extend session (called from warning dialog)
  extendSession(): void {
    this.recordActivity();
    this.refreshToken();
  }

  // Private method to setup activity detection
  private setupActivityDetection(): void {
    // Start monitoring user activity
    this.activityDetector.startMonitoring();
    
    // Listen for activity events
    this.activityDetector.onActivity((_activityType) => {
      this.recordActivity();
    });
    
    console.log('Activity detection integrated with TokenManager');
  }

  // Method to manually record API activity
  recordApiActivity(): void {
    this.activityDetector.recordActivity(ActivityType.API_CALL, 'api');
  }

  // Cleanup method
  destroy(): void {
    this.clearTimers();
    this.eventListeners.clear();
    this.backgroundTasks.clear();
    
    // Stop activity monitoring
    if (this.activityDetector) {
      this.activityDetector.stopMonitoring();
    }
  }
}

// Singleton instance
let tokenManagerInstance: TokenManager | null = null;

export const getTokenManager = (): TokenManager => {
  if (!tokenManagerInstance) {
    tokenManagerInstance = new TokenManager();
  }
  return tokenManagerInstance;
};

export const initializeTokenManager = (config?: Partial<SessionConfig>): TokenManager => {
  if (tokenManagerInstance) {
    tokenManagerInstance.destroy();
  }
  tokenManagerInstance = new TokenManager(config);
  return tokenManagerInstance;
};