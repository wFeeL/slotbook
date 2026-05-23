export interface TelegramInitDataUnsafeUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  language_code?: string;
}

export interface TelegramInitDataUnsafe {
  user?: TelegramInitDataUnsafeUser;
  query_id?: string;
  auth_date?: number;
  hash?: string;
}

export interface TelegramMainButton {
  text: string;
  color: string;
  textColor: string;
  isVisible: boolean;
  isActive: boolean;
  isProgressVisible: boolean;
  setText(text: string): TelegramMainButton;
  onClick(cb: () => void): TelegramMainButton;
  offClick(cb: () => void): TelegramMainButton;
  show(): TelegramMainButton;
  hide(): TelegramMainButton;
  enable(): TelegramMainButton;
  disable(): TelegramMainButton;
  showProgress(leaveActive?: boolean): TelegramMainButton;
  hideProgress(): TelegramMainButton;
  setParams(params: {
    text?: string;
    color?: string;
    text_color?: string;
    is_active?: boolean;
    is_visible?: boolean;
  }): TelegramMainButton;
}

export interface TelegramBackButton {
  isVisible: boolean;
  onClick(cb: () => void): TelegramBackButton;
  offClick(cb: () => void): TelegramBackButton;
  show(): TelegramBackButton;
  hide(): TelegramBackButton;
}

export interface TelegramHapticFeedback {
  impactOccurred(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): TelegramHapticFeedback;
  notificationOccurred(type: 'error' | 'success' | 'warning'): TelegramHapticFeedback;
  selectionChanged(): TelegramHapticFeedback;
}

export interface TelegramCloudStorage {
  setItem(key: string, value: string, callback?: (err: Error | null, ok: boolean) => void): void;
  getItem(key: string, callback: (err: Error | null, value: string | null) => void): void;
  removeItem(key: string, callback?: (err: Error | null, ok: boolean) => void): void;
}

export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: TelegramInitDataUnsafe;
  colorScheme: 'light' | 'dark';
  themeParams: TelegramThemeParams;
  version?: string;
  isVersionAtLeast?: (v: string) => boolean;
  ready(): void;
  expand(): void;
  close(): void;
  MainButton: TelegramMainButton;
  BackButton: TelegramBackButton;
  HapticFeedback: TelegramHapticFeedback;
  CloudStorage?: TelegramCloudStorage;
  showConfirm(message: string, callback: (confirmed: boolean) => void): void;
  showAlert(message: string, callback?: () => void): void;
}

declare global {
  interface Window {
    Telegram?: { WebApp: TelegramWebApp };
  }
}

export function getWebApp(): TelegramWebApp | null {
  return typeof window !== 'undefined' && window.Telegram?.WebApp ? window.Telegram.WebApp : null;
}
