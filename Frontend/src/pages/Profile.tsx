import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { User, Mail, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="responsive-container-content">
      <div className="space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl lg:text-4xl font-bold text-white">
            Profile
          </h1>
          <p className="text-muted-foreground">
            Manage your account settings
          </p>
        </div>

        <Card className="glass border-border overflow-hidden bg-white/5 backdrop-blur-xl glow-sm">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-xl lg:text-2xl">Account Information</CardTitle>
            <CardDescription>Your personal details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 pb-6">
            <div className="grid gap-6 sm:grid-cols-1">
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 p-4 rounded-lg glass-hover">
                <div className="flex h-14 w-14 lg:h-16 lg:w-16 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-primary glow-sm flex-shrink-0 shadow-lg">
                  <User className="h-7 w-7 lg:h-8 lg:w-8 text-white" />
                </div>
                <div className="space-y-1 min-w-0 flex-1">
                  <p className="text-xs lg:text-sm text-muted-foreground">Full Name</p>
                  <p className="text-base lg:text-lg font-semibold text-foreground break-words">{user?.full_name}</p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 p-4 rounded-lg glass-hover">
                <div className="flex h-14 w-14 lg:h-16 lg:w-16 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 border border-accent/30 flex-shrink-0 backdrop-blur-sm">
                  <Mail className="h-7 w-7 lg:h-8 lg:w-8 text-accent" />
                </div>
                <div className="space-y-1 min-w-0 flex-1">
                  <p className="text-xs lg:text-sm text-muted-foreground">Email Address</p>
                  <p className="text-base lg:text-lg font-semibold text-foreground break-all">{user?.email}</p>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-border">
              <Button
                variant="destructive"
                onClick={handleLogout}
                className="w-full sm:w-auto min-w-[140px]"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Sign Out
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Profile;
