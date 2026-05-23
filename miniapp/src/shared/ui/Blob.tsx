import { cn } from '../lib/cn';

interface BlobProps {
  variant?: 'sand' | 'rose';
  size?: number; // viewport units
  className?: string;
  style?: React.CSSProperties;
}

export function Blob({ variant = 'sand', size = 80, className, style }: BlobProps) {
  const fill = variant === 'sand' ? '#E8D5C4' : '#D4736E';
  return (
    <div
      className={cn('pointer-events-none absolute', className)}
      style={{ width: `${size}vw`, height: `${size}vw`, ...style }}
      aria-hidden
    >
      <svg viewBox="0 0 80 80" className="w-full h-full" style={{ animation: 'pulse-soft 6s ease-in-out infinite' }}>
        <path
          d="M40,4 C60,8 74,28 70,50 C66,68 48,80 26,76 C8,72 -2,52 4,32 C10,14 24,2 40,4 Z"
          fill={fill}
          opacity="0.5"
          style={{ animation: 'blob-morph 18s ease-in-out infinite' }}
        />
      </svg>
    </div>
  );
}
