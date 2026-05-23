import type { ReactNode } from 'react';
import { useAuth } from './useAuth';
import { Skeleton } from '@/shared/ui/Skeleton';

export function AuthGate({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  if (status === 'pending') {
    return (
      <div className="min-h-screen p-6">
        <Skeleton height={48} className="mb-4" />
        <Skeleton height={80} className="mb-3" />
        <Skeleton height={80} />
      </div>
    );
  }
  return <>{children}</>;
}
