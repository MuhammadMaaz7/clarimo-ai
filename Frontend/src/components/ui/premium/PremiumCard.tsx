import React from 'react';
import { cn } from '../../../lib/utils';
import { motion, HTMLMotionProps } from 'framer-motion';

interface PremiumCardProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
  hover?: boolean;
  variant?: 'default' | 'accent' | 'glass';
}

const PremiumCard = React.forwardRef<HTMLDivElement, PremiumCardProps>(
  ({ children, className, glow = false, hover = true, variant = 'default', ...props }, ref) => {
    const variants = {
      default: 'bg-[hsl(var(--card)/0.4)] border-[hsl(var(--border)/0.5)]',
      accent: 'bg-[hsl(var(--accent)/0.05)] border-[hsl(var(--accent)/0.2)]',
      glass: 'bg-white/5 backdrop-blur-2xl border-white/10 shadow-2xl',
    };

    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        whileHover={hover ? { y: -4, transition: { duration: 0.2 } } : undefined}
        className={cn(
          'rounded-[2rem] border transition-all duration-300 overflow-hidden relative group',
          variants[variant],
          glow && 'glow-sm hover:glow transition-shadow',
          className
        )}
        {...props}
      >
        {/* Subtle Noise/Grain Effect */}
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-[0.03] pointer-events-none mix-blend-overlay" />
        
        {/* Shine/Reflection effect on hover */}
        {hover && (
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-gradient-to-tr from-transparent via-white/5 to-transparent transition-opacity duration-500 pointer-events-none" />
        )}
        
        <div className="relative z-10 p-6 md:p-8">
          {children}
        </div>
      </motion.div>
    );
  }
);

PremiumCard.displayName = 'PremiumCard';

export { PremiumCard };
