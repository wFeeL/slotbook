import { useNavigate } from 'react-router';
import { useMemo, useState } from 'react';
import { useMyBookings } from '@/entities/booking/api';
import { BookingCard } from '@/entities/booking/ui/BookingCard';
import { Blob } from '@/shared/ui/Blob';
import { Button } from '@/shared/ui/Button';
import { EmptyState } from '@/shared/ui/EmptyState';
import { Skeleton } from '@/shared/ui/Skeleton';
import { useBackButton } from '@/shared/telegram/hooks';
import type { BookingRead } from '@/shared/api/types';

const ACTIVE_STATUSES = new Set(['pending', 'confirmed']);

export function MyBookingsPage() {
  const navigate = useNavigate();
  const bookings = useMyBookings();
  const [showHistory, setShowHistory] = useState(false);

  useBackButton(() => navigate('/'));

  const { upcoming, history } = useMemo(() => {
    const data = bookings.data ?? [];
    const up: BookingRead[] = [];
    const hist: BookingRead[] = [];
    for (const b of data) {
      if (ACTIVE_STATUSES.has(b.status)) up.push(b);
      else hist.push(b);
    }
    up.sort((a, b) => a.starts_at.localeCompare(b.starts_at));
    hist.sort((a, b) => b.starts_at.localeCompare(a.starts_at));
    return { upcoming: up, history: hist };
  }, [bookings.data]);

  return (
    <div className="relative min-h-screen overflow-hidden">
      <Blob variant="sand" size={60} className="-top-24 -right-16" />

      <div className="relative px-5 pt-8 pb-8 max-w-md mx-auto">
        <header className="mb-6" style={{ animation: 'fade-up 320ms ease-out both' }}>
          <h1 className="text-2xl text-ink font-display">
            Ваши записи <span className="text-rose">✦</span>
          </h1>
        </header>

        {bookings.isLoading && (
          <div className="flex flex-col gap-3">
            <Skeleton height={80} />
            <Skeleton height={80} />
          </div>
        )}

        {!bookings.isLoading && upcoming.length === 0 && history.length === 0 && (
          <EmptyState
            glyph="calendar"
            title="Пока тихо"
            description="Здесь будут ваши предстоящие встречи. Запишитесь — и здесь оживёт."
            action={<Button onClick={() => navigate('/book/branch')}>Записаться</Button>}
          />
        )}

        {upcoming.length > 0 && (
          <section className="mb-8">
            <h2 className="text-sienna-deep text-sm font-semibold uppercase mb-3 tracking-wide">
              Скоро
            </h2>
            <div className="flex flex-col gap-3">
              {upcoming.map((b) => (
                <BookingCard
                  key={b.id}
                  booking={b}
                  onSelect={() => navigate(`/my-bookings/${b.id}`)}
                />
              ))}
            </div>
          </section>
        )}

        {history.length > 0 && (
          <section>
            <button
              type="button"
              onClick={() => setShowHistory((v) => !v)}
              className="flex items-center gap-2 text-sienna-deep text-sm font-semibold uppercase mb-3 tracking-wide"
            >
              История {showHistory ? '−' : '+'}
            </button>
            {showHistory && (
              <div className="flex flex-col gap-3">
                {history.map((b) => (
                  <BookingCard
                    key={b.id}
                    booking={b}
                    onSelect={() => navigate(`/my-bookings/${b.id}`)}
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
