import { format, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

export function formatLocalTime(isoUtc: string): string {
  return format(parseISO(isoUtc), 'HH:mm');
}

export function formatLocalDate(isoUtc: string): string {
  return format(parseISO(isoUtc), 'd MMMM', { locale: ru });
}

export function formatLocalWeekday(isoUtc: string): string {
  return format(parseISO(isoUtc), 'EEEE', { locale: ru });
}

export function formatDayLabelShort(isoDate: string): { weekday: string; day: number } {
  const d = parseISO(`${isoDate}T00:00:00`);
  return {
    weekday: format(d, 'EEEEEE', { locale: ru }), // 'пн', 'вт', ...
    day: d.getDate(),
  };
}

export function formatPrice(value: string | null): string {
  if (!value) return '';
  const num = Number(value);
  return `${Math.round(num)} ₽`;
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} мин`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m === 0 ? `${h} ч` : `${h} ч ${m} мин`;
}
