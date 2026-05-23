import { useEffect, useState } from 'react';
import { setReAuthHandler } from '@/shared/api/client';
import { api } from '@/shared/api/endpoints';
import { useAuthStore } from '@/shared/store/auth-store';
import { getWebApp } from '@/shared/telegram/webapp';
import { exchangeInitData } from './api';

async function loadStaffMe() {
  try {
    const staffMe = await api.staffMe.profile();
    useAuthStore.getState().setStaffMe(staffMe);
  } catch {
    // Fallback so RequireStaff doesn't hang in a loading state.
    useAuthStore.getState().setStaffMe({
      linked: false,
      staff: null,
      branch: null,
      business_timezone: 'UTC',
    });
  }
}

export type AuthStatus = 'pending' | 'authenticated' | 'unauthenticated';

export function useAuth(): { status: AuthStatus; firstName: string | null } {
  const { token, user, setSession, loadFromStorage } = useAuthStore();
  const [status, setStatus] = useState<AuthStatus>('pending');

  useEffect(() => {
    let cancelled = false;

    async function run() {
      // 1. Load any persisted token from storage
      await loadFromStorage();
      if (cancelled) return;

      const tg = getWebApp();
      const initData = tg?.initData;

      if (!initData) {
        // Dev mode: support ?devToken=<jwt> query param
        const url = new URL(window.location.href);
        const devToken = url.searchParams.get('devToken');
        if (devToken) {
          await setSession(devToken, {
            id: 0,
            telegram_id: 0,
            first_name: 'Гость',
            last_name: null,
            username: null,
            role: 'client',
          });
          await loadStaffMe();
          if (!cancelled) setStatus('authenticated');
          return;
        }
        if (!cancelled) setStatus('unauthenticated');
        return;
      }

      try {
        const result = await exchangeInitData(initData);
        if (cancelled) return;
        await setSession(result.access_token, result.user);
        await loadStaffMe();
        if (!cancelled) setStatus('authenticated');

        // Register the re-auth handler for 401 retries.
        // Read fresh initData each invocation — Telegram's initData carries a
        // signed timestamp and the captured value would eventually expire.
        setReAuthHandler(async () => {
          const tgNow = getWebApp();
          const freshInitData = tgNow?.initData;
          if (!freshInitData) return null;
          try {
            const r = await exchangeInitData(freshInitData);
            await setSession(r.access_token, r.user);
            return r.access_token;
          } catch {
            return null;
          }
        });
      } catch {
        if (!cancelled) setStatus('unauthenticated');
      }
    }

    run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // If we loaded a token from storage but have no user, treat as authenticated.
  // The user object will be hydrated lazily via /auth/telegram on next launch.
  const effectiveStatus: AuthStatus = token ? 'authenticated' : status;

  return {
    status: effectiveStatus,
    firstName: user?.first_name ?? null,
  };
}
