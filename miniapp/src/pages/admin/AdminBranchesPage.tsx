import { Link } from 'react-router';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { useAdminBranches } from '@/entities/admin-branch/api';

export function AdminBranchesPage() {
  const q = useAdminBranches();

  return (
    <div className="flex flex-col gap-4 pt-2 pb-6">
      <header className="flex items-center justify-between">
        <h2 className="text-xl text-ink font-display">Филиалы</h2>
        <Link to="/admin/branches/new">
          <Button size="md" variant="primary">
            + Добавить
          </Button>
        </Link>
      </header>

      {q.isLoading && <Skeleton height={80} />}
      {!q.isLoading && (q.data ?? []).length === 0 && (
        <p className="text-sienna text-sm">Пока нет филиалов.</p>
      )}
      <div className="flex flex-col gap-2">
        {(q.data ?? []).map((b) => (
          <Link key={b.id} to={`/admin/branches/${b.id}/edit`}>
            <Card interactive surface="shell">
              <div className="flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="text-ink font-semibold">{b.name}</div>
                  <div className="text-sienna text-sm">
                    {b.address ?? '—'} · {b.timezone}
                  </div>
                </div>
                {!b.is_active && <Badge tone="clay">Архив</Badge>}
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
