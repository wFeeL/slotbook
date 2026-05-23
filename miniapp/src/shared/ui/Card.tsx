import type { HTMLAttributes, ReactNode } from 'react';
import React from 'react';
import { cn } from '../lib/cn';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  surface?: 'shell' | 'sand';
  interactive?: boolean;
  /** Asymmetric organic corners (rotate per nth-child). Off by default to preserve stability. */
  organic?: boolean;
  children: ReactNode;
}

export function Card({
  surface = 'shell',
  interactive = false,
  organic = false,
  className,
  children,
  onClick,
  onKeyDown,
  ...rest
}: CardProps) {
  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (interactive && onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick(e as unknown as React.MouseEvent<HTMLDivElement>);
    }
    onKeyDown?.(e);
  }

  return (
    <div
      className={cn(
        'p-5 shadow-warm transition-[transform,box-shadow] duration-200 ease-out',
        organic ? 'card-organic' : 'rounded-card',
        surface === 'shell' ? 'bg-shell' : 'bg-sand',
        interactive &&
          'cursor-pointer hover:shadow-warm-lg hover:-translate-y-0.5 active:scale-[0.985] active:translate-y-0',
        className,
      )}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      {...rest}
    >
      {children}
    </div>
  );
}
