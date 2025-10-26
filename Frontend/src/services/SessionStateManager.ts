/**
 * SessionStateManager - Handles persistence and restoration of session state
 * 
 * Features:
 * - localStorage-based persistence
 * - Token storage with expiration tracking
 * - Session data serialization/deserialization
 * - Data integrity validation
 * - Automatic cleanup of expired data
 */

import { SessionState, BackgroundTask } from './TokenManager';

export interface SessionData {
  token: string;
  tokenExpiresAt: Date;
  lastActivity: Date;
  sessionState: SessionState;
  activeTasks: BackgroundTask[];
  userId: string;
  version: string; // For data migration compatibility
}

export interface TokenData {
  accessToken: string;
  refreshToken?: string;
  expiresAt: Date;
  issuedAt: Date;
  userId: string;
}

export class SessionStateManager {
  private readonly STORAGE_KEYS = {
    SESSION_STATE: 'clarimo_session_state',
    TOKEN: 'auth_token',
    TOKEN_EXPIRATION: 'auth_token_expires_at',
    LAST_ACTIVITY: 'last_activity',
    ACTIVE_TASKS: 'active_background_tasks',
    USER_ID: 'user_id'
  };

  private readonly DATA_VERSION = '1.0.0';

  constructor() {
    this.cleanupExpiredData();
  }

  // Session state persistence
  saveSessionState(state: SessionData): void {
    try {
      const serializedState = {
        ...state,
        tokenExpiresAt: state.tokenExpiresAt.toISOString(),
        lastActivity: state.lastActivity.toISOString(),
        activeTasks: state.activeTasks.map(task => ({
          ...task,
          startTime: task.startTime.toISOString()
        })),
        version: this.DATA_VERSION,
        savedAt: new Date().toISOString()
      };

      localStorage.setItem(this.STORAGE_KEYS.SESSION_STATE, JSON.stringify(serializedState));
      
      // Also save individual components for backward compatibility
      this.saveToken(state.token, state.tokenExpiresAt);
      this.saveLastActivity(state.lastActivity);
      this.saveActiveTasks(state.activeTasks);
      
      if (state.userId) {
        localStorage.setItem(this.STORAGE_KEYS.USER_ID, state.userId);
      }
    } catch (error) {
      console.error('Failed to save session state:', error);
    }
  }

  loadSessionState(): SessionData | null {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEYS.SESSION_STATE);
      if (!stored) {
        // Try to reconstruct from individual components
        return this.reconstructSessionState();
      }

      const parsed = JSON.parse(stored);
      
      // Validate data version
      if (parsed.version !== this.DATA_VERSION) {
        console.warn('Session state version mismatch, attempting migration');
        return this.migrateSessionState(parsed);
      }

      // Deserialize dates
      const sessionData: SessionData = {
        ...parsed,
        tokenExpiresAt: new Date(parsed.tokenExpiresAt),
        lastActivity: new Date(parsed.lastActivity),
        activeTasks: parsed.activeTasks.map((task: any) => ({
          ...task,
          startTime: new Date(task.startTime)
        }))
      };

