/**
 * BackgroundTaskMonitor - Tracks active background processes for session protection
 * 
 * Features:
 * - Task registration and lifecycle management
 * - Status monitoring and updates
 * - Integration with processing APIs
 * - Event emission for task changes
 * - Automatic cleanup and recovery
 */

import { BackgroundTask } from './TokenManager';

export enum TaskStatus {
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum TaskType {
  PROBLEM_DISCOVERY = 'problem_discovery',
  KEYWORD_GENERATION = 'keyword_generation',
  REDDIT_FETCHING = 'reddit_fetching',
  SEMANTIC_FILTERING = 'semantic_filtering',
  EMBEDDING_GENERATION = 'embedding_generation'
}

export interface TaskStatusUpdate {
  taskId: string;
  status: TaskStatus;
  progress?: number;
  message?: string;
  timestamp: Date;
}

type TaskEventCallback = (...args: any[]) => void;

export class BackgroundTaskMonitor {
  private activeTasks: Map<string, BackgroundTask> = new Map();
  private taskStatuses: Map<string, TaskStatus> = new Map();
  private eventListeners: Map<string, TaskEventCallback[]> = new Map();
  private statusPollingIntervals: Map<string, number> = new Map();
  private isMonitoring: boolean = false;

  constructor() {
    this.startMonitoring();
  }

  // Task management
  registerTask(task: BackgroundTask): void {
    console.log(`Registering background task: ${task.id} (${task.type})`);
    
    this.activeTasks.set(task.id, task);
    this.taskStatuses.set(task.id, TaskStatus.RUNNING);
    
    // Start monitoring this task's status
    this.startTaskStatusPolling(task.id);
    
    this.emit('taskStarted', task);
    
    // Save to localStorage for persistence
    this.saveTasksToStorage();
  }

  unregisterTask(taskId: string): void {
    const task = this.activeTasks.get(taskId);
    if (task) {
      console.log(`Unregistering background task: ${taskId}`);
      
      this.activeTasks.delete(taskId);
      this.taskStatuses.delete(taskId);
      
      // Stop status polling for this task
      this.stopTaskStatusPolling(taskId);
      
      this.emit('taskCompleted', taskId);
      
      // Check if all tasks are completed
      if (this.activeTasks.size === 0) {
        this.emit('allTasksCompleted');
      }
      
      // Update localStorage
      this.saveTasksToStorage();
    }
  }

  getActiveTasks(): BackgroundTask[] {
    return Array.from(this.activeTasks.values());
  }

  hasActiveTasks(): boolean {
    return this.activeTasks.size > 0;
  }

  getTaskCount(): number {
    return this.activeTasks.size;
  }

  // Task status monitoring
  updateTaskStatus(taskId: string, status: TaskStatus, progress?: number, message?: string): void {
    const currentStatus = this.taskStatuses.get(taskId);
    
    if (currentStatus !== status) {
      console.log(`Task ${taskId} status changed: ${currentStatus} -> ${status}`);
      
      this.taskStatuses.set(taskId, status);
      
      const update: TaskStatusUpdate = {
        taskId,
        status,
        progress,
        message,
        timestamp: new Date()
      };
      
      this.emit('taskStatusChanged', update);
      
      // If task is completed or failed, unregister it
      if (status === TaskStatus.COMPLETED || status === TaskStatus.FAILED || status === TaskStatus.CANCELLED) {
        this.unregisterTask(taskId);
      }
    }
  }

  getTaskStatus(taskId: string): TaskStatus | null {
    return this.taskStatuses.get(taskId) || null;
  }

  // Event handling
  onTaskStarted(callback: (task: BackgroundTask) => void): void {
    this.on('taskStarted', callback);
  }

  onTaskCompleted(callback: (taskId: string) => void): void {
    this.on('taskCompleted', callback);
  }

  onAllTasksCompleted(callback: () => void): void {
    this.on('allTasksCompleted', callback);
  }

  onTaskStatusChanged(callback: (update: TaskStatusUpdate) => void): void {
    this.on('taskStatusChanged', callback);
  }

