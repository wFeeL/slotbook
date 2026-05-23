// miniapp/src/pages/admin/AdminStaffPage.tsx
import { Link } from 'react-router';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { useAdminStaff } from '@/entities/admin-staff/api';

export function AdminStaffPage() {
  const q = useAdminStaff();

  return (
    <div className="flex flex-col gap-4 pt-2 pb-6">
      <header className="flex items-center justify-between">
        <h2 className="text-xl text-ink font-display">Сотрудники</h2>
        <Link to="/admin/staff/new">
          <Button size="md">+ Добавить</Button>
        </Link>
      </header>

      {q.isLoading && <Skeleton height={80} />}
      {!q.isLoading && (q.data ?? []).length === 0 && (
        <p className="text-sienna text-sm">Пока нет сотрудников.</p>
      )}
      <div className="flex flex-col gap-2">
        {(q.data ?? []).map((s) => (
          <Link key={s.id} to={`/admin/staff/${s.id}`}>
            <Card interactive surface="shell">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-ink font-semibold">{s.name}</div>
                  {s.description && <div className="text-sienna text-sm">{s.description}</div>}
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
