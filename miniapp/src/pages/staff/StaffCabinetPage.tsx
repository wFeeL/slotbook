import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router';
import { Badge } from '@/shared/ui/Badge';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { EmptyState } from '@/shared/ui/EmptyState';
import { Skeleton } from '@/shared/ui/Skeleton';
import {
  useCancelMyBooking,
  useMyBookings,
  useMySchedule,
  useMyStatistics,
  useMyWorkingHours,
  useReplaceMyWorkingHours,
  useStaffMe,
  useUpdateMyBooking,
} from '@/entities/staff-me/api';
import type { StatisticsPeriodT } from '@/shared/api/types';
import { pushToast } from '@/shared/store/toast-store';
import { showConfirm } from '@/shared/telegram/hooks';
import { bookingStatusLabel, bookingStatusTone } from '@/entities/booking/lib/status';
import { WorkingHoursEditor } from '@/features/admin-staff/WorkingHoursEditor';
import { StaffExceptionsEditor } from '@/features/staff-schedule/StaffExceptionsEditor';
import { cn } from '@/shared/lib/cn';
import type { WorkingHoursEntry } from '@/shared/api/types';
import type { StaffBookingRead } from '@/entities/staff-me/model';

type Tab = 'today' | 'week' | 'schedule' | 'stats';

const STAT_PERIODS: { value: StatisticsPeriodT; label: string }[] = [
  { value: '7d', label: '7 дней' },
  { value: '30d', label: '30 дней' },
  { value: '90d', label: '90 дней' },
  { value: '365d', label: 'Год' },
];

function todayLocalISO(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function currentMondayISO(): string {
  const d = new Date();
  const dow = (d.getDay() + 6) % 7; // Monday = 0
  d.setDate(d.getDate() - dow);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function fmtTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function fmtDayHeader(iso: string): string {
  return new Date(iso).toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
  });
}

const EXCEPTION_LABELS: Record<string, string> = {
  day_off: 'Выходной',
  extra_working_time: 'Доп. часы',
  blocked_time: 'Заблокировано',
};

