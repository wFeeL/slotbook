import type { BookingStatus } from '@/shared/api/types';

export const BOOKING_STATUS_LABEL: Record<BookingStatus, string> = {
  pending: 'Ожидает',
  confirmed: 'Подтверждена',
  completed: 'Завершена',
  cancelled_by_client: 'Отменена клиентом',
  cancelled_by_admin: 'Отменена админом',
  no_show: 'Не пришёл',
  rescheduled: 'Перенесена',
};

export type StatusTone = 'sage' | 'clay' | 'sienna' | 'rose' | 'sand';

export function bookingStatusTone(status: BookingStatus): StatusTone {
  if (status === 'pending' || status === 'confirmed') return 'sage';
  if (status === 'completed') return 'sienna';
  if (status === 'no_show') return 'rose';
  if (status === 'cancelled_by_client' || status === 'cancelled_by_admin') return 'clay';
  return 'sand';
}

export function bookingStatusLabel(status: BookingStatus): string {
  return BOOKING_STATUS_LABEL[status] ?? status;
}
