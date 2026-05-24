import type { ReactNode } from 'react';
import { Navigate } from 'react-router';
import { useAuthStore } from '@/shared/store/auth-store';

export function RequireStaff({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const staffMe = useAuthStore((s) => s.staffMe);

  // Resolving auth/profile state — render nothing while waiting.
  if (!user || staffMe === null) return null;
  // Hard gate: only role=staff (or higher) can reach /me.
  // Note: not-yet-linked staff still get in — Cabinet page shows a setup-pending
  // state, so the user is not bounced away from their own cabinet.
  const allowed = user.role === 'staff' || user.role === 'admin' || user.role === 'superadmin';
  if (!allowed) return <Navigate to="/" replace />;
  return <>{children}</>;
}
