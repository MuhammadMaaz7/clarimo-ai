import { Menu, LogOut, User } from 'lucide-react';
import { Button } from './ui/button';
import { useSidebar } from '../contexts/SidebarContext';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';


const Navbar = () => {
  const { toggleSidebar } = useSidebar();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="sticky top-0 z-40 w-full border-b border-border/50 glass bg-white/5 backdrop-blur-xl">
      <div className="flex h-16 lg:h-20 items-center px-4 sm:px-6 lg:px-8 gap-4">
        {user && (
          <Button
            variant="ghost"
            size="icon"
            className="lg:mr-2 hover:bg-primary/10 transition-all duration-300 hover:scale-110 glow-sm"
            onClick={toggleSidebar}
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}
        
        <button 
          className="flex items-center space-x-2 lg:space-x-3 hover:opacity-80 transition-opacity focus:outline-none focus:ring-2 focus:ring-primary/50 rounded-lg p-1"
          onClick={() => navigate('/')}
          aria-label="Go to home page"
        >
          <div className="flex h-9 w-9 lg:h-11 lg:w-11 items-center justify-center rounded-xl overflow-hidden glow-sm">
            <img src="/logo.png" alt="Clarimo AI" className="h-full w-full object-cover" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-lg sm:text-xl lg:text-2xl font-bold text-white leading-tight">
              Clarimo AI
            </h1>
            <span className="hidden sm:block text-[10px] lg:text-xs text-muted-foreground -mt-0.5">
              Startup Accelerator
            </span>
          </div>
        </button>
        
        <div className="ml-auto flex items-center gap-2 lg:gap-4">
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2 hover:bg-primary/10 transition-all">
                  <div className="flex h-8 w-8 lg:h-9 lg:w-9 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-primary glow-sm shadow-lg">
                    <User className="h-4 w-4 text-white" />
                  </div>
                  <span className="hidden md:inline text-sm lg:text-base font-medium text-white">{user.full_name?.split(' ')[0]}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 glass border-border">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{user.full_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-border" />
                <DropdownMenuItem onClick={() => navigate('/profile')} className="cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout} className="text-destructive cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <div className="flex items-center gap-2">
              <Button 
                variant="ghost" 
                onClick={() => navigate('/login')}
                className="hover:bg-primary/10 transition-all text-sm lg:text-base"
              >
                Login
              </Button>
              <Button 
                className="bg-gradient-to-r from-accent to-primary hover:from-accent/90 hover:to-primary/90 text-white hover:opacity-90 transition-opacity glow-sm text-sm lg:text-base shadow-lg"
                onClick={() => navigate('/signup')}
              >
                Sign Up
              </Button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
