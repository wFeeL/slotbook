// miniapp/src/pages/admin/AdminBookingsPage.tsx
import { Link } from 'react-router';
import { useState } from 'react';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { BookingFilters, type FilterValues } from '@/features/admin-bookings/BookingFilters';
import { useAdminBookings } from '@/entities/admin-booking/api';
import { bookingStatusLabel, bookingStatusTone } from '@/entities/booking/lib/status';

function todayDateString(): string {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

export function AdminBookingsPage() {
  const [filters, setFilters] = useState<FilterValues>({
    date: todayDateString(),
    status: '',
  });

  const q = useAdminBookings({
    date: filters.date || undefined,
    status: filters.status || undefined,
    limit: 50,
  });

  return (
    <div className="pt-2 pb-6 flex flex-col gap-4">
      <header className="flex items-center justify-between">
        <h2 className="text-xl text-ink font-display">Записи</h2>
        <Link to="/admin/bookings/new">
          <Button size="md">+ Создать</Button>
        </Link>
      </header>

      <BookingFilters values={filters} onChange={setFilters} />

      {q.isLoading && <Skeleton height={80} />}
      {!q.isLoading && (q.data ?? []).length === 0 && (
        <p className="text-sienna text-sm">Нет записей по выбранным фильтрам.</p>
      )}

      <div className="flex flex-col gap-2">
        {(q.data ?? []).map((b) => (
          <Link key={b.id} to={`/admin/bookings/${b.id}`}>
            <Card interactive surface="shell">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-ink font-semibold">
                    {new Date(b.starts_at).toLocaleString('ru-RU', {
                      day: '2-digit',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                  <div className="text-sienna text-sm">
                    {b.service_title ?? `Услуга #${b.service_id}`}
                    {' · '}
                    {b.staff_name ?? `Сотрудник #${b.staff_id}`}
                  </div>
                  {b.client_first_name && (
                    <div className="text-sienna text-xs mt-0.5">
                      {b.client_first_name}
                      {b.client_last_name ? ` ${b.client_last_name}` : ''}
                    </div>
                  )}
                </div>
                <Badge tone={bookingStatusTone(b.status)}>{bookingStatusLabel(b.status)}</Badge>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
