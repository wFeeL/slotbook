import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { addDays, format } from 'date-fns';
import { useMyBookings, useRescheduleMyBooking } from '@/entities/staff-me/api';
import { useSlotsForDay } from '@/entities/slot/api';
import { SlotChip } from '@/entities/slot/ui/SlotChip';
import { useAuthStore } from '@/shared/store/auth-store';
import { Blob } from '@/shared/ui/Blob';
import { Button } from '@/shared/ui/Button';
import { Skeleton } from '@/shared/ui/Skeleton';
import { formatDayLabelShort, formatLocalDate } from '@/shared/lib/date';
import { cn } from '@/shared/lib/cn';
import { pushToast } from '@/shared/store/toast-store';
import { useBackButton, useHaptic } from '@/shared/telegram/hooks';

const DAYS_AHEAD = 14;

export function StaffRescheduleWizardPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const bookingId = id ? Number(id) : null;

  const haptic = useHaptic();
  const reschedule = useRescheduleMyBooking();
  // Load all upcoming bookings of this staff (no date filter) so we can find the target.
  const bookings = useMyBookings({});

  const booking = useMemo(
    () => bookings.data?.find((b) => b.id === bookingId) ?? null,
    [bookings.data, bookingId],
  );

  const today = useMemo(() => new Date(), []);
  const days = useMemo(
    () => Array.from({ length: DAYS_AHEAD }, (_, i) => addDays(today, i)),
    [today],
  );

  const [selectedDate, setSelectedDate] = useState<string>(() => format(today, 'yyyy-MM-dd'));
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);

  // Slot picker needs staff_id; AuthGate has populated staffMe in the store.
  const staffMeStaffId = useAuthStore((s) => s.staffMe?.staff?.id ?? null);

  const slots = useSlotsForDay({
    serviceId: booking?.service_id ?? null,
    staffId: staffMeStaffId,
    date: booking ? selectedDate : null,
  });

  useBackButton(() => {
    navigate('/me');
  });

  if (bookings.isLoading) {
    return <div className="p-6 text-sienna-deep">Загружаем...</div>;
  }

  if (!booking) {
    return (
      <div className="p-6 flex flex-col gap-4">
        <p className="text-sienna-deep">Запись не найдена.</p>
        <Button onClick={() => navigate('/me')}>В кабинет</Button>
      </div>
    );
  }

  async function handleSubmit() {
    if (!selectedSlot || !booking) return;
    try {
      await reschedule.mutateAsync({ id: booking.id, starts_at: selectedSlot });
      haptic.success();
      pushToast('success', 'Запись перенесена');
      navigate('/me');
    } catch (err) {
      haptic.error();
      const message =
        err instanceof Error && err.message ? err.message : 'Не удалось перенести запись';
      pushToast('error', message);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blob variant="sand" size={55} className="-top-20 -left-12" />
      <div
        className="relative px-5 pt-8 pb-32 max-w-md mx-auto"
        style={{ animation: 'fade-up 320ms ease-out both' }}
      >
        <header className="mb-6">
          <span className="text-sienna-deep text-sm font-semibold uppercase">
            Перенос записи № {booking.id}
          </span>
          <h1 className="text-2xl text-ink font-display mt-1">Новое время</h1>
          <p className="text-sienna-deep text-base mt-2">
            Клиент: {booking.client_first_name ?? '—'}
            <br />
            Текущее: {formatLocalDate(booking.starts_at)}
          </p>
        </header>

        <section className="mb-6">
          <h2 className="text-ink font-display text-lg mb-3">День</h2>
          <div className="-mx-5 px-5 overflow-x-auto no-scrollbar">
            <div className="flex gap-2 pb-2 min-w-max">
              {days.map((d) => {
                const iso = format(d, 'yyyy-MM-dd');
                const label = formatDayLabelShort(iso);
                const selected = selectedDate === iso;
                return (
                  <button
                    key={iso}
                    type="button"
                    onClick={() => {
                      haptic.light();
                      setSelectedDate(iso);
                      setSelectedSlot(null);
                    }}
                    className={cn(
                      'flex flex-col items-center justify-center w-16 py-3 rounded-card border transition active:scale-[0.97]',
                      selected
                        ? 'bg-rose text-white border-rose shadow-warm'
                        : 'bg-shell text-ink border-sand hover:bg-sand/30',
                    )}
                  >
                    <span
                      className={cn(
                        'text-xs uppercase',
                        selected ? 'opacity-90' : 'text-sienna-deep',
                      )}
                    >
                      {label.weekday}
                    </span>
                    <span className="text-2xl font-display leading-none mt-1">{label.day}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        <section className="mb-6">
          <h2 className="text-ink font-display text-lg mb-3">Время</h2>
          {slots.isLoading && (
            <div className="grid grid-cols-4 gap-2">
              {Array.from({ length: 12 }).map((_, i) => (
                <Skeleton key={i} height={56} />
              ))}
            </div>
          )}
          {slots.data && slots.data.slots.length === 0 && (
            <p className="text-sienna-deep text-center mt-6">
              На этот день нет свободных слотов.
            </p>
          )}
          {slots.data && slots.data.slots.length > 0 && (
            <div className="grid grid-cols-4 gap-2">
              {slots.data.slots.map((slot) => (
                <SlotChip
                  key={slot.starts_at}
                  startsAt={slot.starts_at}
                  selected={selectedSlot === slot.starts_at}
                  onSelect={() => {
                    haptic.light();
                    setSelectedSlot(slot.starts_at);
                  }}
                />
              ))}
            </div>
          )}
        </section>

        <div className="fixed bottom-0 left-0 right-0 p-4 bg-cream/95 backdrop-blur border-t border-sand">
          <Button
            className="w-full"
            onClick={handleSubmit}
            disabled={!selectedSlot || reschedule.isPending}
          >
            {reschedule.isPending ? 'Переносим...' : 'Подтвердить перенос'}
          </Button>
        </div>
      </div>
    </div>
  );
}

