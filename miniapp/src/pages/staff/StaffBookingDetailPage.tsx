import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { Badge } from '@/shared/ui/Badge';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Textarea } from '@/shared/ui/Textarea';
import {
  useCancelMyBooking,
  useMyBookings,
  useUpdateMyBooking,
} from '@/entities/staff-me/api';
import { pushToast } from '@/shared/store/toast-store';
import { showConfirm } from '@/shared/telegram/hooks';
import { bookingStatusLabel, bookingStatusTone } from '@/entities/booking/lib/status';
import { formatLocalDate } from '@/shared/lib/date';
import type { StaffBookingRead } from '@/entities/staff-me/model';

export function StaffBookingDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const bookingId = id ? Number(id) : null;

  // Pull all upcoming + recent — the API is paginated so we get enough by default (50).
  const bookings = useMyBookings({});
  const booking: StaffBookingRead | null = useMemo(
    () => bookings.data?.find((b) => b.id === bookingId) ?? null,
    [bookings.data, bookingId],
  );

  const update = useUpdateMyBooking();
  const cancel = useCancelMyBooking();

  const [comment, setComment] = useState<string>('');
  const [commentInited, setCommentInited] = useState(false);
  if (booking && !commentInited) {
    setComment(booking.admin_comment ?? '');
    setCommentInited(true);
  }

  if (bookings.isLoading) {
    return (
      <div className="p-5">
        <Skeleton height={200} />
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="p-5 flex flex-col gap-3">
        <p className="text-sienna-deep">Запись не найдена.</p>
        <Button onClick={() => navigate('/me')}>В кабинет</Button>
      </div>
    );
  }

  async function mark(status: 'completed' | 'no_show') {
    if (!booking) return;
    const ok = await showConfirm(
      status === 'completed'
        ? 'Отметить запись завершённой?'
        : 'Отметить, что клиент не пришёл?',
    );
    if (!ok) return;
    try {
      await update.mutateAsync({ id: booking.id, status });
      pushToast('success', 'Статус обновлён');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function saveComment() {
    if (!booking) return;
    try {
      await update.mutateAsync({ id: booking.id, admin_comment: comment || null });
      pushToast('success', 'Комментарий сохранён');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function doCancel() {
    if (!booking) return;
    const ok = await showConfirm('Отменить эту запись? Клиент получит уведомление.');
    if (!ok) return;
    try {
      await cancel.mutateAsync(booking.id);
      pushToast('success', 'Запись отменена');
      navigate('/me');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  const isActive = booking.status === 'pending' || booking.status === 'confirmed';

  return (
    <div className="pt-2 pb-6 px-5 max-w-md mx-auto flex flex-col gap-4">
      <header className="flex flex-col gap-1">
        <button
          type="button"
          className="self-start text-sienna-deep text-sm"
          onClick={() => navigate('/me')}
        >
          ← В кабинет
        </button>
        <div className="flex items-center justify-between gap-2">
          <h1 className="text-xl text-ink font-display">Запись № {booking.id}</h1>
          <Badge tone={bookingStatusTone(booking.status)}>
            {bookingStatusLabel(booking.status)}
          </Badge>
        </div>
      </header>

      <Card surface="shell">
        <div className="flex flex-col gap-2">
          <div className="text-ink font-semibold">{booking.service_title}</div>
          <div className="text-sienna-deep text-sm">
            {formatLocalDate(booking.starts_at)} · {booking.service_duration_minutes} мин
            {booking.service_price && ` · ${booking.service_price} ₽`}
          </div>
        </div>
      </Card>

      <Card surface="shell">
        <div className="flex flex-col gap-2">
          <div className="text-sienna-deep text-xs uppercase tracking-wide">Клиент</div>
          <div className="text-ink font-semibold">
            {[booking.client_first_name, booking.client_last_name]
              .filter(Boolean)
              .join(' ') || 'Клиент'}
            {booking.client_username && (
              <span className="text-sienna-deep text-sm"> @{booking.client_username}</span>
            )}
          </div>
          {booking.client_phone && (
            <a href={`tel:${booking.client_phone}`} className="text-rose text-sm font-semibold">
              📞 {booking.client_phone}
            </a>
          )}
          {booking.client_comment && (
            <div className="text-sienna-deep text-sm italic">«{booking.client_comment}»</div>
          )}
        </div>
      </Card>

      <Card surface="shell">
        <div className="flex flex-col gap-2">
          <div className="text-sienna-deep text-xs uppercase tracking-wide">
            Внутренний комментарий
          </div>
          <Textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Заметки по записи (не видны клиенту)"
          />
          <Button size="md" onClick={saveComment} disabled={update.isPending}>
            Сохранить комментарий
          </Button>
        </div>
      </Card>

      {isActive && (
        <div className="flex flex-col gap-2">
          <div className="flex gap-2 flex-wrap">
            <Button onClick={() => mark('completed')}>Завершить</Button>
            <Button variant="secondary" onClick={() => mark('no_show')}>
              Не пришёл
            </Button>
          </div>
          <Button
            variant="secondary"
            onClick={() => navigate(`/me/bookings/${booking.id}/reschedule`)}
          >
            Перенести
          </Button>
          <Button variant="ghost" onClick={doCancel}>
            Отменить запись
          </Button>
        </div>
      )}
    </div>
  );
}
