import { create } from 'zustand';
import { setAuthToken } from '../api/client';
import type { StaffMeResponse, UserRead } from '../api/types';
import { getWebApp } from '../telegram/webapp';

const STORAGE_KEY = 'slotbook.jwt';

interface AuthState {
  token: string | null;
  user: UserRead | null;
  staffMe: StaffMeResponse | null;
  setSession(token: string, user: UserRead): Promise<void>;
  setStaffMe(value: StaffMeResponse | null): void;
  clearSession(): Promise<void>;
  loadFromStorage(): Promise<void>;
}

// CloudStorage was added in Telegram WebApp 6.9. Older clients (and the
// standalone telegram-web-app.js loaded in a plain browser) expose the
// CloudStorage object but throw WebAppMethodUnsupported when called.
// We probe `isVersionAtLeast('6.9')` and fall back to sessionStorage when
// unsupported. A timeout safeguards against callbacks that never fire.

function cloudStorageSupported(): boolean {
  const tg = getWebApp();
  if (!tg?.CloudStorage) return false;
  if (typeof tg.isVersionAtLeast !== 'function') return false;
  try {
    return tg.isVersionAtLeast('6.9') === true;
  } catch {
    return false;
  }
}

async function readCloudStorage(): Promise<string | null> {
  if (!cloudStorageSupported()) {
    return sessionStorage.getItem(STORAGE_KEY);
  }
  const tg = getWebApp()!;
  return new Promise((resolve) => {
    const fallback = () => resolve(sessionStorage.getItem(STORAGE_KEY));
    const timer = setTimeout(fallback, 1000);
    try {
      tg.CloudStorage!.getItem(STORAGE_KEY, (_err, value) => {
        clearTimeout(timer);
        resolve(value ?? null);
      });
    } catch {
      clearTimeout(timer);
      fallback();
    }
  });
}

async function writeCloudStorage(value: string): Promise<void> {
  sessionStorage.setItem(STORAGE_KEY, value); // mirror locally so reads work even if cloud write fails
  if (!cloudStorageSupported()) return;
  const tg = getWebApp()!;
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(), 1000);
    try {
      tg.CloudStorage!.setItem(STORAGE_KEY, value, () => {
        clearTimeout(timer);
        resolve();
      });
    } catch {
      clearTimeout(timer);
      resolve();
    }
  });
}

async function removeCloudStorage(): Promise<void> {
  sessionStorage.removeItem(STORAGE_KEY);
  if (!cloudStorageSupported()) return;
  const tg = getWebApp()!;
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(), 1000);
    try {
      tg.CloudStorage!.removeItem(STORAGE_KEY, () => {
        clearTimeout(timer);
        resolve();
      });
    } catch {
      clearTimeout(timer);
      resolve();
    }
  });
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  staffMe: null,
  async setSession(token, user) {
    setAuthToken(token);
    await writeCloudStorage(token);
    set({ token, user });
  },
  setStaffMe(value) {
    set({ staffMe: value });
  },
  async clearSession() {
    setAuthToken(null);
    await removeCloudStorage();
    set({ token: null, user: null, staffMe: null });
  },
  async loadFromStorage() {
    const token = await readCloudStorage();
    if (token) {
      setAuthToken(token);
      set({ token });
    }
  },
}));
