// miniapp/src/pages/admin/AdminServicesPage.tsx
import { Link } from 'react-router';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { useAdminServices } from '@/entities/admin-service/api';

export function AdminServicesPage() {
  const q = useAdminServices();

  return (
    <div className="flex flex-col gap-4 pt-2 pb-6">
      <header className="flex items-center justify-between">
        <h2 className="text-xl text-ink font-display">Услуги</h2>
        <Link to="/admin/services/new">
          <Button size="md" variant="primary">
            + Добавить
          </Button>
        </Link>
      </header>

      {q.isLoading && <Skeleton height={80} />}
      {!q.isLoading && (q.data ?? []).length === 0 && (
        <p className="text-sienna-deep text-sm">Пока нет услуг.</p>
      )}
      <div className="flex flex-col gap-2">
        {(q.data ?? []).map((s) => (
          <Link key={s.id} to={`/admin/services/${s.id}/edit`}>
            <Card interactive surface="shell">
              <div className="flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="text-ink font-semibold">{s.title}</div>
                  <div className="text-sienna-deep text-sm">
                    {s.duration_minutes} мин · {s.price ?? '—'} ₽
                  </div>
                </div>
                {!s.is_active && <Badge tone="clay">Архив</Badge>}
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
