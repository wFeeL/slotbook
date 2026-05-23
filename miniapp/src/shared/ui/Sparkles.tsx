/**
 * Decorative ornament that sits under display headings.
 * Adds a small "handmade" rhythm without occupying space like an icon would.
 * Two tone variants — rose for primary headers, sienna for muted.
 */
import { cn } from '../lib/cn';

interface SparklesProps {
  tone?: 'rose' | 'sienna';
  className?: string;
}

export function Sparkles({ tone = 'rose', className }: SparklesProps) {
  const color = tone === 'rose' ? 'var(--color-rose)' : 'var(--color-sienna)';
  return (
    <svg
      aria-hidden="true"
      width="64"
      height="10"
      viewBox="0 0 64 10"
      fill="none"
      className={cn('shrink-0', className)}
    >
      <path
        d="M2 5h18"
        stroke={color}
        strokeWidth="1.4"
        strokeLinecap="round"
        opacity="0.55"
      />
      <path
        d="M32 1l1.4 2.8L36 5l-2.6 1.2L32 9l-1.4-2.8L28 5l2.6-1.2z"
        fill={color}
      />
      <path
        d="M44 5h18"
        stroke={color}
        strokeWidth="1.4"
        strokeLinecap="round"
        opacity="0.55"
      />
    </svg>
  );
}
