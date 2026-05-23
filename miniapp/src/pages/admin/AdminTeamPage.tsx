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

function roleLabel(role: string): string {
  if (role === 'admin') return 'Администратор';
  if (role === 'superadmin') return 'Главный администратор';
  if (role === 'staff') return 'Сотрудник';
  return role;
}

async function copyText(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* fall through */
  }
  // Fallback for iOS Telegram WebView lacking clipboard API.
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
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
                  <div className="flex flex-col gap-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="text-ink font-semibold">
                          {roleLabel(i.role)}
                        </div>
                        <div className="text-sienna-deep text-xs">
                          создано {fmtDate(i.created_at)} · истекает {fmtDate(i.expires_at)}
                        </div>
                      </div>
                      <Badge tone={i.role === 'admin' || i.role === 'superadmin' ? 'rose' : 'sage'}>
                        {i.role}
                      </Badge>
                    </div>
                    <div className="rounded-2xl bg-cream border border-sand p-2.5 text-xs text-ink font-mono break-all">
                      {i.url}
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      <Button
                        size="md"
                        variant="secondary"
                        onClick={async () => {
                          const ok = await copyText(i.url);
                          pushToast(
                            ok ? 'success' : 'error',
                            ok ? 'Ссылка скопирована' : 'Не удалось скопировать',
                          );
                        }}
                      >
                        Скопировать
                      </Button>
                      <Button variant="ghost" onClick={() => handleRevoke(i.id)}>
                        Отозвать
                      </Button>
                    </div>
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
