import { Menu, LogOut, User, Settings } from 'lucide-react';
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

  const initials = user?.full_name
    ? user.full_name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  return (
    // Brand navbar: #211c37 with #442754 bottom border
    <nav className="flex-shrink-0 z-40 w-full border-b border-[#442754] bg-[#211c37]/95 backdrop-blur-xl">
      <div className="flex h-16 items-center px-4 sm:px-6 gap-4">
        {/* Sidebar toggle */}
        {user && (
          <button
            onClick={toggleSidebar}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-fuchsia-200/40 hover:text-fuchsia-100 hover:bg-white/[0.08] transition-all duration-200"
            aria-label="Toggle sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}

        {/* Logo / Brand */}
        <button
          className="flex items-center gap-3 hover:opacity-80 transition-opacity focus:outline-none rounded-lg px-1"
          onClick={() => navigate('/dashboard')}
          aria-label="Go to dashboard"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl overflow-hidden shadow-lg shadow-primary/20 ring-1 ring-white/10">
            <img src="/logo.png" alt="Clarimo AI" className="h-full w-full object-cover" />
          </div>
          <div className="flex flex-col -space-y-0.5">
            <span className="text-lg font-black text-white leading-tight tracking-tight">Clarimo AI</span>
            <span className="hidden sm:block text-[10px] font-bold uppercase tracking-[0.15em] text-fuchsia-200/30">
              Startup Accelerator
            </span>
          </div>
        </button>

        {/* Right side */}
        <div className="ml-auto flex items-center gap-3">
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2.5 rounded-xl px-2.5 py-1.5 hover:bg-white/[0.08] transition-all duration-200 outline-none">
                  {/* Avatar */}
                  <div className="relative">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary/80 to-accent/80 text-[11px] font-black text-white shadow-md shadow-primary/20">
                      {initials}
                    </div>
                    <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-green-400 border-2 border-[#211c37]" />
                  </div>
                  <span className="hidden sm:block text-sm font-semibold text-fuchsia-100/80">
                    {user.full_name?.split(' ')[0]}
                  </span>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="w-52 border border-[#442754] bg-[#2d2047] backdrop-blur-xl shadow-2xl rounded-2xl p-1"
              >
                <DropdownMenuLabel className="px-3 py-2">
                  <p className="text-sm font-bold text-white">{user.full_name}</p>
                  <p className="text-xs text-fuchsia-200/40 truncate mt-0.5">{user.email}</p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-[#442754]/60 my-1" />
                <DropdownMenuItem
                  onClick={() => navigate('/profile')}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm text-fuchsia-100/70 hover:text-white hover:bg-white/[0.08] cursor-pointer transition-all"
                >
                  <User className="h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => navigate('/settings')}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm text-fuchsia-100/70 hover:text-white hover:bg-white/[0.08] cursor-pointer transition-all"
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-[#442754]/60 my-1" />
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm text-red-400/80 hover:text-red-300 hover:bg-red-500/10 cursor-pointer transition-all"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate('/login')}
                className="px-4 py-2 rounded-xl text-sm font-semibold text-fuchsia-100/60 hover:text-fuchsia-100 hover:bg-white/[0.08] transition-all"
              >
                Login
              </button>
              <button
                onClick={() => navigate('/signup')}
                className="px-4 py-2 rounded-xl text-sm font-black text-white gradient-primary shadow-lg shadow-primary/20 hover:opacity-90 transition-all"
              >
                Sign Up
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
