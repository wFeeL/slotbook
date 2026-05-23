import { useState } from 'react';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { useRevokeInvite, useTeam } from '@/entities/admin-team/api';
import { InviteSheet } from '@/features/admin-team/InviteSheet';
import { pushToast } from '@/shared/store/toast-store';
import { showConfirm } from '@/shared/telegram/hooks';

function fmtDate(s: string): string {
  return new Date(s).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
}

export function AdminTeamPage() {
  const q = useTeam();
  const revoke = useRevokeInvite();
  const [open, setOpen] = useState(false);

  async function handleRevoke(id: number) {
    const ok = await showConfirm('Отозвать приглашение?');
    if (!ok) return;
    try {
      await revoke.mutateAsync(id);
      pushToast('success', 'Приглашение отозвано');
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  return (
    <div className="pt-2 pb-6 flex flex-col gap-4">
      <header className="flex items-center justify-between">
        <h2 className="text-xl text-ink font-display">Команда</h2>
        <Button size="md" onClick={() => setOpen(true)}>
          + Пригласить
        </Button>
      </header>

      {q.isLoading && <Skeleton height={120} />}
      {q.data && (
        <>
          <section className="flex flex-col gap-2">
            <h3 className="text-sienna-deep text-xs uppercase tracking-wide">Участники</h3>
            {q.data.members.length === 0 && (
              <p className="text-sienna-deep text-sm">Пока пусто.</p>
            )}
            {q.data.members.map((m) => (
              <Card key={m.id} surface="shell">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-ink font-semibold">
                      {m.first_name ?? '—'} {m.last_name ?? ''}
                      {m.username && (
                        <span className="text-sienna-deep text-sm"> @{m.username}</span>
                      )}
                    </div>
                    <div className="text-sienna-deep text-xs">
                      TG: {m.telegram_id} · с {fmtDate(m.created_at)}
                    </div>
                  </div>
                  <Badge
                    tone={m.role === 'admin' || m.role === 'superadmin' ? 'rose' : 'sage'}
                  >
                    {m.role}
                  </Badge>
                </div>
              </Card>
            ))}
          </section>

          {q.data.invites.length > 0 && (
            <section className="flex flex-col gap-2">
              <h3 className="text-sienna-deep text-xs uppercase tracking-wide">
                Активные приглашения
              </h3>
              {q.data.invites.map((i) => (
                <Card key={i.id} surface="shell">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="text-ink font-semibold">{i.role}</div>
                      <div className="text-sienna-deep text-xs">
                        истекает {fmtDate(i.expires_at)}
                      </div>
                      <div className="text-sienna-deep text-xs truncate">{i.url}</div>
                    </div>
                    <Button variant="ghost" onClick={() => handleRevoke(i.id)}>
                      Отозвать
                    </Button>
                  </div>
                </Card>
              ))}
            </section>
          )}
        </>
      )}

      <InviteSheet open={open} onClose={() => setOpen(false)} />
    </div>
  );
}
