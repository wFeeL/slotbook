import { useState } from 'react';
import { Card } from '@/shared/ui/Card';
import { Skeleton } from '@/shared/ui/Skeleton';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Sheet } from '@/shared/ui/Sheet';
import { Select } from '@/shared/ui/Select';
import {
  useRemoveMember,
  useRevokeInvite,
  useSetMemberRole,
  useTeam,
} from '@/entities/admin-team/api';
import { InviteSheet } from '@/features/admin-team/InviteSheet';
import { pushToast } from '@/shared/store/toast-store';
import { showConfirm } from '@/shared/telegram/hooks';
import { useAuthStore } from '@/shared/store/auth-store';

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
  const setRole = useSetMemberRole();
  const removeMember = useRemoveMember();
  const [open, setOpen] = useState(false);
  const [roleSheetUserId, setRoleSheetUserId] = useState<number | null>(null);
  const [roleDraft, setRoleDraft] = useState<'admin' | 'staff' | 'client'>('staff');
  const currentUserId = useAuthStore((s) => s.user?.id ?? null);

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

  function openRoleSheet(userId: number, role: string) {
    setRoleSheetUserId(userId);
    setRoleDraft(role === 'admin' || role === 'staff' || role === 'client' ? role : 'staff');
  }

  async function saveRole() {
    if (roleSheetUserId === null) return;
    try {
      await setRole.mutateAsync({ userId: roleSheetUserId, role: roleDraft });
      pushToast('success', 'Роль обновлена');
      setRoleSheetUserId(null);
    } catch (e) {
      pushToast('error', e instanceof Error ? e.message : 'Не удалось');
    }
  }

  async function handleRemove(userId: number, name: string) {
    const ok = await showConfirm(`Удалить ${name} из команды?`);
    if (!ok) return;
    try {
      await removeMember.mutateAsync(userId);
      pushToast('success', 'Удалён из команды');
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
            {q.data.members.map((m) => {
              const isSelf = m.id === currentUserId;
              const isProtected = m.role === 'superadmin' || isSelf;
              const displayName =
                [m.first_name, m.last_name].filter(Boolean).join(' ') || `TG ${m.telegram_id}`;
              return (
                <Card key={m.id} surface="shell">
                  <div className="flex flex-col gap-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="text-ink font-semibold">
                          {displayName}
                          {m.username && (
                            <span className="text-sienna-deep text-sm">
                              {' '}
                              @{m.username}
                            </span>
                          )}
                          {isSelf && (
                            <span className="text-rose text-xs ml-2">вы</span>
                          )}
                        </div>
                        <div className="text-sienna-deep text-xs">
                          {roleLabel(m.role)} · с {fmtDate(m.created_at)}
                        </div>
                      </div>
                      <Badge
                        tone={
                          m.role === 'admin' || m.role === 'superadmin' ? 'rose' : 'sage'
                        }
                      >
                        {roleLabel(m.role)}
                      </Badge>
                    </div>
                    {!isProtected && (
                      <div className="flex gap-2 flex-wrap">
                        <Button
                          size="md"
                          variant="secondary"
                          onClick={() => openRoleSheet(m.id, m.role)}
                        >
                          Изменить роль
                        </Button>
                        <Button
                          variant="ghost"
                          onClick={() => handleRemove(m.id, displayName)}
                        >
                          Удалить
                        </Button>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
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

      <Sheet
        open={roleSheetUserId !== null}
        onClose={() => setRoleSheetUserId(null)}
        title="Новая роль"
      >
        <div className="flex flex-col gap-3">
          <Select
            label="Роль"
            value={roleDraft}
            onChange={(e) =>
              setRoleDraft(e.target.value as 'admin' | 'staff' | 'client')
            }
          >
            <option value="admin">Администратор</option>
            <option value="staff">Сотрудник</option>
            <option value="client">Клиент</option>
          </Select>
          <p className="text-sienna-deep text-xs">
            Понижение из «Сотрудника» снимет связь с записью мастера.
          </p>
          <div className="flex gap-2">
            <Button onClick={saveRole} disabled={setRole.isPending}>
              Сохранить
            </Button>
            <Button variant="secondary" onClick={() => setRoleSheetUserId(null)}>
              Отмена
            </Button>
          </div>
        </div>
      </Sheet>
    </div>
  );
}
