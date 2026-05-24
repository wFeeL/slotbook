// miniapp/src/pages/admin/AdminBookingDetailPage.tsx
import { useNavigate, useParams } from 'react-router';
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Textarea } from '@/shared/ui/Textarea';
import { Sheet } from '@/shared/ui/Sheet';
import { Input } from '@/shared/ui/Input';
import {
  useAdminCancelBooking,
  useAdminRescheduleBooking,
  usePatchBooking,
} from '@/entities/admin-booking/api';
import { pushToast } from '@/shared/store/toast-store';
import { showConfirm } from '@/shared/telegram/hooks';
import { request } from '@/shared/api/client';
import { AdminBookingReadSchema, type AdminBookingRead } from '@/shared/api/types';
import { bookingStatusLabel, bookingStatusTone } from '@/entities/booking/lib/status';
import { ContactLinks } from '@/shared/ui/ContactLinks';

function useAdminBookingDetail(id: number) {
  return useQuery({
    queryKey: ['admin', 'booking', id],
    queryFn: () =>
      // The backend doesn't have a GET /admin/bookings/{id}; we list and find,
      // but for robustness fetch a list filtered minimally and pick by id.
      request(
        `/api/v1/admin/bookings?limit=200`,
        { method: 'GET' },
        z.array(AdminBookingReadSchema),
      ).then((all: AdminBookingRead[]) => all.find((b) => b.id === id) ?? null),
    staleTime: 5 * 1000,
  });
}

export function AdminBookingDetailPage() {
  const params = useParams();
  const navigate = useNavigate();
  const id = Number(params.id);
  const detail = useAdminBookingDetail(id);
  const patch = usePatchBooking();
  const cancel = useAdminCancelBooking();
  const reschedule = useAdminRescheduleBooking();
  const [adminComment, setAdminComment] = useState('');
  const [rescheduleOpen, setRescheduleOpen] = useState(false);
  const [rescheduleDate, setRescheduleDate] = useState('');
  const [rescheduleTime, setRescheduleTime] = useState('10:00');
  const [rescheduleError, setRescheduleError] = useState<string | null>(null);

  useEffect(() => {
    if (detail.data) setAdminComment(detail.data.admin_comment ?? '');
  }, [detail.data]);

  if (detail.isLoading) return <Skeleton height={160} />;
  if (!detail.data) return <p className="text-sienna-deep">Запись не найдена.</p>;
  const b = detail.data;

  async function setStatus(status: 'completed' | 'no_show') {
    try {
      await patch.mutateAsync({ id, patch: { status } });
      pushToast('success', 'Статус обновлён');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function saveComment() {
    try {
      await patch.mutateAsync({ id, patch: { admin_comment: adminComment || null } });
      pushToast('success', 'Комментарий сохранён');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function cancelBooking() {
    const ok = await showConfirm('Отменить запись?');
    if (!ok) return;
    try {
      await cancel.mutateAsync(id);
      pushToast('success', 'Запись отменена');
      navigate('/admin/bookings');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  function openReschedule() {
    setRescheduleError(null);
    // Prefill with the current booking starts_at (local-time view).
    const current = new Date(b.starts_at);
    const pad = (n: number) => String(n).padStart(2, '0');
    setRescheduleDate(
      `${current.getFullYear()}-${pad(current.getMonth() + 1)}-${pad(current.getDate())}`,
    );
    setRescheduleTime(`${pad(current.getHours())}:${pad(current.getMinutes())}`);
    setRescheduleOpen(true);
  }

  async function submitReschedule() {
    setRescheduleError(null);
    if (!rescheduleDate || !rescheduleTime) {
      setRescheduleError('Укажите дату и время');
      return;
    }
    // Build an ISO string with the admin's local UTC offset (copied from BookingForm).
    const local = new Date(`${rescheduleDate}T${rescheduleTime}:00`);
    const offsetMin = -local.getTimezoneOffset();
    const sign = offsetMin >= 0 ? '+' : '-';
    const abs = Math.abs(offsetMin);
    const offHH = String(Math.floor(abs / 60)).padStart(2, '0');
    const offMM = String(abs % 60).padStart(2, '0');
    const startsAt = `${rescheduleDate}T${rescheduleTime}:00${sign}${offHH}:${offMM}`;
    try {
      await reschedule.mutateAsync({ id, startsAt });
      pushToast('success', 'Запись перенесена');
      setRescheduleOpen(false);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Не удалось перенести';
      setRescheduleError(msg);
      pushToast('error', msg);
    }
  }

  const active = b.status === 'pending' || b.status === 'confirmed';

  return (
    <div className="pt-2 pb-6 flex flex-col gap-4">
      <Card surface="shell">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-ink font-semibold text-lg">
              {new Date(b.starts_at).toLocaleString('ru-RU', {
                day: '2-digit',
                month: 'long',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </div>
            <div className="text-sienna-deep text-sm mt-1">
              {b.service_title ?? `Услуга #${b.service_id}`}
              {' · '}
              {b.staff_name ?? `Сотрудник #${b.staff_id}`}
            </div>
            <div className="text-sienna-deep text-xs mt-0.5">
              Клиент: {b.client_first_name ?? `#${b.client_id}`}
              {b.client_last_name ? ` ${b.client_last_name}` : ''}
            </div>
            <div className="mt-2">
              <ContactLinks
                username={b.client_username}
                phone={b.client_phone}
                telegramId={b.client_telegram_id}
              />
            </div>
            {b.client_comment && (
              <div className="text-ink text-sm mt-2 italic">«{b.client_comment}»</div>
            )}
          </div>
          <Badge tone={bookingStatusTone(b.status)}>{bookingStatusLabel(b.status)}</Badge>
        </div>
      </Card>

      <div>
        <Textarea
          label="Комментарий администратора"
          value={adminComment}
          onChange={(e) => setAdminComment(e.target.value)}
        />
        <Button className="mt-2" variant="secondary" onClick={saveComment} disabled={patch.isPending}>
          Сохранить комментарий
        </Button>
      </div>

      {active && (
        <div className="flex flex-col gap-2 pt-2 border-t border-sand">
          <Button onClick={() => setStatus('completed')} disabled={patch.isPending}>
            Завершено
          </Button>
          <Button variant="secondary" onClick={() => setStatus('no_show')} disabled={patch.isPending}>
            Не пришёл
          </Button>
          <Button variant="secondary" onClick={openReschedule} disabled={reschedule.isPending}>
            Перенести
          </Button>
          <Button variant="ghost" onClick={cancelBooking} disabled={cancel.isPending}>
            Отменить запись
          </Button>
        </div>
      )}

      <Sheet
        open={rescheduleOpen}
        onClose={() => setRescheduleOpen(false)}
        title="Перенести запись"
      >
        <div className="flex flex-col gap-3">
          <div className="flex gap-2">
            <Input
              label="Дата"
              type="date"
              value={rescheduleDate}
              onChange={(e) => setRescheduleDate(e.target.value)}
            />
            <Input
              label="Время"
              type="time"
              value={rescheduleTime}
              onChange={(e) => setRescheduleTime(e.target.value)}
            />
          </div>
          {rescheduleError && (
            <p className="text-clay text-sm">{rescheduleError}</p>
          )}
          <div className="flex gap-2 pt-2">
            <Button onClick={submitReschedule} disabled={reschedule.isPending}>
              {reschedule.isPending ? '...' : 'Перенести'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setRescheduleOpen(false)}
              disabled={reschedule.isPending}
            >
              Отмена
            </Button>
          </div>
        </div>
      </Sheet>
    </div>
  );
}
