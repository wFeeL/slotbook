// miniapp/src/features/admin-guard/RequireAdmin.tsx
import { useEffect, useRef, type ReactNode } from 'react';
import { Navigate } from 'react-router';
import { useAuthStore } from '@/shared/store/auth-store';
import { pushToast } from '@/shared/store/toast-store';

interface RequireAdminProps {
  children: ReactNode;
}

export function RequireAdmin({ children }: RequireAdminProps) {
  const user = useAuthStore((s) => s.user);
  const role = user?.role;
  const allowed = role === 'admin' || role === 'superadmin';
  const lastShownRef = useRef<number | null>(null);

  useEffect(() => {
    if (user && !allowed && user.id !== lastShownRef.current) {
      pushToast('error', 'Доступ только для администратора');
      lastShownRef.current = user.id;
    }
  }, [user, allowed]);

  if (!user) {
    // Auth still resolving — show nothing rather than redirect prematurely.
    return null;
  }
  if (!allowed) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
