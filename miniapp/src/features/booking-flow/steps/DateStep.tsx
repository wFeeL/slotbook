import { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { format, addDays } from 'date-fns';
import { useBookingFlowStore } from '@/shared/store/booking-flow-store';
import { useHaptic, useBackButton } from '@/shared/telegram/hooks';
import { cn } from '@/shared/lib/cn';
import { formatDayLabelShort } from '@/shared/lib/date';

const DAYS_AHEAD = 14;

export function DateStep() {
  const navigate = useNavigate();
  const { serviceId, staffId, date, setDate } = useBookingFlowStore();
  const haptic = useHaptic();

  useBackButton(() => navigate('/book/staff'));

  useEffect(() => {
    if (serviceId === null) {
      navigate('/book/service', { replace: true });
    } else if (staffId === null) {
      navigate('/book/staff', { replace: true });
    }
  }, [serviceId, staffId, navigate]);

  const today = new Date();
  const days = Array.from({ length: DAYS_AHEAD }, (_, i) => addDays(today, i));

  function handleSelect(iso: string) {
    haptic.light();
    setDate(iso);
    navigate('/book/time');
  }

  return (
    <div className="px-5 pt-8 pb-32 max-w-md mx-auto" style={{ animation: 'fade-up 320ms ease-out both' }}>
      <header className="mb-6">
        <span className="text-sienna text-sm font-semibold">№ 04</span>
        <h1 className="text-2xl text-ink font-display mt-1">День</h1>
        <p className="text-sienna text-base mt-2">Выберите удобный день</p>
      </header>

      <div className="-mx-5 px-5 overflow-x-auto no-scrollbar">
        <div className="flex gap-2 pb-2 min-w-max">
          {days.map((d) => {
            const iso = format(d, 'yyyy-MM-dd');
            const label = formatDayLabelShort(iso);
            const selected = date === iso;
            return (
              <button
                key={iso}
                type="button"
                onClick={() => handleSelect(iso)}
                className={cn(
                  'flex flex-col items-center justify-center w-16 py-3 rounded-card border transition active:scale-[0.97]',
                  selected
                    ? 'bg-rose text-white border-rose shadow-warm'
                    : 'bg-shell text-ink border-sand hover:bg-sand/30',
                )}
              >
                <span className={cn('text-xs uppercase', selected ? 'opacity-90' : 'text-sienna')}>
                  {label.weekday}
                </span>
                <span className="text-2xl font-display leading-none mt-1">{label.day}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
