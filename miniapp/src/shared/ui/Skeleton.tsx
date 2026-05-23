import { cn } from '../lib/cn';

interface SkeletonProps {
  className?: string;
  height?: number;
}

export function Skeleton({ className, height = 80 }: SkeletonProps) {
  return (
    <div
      className={cn('rounded-card bg-sand/60 animate-[pulse-soft_2.4s_ease-in-out_infinite]', className)}
      style={{ height: `${height}px` }}
      aria-hidden
    />
  );
}
