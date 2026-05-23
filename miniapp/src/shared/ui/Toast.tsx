import { useEffect } from 'react';
import { cn } from '../lib/cn';
import { useToastStore, type Toast as ToastT, type ToastTone } from '../store/toast-store';

const toneClass: Record<ToastTone, string> = {
  success: 'bg-sage text-shell',
  error: 'bg-rose-deep text-shell',
  info: 'bg-sienna text-shell',
};

function ToastItem({ toast }: { toast: ToastT }) {
  const dismiss = useToastStore((s) => s.dismiss);
  useEffect(() => {
    const timer = setTimeout(() => dismiss(toast.id), 3000);
    return () => clearTimeout(timer);
  }, [toast.id, dismiss]);

  return (
    <div
      role="status"
      className={cn(
        'rounded-card px-4 py-3 shadow-warm-lg text-sm font-semibold max-w-sm',
        toneClass[toast.tone],
      )}
      style={{ animation: 'fade-up 200ms ease-out both' }}
    >
      {toast.message}
    </div>
  );
}

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  if (toasts.length === 0) return null;
  return (
    <div
      aria-live="polite"
      className="fixed top-4 left-0 right-0 z-[60] flex flex-col items-center gap-2 px-4 pointer-events-none"
    >
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <ToastItem toast={t} />
        </div>
      ))}
    </div>
  );
}
