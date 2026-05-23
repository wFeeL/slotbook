import type { HTMLAttributes, ReactNode } from 'react';
import { cn } from '../lib/cn';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  surface?: 'shell' | 'sand';
  interactive?: boolean;
  children: ReactNode;
}

export function Card({
  surface = 'shell',
  interactive = false,
  className,
  children,
  ...rest
}: CardProps) {
  return (
    <div
      className={cn(
        'rounded-card p-5 shadow-[var(--shadow-warm)]',
        surface === 'shell' ? 'bg-shell' : 'bg-sand',
        interactive && 'cursor-pointer transition active:scale-[0.97] hover:shadow-[var(--shadow-warm-lg)]',
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
