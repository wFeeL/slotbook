import type { ReactNode } from 'react';
import { cn } from '../lib/cn';

type Tone = 'sage' | 'clay' | 'sienna' | 'rose' | 'sand';

interface BadgeProps {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}

const toneClass: Record<Tone, string> = {
  sage: 'bg-sage/20 text-sage',
  clay: 'bg-clay/20 text-clay',
  sienna: 'bg-sienna/20 text-sienna-deep',
  rose: 'bg-rose/20 text-rose-deep',
  sand: 'bg-sand text-ink',
};

export function Badge({ tone = 'sienna', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
        toneClass[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
