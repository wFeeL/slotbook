import { useNavigate, useParams } from 'react-router';
import { useMyBookings } from '@/entities/booking/api';
import { useServices } from '@/entities/service/api';
import { useStaffForService } from '@/entities/staff/api';
import { useCancelWithConfirm } from '@/features/cancel-booking/useCancelWithConfirm';
import { useBackButton } from '@/shared/telegram/hooks';
import { Blob } from '@/shared/ui/Blob';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { formatLocalDate, formatLocalTime, formatLocalWeekday } from '@/shared/lib/date';
import type { BookingRead } from '@/shared/api/types';

const CANCELLABLE = new Set<BookingRead['status']>(['pending', 'confirmed']);

export function BookingDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const bookings = useMyBookings();
  const services = useServices();
  const cancel = useCancelWithConfirm();

  useBackButton(() => navigate('/my-bookings'));

  const booking = bookings.data?.find((b) => String(b.id) === id);
  const service = services.data?.find((s) => s.id === booking?.service_id);
  const staff = useStaffForService(booking?.service_id ?? null);
  const member = staff.data?.find((s) => s.id === booking?.staff_id);

  if (bookings.isLoading) {
    return <div className="p-6 text-sienna">Загружаем...</div>;
  }

  if (!booking) {
    return (
      <div className="p-6 flex flex-col gap-4">
        <p className="text-sienna">Запись не найдена.</p>
        <Button onClick={() => navigate('/my-bookings')}>К списку</Button>
      </div>
    );
  }

  async function handleCancel() {
    const ok = await cancel.execute(booking!.id);
    if (ok) navigate('/my-bookings');
  }

  const isActive = CANCELLABLE.has(booking.status);
  const startsInPast = new Date(booking.starts_at) < new Date();

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blob variant="sand" size={55} className="-top-20 -left-12" />
      <div
        className="relative px-5 pt-8 pb-8 max-w-md mx-auto"
        style={{ animation: 'fade-up 320ms ease-out both' }}
      >
        <header className="mb-6">
          <span className="text-sienna text-sm font-semibold uppercase">
            Запись № {booking.id}
          </span>
          <h1 className="text-2xl text-ink font-display mt-1">
            {formatLocalWeekday(booking.starts_at).charAt(0).toUpperCase() +
              formatLocalWeekday(booking.starts_at).slice(1)}
            , {formatLocalDate(booking.starts_at)}
          </h1>
          <p className="text-sienna text-base mt-2 tabular-nums">
            {formatLocalTime(booking.starts_at)}
          </p>
        </header>

        <Card surface="sand" className="mb-4">
          <dl className="flex flex-col gap-3">
            <Row label="Услуга" value={service?.title ?? '...'} />
            <Row label="Специалист" value={member?.name ?? '...'} />
            {booking.client_comment && (
              <Row label="Комментарий" value={booking.client_comment} />
            )}
          </dl>
        </Card>

        {isActive && !startsInPast && (
          <div className="flex flex-col gap-3">
            <Button
              variant="secondary"
              className="w-full"
              onClick={() => navigate(`/my-bookings/${booking.id}/reschedule`)}
            >
              Перенести
            </Button>
            <Button
              variant="secondary"
              className="w-full text-clay border-clay/30"
              onClick={handleCancel}
              disabled={cancel.isPending}
            >
              {cancel.isPending ? 'Отменяем...' : 'Отменить запись'}
            </Button>
          </div>
        )}

        {!isActive && (
          <p className="text-sienna text-sm text-center mt-4">
            Эта запись больше не активна.
          </p>
        )}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 items-baseline">
      <dt className="text-sienna text-sm">{label}</dt>
      <dd className="text-ink font-semibold text-right break-words max-w-[60%]">{value}</dd>
    </div>
  );
}
