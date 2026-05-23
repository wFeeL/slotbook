import { create } from 'zustand';
import { setAuthToken } from '../api/client';
import type { UserRead } from '../api/types';
import { getWebApp } from '../telegram/webapp';

const STORAGE_KEY = 'slotbook.jwt';

interface AuthState {
  token: string | null;
  user: UserRead | null;
  setSession(token: string, user: UserRead): Promise<void>;
  clearSession(): Promise<void>;
  loadFromStorage(): Promise<void>;
}

async function readCloudStorage(): Promise<string | null> {
  const tg = getWebApp();
  if (!tg?.CloudStorage) {
    return sessionStorage.getItem(STORAGE_KEY);
  }
  return new Promise((resolve) => {
    tg.CloudStorage!.getItem(STORAGE_KEY, (_err, value) => resolve(value ?? null));
  });
}

async function writeCloudStorage(value: string): Promise<void> {
  const tg = getWebApp();
  if (!tg?.CloudStorage) {
    sessionStorage.setItem(STORAGE_KEY, value);
    return;
  }
  return new Promise((resolve) => {
    tg.CloudStorage!.setItem(STORAGE_KEY, value, () => resolve());
  });
}

async function removeCloudStorage(): Promise<void> {
  const tg = getWebApp();
  if (!tg?.CloudStorage) {
    sessionStorage.removeItem(STORAGE_KEY);
    return;
  }
  return new Promise((resolve) => {
    tg.CloudStorage!.removeItem(STORAGE_KEY, () => resolve());
  });
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  async setSession(token, user) {
    setAuthToken(token);
    await writeCloudStorage(token);
    set({ token, user });
  },
  async clearSession() {
    setAuthToken(null);
    await removeCloudStorage();
    set({ token: null, user: null });
  },
  async loadFromStorage() {
    const token = await readCloudStorage();
    if (token) {
      setAuthToken(token);
      set({ token });
    }
  },
}));