export function StaffCabinetPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('today');
  const me = useStaffMe();
  const today = useMemo(todayLocalISO, []);
  const todays = useMyBookings({ date: today });
  const updateBooking = useUpdateMyBooking();
  const cancelBooking = useCancelMyBooking();

  const [weekStart, setWeekStart] = useState<string>(() => currentMondayISO());
  const schedule = useMySchedule(weekStart);
  const workingHours = useMyWorkingHours();
  const replaceWH = useReplaceMyWorkingHours();
  const [editHours, setEditHours] = useState(false);
  const [statsPeriod, setStatsPeriod] = useState<StatisticsPeriodT>('30d');
  const stats = useMyStatistics(statsPeriod);

  function shiftWeek(deltaDays: number) {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + deltaDays);
    setWeekStart(d.toISOString().slice(0, 10));
  }

  async function saveHours(entries: WorkingHoursEntry[]) {
    try {
      await replaceWH.mutateAsync(entries);
      pushToast('success', 'Часы обновлены');
      setEditHours(false);
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function mark(b: StaffBookingRead, status: 'completed' | 'no_show') {
    const ok = await showConfirm(
      status === 'completed'
        ? 'Отметить запись завершённой?'
        : 'Отметить, что клиент не пришёл?',
    );
    if (!ok) return;
    try {
      await updateBooking.mutateAsync({ id: b.id, status });
      pushToast('success', 'Статус обновлён');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function cancel(b: StaffBookingRead) {
    const ok = await showConfirm('Отменить эту запись? Клиент получит уведомление.');
    if (!ok) return;
    try {
      await cancelBooking.mutateAsync(b.id);
      pushToast('success', 'Запись отменена');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  return (
    <div className="pt-2 pb-6 px-5 max-w-md mx-auto flex flex-col gap-4">
      <header className="flex flex-col gap-1">
        <button
          type="button"
          className="self-start text-sienna-deep text-sm"
          onClick={() => navigate('/')}
        >
          ← На главную
        </button>
        <h1 className="text-xl text-ink font-display">Кабинет мастера</h1>
        {me.data?.staff && (
          <p className="text-sienna-deep text-sm">{me.data.staff.name}</p>
        )}
      </header>

      <nav className="flex gap-2 overflow-x-auto no-scrollbar -mx-5 px-5">
        {(['today', 'week', 'schedule', 'stats'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={cn(
              'rounded-full px-3 py-1 text-sm font-semibold whitespace-nowrap',
              tab === t
                ? 'bg-rose text-shell'
                : 'bg-shell border border-sand text-sienna-deep',
            )}
          >
            {t === 'today'
              ? 'Сегодня'
              : t === 'week'
                ? 'Неделя'
                : t === 'schedule'
                  ? 'Расписание'
                  : 'Статистика'}
          </button>
        ))}
      </nav>

      {tab === 'today' && (
        <section className="flex flex-col gap-2">
          {todays.isLoading && <Skeleton height={120} />}
          {todays.data && todays.data.length === 0 && (
            <EmptyState
              title="На сегодня пусто"
              description="Свободный день — отдохните."
              glyph="leaf"
            />
          )}
          {todays.data?.map((b) => (
            <Card key={b.id} surface="shell">
              <div className="flex flex-col gap-2">
                <button
                  type="button"
                  onClick={() => navigate(`/me/bookings/${b.id}`)}
                  className="flex items-center justify-between gap-2 text-left"
                >
                  <div className="text-ink font-semibold">
                    {fmtTime(b.starts_at)} — {fmtTime(b.ends_at)}
                  </div>
                  <Badge tone={bookingStatusTone(b.status)}>
                    {bookingStatusLabel(b.status)}
                  </Badge>
                </button>
                <div className="text-ink">{b.service_title}</div>
                <div className="text-sienna-deep text-sm">
                  {b.client_first_name ?? 'Клиент'}
                  {b.client_username && ` · @${b.client_username}`}
                </div>
                {b.client_phone && (
                  <a
                    href={`tel:${b.client_phone}`}
                    className="text-rose text-sm font-semibold"
                  >
                    📞 {b.client_phone}
                  </a>
                )}
                {b.client_comment && (
                  <div className="text-sienna-deep text-sm italic">
                    «{b.client_comment}»
                  </div>
                )}
                {(b.status === 'pending' || b.status === 'confirmed') && (
                  <div className="flex gap-2 pt-1 flex-wrap">
                    <Button size="md" onClick={() => mark(b, 'completed')}>
                      Завершить
                    </Button>
                    <Button
                      size="md"
                      variant="secondary"
                      onClick={() => mark(b, 'no_show')}
                    >
                      Не пришёл
                    </Button>
                    <Button
                      size="md"
                      variant="secondary"
                      onClick={() => navigate(`/me/bookings/${b.id}/reschedule`)}
                    >
                      Перенести
                    </Button>
                    <Button size="md" variant="ghost" onClick={() => cancel(b)}>
                      Отменить
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </section>
      )}

      {tab === 'week' && (
        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between gap-2">
            <Button size="md" variant="secondary" onClick={() => shiftWeek(-7)}>
              ← Назад
            </Button>
            <div className="text-sienna-deep text-sm">с {weekStart}</div>
            <Button size="md" variant="secondary" onClick={() => shiftWeek(7)}>
              Вперёд →
            </Button>
          </div>
          {schedule.isLoading && <Skeleton height={200} />}
          {schedule.data?.days.map((day) => (
            <Card key={day.date} surface="shell">
              <div className="flex flex-col gap-2">
                <div className="text-ink font-semibold capitalize">
                  {fmtDayHeader(day.date)}
                </div>
                {day.bookings.length === 0 && (
                  <div className="text-sienna-deep text-sm">Свободный день</div>
                )}
                {day.bookings.map((b) => (
                  <button
                    key={b.id}
                    type="button"
                    onClick={() => navigate(`/me/bookings/${b.id}`)}
                    className="flex items-center justify-between gap-2 text-sm text-left active:scale-[0.99]"
                  >
                    <span className="text-ink">
                      {fmtTime(b.starts_at)} — {b.service_title}
                    </span>
                    <span className="text-sienna-deep">
                      {b.client_first_name ?? 'Клиент'}
                    </span>
                  </button>
                ))}
              </div>
            </Card>
          ))}
        </section>
      )}

      {tab === 'stats' && (
        <section className="flex flex-col gap-3">
          <div className="flex gap-2 overflow-x-auto no-scrollbar -mx-5 px-5">
            {STAT_PERIODS.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => setStatsPeriod(p.value)}
                className={cn(
                  'rounded-full px-3 py-1 text-sm font-semibold whitespace-nowrap',
                  statsPeriod === p.value
                    ? 'bg-rose text-shell'
                    : 'bg-shell border border-sand text-sienna-deep',
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
          {stats.isLoading && <Skeleton height={120} />}
          {stats.data && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <Card surface="shell">
                  <div className="text-sienna-deep text-xs uppercase">Выручка</div>
                  <div className="text-2xl text-ink font-display">{stats.data.revenue} ₽</div>
                </Card>
                <Card surface="shell">
                  <div className="text-sienna-deep text-xs uppercase">Всего записей</div>
                  <div className="text-2xl text-ink font-display">{stats.data.total_bookings}</div>
                </Card>
                <Card surface="shell">
                  <div className="text-sienna-deep text-xs uppercase">Завершено</div>
                  <div className="text-2xl text-ink font-display">{stats.data.completed_count}</div>
                </Card>
                <Card surface="shell">
                  <div className="text-sienna-deep text-xs uppercase">Не пришли</div>
                  <div className="text-2xl text-ink font-display">{stats.data.no_show_count}</div>
                </Card>
              </div>
              {stats.data.top_services.length > 0 && (
                <Card surface="shell">
                  <div className="text-sienna-deep text-xs uppercase mb-2">Топ услуг</div>
                  <div className="flex flex-col gap-1">
                    {stats.data.top_services.map((s) => (
                      <div key={s.service_id} className="flex justify-between text-sm">
                        <span className="text-ink">{s.service_title}</span>
                        <span className="text-sienna-deep">{s.completed_count}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}
        </section>
      )}

      {tab === 'schedule' && (
        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sienna-deep text-xs uppercase tracking-wide">
              Рабочие часы по дням недели
            </h3>
            {!editHours && (
              <button
                type="button"
                className="text-rose text-sm font-semibold"
                onClick={() => setEditHours(true)}
              >
                Изменить
              </button>
            )}
          </div>
          {workingHours.isLoading && <Skeleton height={120} />}
          {editHours ? (
            <WorkingHoursEditor
              initial={workingHours.data ?? []}
              onSave={saveHours}
              saving={replaceWH.isPending}
            />
          ) : (
            <>
              {schedule.data?.days.map((day) => (
                <Card key={day.date} surface="shell">
                  <div className="flex flex-col gap-1">
                    <div className="text-ink font-semibold capitalize">
                      {fmtDayHeader(day.date)}
                    </div>
                    {day.working_intervals.length === 0 ? (
                      <div className="text-sienna-deep text-sm">Выходной</div>
                    ) : (
                      <div className="text-ink text-sm">
                        {day.working_intervals
                          .map(
                            (i) =>
                              `${i.start_time.slice(0, 5)}–${i.end_time.slice(0, 5)}`,
                          )
                          .join(', ')}
                      </div>
                    )}
                    {day.exceptions.length > 0 && (
                      <div className="text-rose text-xs">
                        {day.exceptions
                          .map((e) => {
                            const label = EXCEPTION_LABELS[e.type] ?? e.type;
                            return e.reason ? `${label}: ${e.reason}` : label;
                          })
                          .join(' • ')}
                      </div>
                    )}
                  </div>
                </Card>
              ))}
              {schedule.data && (
                <StaffExceptionsEditor days={schedule.data.days} />
              )}
            </>
          )}
        </section>
      )}
    </div>
  );
}