  // Private event system
  private on(event: string, callback: TaskEventCallback): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event)!.push(callback);
  }

  private emit(event: string, ...args: any[]): void {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(...args);
        } catch (error) {
          console.error(`Error in task event listener for ${event}:`, error);
        }
      });
    }
  }

  // Status polling for active tasks
  private startTaskStatusPolling(taskId: string): void {
    // Poll every 5 seconds to check task status
    const interval = window.setInterval(async () => {
      await this.checkTaskStatus(taskId);
    }, 5000);
    
    this.statusPollingIntervals.set(taskId, interval);
  }

  private stopTaskStatusPolling(taskId: string): void {
    const interval = this.statusPollingIntervals.get(taskId);
    if (interval) {
      clearInterval(interval);
      this.statusPollingIntervals.delete(taskId);
    }
  }

  private async checkTaskStatus(taskId: string): Promise<void> {
    try {
      // Import API to avoid circular dependencies
      const { api } = await import('../lib/api');
      
      // Check if this is a problem discovery task
      if (taskId.startsWith('problem_discovery_')) {
        const inputId = taskId.replace('problem_discovery_', '');
        const status = await api.status.getProcessingStatus(inputId);
        
        // Map processing status to task status
        let taskStatus: TaskStatus;
        switch (status.overall_status) {
          case 'completed':
            taskStatus = TaskStatus.COMPLETED;
            break;
          case 'failed':
          case 'error':
            taskStatus = TaskStatus.FAILED;
            break;
          case 'cancelled':
            taskStatus = TaskStatus.CANCELLED;
            break;
          default:
            taskStatus = TaskStatus.RUNNING;
        }
        
        this.updateTaskStatus(taskId, taskStatus, status.progress_percentage, status.message);
      }
    } catch (error) {
      console.error(`Failed to check status for task ${taskId}:`, error);
      
      // If we can't check status for too long, assume task failed
      const task = this.activeTasks.get(taskId);
      if (task) {
        const taskAge = Date.now() - task.startTime.getTime();
        const maxTaskAge = 30 * 60 * 1000; // 30 minutes
        
        if (taskAge > maxTaskAge) {
          console.warn(`Task ${taskId} has been running for too long, marking as failed`);
          this.updateTaskStatus(taskId, TaskStatus.FAILED, undefined, 'Task timeout');
        }
      }
    }
  }

  // Monitoring control
  private startMonitoring(): void {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    
    // Restore tasks from localStorage
    this.loadTasksFromStorage();
    
    console.log('Background task monitoring started');
  }

  stopMonitoring(): void {
    if (!this.isMonitoring) return;
    
    this.isMonitoring = false;
    
    // Stop all status polling
    this.statusPollingIntervals.forEach((interval) => {
      clearInterval(interval);
    });
    this.statusPollingIntervals.clear();
    
    console.log('Background task monitoring stopped');
  }

  // Persistence
  private saveTasksToStorage(): void {
    try {
      const tasksData = {
        activeTasks: Array.from(this.activeTasks.entries()).map(([id, task]) => ({
          id,
          task: {
            ...task,
            startTime: task.startTime.toISOString()
          }
        })),
        taskStatuses: Array.from(this.taskStatuses.entries())
      };
      
      localStorage.setItem('background_tasks', JSON.stringify(tasksData));
    } catch (error) {
      console.error('Failed to save background tasks to storage:', error);
    }
  }

  private loadTasksFromStorage(): void {
    try {
      const stored = localStorage.getItem('background_tasks');
      if (!stored) return;
      
      const tasksData = JSON.parse(stored);
      
      // Restore active tasks
      if (tasksData.activeTasks) {
        tasksData.activeTasks.forEach(({ id, task }: any) => {
          const restoredTask: BackgroundTask = {
            ...task,
            startTime: new Date(task.startTime)
          };
          
          this.activeTasks.set(id, restoredTask);
          
          // Start monitoring restored task
          this.startTaskStatusPolling(id);
        });
      }
      
      // Restore task statuses
      if (tasksData.taskStatuses) {
        tasksData.taskStatuses.forEach(([id, status]: [string, TaskStatus]) => {
          this.taskStatuses.set(id, status);
        });
      }
      
      console.log(`Restored ${this.activeTasks.size} background tasks from storage`);
    } catch (error) {
      console.error('Failed to load background tasks from storage:', error);
      // Clear corrupted data
      localStorage.removeItem('background_tasks');
    }
  }

  // Utility methods
  getTaskById(taskId: string): BackgroundTask | null {
    return this.activeTasks.get(taskId) || null;
  }

  getTasksByType(type: TaskType): BackgroundTask[] {
    return Array.from(this.activeTasks.values()).filter(task => task.type === type);
  }

  cancelTask(taskId: string): void {
    this.updateTaskStatus(taskId, TaskStatus.CANCELLED, undefined, 'Task cancelled by user');
  }

  cancelAllTasks(): void {
    Array.from(this.activeTasks.keys()).forEach(taskId => {
      this.cancelTask(taskId);
    });
  }

  getTaskSummary(): {
    totalTasks: number;
    runningTasks: number;
    completedTasks: number;
    failedTasks: number;
    tasksByType: Record<string, number>;
  } {
    const tasks = this.getActiveTasks();
    const summary = {
      totalTasks: tasks.length,
      runningTasks: 0,
      completedTasks: 0,
      failedTasks: 0,
      tasksByType: {} as Record<string, number>
    };

    tasks.forEach(task => {
      const status = this.getTaskStatus(task.id);
      
      switch (status) {
        case TaskStatus.RUNNING:
          summary.runningTasks++;
          break;
        case TaskStatus.COMPLETED:
          summary.completedTasks++;
          break;
        case TaskStatus.FAILED:
        case TaskStatus.CANCELLED:
          summary.failedTasks++;
          break;
      }
      
      summary.tasksByType[task.type] = (summary.tasksByType[task.type] || 0) + 1;
    });

    return summary;
  }

  // Cleanup method
  destroy(): void {
    this.stopMonitoring();
    this.activeTasks.clear();
    this.taskStatuses.clear();
    this.eventListeners.clear();
  }
}

// Singleton instance
let backgroundTaskMonitorInstance: BackgroundTaskMonitor | null = null;

export const getBackgroundTaskMonitor = (): BackgroundTaskMonitor => {
  if (!backgroundTaskMonitorInstance) {
    backgroundTaskMonitorInstance = new BackgroundTaskMonitor();
  }
  return backgroundTaskMonitorInstance;
};

export const initializeBackgroundTaskMonitor = (): BackgroundTaskMonitor => {
  if (backgroundTaskMonitorInstance) {
    backgroundTaskMonitorInstance.destroy();
  }
  backgroundTaskMonitorInstance = new BackgroundTaskMonitor();
  return backgroundTaskMonitorInstance;
};