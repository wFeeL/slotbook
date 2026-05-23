import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router';
import { useSlotsForDay } from '@/entities/slot/api';
import { SlotChip } from '@/entities/slot/ui/SlotChip';
import { useBookingFlowStore } from '@/shared/store/booking-flow-store';
import { useHaptic, useBackButton, useMainButton } from '@/shared/telegram/hooks';
import { getWebApp } from '@/shared/telegram/webapp';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { formatLocalDate } from '@/shared/lib/date';

export function TimeStep() {
  const navigate = useNavigate();
  const { serviceId, staffId, date, startsAt, setStartsAt } = useBookingFlowStore();
  const haptic = useHaptic();
  const slots = useSlotsForDay({ serviceId, staffId, date });

  // True when running in a real browser without Telegram WebApp
  const isTg = useMemo(() => getWebApp() !== null, []);

  useBackButton(() => navigate('/book/date'));

  useEffect(() => {
    if (!date) navigate('/book/date', { replace: true });
  }, [date, navigate]);

  useMainButton({
    text: 'Далее →',
    onClick: () => navigate('/book/confirm'),
    visible: startsAt !== null,
  });

  function handleSelect(iso: string) {
    haptic.light();
    setStartsAt(iso);
  }

  return (
    <div className="px-5 pt-8 pb-32 max-w-md mx-auto" style={{ animation: 'fade-up 320ms ease-out both' }}>
      <header className="mb-6">
        <span className="text-sienna-deep text-sm font-semibold">№ 05</span>
        <h1 className="text-2xl text-ink font-display mt-1">Время</h1>
        <p className="text-sienna-deep text-base mt-2">
          {date && `Свободное время на ${formatLocalDate(`${date}T00:00:00`)}`}
        </p>
      </header>

      {slots.isLoading && (
        <div className="grid grid-cols-4 gap-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton key={i} height={56} />
          ))}
        </div>
      )}

      {slots.data && slots.data.slots.length === 0 && (
        <div className="text-sienna-deep text-center mt-12 flex flex-col gap-3 items-center">
          <p>На этот день нет свободных слотов.</p>
          <Button variant="secondary" onClick={() => navigate('/book/date')}>
            Выбрать другой день
          </Button>
        </div>
      )}

      {slots.data && slots.data.slots.length > 0 && (
        <div className="grid grid-cols-4 gap-2">
          {slots.data.slots.map((slot) => (
            <SlotChip
              key={slot.starts_at}
              startsAt={slot.starts_at}
              selected={startsAt === slot.starts_at}
              onSelect={() => handleSelect(slot.starts_at)}
            />
          ))}
        </div>
      )}

      {/* Fallback for browser preview where Telegram MainButton is unavailable */}
      {!isTg && startsAt !== null && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-cream/95 backdrop-blur border-t border-sand">
          <Button className="w-full" onClick={() => navigate('/book/confirm')}>
            Далее →
          </Button>
        </div>
      )}
    </div>
  );
}
