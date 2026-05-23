import { useEffect, type ReactNode } from 'react';
import { cn } from '../lib/cn';

interface SheetProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
}

export function Sheet({ open, onClose, title, children }: SheetProps) {
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <div
        data-testid="sheet-backdrop"
        className="absolute inset-0 bg-ink/30 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        className={cn(
          'relative w-full max-w-md max-h-[85vh] overflow-y-auto',
          'rounded-t-card bg-cream p-5 shadow-warm-lg',
        )}
        style={{ animation: 'fade-up 240ms ease-out both' }}
      >
        {title && <h2 className="text-2xl text-ink font-display mb-4">{title}</h2>}
        {children}
      </div>
    </div>
  );
}
