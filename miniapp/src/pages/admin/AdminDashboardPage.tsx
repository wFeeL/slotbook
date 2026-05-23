// miniapp/src/pages/admin/AdminDashboardPage.tsx
import { Link } from 'react-router';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Badge } from '@/shared/ui/Badge';
import { useAdminDashboard } from '@/entities/admin-dashboard/api';
import { useAdminBookings } from '@/entities/admin-booking/api';
import { bookingStatusLabel, bookingStatusTone } from '@/entities/booking/lib/status';

function todayDateString(): string {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

function Counter({ label, value, loading }: { label: string; value?: number; loading: boolean }) {
  return (
    <Card surface="shell">
      <div className="text-sienna text-xs font-semibold uppercase tracking-wide">{label}</div>
      <div className="text-3xl text-ink font-display mt-1">
        {loading ? <Skeleton height={32} className="w-12" /> : (value ?? 0)}
      </div>
    </Card>
  );
}

export function AdminDashboardPage() {
  const dash = useAdminDashboard();
  const today = useAdminBookings({ date: todayDateString(), limit: 10 });

  return (
    <div className="flex flex-col gap-5 pt-2 pb-6">
      <div className="grid grid-cols-3 gap-3">
        <Counter label="Сегодня" value={dash.data?.counts.today} loading={dash.isLoading} />
        <Counter label="Неделя" value={dash.data?.counts.this_week} loading={dash.isLoading} />
        <Counter label="Не пришли" value={dash.data?.counts.no_show_30d} loading={dash.isLoading} />
      </div>

      <section>
        <h2 className="text-xl text-ink font-display mb-3">Записи на сегодня</h2>
        {today.isLoading && <Skeleton height={80} />}
        {!today.isLoading && (today.data ?? []).length === 0 && (
          <p className="text-sienna text-sm">На сегодня записей нет.</p>
        )}
        <div className="flex flex-col gap-2">
          {(today.data ?? []).map((b) => (
            <Link key={b.id} to={`/admin/bookings/${b.id}`}>
              <Card interactive surface="shell">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-ink font-semibold">
                      {new Date(b.starts_at).toLocaleTimeString('ru-RU', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                    <div className="text-sienna text-sm">
                      {b.service_title ?? `Услуга #${b.service_id}`}
                      {' · '}
                      {b.staff_name ?? `Сотрудник #${b.staff_id}`}
                    </div>
                  </div>
                  <Badge tone={bookingStatusTone(b.status)}>{bookingStatusLabel(b.status)}</Badge>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <Link to="/admin/statistics">
        <Card interactive surface="shell">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-ink font-semibold">Статистика</div>
              <div className="text-sienna text-xs">Выручка, топ услуг, экспорт CSV/XLSX</div>
            </div>
            <span className="text-sienna text-xl">›</span>
          </div>
        </Card>
      </Link>

      <Link to="/admin/team">
        <Card interactive surface="shell">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-ink font-semibold">Команда</div>
              <div className="text-sienna text-xs">Участники и приглашения</div>
            </div>
            <span className="text-sienna text-xl">›</span>
          </div>
        </Card>
      </Link>

      <Link to="/admin/branches">
        <Card interactive surface="shell">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-ink font-semibold">Филиалы</div>
              <div className="text-sienna text-xs">Адреса, часовые пояса, активные точки</div>
            </div>
            <span className="text-sienna text-xl">›</span>
          </div>
        </Card>
      </Link>

      <Link to="/admin/settings">
        <Card interactive surface="shell">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-ink font-semibold">Настройки бизнеса</div>
              <div className="text-sienna text-xs">Имя, часовой пояс, шаг слотов, буфер</div>
            </div>
            <span className="text-sienna text-xl">›</span>
          </div>
        </Card>
      </Link>
    </div>
  );
}
