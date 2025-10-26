/**
 * ActivityDetector - Monitors user interactions and system activity
 * 
 * Features:
 * - Passive event listeners for performance
 * - Throttled activity tracking
 * - Tab visibility detection
 * - Activity type classification
 * - Configurable monitoring options
 */

import { ActivityType } from './TokenManager';

export interface ActivityEvent {
  type: ActivityType;
  timestamp: Date;
  source: string;
}

export interface ActivityConfig {
  throttleMs: number;
  monitorMouseMovement: boolean;
  monitorKeyboard: boolean;
  monitorClicks: boolean;
  monitorApiCalls: boolean;
  monitorTabFocus: boolean;
  activityThresholdMinutes: number;
}

type ActivityCallback = (activityType: ActivityType, event?: ActivityEvent) => void;

export class ActivityDetector {
  private isMonitoring: boolean = false;
  private lastActivity: Date = new Date();
  private activityCallbacks: ActivityCallback[] = [];
  private throttleTimers: Map<ActivityType, number> = new Map();
  private isTabVisible: boolean = true;
  
  private config: ActivityConfig = {
    throttleMs: 1000,
    monitorMouseMovement: true,
    monitorKeyboard: true,
    monitorClicks: true,
    monitorApiCalls: true,
    monitorTabFocus: true,
    activityThresholdMinutes: 5
  };

  // Event listener references for cleanup
  private eventListeners: Map<string, EventListener> = new Map();

  constructor(config?: Partial<ActivityConfig>) {
    if (config) {
      this.config = { ...this.config, ...config };
    }
    
    this.setupEventListeners();
  }

  // Activity monitoring control
  startMonitoring(): void {
    if (this.isMonitoring) {
      console.log('Activity monitoring already started');
      return;
    }

    this.isMonitoring = true;
    this.attachEventListeners();
    console.log('Activity monitoring started');
  }

  stopMonitoring(): void {
    if (!this.isMonitoring) {
      console.log('Activity monitoring already stopped');
      return;
    }

    this.isMonitoring = false;
    this.detachEventListeners();
    this.clearThrottleTimers();
    console.log('Activity monitoring stopped');
  }

  // Activity status
  getLastActivity(): Date {
    return this.lastActivity;
  }

  isUserActive(): boolean {
    const thresholdMs = this.config.activityThresholdMinutes * 60 * 1000;
    return Date.now() - this.lastActivity.getTime() < thresholdMs;
  }

  // Event registration
  onActivity(callback: ActivityCallback): void {
    this.activityCallbacks.push(callback);
  }

  offActivity(callback: ActivityCallback): void {
    const index = this.activityCallbacks.indexOf(callback);
    if (index > -1) {
      this.activityCallbacks.splice(index, 1);
    }
  }

  // Configuration
  setActivityThreshold(minutes: number): void {
    this.config.activityThresholdMinutes = minutes;
  }

  setMonitoringEnabled(enabled: boolean): void {
    if (enabled) {
      this.startMonitoring();
    } else {
      this.stopMonitoring();
    }
  }

  updateConfig(config: Partial<ActivityConfig>): void {
    const wasMonitoring = this.isMonitoring;
    
    if (wasMonitoring) {
      this.stopMonitoring();
    }
    
    this.config = { ...this.config, ...config };
    
    if (wasMonitoring) {
      this.startMonitoring();
    }
  }

  // Manual activity recording (for API calls, etc.)
  recordActivity(type: ActivityType, source: string = 'manual'): void {
    if (!this.isMonitoring && type !== ActivityType.API_CALL) {
      return;
    }

    this.handleActivity(type, source);
  }

  // Private methods
  private setupEventListeners(): void {
    // Mouse movement (throttled)
    if (this.config.monitorMouseMovement) {
      this.eventListeners.set('mousemove', this.createThrottledHandler(
        ActivityType.MOUSE_MOVE,
        'mouse'
      ));
    }

    // Mouse clicks
    if (this.config.monitorClicks) {
      this.eventListeners.set('click', (_event) => {
        this.handleActivity(ActivityType.MOUSE_CLICK, 'mouse');
      });
      
      this.eventListeners.set('mousedown', (_event) => {
        this.handleActivity(ActivityType.MOUSE_CLICK, 'mouse');
      });
    }

    // Keyboard events
    if (this.config.monitorKeyboard) {
      this.eventListeners.set('keydown', this.createThrottledHandler(
        ActivityType.KEYBOARD,
        'keyboard'
      ));
      
      this.eventListeners.set('keypress', this.createThrottledHandler(
        ActivityType.KEYBOARD,
        'keyboard'
      ));
    }

    // Tab visibility
    if (this.config.monitorTabFocus) {
      this.eventListeners.set('visibilitychange', () => {
        this.isTabVisible = !document.hidden;
        
        if (this.isTabVisible) {
          this.handleActivity(ActivityType.TAB_FOCUS, 'tab');
        }
        
        console.log(`Tab visibility changed: ${this.isTabVisible ? 'visible' : 'hidden'}`);
      });

      this.eventListeners.set('focus', () => {
        this.handleActivity(ActivityType.TAB_FOCUS, 'window');
      });

      this.eventListeners.set('blur', () => {
        console.log('Window lost focus');
      });
    }

    // Touch events for mobile
    this.eventListeners.set('touchstart', (_event) => {
      this.handleActivity(ActivityType.MOUSE_CLICK, 'touch');
    });

    this.eventListeners.set('touchmove', this.createThrottledHandler(
      ActivityType.MOUSE_MOVE,
      'touch'
    ));

    // Scroll events (throttled)
    this.eventListeners.set('scroll', this.createThrottledHandler(
      ActivityType.MOUSE_MOVE,
      'scroll'
    ));
  }

