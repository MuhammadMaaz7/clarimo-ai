import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils';
import { motion } from 'framer-motion';

interface ModuleHeaderProps {
  icon: LucideIcon;
  title: string;
  description: string;
  iconClassName?: string;
  iconBgClassName?: string;
  actions?: React.ReactNode;
}

export function ModuleHeader({
  icon: Icon,
  title,
  description,
  iconClassName,
  iconBgClassName,
  actions,
}: ModuleHeaderProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-white/5 pb-8 mb-8">
      <div className="flex items-center gap-5">
        <motion.div 
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={cn(
            "p-4 rounded-3xl bg-primary/10 border border-primary/20 shadow-lg shadow-primary/5",
            iconBgClassName
          )}
        >
          <Icon className={cn("h-9 w-9 text-primary", iconClassName)} />
        </motion.div>
        <div>
          <div className="flex flex-col">
            <h1 className="text-4xl font-black tracking-tight text-white">{title}</h1>
            <p className="text-muted-foreground mt-1 max-w-2xl leading-relaxed">
              {description}
            </p>
          </div>
        </div>
      </div>
      
      {actions && (
        <div className="flex items-center gap-3">
          {actions}
        </div>
      )}
    </div>
  );
}
