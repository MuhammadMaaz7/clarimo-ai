import { NavLink } from 'react-router-dom';
import { cn } from '../lib/utils';
import { useSidebar } from '../contexts/SidebarContext';
import {
  LayoutDashboard,
  Sparkles,
  Lightbulb,
  Users,
  Target,
  Rocket,
  Megaphone,
  X,
  ChevronRight,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, color: 'text-violet-300', bg: 'bg-violet-500/15', activeBg: 'bg-violet-500/20' },
  { name: 'Problem Discovery', href: '/problem-discovery', icon: Sparkles, color: 'text-purple-300', bg: 'bg-purple-500/15', activeBg: 'bg-purple-500/20' },
  { name: 'Idea Validation', href: '/ideas/new', icon: Lightbulb, color: 'text-yellow-300', bg: 'bg-yellow-500/15', activeBg: 'bg-yellow-500/20' },
  { name: 'Competitor Analysis', href: '/competitor-analysis', icon: Target, color: 'text-red-300', bg: 'bg-red-500/15', activeBg: 'bg-red-500/20' },
  { name: 'Customer Finding', href: '/customer-finding', icon: Users, color: 'text-cyan-300', bg: 'bg-cyan-500/15', activeBg: 'bg-cyan-500/20' },
  { name: 'Launch Planning', href: '/launch-planning', icon: Rocket, color: 'text-orange-300', bg: 'bg-orange-500/15', activeBg: 'bg-orange-500/20' },
  { name: 'Go-to-Market', href: '/go-to-market', icon: Megaphone, color: 'text-green-300', bg: 'bg-green-500/15', activeBg: 'bg-green-500/20' },
];

const Sidebar = () => {
  const { isOpen, closeSidebar } = useSidebar();

  return (
    <>
      {/* Mobile overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-[#211c37]/80 backdrop-blur-sm lg:hidden border-none outline-none"
            onClick={closeSidebar}
            onKeyDown={(e) => e.key === 'Escape' && closeSidebar()}
            aria-label="Close sidebar"
          />
        )}
      </AnimatePresence>

      {/* Sidebar panel */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 transition-all duration-300 bg-[#211c37] border-r border-[#442754]',
          'lg:relative lg:translate-x-0 lg:z-30 lg:h-full',
          isOpen ? 'w-72 translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-20'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Mobile close button */}
          <div className="flex h-16 items-center justify-between px-5 border-b border-[#442754] lg:hidden">
            <span className="text-sm font-bold uppercase tracking-widest text-fuchsia-200/50">Menu</span>
            <button
              onClick={closeSidebar}
              className="h-8 w-8 flex items-center justify-center rounded-lg text-fuchsia-200/40 hover:text-white hover:bg-white/10 transition-all"
              aria-label="Close sidebar"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-6 overflow-y-auto scrollbar-thin space-y-1 lg:min-h-0">
            <p className={cn(
              'mb-4 px-3 text-[10px] font-black uppercase tracking-[0.2em] text-fuchsia-200/25 transition-opacity',
              !isOpen && 'lg:opacity-0 lg:hidden'
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
                    'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'bg-white/10 text-white shadow-sm'
                      : 'text-fuchsia-200/50 hover:text-fuchsia-100 hover:bg-white/[0.06]',
                    !isOpen && 'lg:justify-center lg:px-2'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {/* Animated active bar */}
                    {isActive && (
                      <motion.div
                        layoutId="sidebar-active-bar"
                        className="absolute left-0 top-2 bottom-2 w-0.5 rounded-full bg-primary"
                        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                      />
                    )}

                    <div className={cn(
                      'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors',
                      isActive ? `${item.activeBg} ${item.color}` : 'text-fuchsia-200/30 group-hover:text-fuchsia-200/60'
                    )}>
                      <item.icon className="h-4 w-4" />
                    </div>

                    <span className={cn(
                      'flex-1 truncate transition-all duration-200',
                      !isOpen && 'lg:hidden'
                    )}>
                      {item.name}
                    </span>

                    {isActive && isOpen && (
                      <ChevronRight className={cn('h-3.5 w-3.5 shrink-0 opacity-60', item.color, !isOpen && 'lg:hidden')} />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          {/* Footer */}
          <div className="flex-shrink-0 mt-auto border-t border-[#442754] p-4">
            <p className={cn(
              'text-[10px] font-black uppercase tracking-[0.15em] text-fuchsia-200/20 text-center transition-opacity',
              !isOpen && 'lg:hidden'
            )}>
              © 2025 Clarimo AI
            </p>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;