import type { ReactNode } from 'react';
import { useEffect, useRef } from 'react';
import { Navigate } from 'react-router';
import { useAuthStore } from '@/shared/store/auth-store';
import { pushToast } from '@/shared/store/toast-store';

export function RequireStaff({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const staffMe = useAuthStore((s) => s.staffMe);
  const toastedRef = useRef(false);

  useEffect(() => {
    if (user && staffMe && !staffMe.linked && !toastedRef.current) {
      pushToast('error', 'Учётная запись не связана с мастером');
      toastedRef.current = true;
    }
  }, [user, staffMe]);

  if (!user || staffMe === null) return null;
  if (!staffMe.linked) return <Navigate to="/" replace />;
  return <>{children}</>;
}
