import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';
import { useCreateBooking } from '@/entities/booking/api';
import { useServices } from '@/entities/service/api';
import { useStaffForService } from '@/entities/staff/api';
import { useBookingFlowStore } from '@/shared/store/booking-flow-store';
import { useHaptic, useBackButton, useMainButton } from '@/shared/telegram/hooks';
import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import {
  formatDuration,
  formatLocalDate,
  formatLocalTime,
  formatLocalWeekday,
  formatPrice,
} from '@/shared/lib/date';
import { ApiError } from '@/shared/api/client';
import { getWebApp } from '@/shared/telegram/webapp';

export function ConfirmStep() {
  const navigate = useNavigate();
  const { serviceId, staffId, startsAt, comment, setComment } = useBookingFlowStore();
  const haptic = useHaptic();
  const services = useServices();
  const staff = useStaffForService(serviceId);
  const createBooking = useCreateBooking();
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const slotTakenTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useBackButton(() => navigate('/book/time'));

  useEffect(() => {
    if (!serviceId) navigate('/book/service', { replace: true });
    else if (!staffId) navigate('/book/staff', { replace: true });
    else if (!startsAt) navigate('/book/time', { replace: true });
  }, [serviceId, staffId, startsAt, navigate]);

  useEffect(() => () => {
    if (slotTakenTimerRef.current) clearTimeout(slotTakenTimerRef.current);
  }, []);

  const service = services.data?.find((s) => s.id === serviceId);
  const member = staff.data?.find((s) => s.id === staffId);

  async function handleConfirm() {
    if (!serviceId || !staffId || !startsAt) return;
    setErrorBanner(null);
    try {
      const booking = await createBooking.mutateAsync({
        service_id: serviceId,
        staff_id: staffId,
        starts_at: startsAt,
        client_comment: comment.trim() || null,
      });
      haptic.success();
      // Navigate first; BookingSuccessPage will call reset() on mount to avoid
      // triggering the guard-effects in still-mounted booking-flow steps.
      navigate(`/book/success/${booking.id}`);
    } catch (err) {
      haptic.error();
      if (err instanceof ApiError) {
        setErrorBanner(err.message);
        if (err.code === 'slot_already_taken') {
          // Send user back to time step to pick another slot
          slotTakenTimerRef.current = setTimeout(() => navigate('/book/time'), 1200);
        }
      } else {
        setErrorBanner('Что-то пошло не так. Попробуйте ещё раз.');
      }
    }
  }

  useMainButton({
    text: createBooking.isPending ? 'Подтверждаем...' : 'Подтвердить запись',
    onClick: handleConfirm,
    visible: Boolean(startsAt),
    loading: createBooking.isPending,
  });

  if (!service || !member || !startsAt) {
    return null;
  }

  return (
    <div
      className="px-5 pt-8 pb-32 max-w-md mx-auto"
      style={{ animation: 'fade-up 320ms ease-out both' }}
    >
      <header className="mb-6">
        <span className="text-sienna text-sm font-semibold">№ 05</span>
        <h1 className="text-2xl text-ink font-display mt-1">Подтверждение</h1>
        <p className="text-sienna text-base mt-2">Проверьте детали записи</p>
      </header>

      {errorBanner && (
        <div className="mb-4 rounded-card bg-clay/10 border border-clay/30 p-4 text-clay text-sm">
          {errorBanner}
        </div>
      )}

      <Card surface="sand" className="mb-4">
        <dl className="flex flex-col gap-3">
          <Row label="Услуга" value={service.title} />
          <Row label="Специалист" value={member.name} />
          <Row
            label="Когда"
            value={`${capitalize(formatLocalWeekday(startsAt))}, ${formatLocalDate(startsAt)} · ${formatLocalTime(startsAt)}`}
          />
          <Row label="Длительность" value={formatDuration(service.duration_minutes)} />
          {service.price && <Row label="Стоимость" value={formatPrice(service.price)} />}
        </dl>
      </Card>

      <label className="block">
        <span className="text-sienna text-sm font-semibold">Комментарий (опционально)</span>
        <textarea
          rows={4}
          maxLength={1000}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Например: впервые у вас, есть пожелания..."
          className="mt-2 w-full rounded-card border border-sand bg-shell p-4 text-ink resize-none focus:border-rose focus:outline-none"
        />
        <span className="text-sienna text-xs">{comment.length}/1000</span>
      </label>

      {/* Browser preview fallback button — only shown when not inside Telegram */}
      {getWebApp() === null && (
        <div className="mt-6">
          <Button className="w-full" onClick={handleConfirm} disabled={createBooking.isPending}>
            {createBooking.isPending ? 'Подтверждаем...' : 'Подтвердить запись'}
          </Button>
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 items-baseline">
      <dt className="text-sienna text-sm">{label}</dt>
      <dd className="text-ink font-semibold text-right">{value}</dd>
    </div>
  );
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
