import { create } from 'zustand';

export type ToastTone = 'success' | 'error' | 'info';

export interface Toast {
  id: string;
  tone: ToastTone;
  message: string;
}

interface ToastState {
  toasts: Toast[];
  push(t: { tone: ToastTone; message: string }): string;
  dismiss(id: string): void;
}

let counter = 0;
function nextId(): string {
  counter += 1;
  return `t${counter}-${Date.now()}`;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push({ tone, message }) {
    const id = nextId();
    set((s) => ({ toasts: [...s.toasts, { id, tone, message }] }));
    return id;
  },
  dismiss(id) {
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
  },
}));

export function pushToast(tone: ToastTone, message: string): string {
  return useToastStore.getState().push({ tone, message });
}
