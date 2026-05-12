import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';

interface AnimatedButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
  href?: string;
  smoothScroll?: boolean;
}

const AnimatedButton: React.FC<AnimatedButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  onClick,
  href,
  smoothScroll = false
}) => {
  const buttonRef = useRef<HTMLButtonElement | HTMLAnchorElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  };

  const handleClick = (e: React.MouseEvent) => {
    if (smoothScroll && href?.startsWith('#')) {
      e.preventDefault();
      const targetId = href.substring(1);
      const targetElement = document.getElementById(targetId);
      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    }
    if (onClick) {
      onClick();
    }
  };

  const sizeClasses = {
    sm: 'h-10 px-6 text-sm',
    md: 'h-12 px-8 text-base',
    lg: 'h-14 px-10 text-lg'
  };

  const baseClasses = `
    relative overflow-hidden rounded-xl font-semibold
    transition-all duration-300 inline-flex items-center justify-center gap-2
    ${sizeClasses[size]} ${className}
  `;

  const variantClasses = {
    primary: `
      bg-primary text-white
      shadow-[0_0_20px_-5px_rgba(167,139,250,0.4)]
      hover:shadow-[0_0_35px_-5px_rgba(167,139,250,0.6)]
      hover:bg-primary/90
      border border-primary/30
    `,
    secondary: `
      bg-transparent text-white border-2 border-white/20
      hover:bg-white/5 hover:border-white/30
      backdrop-blur-sm
    `
  };

  const content = (
    <>
      {/* Glow effect on hover */}
      {variant === 'primary' && isHovered && (
        <motion.div
          className="absolute inset-0 opacity-30"
          style={{
            background: `radial-gradient(circle 100px at ${mousePosition.x}px ${mousePosition.y}px, rgba(255,255,255,0.8), transparent 80%)`
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.3 }}
          exit={{ opacity: 0 }}
        />
      )}
      
      {/* Border glow effect */}
      {variant === 'secondary' && isHovered && (
        <motion.div
          className="absolute inset-0 rounded-xl"
          style={{
            background: `radial-gradient(circle 150px at ${mousePosition.x}px ${mousePosition.y}px, rgba(167,139,250,0.4), transparent 80%)`
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        />
      )}

      <span className="relative z-10">{children}</span>
    </>
  );

  const commonProps = {
    ref: buttonRef as any,
    className: `${baseClasses} ${variantClasses[variant]}`,
    onMouseMove: handleMouseMove,
    onMouseEnter: () => setIsHovered(true),
    onMouseLeave: () => setIsHovered(false),
    onClick: handleClick
  };

  if (href) {
    return (
      <motion.a
        {...commonProps}
        href={href}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {content}
      </motion.a>
    );
  }

  return (
    <motion.button
      {...commonProps}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      {content}
    </motion.button>
  );
};

export default AnimatedButton;
