import { NavLink } from 'react-router-dom';
import { cn } from '../lib/utils';
import { useSidebar } from '../contexts/SidebarContext';
import {
  Lightbulb,
  CheckCircle,
  Users,
  Target,
  Rocket,
  TrendingUp,
  X,
} from 'lucide-react';
import { Button } from './ui/button';

const navigation = [
  { name: 'Problem Discovery', href: '/', icon: Lightbulb },
  { name: 'Idea Validation', href: '/ideas/new', icon: CheckCircle },
  { name: 'Competitor Analysis', href: '/competitor-analysis', icon: Target },
  { name: 'Customer Finding', href: '/customer-finding', icon: Users },
  { name: 'Launch Planning', href: '/launch-planning', icon: Rocket },
  { name: 'Go-to-Market', href: '/go-to-market', icon: TrendingUp },
];

const Sidebar = () => {
  const { isOpen, closeSidebar } = useSidebar();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <button
          className="fixed inset-0 z-40 bg-background/95 backdrop-blur-sm lg:hidden border-none outline-none"
          onClick={closeSidebar}
          onKeyDown={(e) => e.key === 'Escape' && closeSidebar()}
          aria-label="Close sidebar"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-50 w-72 glass border-r border-border/50 transition-all duration-300 lg:sticky lg:top-16 lg:translate-x-0',
          'sidebar-full-height', // Use custom CSS class for reliable height
          isOpen ? 'translate-x-0' : '-translate-x-full lg:w-20'
        )}
      >
        <div className="flex h-full flex-col lg:min-h-[calc(100vh-4rem)]">
          {/* Mobile close button */}
          <div className="flex h-16 items-center justify-between px-4 border-b border-border/50 lg:hidden">
            <h2 className="text-lg font-semibold">Menu</h2>
            <Button variant="ghost" size="icon" onClick={closeSidebar} className="hover:bg-accent/50">
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-2 px-3 py-6 overflow-y-auto scrollbar-thin lg:min-h-0">
            <p className={cn(
              "mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground transition-opacity",
              !isOpen && "lg:opacity-0 lg:hidden"
            )}>
              Modules
            </p>
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={() => window.innerWidth < 1024 && closeSidebar()}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300 group',
                    isActive
                      ? 'bg-gradient-to-r from-primary to-accent text-white glow-sm'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent/50',
                    !isOpen && 'lg:justify-center lg:px-2'
                  )
                }
              >
                <item.icon className="h-5 w-5 flex-shrink-0 transition-transform group-hover:scale-110" />
                <span className={cn(
                  "transition-all duration-300",
                  !isOpen && "lg:hidden"
                )}>{item.name}</span>
              </NavLink>
            ))}


          </nav>

          {/* Footer - Spacer to push to bottom */}
          <div className="flex-shrink-0 mt-auto">
            <div className={cn(
              "border-t border-border/50 p-4 transition-all",
              !isOpen && "lg:p-2"
            )}>
              <p className={cn(
                "text-xs text-muted-foreground text-center transition-opacity",
                !isOpen && "lg:hidden"
              )}>
                © 2025 Clarimo AI
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
