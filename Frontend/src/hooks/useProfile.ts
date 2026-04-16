import { useState, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useAsyncAction } from './useAsyncAction';
import { unifiedToast } from '../lib/toast-utils';

interface ProfileFormData {
  fullName: string;
  email: string;
}

export function useProfile() {
  const { user, updateProfile: updateAuthProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<ProfileFormData>({
    fullName: user?.full_name || '',
    email: user?.email || ''
  });

  const { execute, loading: isSaving } = useAsyncAction({
    successMessage: 'Profile intelligence synchronized.',
    loadingMessage: 'Updating profile core...'
  });

  const updateProfile = useCallback(async () => {
    // Validation Logic
    if (!formData.fullName.trim()) {
      unifiedToast.error({ title: "Validation Error", description: "Full name is required" });
      return;
    }

    if (!formData.email.trim()) {
      unifiedToast.error({ title: "Validation Error", description: "Email is required" });
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      unifiedToast.error({ title: "Validation Error", description: "Invalid email format" });
      return;
    }

    const result = await execute(() => updateAuthProfile({
      full_name: formData.fullName,
      email: formData.email
    }));

    if (result !== null) {
      setIsEditing(false);
    }
  }, [formData, execute, updateAuthProfile]);

  const cancelEdit = useCallback(() => {
    setFormData({
      fullName: user?.full_name || '',
      email: user?.email || ''
    });
    setIsEditing(false);
  }, [user]);

  const startEditing = useCallback(() => {
    setIsEditing(true);
  }, []);

  return {
    user,
    formData,
    setFormData,
    isEditing,
    isSaving,
    updateProfile,
    cancelEdit,
    startEditing
  };
}