      // Validate data integrity
      if (this.validateSessionData(sessionData)) {
        return sessionData;
      } else {
        console.warn('Session data validation failed, clearing state');
        this.clearSessionState();
        return null;
      }
    } catch (error) {
      console.error('Failed to load session state:', error);
      this.clearSessionState();
      return null;
    }
  }

  clearSessionState(): void {
    try {
      Object.values(this.STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key);
      });
    } catch (error) {
      console.error('Failed to clear session state:', error);
    }
  }

  // Token management
  saveToken(token: string, expiresAt: Date): void {
    try {
      localStorage.setItem(this.STORAGE_KEYS.TOKEN, token);
      localStorage.setItem(this.STORAGE_KEYS.TOKEN_EXPIRATION, expiresAt.toISOString());
    } catch (error) {
      console.error('Failed to save token:', error);
    }
  }

  getToken(): string | null {
    try {
      return localStorage.getItem(this.STORAGE_KEYS.TOKEN);
    } catch (error) {
      console.error('Failed to get token:', error);
      return null;
    }
  }

  getTokenExpiration(): Date | null {
    try {
      const expiration = localStorage.getItem(this.STORAGE_KEYS.TOKEN_EXPIRATION);
      return expiration ? new Date(expiration) : null;
    } catch (error) {
      console.error('Failed to get token expiration:', error);
      return null;
    }
  }

  isTokenExpired(): boolean {
    const expiration = this.getTokenExpiration();
    if (!expiration) return true;
    
    return Date.now() >= expiration.getTime();
  }

  getTokenTimeRemaining(): number {
    const expiration = this.getTokenExpiration();
    if (!expiration) return 0;
    
    return Math.max(0, expiration.getTime() - Date.now());
  }

  // Activity tracking
  saveLastActivity(timestamp: Date): void {
    try {
      localStorage.setItem(this.STORAGE_KEYS.LAST_ACTIVITY, timestamp.toISOString());
    } catch (error) {
      console.error('Failed to save last activity:', error);
    }
  }

  getLastActivity(): Date | null {
    try {
      const activity = localStorage.getItem(this.STORAGE_KEYS.LAST_ACTIVITY);
      return activity ? new Date(activity) : null;
    } catch (error) {
      console.error('Failed to get last activity:', error);
      return null;
    }
  }

  // Background tasks
  saveActiveTasks(tasks: BackgroundTask[]): void {
    try {
      const serializedTasks = tasks.map(task => ({
        ...task,
        startTime: task.startTime.toISOString()
      }));
      localStorage.setItem(this.STORAGE_KEYS.ACTIVE_TASKS, JSON.stringify(serializedTasks));
    } catch (error) {
      console.error('Failed to save active tasks:', error);
    }
  }

  getActiveTasks(): BackgroundTask[] {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEYS.ACTIVE_TASKS);
      if (!stored) return [];

      const parsed = JSON.parse(stored);
      return parsed.map((task: any) => ({
        ...task,
        startTime: new Date(task.startTime)
      }));
    } catch (error) {
      console.error('Failed to get active tasks:', error);
      return [];
    }
  }

  // User ID management
  saveUserId(userId: string): void {
    try {
      localStorage.setItem(this.STORAGE_KEYS.USER_ID, userId);
    } catch (error) {
      console.error('Failed to save user ID:', error);
    }
  }

  getUserId(): string | null {
    try {
      return localStorage.getItem(this.STORAGE_KEYS.USER_ID);
    } catch (error) {
      console.error('Failed to get user ID:', error);
      return null;
    }
  }

  // Data validation and integrity
  private validateSessionData(data: SessionData): boolean {
    try {
      // Check required fields
      if (!data.token || !data.tokenExpiresAt || !data.lastActivity || !data.sessionState) {
        return false;
      }

      // Check date validity
      if (isNaN(data.tokenExpiresAt.getTime()) || isNaN(data.lastActivity.getTime())) {
        return false;
      }

      // Check session state validity
      if (!Object.values(SessionState).includes(data.sessionState)) {
        return false;
      }

      // Validate active tasks
      if (data.activeTasks && Array.isArray(data.activeTasks)) {
        for (const task of data.activeTasks) {
          if (!task.id || !task.type || !task.startTime || isNaN(task.startTime.getTime())) {
            return false;
          }
        }
      }

      return true;
    } catch (error) {
      console.error('Session data validation error:', error);
      return false;
    }
  }

  // Reconstruct session state from individual components (backward compatibility)
  private reconstructSessionState(): SessionData | null {
    try {
      const token = this.getToken();
      const tokenExpiration = this.getTokenExpiration();
      const lastActivity = this.getLastActivity();
      const activeTasks = this.getActiveTasks();
      const userId = this.getUserId();

      if (!token || !tokenExpiration || !lastActivity) {
        return null;
      }

      return {
        token,
        tokenExpiresAt: tokenExpiration,
        lastActivity,
        sessionState: activeTasks.length > 0 ? SessionState.PROCESSING : SessionState.ACTIVE,
        activeTasks,
        userId: userId || '',
        version: this.DATA_VERSION
      };
    } catch (error) {
      console.error('Failed to reconstruct session state:', error);
      return null;
    }
  }

  // Migrate session state from older versions
  private migrateSessionState(oldData: any): SessionData | null {
    try {
      // For now, just try to reconstruct from individual components
      // In the future, add specific migration logic for different versions
      console.log('Migrating session state from version:', oldData.version || 'unknown');
      return this.reconstructSessionState();
    } catch (error) {
      console.error('Session state migration failed:', error);
      return null;
    }
  }

  // Cleanup expired data
  private cleanupExpiredData(): void {
    try {
      // Remove expired tokens
      if (this.isTokenExpired()) {
        console.log('Cleaning up expired token');
        localStorage.removeItem(this.STORAGE_KEYS.TOKEN);
        localStorage.removeItem(this.STORAGE_KEYS.TOKEN_EXPIRATION);
      }

      // Remove old activity data (older than 7 days)
      const lastActivity = this.getLastActivity();
      if (lastActivity) {
        const sevenDaysAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
        if (lastActivity.getTime() < sevenDaysAgo) {
          console.log('Cleaning up old activity data');
          localStorage.removeItem(this.STORAGE_KEYS.LAST_ACTIVITY);
        }
      }

      // Remove old background tasks (older than 1 day)
      const activeTasks = this.getActiveTasks();
      const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
      const validTasks = activeTasks.filter(task => task.startTime.getTime() > oneDayAgo);
      
      if (validTasks.length !== activeTasks.length) {
        console.log('Cleaning up old background tasks');
        this.saveActiveTasks(validTasks);
      }
    } catch (error) {
      console.error('Failed to cleanup expired data:', error);
    }
  }

  // Utility methods
  getStorageUsage(): { used: number; available: number; percentage: number } {
    try {
      let used = 0;
      Object.values(this.STORAGE_KEYS).forEach(key => {
        const value = localStorage.getItem(key);
        if (value) {
          used += value.length;
        }
      });

      // Estimate available space (localStorage typically has 5-10MB limit)
      const estimated = 5 * 1024 * 1024; // 5MB estimate
      
      return {
        used,
        available: estimated - used,
        percentage: (used / estimated) * 100
      };
    } catch (error) {
      console.error('Failed to calculate storage usage:', error);
      return { used: 0, available: 0, percentage: 0 };
    }
  }

  exportSessionData(): string {
    try {
      const sessionData = this.loadSessionState();
      return JSON.stringify(sessionData, null, 2);
    } catch (error) {
      console.error('Failed to export session data:', error);
      return '{}';
    }
  }

  importSessionData(data: string): boolean {
    try {
      const parsed = JSON.parse(data);
      if (this.validateSessionData(parsed)) {
        this.saveSessionState(parsed);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to import session data:', error);
      return false;
    }
  }
}

// Singleton instance
let sessionStateManagerInstance: SessionStateManager | null = null;

export const getSessionStateManager = (): SessionStateManager => {
  if (!sessionStateManagerInstance) {
    sessionStateManagerInstance = new SessionStateManager();
  }
  return sessionStateManagerInstance;
};

export const initializeSessionStateManager = (): SessionStateManager => {
  sessionStateManagerInstance = new SessionStateManager();
  return sessionStateManagerInstance;
};