/**
 * Soft empty state with a decorative blob behind a glyph + message + optional action.
 * Keeps the Organic theme alive in moments where there's no content to show.
 */
import type { ReactNode } from 'react';
import { cn } from '../lib/cn';

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
  glyph?: 'leaf' | 'calendar' | 'spark';
  className?: string;
}

function Glyph({ kind }: { kind: NonNullable<EmptyStateProps['glyph']> }) {
  const stroke = {
    fill: 'none',
    stroke: 'var(--color-rose)',
    strokeWidth: 1.6,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  };
  if (kind === 'calendar') {
    return (
      <svg width="40" height="40" viewBox="0 0 24 24" {...stroke}>
        <rect x="3" y="5" width="18" height="16" rx="3" />
        <path d="M8 3v4M16 3v4M3 10h18" />
      </svg>
    );
  }
  if (kind === 'leaf') {
    return (
      <svg width="40" height="40" viewBox="0 0 24 24" {...stroke}>
        <path d="M21 3c-9 0-15 6-15 15l3 3c0-9 6-15 15-15l-3-3z" />
        <path d="M9 21c0-6 4-12 12-15" />
      </svg>
    );
  }
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" {...stroke}>
      <path d="M12 3v6M12 15v6M3 12h6M15 12h6M5.5 5.5l4 4M14.5 14.5l4 4M5.5 18.5l4-4M14.5 9.5l4-4" />
    </svg>
  );
}

export function EmptyState({
  title,
  description,
  action,
  glyph = 'spark',
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center py-10 px-6 gap-4',
        className,
      )}
    >
      <div className="relative w-24 h-24 flex items-center justify-center">
        {/* decorative blob */}
        <svg
          aria-hidden="true"
          viewBox="0 0 96 96"
          className="absolute inset-0 w-full h-full"
        >
          <path
            d="M48 6c20 3 38 18 36 40c-2 22-20 38-40 36c-22-2-36-20-34-40c2-22 18-38 38-36z"
            fill="var(--color-sand)"
            opacity="0.5"
          />
        </svg>
        <div className="relative text-rose">
          <Glyph kind={glyph} />
        </div>
      </div>
      <div className="flex flex-col gap-1 max-w-xs">
        <h3 className="text-xl text-ink font-display">{title}</h3>
        {description && (
          <p className="text-sienna-deep text-sm leading-relaxed">{description}</p>
        )}
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
