/**
 * SessionWarning - Modal component for session expiration warnings
 * 
 * Features:
 * - Countdown timer display
 * - Stay logged in / Logout actions
 * - Auto-logout when countdown expires
 * - Non-intrusive but attention-grabbing design
 */

import { useState, useEffect } from 'react';
import { Clock, AlertTriangle, RefreshCw, LogOut } from 'lucide-react';

interface SessionWarningProps {
  isVisible: boolean;
  timeRemainingMinutes: number;
  onStayLoggedIn: () => void;
  onLogout: () => void;
  onAutoLogout?: () => void;
}

export default function SessionWarning({
  isVisible,
  timeRemainingMinutes,
  onStayLoggedIn,
  onLogout,
  onAutoLogout
}: SessionWarningProps) {
  const [timeRemaining, setTimeRemaining] = useState(timeRemainingMinutes * 60); // Convert to seconds
  const [isExtending, setIsExtending] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setTimeRemaining(timeRemainingMinutes * 60);
    }
  }, [isVisible, timeRemainingMinutes]);

  useEffect(() => {
    if (!isVisible || timeRemaining <= 0) return;

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          // Time expired, trigger auto logout
          if (onAutoLogout) {
            onAutoLogout();
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isVisible, timeRemaining, onAutoLogout]);

  const handleStayLoggedIn = async () => {
    setIsExtending(true);
    try {
      await onStayLoggedIn();
    } finally {
      setIsExtending(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getUrgencyLevel = (): 'low' | 'medium' | 'high' => {
    if (timeRemaining <= 30) return 'high';
    if (timeRemaining <= 60) return 'medium';
    return 'low';
  };

  const urgencyLevel = getUrgencyLevel();

  if (!isVisible) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        {/* Modal */}
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 animate-in fade-in-0 zoom-in-95 duration-200">
          {/* Header */}
          <div className={`px-6 py-4 border-b border-gray-200 ${
            urgencyLevel === 'high' ? 'bg-red-50' : 
            urgencyLevel === 'medium' ? 'bg-orange-50' : 'bg-yellow-50'
          }`}>
            <div className="flex items-center space-x-3">
              <div className={`p-2 rounded-full ${
                urgencyLevel === 'high' ? 'bg-red-100 text-red-600' : 
                urgencyLevel === 'medium' ? 'bg-orange-100 text-orange-600' : 'bg-yellow-100 text-yellow-600'
              }`}>
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Session Expiring Soon
                </h3>
                <p className="text-sm text-gray-600">
                  Your session will expire due to inactivity
                </p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-6">
            {/* Countdown Display */}
            <div className="text-center mb-6">
              <div className="flex items-center justify-center space-x-2 mb-2">
                <Clock className={`w-6 h-6 ${
                  urgencyLevel === 'high' ? 'text-red-500' : 
                  urgencyLevel === 'medium' ? 'text-orange-500' : 'text-yellow-500'
                }`} />
                <span className="text-sm text-gray-600">Time remaining:</span>
              </div>
              <div className={`text-4xl font-mono font-bold ${
                urgencyLevel === 'high' ? 'text-red-600' : 
                urgencyLevel === 'medium' ? 'text-orange-600' : 'text-yellow-600'
              }`}>
                {formatTime(timeRemaining)}
              </div>
            </div>

            {/* Message */}
            <div className="text-center mb-6">
              <p className="text-gray-700 mb-2">
                You've been inactive for a while. To keep your session active and protect your work:
              </p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Click "Stay Logged In" to extend your session</li>
                <li>• Any ongoing processes will continue running</li>
                <li>• Your work and progress will be preserved</li>
              </ul>
            </div>

            {/* Progress Bar */}
            <div className="mb-6">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-1000 ${
                    urgencyLevel === 'high' ? 'bg-red-500' : 
                    urgencyLevel === 'medium' ? 'bg-orange-500' : 'bg-yellow-500'
                  }`}
                  style={{ 
                    width: `${(timeRemaining / (timeRemainingMinutes * 60)) * 100}%` 
                  }}
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-3">
              <button
                onClick={handleStayLoggedIn}
                disabled={isExtending}
                className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-colors ${
                  urgencyLevel === 'high' 
                    ? 'bg-red-600 hover:bg-red-700 text-white' 
                    : urgencyLevel === 'medium'
                    ? 'bg-orange-600 hover:bg-orange-700 text-white'
                    : 'bg-yellow-600 hover:bg-yellow-700 text-white'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isExtending ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Extending...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    <span>Stay Logged In</span>
                  </>
                )}
              </button>
              
              <button
                onClick={onLogout}
                className="flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout Now</span>
              </button>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-3 bg-gray-50 rounded-b-lg">
            <p className="text-xs text-gray-500 text-center">
              This helps protect your account when you're away from your device
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

// Hook for using session warning in components
export function useSessionWarning() {
  const [isVisible, setIsVisible] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(2); // Default 2 minutes

  const showWarning = (minutes: number = 2) => {
    setTimeRemaining(minutes);
    setIsVisible(true);
  };

  const hideWarning = () => {
    setIsVisible(false);
  };

  return {
    isVisible,
    timeRemaining,
    showWarning,
    hideWarning
  };
}