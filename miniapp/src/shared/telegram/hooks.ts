import { useEffect, useRef } from 'react';
import { getWebApp } from './webapp';

interface MainButtonOptions {
  text: string;
  onClick: () => void;
  visible?: boolean;
  loading?: boolean;
  color?: string;
}

export function useMainButton(options: MainButtonOptions): void {
  const onClickRef = useRef(options.onClick);
  onClickRef.current = options.onClick;

  useEffect(() => {
    const tg = getWebApp();
    if (!tg) return;

    const handler = () => onClickRef.current();
    tg.MainButton.setParams({
      text: options.text,
      color: options.color ?? '#D4736E',
      text_color: '#FFFFFF',
    });
    tg.MainButton.onClick(handler);
    if (options.visible ?? true) tg.MainButton.show(); else tg.MainButton.hide();
    if (options.loading) tg.MainButton.showProgress(false); else tg.MainButton.hideProgress();
    return () => {
      tg.MainButton.offClick(handler);
      tg.MainButton.hide();
      tg.MainButton.hideProgress();
    };
  }, [options.text, options.visible, options.loading, options.color]);
}

export function useBackButton(onClick: () => void, enabled = true): void {
  const onClickRef = useRef(onClick);
  onClickRef.current = onClick;

  useEffect(() => {
    const tg = getWebApp();
    if (!tg) return;
    if (!enabled) {
      tg.BackButton.hide();
      return;
    }
    const handler = () => onClickRef.current();
    tg.BackButton.onClick(handler);
    tg.BackButton.show();
    return () => {
      tg.BackButton.offClick(handler);
      tg.BackButton.hide();
    };
  }, [enabled]);
}

export function useHaptic() {
  return {
    light(): void { getWebApp()?.HapticFeedback.impactOccurred('light'); },
    medium(): void { getWebApp()?.HapticFeedback.impactOccurred('medium'); },
    success(): void { getWebApp()?.HapticFeedback.notificationOccurred('success'); },
    error(): void { getWebApp()?.HapticFeedback.notificationOccurred('error'); },
    selection(): void { getWebApp()?.HapticFeedback.selectionChanged(); },
  };
}

export function showConfirm(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    const tg = getWebApp();
    if (!tg) {
      resolve(window.confirm(message));
      return;
    }
    tg.showConfirm(message, resolve);
  });
}
