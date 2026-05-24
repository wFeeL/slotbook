import { useMemo, useState } from 'react';
import { Link } from 'react-router';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Badge } from '@/shared/ui/Badge';
import { useAdminBookings } from '@/entities/admin-booking/api';
import { useAdminStaff } from '@/entities/admin-staff/api';
import { cn } from '@/shared/lib/cn';
import { bookingStatusLabel, bookingStatusTone } from '@/entities/booking/lib/status';
import type { BookingStatus } from '@/shared/api/types';

function startOfWeek(d: Date): Date {
  const x = new Date(d);
  const day = (x.getDay() + 6) % 7; // 0 = Monday
  x.setDate(x.getDate() - day);
  x.setHours(0, 0, 0, 0);
  return x;
}

function fmtDateYMD(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

type CalendarBooking = {
  id: number;
  starts_at: string;
  ends_at: string;
  status: string;
  service_id: number;
  staff_id: number;
  service_title?: string | null;
  staff_name?: string | null;
};

export function AdminCalendarPage() {
  const [anchor, setAnchor] = useState<Date>(() => startOfWeek(new Date()));
  const [staffId, setStaffId] = useState<number | null>(null);
  const weekStart = fmtDateYMD(anchor);
  const q = useAdminBookings({
    week_start: weekStart,
    staff_id: staffId ?? undefined,
    limit: 200,
  });
  const staffQ = useAdminStaff();

  const days = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(anchor);
      d.setDate(anchor.getDate() + i);
      return d;
    });
  }, [anchor]);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const bookingsByDay = useMemo(() => {
    const map = new Map<string, CalendarBooking[]>();
    for (const d of days) map.set(fmtDateYMD(d), []);
    for (const b of q.data ?? []) {
      const key = b.starts_at.slice(0, 10);
      const arr = map.get(key);
      if (arr) arr.push(b as CalendarBooking);
    }
    return map;
  }, [q.data, days]);

  function shiftWeek(direction: -1 | 1) {
    const next = new Date(anchor);
    next.setDate(anchor.getDate() + direction * 7);
    setAnchor(next);
  }

  const headerLabel = `${anchor.getDate()}–${days[6].getDate()} ${anchor.toLocaleDateString('ru-RU', { month: 'long' })}`;

  return (
    <div className="pt-2 pb-6 flex flex-col gap-3">
      <header className="flex items-center justify-between gap-2">
        <button
          type="button"
          aria-label="Предыдущая неделя"
          onClick={() => shiftWeek(-1)}
          className="w-12 h-12 rounded-full bg-shell border border-sand text-ink text-2xl flex items-center justify-center active:scale-95 transition shadow-sm"
        >
          ‹
        </button>
        <h2 className="text-xl text-ink font-display flex-1 text-center">{headerLabel}</h2>
        <button
          type="button"
          aria-label="Следующая неделя"
          onClick={() => shiftWeek(1)}
          className="w-12 h-12 rounded-full bg-shell border border-sand text-ink text-2xl flex items-center justify-center active:scale-95 transition shadow-sm"
        >
          ›
        </button>
      </header>

      <div className="flex gap-2 overflow-x-auto no-scrollbar -mx-5 px-5 pb-1">
        <button
          type="button"
          onClick={() => setStaffId(null)}
          className={cn(
            'rounded-full px-3 py-1 text-sm font-semibold whitespace-nowrap',
            staffId === null
              ? 'bg-rose text-shell'
              : 'bg-shell border border-sand text-sienna-deep',
          )}
        >
          Все
        </button>
        {(staffQ.data ?? []).map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setStaffId(s.id)}
            className={cn(
              'rounded-full px-3 py-1 text-sm font-semibold whitespace-nowrap',
              staffId === s.id
                ? 'bg-rose text-shell'
                : 'bg-shell border border-sand text-sienna-deep',
            )}
          >
            {s.name}
          </button>
        ))}
      </div>

      {q.isLoading && <Skeleton height={120} />}

      <div className="flex flex-col gap-3">
        {days.map((d) => {
          const key = fmtDateYMD(d);
          const dayBookings = bookingsByDay.get(key) ?? [];
          const isToday = d.getTime() === today.getTime();
          return (
            <section
              key={key}
              className={cn('flex flex-col gap-2', isToday && 'border-l-2 border-rose pl-2')}
            >
              <div
                className={cn(
                  'text-sienna-deep text-xs font-semibold uppercase tracking-wide',
                  isToday && 'text-rose',
                )}
              >
                {WEEKDAYS[(d.getDay() + 6) % 7]} · {d.getDate()}
              </div>
              {dayBookings.length === 0 ? (
                <div className="text-sienna-deep/60 text-xs italic">Нет записей</div>
              ) : (
                [...dayBookings]
                  .sort((a, b) => a.starts_at.localeCompare(b.starts_at))
                  .map((b) => (
                    <Link key={b.id} to={`/admin/bookings/${b.id}`}>
                      <Card interactive surface="shell">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <div className="text-ink font-semibold">
                              {new Date(b.starts_at).toLocaleTimeString('ru-RU', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                              {' – '}
                              {new Date(b.ends_at).toLocaleTimeString('ru-RU', {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </div>
                            <div className="text-sienna-deep text-xs">
                              {b.service_title ?? `Услуга #${b.service_id}`}
                              {' · '}
                              {b.staff_name ?? `Сотрудник #${b.staff_id}`}
                            </div>
                          </div>
                          <Badge tone={bookingStatusTone(b.status as BookingStatus)}>
                            {bookingStatusLabel(b.status as BookingStatus)}
                          </Badge>
                        </div>
                      </Card>
                    </Link>
                  ))
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
