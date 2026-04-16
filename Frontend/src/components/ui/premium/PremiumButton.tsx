import React from 'react';
import { cn } from '../../../lib/utils';
import { motion, HTMLMotionProps } from 'framer-motion';

interface PremiumButtonProps extends HTMLMotionProps<"button"> {
  children: React.ReactNode;
  className?: string;
  variant?: 'primary' | 'secondary' | 'accent' | 'outlined' | 'ghost';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  loading?: boolean;
}

const PremiumButton = React.forwardRef<HTMLButtonElement, PremiumButtonProps>(
  ({ children, className, variant = 'primary', size = 'md', loading = false, disabled, ...props }, ref) => {
    const variants = {
      primary: 'bg-white text-black hover:bg-white/90 shadow-[0_0_20px_-5px_rgba(255,255,255,0.4)] active:scale-[0.98]',
      secondary: 'bg-[hsl(var(--secondary))] border-[hsl(var(--border)/0.5)] text-white hover:bg-[hsl(var(--secondary)/0.8)] active:scale-[0.98]',
      accent: 'gradient-primary text-white border-none glow-sm hover:glow active:scale-[0.95]',
      outlined: 'bg-transparent border-white/20 text-white hover:bg-white/10 active:scale-[0.98]',
      ghost: 'bg-transparent text-[hsl(var(--muted-foreground))] hover:text-white transition-colors active:scale-[0.95]',
    };

    const sizes = {
      sm: 'px-4 py-2 text-xs rounded-lg',
      md: 'px-6 py-3 text-sm font-semibold rounded-xl',
      lg: 'px-8 py-4 text-base font-bold rounded-2xl',
      icon: 'p-2 rounded-xl h-10 w-10 flex items-center justify-center',
    };

    return (
      <motion.button
        ref={ref}
        whileHover={!disabled && !loading ? { scale: 1.02 } : undefined}
        whileTap={!disabled && !loading ? { scale: 0.98 } : undefined}
        className={cn(
          'inline-flex items-center justify-center transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed',
          variants[variant],
          sizes[size],
          className
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : null}
        <span className="relative z-10 flex items-center gap-2">
          {children}
        </span>
      </motion.button>
    );
  }
);

PremiumButton.displayName = 'PremiumButton';

export { PremiumButton };
