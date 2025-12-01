import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { User, Mail, Settings, History, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';

const Profile = () => {
  const { user, logout, updateProfile } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    fullName: user?.full_name || '',
    email: user?.email || ''
  });

  const handleSave = async () => {
    // Basic validation
    if (!formData.fullName.trim()) {
      toast({
        variant: "destructive",
        title: "Validation Error",
        description: "Full name is required",
      });
      return;
    }

    if (!formData.email.trim()) {
      toast({
        variant: "destructive",
        title: "Validation Error",
        description: "Email is required",
      });
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      toast({
        variant: "destructive",
        title: "Validation Error",
        description: "Please enter a valid email address",
      });
      return;
    }

    setIsSaving(true);

    try {
      await updateProfile({
        full_name: formData.fullName,
        email: formData.email
      });

      toast({
        title: "Success!",
        description: "Profile updated successfully!",
      });
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
      toast({
        variant: "destructive",
        title: "Update Failed",
        description: error instanceof Error ? error.message : 'Failed to update profile. Please try again.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    // Reset form data to original values
    setFormData({
      fullName: user?.full_name || '',
      email: user?.email || ''
    });
    setIsEditing(false);
  };

  return (
    <div className="px-4 md:px-6 lg:px-8 pt-4 pb-8">
      {/* Profile Header */}
      <div className="glass border-border/50 rounded-2xl p-6 md:p-8 bg-white/5 backdrop-blur-xl mb-8">
        <div className="flex items-center gap-6">
          <div className="rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 p-4 glow-sm shadow-lg">
            <User className="h-12 w-12 text-white" />
          </div>
          <div className="flex-1">
            <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
              {user?.full_name}
            </h1>
            <p className="text-muted-foreground flex items-center gap-2">
              <Mail className="h-4 w-4" />
              {user?.email}
            </p>
            {/* <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Member since Recently
            </p> */}
          </div>
          <Button
            variant="outline"
            onClick={() => setIsEditing(!isEditing)}
            className="border-border/50 text-white hover:bg-white/10"
          >
            <Settings className="h-4 w-4 mr-2" />
            {isEditing ? 'Cancel' : 'Edit Profile'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Information */}
        <div className="lg:col-span-2">
          <Card className="glass border-border/50 bg-white/5 backdrop-blur-xl">
            <CardHeader>
              <CardTitle className="text-xl text-white flex items-center gap-3">
                <User className="h-6 w-6 text-blue-400" />
                Profile Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {isEditing ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="fullName" className="text-white">Full Name</Label>
                    <Input
                      id="fullName"
                      value={formData.fullName}
                      onChange={(e) => setFormData(prev => ({ ...prev, fullName: e.target.value }))}
                      className="glass border-border/50 bg-white/5 text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-white">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                      className="glass border-border/50 bg-white/5 text-white"
                    />
                  </div>
                  <div className="flex gap-3">
                    <Button
                      onClick={handleSave}
                      disabled={isSaving}
                      className="bg-primary hover:bg-primary/90"
                    >
                      {isSaving ? 'Saving...' : 'Save Changes'}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleCancel}
                      disabled={isSaving}
                    >
                      Cancel
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <Label className="text-muted-foreground">Full Name</Label>
                    <p className="text-white font-medium mt-1">{user?.full_name}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Email Address</Label>
                    <p className="text-white font-medium mt-1">{user?.email}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">Account Status</Label>
                    <p className="text-green-400 font-medium mt-1">Active</p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions & Navigation */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <Card className="glass border-border/50 bg-white/5 backdrop-blur-xl">
            <CardHeader>
              <CardTitle className="text-lg text-white">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                variant="ghost"
                className="w-full justify-start text-white hover:bg-white/10"
                onClick={() => navigate('/ideas')}
              >
                <CheckCircle className="h-4 w-4 mr-3 text-blue-400" />
                My Ideas
              </Button>
              <Button
                variant="ghost"
                className="w-full justify-start text-white hover:bg-white/10"
                onClick={() => navigate('/discovered-problems')}
              >
                <History className="h-4 w-4 mr-3 text-green-400" />
                My Discovered Problems
              </Button>
            </CardContent>
          </Card>

          {/* Account Actions */}
          <Card className="glass border-border/50 bg-white/5 backdrop-blur-xl">
            <CardHeader>
              <CardTitle className="text-lg text-white">Account</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                variant="ghost"
                className="w-full justify-start text-white hover:bg-white/10"
              >
                <Settings className="h-4 w-4 mr-3 text-gray-400" />
                Account Settings
              </Button>
              <Button
                variant="ghost"
                className="w-full justify-start text-red-400 hover:bg-red-500/10"
                onClick={logout}
              >
                <User className="h-4 w-4 mr-3" />
                Sign Out
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Profile;