  private attachEventListeners(): void {
    this.eventListeners.forEach((listener, event) => {
      if (event === 'visibilitychange') {
        document.addEventListener(event, listener, { passive: true });
      } else if (event === 'focus' || event === 'blur') {
        window.addEventListener(event, listener, { passive: true });
      } else {
        document.addEventListener(event, listener, { passive: true });
      }
    });

    // Initialize tab visibility state
    this.isTabVisible = !document.hidden;
  }

  private detachEventListeners(): void {
    this.eventListeners.forEach((listener, event) => {
      if (event === 'visibilitychange') {
        document.removeEventListener(event, listener);
      } else if (event === 'focus' || event === 'blur') {
        window.removeEventListener(event, listener);
      } else {
        document.removeEventListener(event, listener);
      }
    });
  }

  private createThrottledHandler(activityType: ActivityType, source: string): EventListener {
    return (_event: Event) => {
      const now = Date.now();
      const lastThrottle = this.throttleTimers.get(activityType) || 0;
      
      if (now - lastThrottle >= this.config.throttleMs) {
        this.throttleTimers.set(activityType, now);
        this.handleActivity(activityType, source);
      }
    };
  }

  private handleActivity(type: ActivityType, source: string): void {
    // Don't record activity if tab is not visible (except for API calls)
    if (!this.isTabVisible && type !== ActivityType.API_CALL) {
      return;
    }

    const now = new Date();
    this.lastActivity = now;

    const activityEvent: ActivityEvent = {
      type,
      timestamp: now,
      source
    };

    // Notify all callbacks
    this.activityCallbacks.forEach(callback => {
      try {
        callback(type, activityEvent);
      } catch (error) {
        console.error('Error in activity callback:', error);
      }
    });

    // Log activity (only in development)
    if (process.env.NODE_ENV === 'development') {
      console.log(`Activity detected: ${type} from ${source}`);
    }
  }

  private clearThrottleTimers(): void {
    this.throttleTimers.clear();
  }

  // Utility methods
  getActivityStats(): {
    isMonitoring: boolean;
    lastActivity: Date;
    isUserActive: boolean;
    isTabVisible: boolean;
    callbackCount: number;
    config: ActivityConfig;
  } {
    return {
      isMonitoring: this.isMonitoring,
      lastActivity: this.lastActivity,
      isUserActive: this.isUserActive(),
      isTabVisible: this.isTabVisible,
      callbackCount: this.activityCallbacks.length,
      config: { ...this.config }
    };
  }

  // Method to simulate activity (useful for testing)
  simulateActivity(type: ActivityType, source: string = 'simulation'): void {
    this.handleActivity(type, source);
  }

  // Method to get time since last activity
  getTimeSinceLastActivity(): number {
    return Date.now() - this.lastActivity.getTime();
  }

  // Method to check if specific activity types are being monitored
  isMonitoringType(type: ActivityType): boolean {
    switch (type) {
      case ActivityType.MOUSE_MOVE:
        return this.config.monitorMouseMovement;
      case ActivityType.MOUSE_CLICK:
        return this.config.monitorClicks;
      case ActivityType.KEYBOARD:
        return this.config.monitorKeyboard;
      case ActivityType.API_CALL:
        return this.config.monitorApiCalls;
      case ActivityType.TAB_FOCUS:
        return this.config.monitorTabFocus;
      default:
        return false;
    }
  }

  // Cleanup method
  destroy(): void {
    this.stopMonitoring();
    this.activityCallbacks.length = 0;
    this.eventListeners.clear();
    this.throttleTimers.clear();
  }
}

// Singleton instance
let activityDetectorInstance: ActivityDetector | null = null;

export const getActivityDetector = (): ActivityDetector => {
  if (!activityDetectorInstance) {
    activityDetectorInstance = new ActivityDetector();
  }
  return activityDetectorInstance;
};

export const initializeActivityDetector = (config?: Partial<ActivityConfig>): ActivityDetector => {
  if (activityDetectorInstance) {
    activityDetectorInstance.destroy();
  }
  activityDetectorInstance = new ActivityDetector(config);
  return activityDetectorInstance;
};